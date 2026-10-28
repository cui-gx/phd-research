"""B1-R1の派生表から日本語審査資料を生成する。サーバCPUでのみ使用する。"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

import numpy as np


MODES = ('ORIGINAL_HISTORY', 'COMMON_A4', 'COMMON_A2', 'MATCHED_COUNT')
ROOTS = tuple(f'r{i:02d}' for i in range(1, 9))
CONT = ('distance_mean_A', 'distance_median_A', 'distance_p90_A', 'Rg_mean_A',
        'Q8_mean', 'angle_to_geometric_neighbor_median_deg')


def read_csv(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f))


def json_read(path):
    return json.loads(Path(path).read_text())


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def table(rows, header):
    """Markdown表を生成し、元数値を手編集しない。"""
    return '\n'.join(['|'+'|'.join(header)+'|', '|'+'|'.join(['---']*len(header))+'|']+
                     ['|'+'|'.join(str(v) for v in row)+'|' for row in rows])


def number(x, digits=6):
    return f'{float(x):+.{digits}f}'


def interval(row):
    return f"{number(row['mean'])} [{number(row['bootstrap95_low'])}, {number(row['bootstrap95_high'])}]"


def finalize_delivery(out):
    """最終監査後の費用・イベント・公開索引を追記する。科学値を再計算しない。"""
    if json_read(out/'status.json')['status'] != 'COMPLETE':
        raise RuntimeError('最終不変監査の完了が必要です。')
    events = [json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
    stages = [r for r in events if r['event'] == 'stage_complete']
    generation = json_read(out/'report-generation-cost.json')
    cost = dict(status='MEASURED_AND_DERIVED', stage_costs=stages,
        stage_wall_sum_s=sum(r['wall_s'] for r in stages),
        stage_CPU_sum_s=sum(r['CPU_s'] for r in stages), report_generation=generation,
        scope='工程内wall/CPU合計と報告生成を別記。シェル起動・配備・人の待機は含まない。',
        first_execution_UTC=events[0]['UTC'], last_execution_UTC=events[-1]['UTC'],
        GPU_s=0, MD=0, training=0, model_inference=0)
    write_json(out/'delivery-costs.json', cost)
    write_json(out/'execution-events.json', events)
    failures = [r for r in events if r['event'] == 'stopped']
    write_json(out/'failures.json', dict(scientific_stops=failures,
        deployment_failures=[dict(kind='AppleDouble_manifest_mismatch',
            resolved='科学解析前にv2 allowlistからメタデータを除外し、全6実ファイルSHA一致。',
            original_scientific_data_changed=False)],
        unperformed_conditions=0, ignored_negative_results=0))
    notice = '''\n\n## 最終技術検証の追記\n\n原入力15,208ファイルと9archiveの最終SHA再照合PASS、原B1保持。CPU全工程と日本語資料生成は完了し、GitHub同期/本文回読で最終技術交付を確定する。費用はdelivery-costs.json、全イベントはexecution-events.json、失敗はfailures.json、公開ファイルはpublic-evidence-index.jsonを参照。独立科学審査・研究者科学受入れはPENDINGのまま停止する。\n'''
    for name in ('review-dossier.md', 'handoff-to-chatgpt.md'):
        with (out/name).open('a') as f:
            f.write(notice)
    allowed = ('.md', '.csv', '.json', '.png', '.txt', '.log')
    rows = []
    for path in sorted(out.iterdir()):
        if path.is_file() and path.suffix in allowed and path.name != 'public-evidence-index.json':
            rows.append(dict(path=path.name, bytes=path.stat().st_size,
                             sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    write_json(out/'public-evidence-index.json', dict(status='SERVER_GENERATED', files=rows,
        raw_arrays_included=False, original_archives_retained=True,
        scope='トップレベルの派生表・図・報告・監査。branches/distancesの完全配列はサーバ保持。'))
    print('最終交付索引と費用を保存しました。')


def main():
    """全条件を読み、固定主表示と完全索引を備えた報告を作る。"""
    p = argparse.ArgumentParser(description='B1-R1日本語報告と全尺度図の生成')
    p.add_argument('--project', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--implementation-commit', required=True)
    p.add_argument('--finalize', action='store_true')
    args = p.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise RuntimeError('GPUを不可視にしてください。')
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        if os.environ.get(name) != '1':
            raise RuntimeError('数値thread1が必須です。')
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    os.nice(10)
    start, cpu = time.perf_counter(), time.process_time()
    root, out = Path(args.project), Path(args.output)
    if args.finalize:
        finalize_delivery(out)
        return
    if (out/'review-dossier.md').exists():
        raise RuntimeError('生成済み報告を上書きしません。新しい報告版を用意してください。')
    raw = root/'runs/b1-expansion-20261026/tasks'
    summary = read_csv(out/'root-summary.csv')
    roots = read_csv(out/'root-stage-effects.csv')
    dec = read_csv(out/'reference-decomposition-summary.csv')
    pool = read_csv(out/'pool-selection-diagnostic.csv')
    origins = read_csv(out/'selected-origins.csv')
    states = read_csv(out/'state-effects.csv')
    randomness = json_read(out/'randomness-decomposition.json')
    input_audit = json_read(out/'input-audit.json')
    result_audit = json_read(out/'result-audit.json')
    lof_audit = json_read(out/'LOF-audit.json')
    events = [json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
    original_check = json_read(out/'original-reproduction.json')
    if any(x['status'] != 'PASS' for x in (input_audit, result_audit, lof_audit, original_check)):
        raise RuntimeError('完全な入力/原再現/結果/LOF監査が必要です。')
    spec = importlib.util.spec_from_file_location('frozen_r1_report_gq',
          root/'artifacts/b1-expansion-20261026/executed-source/p1/server/gq_r2.py')
    gq = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gq)

    def is_main(r):
        return float(r['burn_ps']) == 100 and float(r['prefix_ns']) == 4

    def key(r):
        return (r['metric'], float(r['epsilon_A']) if r['epsilon_A'] not in ('', None) else None,
                float(r['tau_ps']) if r['tau_ps'] not in ('', None) else None)

    main_rows = [r for r in summary if is_main(r)]
    lookup = {(r['reference_mode'], r['comparison'], r['estimand'], key(r)): r for r in main_rows}
    units = {x: 'Å' for x in CONT[:4]}
    units.update(Q8_mean='無次元', angle_to_geometric_neighbor_median_deg='度', added_regions='個')
    metrics = [(m, None, None) for m in CONT]+[('added_regions', e, t) for e in (1.5, 2., 3.) for t in (0., 5.)]
    main_metric = ('distance_mean_A', None, None)

    def metric_label(k):
        return k[0] if k[0] != 'added_regions' else f'領域 ε{k[1]:g}Å/τ{k[2]:g}ps'

    def row(mode, comp='F2-F1', estimand='STAGE_DIFFERENCE', metric=main_metric):
        return lookup[(mode, comp, estimand, metric)]

    # 同状態・同学習ブロックの選点と、実行済み下流差を結合する。
    selection_pairs = []
    paired_all = read_csv(out/'paired-effects.csv')
    paired_main = [r for r in paired_all if is_main(r) and r['metric'] == 'distance_mean_A' and r['comparison'] == 'F2-F1']
    origin_lookup = {(r['state_id'], r['label']): r for r in origins}
    for sid in [r+'-s'+str(s) for r in ROOTS for s in (4, 8)]:
        a = dict(np.load(raw/(sid+'-decision-pool')/'science/features.npz', allow_pickle=False))
        for t in (1, 2):
            f1, f2 = origin_lookup[(sid, f'F1-t{t}')], origin_lookup[(sid, f'F2-t{t}')]
            i1, i2 = int(f1['frame_id']), int(f2['frame_id'])
            r = dict(root_id=sid[:3], state_id=sid, training_block=t,
                     F1_frame_id=i1, F2_frame_id=i2, F1_time_ps=float(f1['time_ps']), F2_time_ps=float(f2['time_ps']),
                     F1_in_P4=f1['in_P4'], F2_in_P4=f2['in_P4'],
                     selected_pair_dRMSD_A=float(gq.distances(a['distances_A'][i1], a['distances_A'][i2])[0, 0]),
                     selected_pair_angle_deg=float(gq.circular(a['angles_rad'][i1], a['angles_rad'][i2])),
                     F1_m_H4_A=float(f1['selected_m_H4_A']), F2_m_H4_A=float(f2['selected_m_H4_A']))
            for mode in MODES:
                values = [float(x['difference']) for x in paired_main if x['reference_mode'] == mode and
                          x['state_id'] == sid and int(x['training_block']) == t]
                if len(values) != 3:
                    raise RuntimeError('同Tの3MDseed対応が不完全です。')
                r[mode+'_MDmean_F2_minus_F1_A'] = float(np.mean(values))
            selection_pairs.append(r)
    from p1.r1_cpu_review import write_table
    write_table(out/'selection-effect-links.csv', selection_pairs)

    full_table = []
    for mode in MODES:
        for comp in ('F2-F1', 'F2-F0', 'F1-F0'):
            full_table.append([mode, comp, interval(row(mode, comp, 'S4')),
                               interval(row(mode, comp, 'S8')), interval(row(mode, comp, 'ROOT_MEAN')),
                               interval(row(mode, comp, 'STAGE_DIFFERENCE'))])
    all_metric_table = [[metric_label(k), units[k[0]]]+[interval(row(m, metric=k)) for m in MODES] for k in metrics]
    all_metric_dec = []
    for k in metrics:
        selected = [r for r in dec if is_main(r) and r['comparison'] == 'F2-F1' and key(r) == k]
        by = {r['estimand']: r for r in selected}
        all_metric_dec.append([metric_label(k), interval(by['Gamma_original']),
                               interval(by['Gamma_common_A4']), interval(by['reference_contribution'])])
    root_main = [r for r in roots if is_main(r) and r['comparison'] == 'F2-F1' and r['metric'] == 'distance_mean_A']
    root_lookup = {(r['reference_mode'], r['root_id']): r for r in root_main}
    root_table = [[rid]+[number(root_lookup[(mode, rid)][column]) for mode in MODES
                        for column in ('S4', 'S8', 'S8_minus_S4')] for rid in ROOTS]

    # 全量に対する尺度・burn・prefixの不一致を完全表にする。
    sensitivity = []
    for r in summary:
        if r['comparison'] == 'F2-F1' and r['estimand'] == 'STAGE_DIFFERENCE':
            sensitivity.append(r)
    write_table(out/'all-scale-stage-differences.csv', sensitivity)
    seed_rows = []
    for r in randomness:
        if r['burn_ps'] == 100 and r['prefix_ns'] == 4 and r['metric'] == 'distance_mean_A' and r['quantity'] == 'paired_F2-F1':
            seed_rows.append({k: r[k] for k in ('reference_mode', 'root_id', 'state_id', 'milestone_ns', 'mean',
                             'training_mean_difference', 'training_mean_SD', 'MD_SD_by_training',
                             'additive_residual_RMS', 'pure_interaction_variance_identified')})
    write_table(out/'main-randomness-diagnostic.csv',
                [{k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()} for r in seed_rows])

    origin_counts = []
    for milestone in (4, 8):
        for arm in ('F0', 'F1', 'F2'):
            selected = [r for r in origins if int(r['milestone_ns']) == milestone and r['label'].startswith(arm)]
            origin_counts.append([f'S{milestone}', arm, len(selected),
                sum(r['in_P4'] == 'True' for r in selected), sum(r['in_old800'] == 'True' for r in selected),
                sum(r['in_new400'] == 'True' for r in selected), sum(r['in_validation200'] == 'True' for r in selected)])
    lof_counts = []
    for pm, scoring in [('FULL', 'FULL_REFIT'), ('PREFIX4', 'FIXED_FULL_SCORE'),
                        ('PREFIX4', 'SUBSET_REFIT'), ('COUNT_MATCH', 'FIXED_FULL_SCORE'), ('COUNT_MATCH', 'SUBSET_REFIT')]:
        selected = [r for r in pool if r['pool_mode'] == pm and r['scoring_mode'] == scoring]
        lof_counts.append([pm, scoring, len(selected), sum(r['selected_same_as_original'] == 'True' for r in selected),
                           sum(r['downstream_status'] == 'NOT_OBSERVED' for r in selected)])
    source_text = '\n'.join((out/'events.jsonl').read_text().splitlines())
    if 'stopped' in source_text:
        raise RuntimeError('停止履歴を先に審査し、完成報告へ進む条件を確認してください。')
    stage_cost = [r for r in events if r['event'] == 'stage_complete']
    cost_table = [[r['stage'], f"{r['wall_s']:.6f}", f"{r['CPU_s']:.6f}"] for r in stage_cost]
    eval_costs = read_csv(out/'evaluation-costs.csv')
    peak = max(float(r['peak_RSS_bytes']) for r in eval_costs)
    orig = row('ORIGINAL_HISTORY')
    common = row('COMMON_A4')
    dr = next(r for r in dec if is_main(r) and r['comparison'] == 'F2-F1' and key(r) == main_metric and r['estimand'] == 'reference_contribution')
    common_roots = [root_lookup[('COMMON_A4', rid)] for rid in ROOTS]
    negative_common = [r['root_id'] for r in common_roots if float(r['S8_minus_S4']) < 0]
    if float(common['bootstrap95_low']) > 0:
        interpretation = '共通H4でも平均段階差は正で、探索的区間は正側にあった。評価参照変更だけではこの条件下の差を説明しきれないが、状態条件の組合せに関する記述に留まり、独立確認やXの増分価値を示さない。'
    elif float(common['bootstrap95_high']) < 0:
        interpretation = '共通H4では平均段階差が負で、探索的区間も負側にあった。元の正方向は共通参照へ頑健ではなく、評価参照依存を明示する必要がある。Xや更新そのものの一般的無効性は導かれない。'
    else:
        interpretation = '共通H4の探索的区間は0を含む。安定した段階差の方向は確認できず、元の正方向をそのまま共通参照へ一般化できない。これは無効果や等価性の証明でもない。'
    stamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat()
    report_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = f'''# P1-B1-R1：評価参照と段階差のCPU科学復核

作成：{stamp}。状態：CPU解析完了、最終原入力再監査・GitHub交付は後段で検証する。独立科学審査PENDING、研究者科学受入れPENDING。証拠種別は **derived analysis（既存の実MD軌道のCPU再解析）** である。

## Executive Summary

既存B1 Expansionの8根・16状態・240下流枝を、登録した四参照で再評価した。原評価ORIGINAL_HISTORYは全240枝・全6連続量・全6離散条件・全12時間窓と最近傍/代表/確認IDで再現した。15,208 rawファイルと9原archiveのSHA、原子順・選点座標・時間凍結の入力監査はPASSだった。新MD・CVAE学習・モデル推論・GPU計算は0。

事前指定の主表示（4 ns下流、先頭100 ps除外、平均幾何距離、F2−F1）で、同根S8−S4は元参照で **{interval(orig)} Å**、共通H4で **{interval(common)} Å**。参照変更の数値的寄与は **{interval(dr)} Å**。正の根数は元{orig['positive_roots']}/8、共通H4 {common['positive_roots']}/8である。これは同じ実軌道の測定関数を変えた結果で、M0・候補・訓練窓・起点の因果寄与を分離したものではない。

{interpretation}

共通H4で負の段階差となる根：{', '.join(negative_common) if negative_common else 'なし'}。全指標・尺度・全根を以下と完全CSVに掲載する。区間0包含を無効果や等価性の証明としない。指標多数決で探索改善を認定しない。CのXがZ/Wを超える独立予測価値、B2の固定wall-clock純利益、MD物理資格、CVAE学習十分性は今回も未検証である。

## 1. 目的と事前の問い

R1-Aは同根S4/S8を同じ合法な過去参照で測った段階差、R1-Bは候補Top1の歴史的出所と候補集合依存、R1-Cは評価上の交絡と未識別要因の境界である。承認設計は `59f97821ae6ffe283c371f710546abf84f691642`、CPU実装版は `{args.implementation_commit}`。B1科学生成版 `40a911e1f36d1365fc5ee7d8753a7feb1edd964d` と区別する。報告生成ソースSHA-256は `{report_sha}`。

この計画はB1の既報段階差を知った後、新たな再評価結果を見る前に登録した**事後感度分析**である。盲検・独立確認実験や第三者査読への格上げではない。採用設計・許可はCONFIRMED、実際のCPU時間等はMEASURED、以下の比較・区間はDERIVED、将来の対照案はPROPOSED、物理/学習/C/B2の未確認はUNVERIFIEDとする。

## 2. 対象、系譜、入力の完全性

FSD-EY（PDB 1FME）、OpenMM、既存mdlearn CVAE、Amber14-all/GBn2/NoCutoff・非周期・300 K・2 fs・HBondsの既存B1を固定した。蛋白質折り畳み機構や新CVAEの研究ではない。8根は同じ準備済み初期構造から別履歴seedで開始した系列で、8種類の独立準備構造や平衡試料ではない。各根連続8 ns、S4/S8の16状態、F0共有3MD枝、F1/F2各2学習seed×3MDseed、各枝4 ns、合計240枝。履歴64 ns＋下流960 nsは分枝合算である。

M0は同じ未学習初期重みseed1600000001から、各状態の旧800点をbatch4×200歩学習して構築した。S8でS4から継続学習していない。F1は旧800を追加200歩、F2は旧400＋新400を追加200歩、共通model/optimizer/初期RNGを制御する。Δ21は容量一定のデータ置換総効果で、新規性だけの効果ではない。S4旧窓(0.1,1.6] ns/新窓(2,3.6]、S8旧窓(4.1,5.6]/新窓(6,7.6]。候補は各状態までの100 ps以後の全適格点なので、訓練所属と候補の時間的出所は一致しない。

入力検査は504原子/28Cα順序、保存Cαと325距離の単位対応、H4のH8内prefix完全一致、候補7,800/15,800点、選点のsegment/local/global IDと原時刻、実MD投入座標、凍結SHAと公開時計の順序を確認した。[input-audit.json](input-audit.json)、[全ファイルSHA](input-file-sha256.csv)、[枝監査](branch-input-audit.csv)、[参照ID](reference-manifest.json)を参照。相関保存点1,920,000個を独立反復と数えない。9原archiveは保持し、Macへコピーしていない。

## 3. 物理代理と数学定義

28Cαの非周期座標[Å]から、P3={{(i,j):j−i≥3}}の325内部距離をv(x)とする。d(x,h)=sqrt(Σ_P3(v_ij(x)−v_ij(h))²/325) [Å]、m_A(x)=min_h∈A d(x,h)。並進・回転不変だが鏡像を識別せず、有限履歴への距離であって絶対的構象空間の被覆率ではない。

連続6量はm_Aの平均/中央値/p90 [Å]、Rg平均[Å]、Q8平均[無次元]、幾何最近傍の54角との周期RMS角差中央値[度]。Q8はj−i≥4の300対に対する距離<8 Åの割合で、native接触率ではない。角差はwrap(θ−θ′)のRMS×180/πであり、角による別最近傍を求めない。Rg/Q8は同じ枝/mask/窓なら参照不変、角差は参照依存である。

離散6条件はε={{1.5,2,3}} Å×τ={{0,5}} ps。元のgreedy仮代表・連続支持・欠測gap規則と代表/確認IDを維持する。既知判定≤ε+10⁻¹⁰ Å、持続≥τ−10⁻⁹ ps、2 ps観測なのでτ5 psは最短6 ps支持である。初点を無料で新領域に数えない。尺度は生物学的状態を独立校正した閾値ではない。

burn={{0,100,200,500}} ps、prefix={{1,2,4}} nsの12窓を全保存した。連続0.5 ps、離散は時間窓位置を[::4]した後に元validを渡す。100 ps窓、lag0.5/2/10/100 ps相関も全条件で記録したが、平衡性や有効独立標本数の認定に用いない。

## 4. 四参照と時間合法性

|参照法|S4|S8|推定対象|
|---|---|---|---|
|ORIGINAL_HISTORY|H4|H8|当時までの既知履歴に対する距離|
|COMMON_A4|H4|同じH4|共通の早期履歴からの変化|
|COMMON_A2|H2|同じH2|より早い履歴を基準にした感度|
|MATCHED_COUNT|H4|T_K(H8), K=7,800|点数を合わせた決定的間引きへの感度|

H2/H4は根ごとに作り、根を混ぜない。H2は元h1区間IDから取る。T_Kはglobal ID順n点からfloor[j(n−1)/(K−1)]、j=0…K−1。下流、効果、LOF、状態中心を参照選択に使わない。S4を未来H8で評価する条件は実行していない。COMMON_A4のS8で高い値は4–8 ns中に既知になった構造でも取り得るため、S8で未知だった領域と同義ではない。これは実行済み枝の事後測定で、当時のオンライン方策を再実行したものではない。

## 5. 統計階層と数値分解

各根r・段階s・指標/窓/参照でD_rs21=Σ_(t=1,2;m=1,2,3)(Y_F2−Y_F1)/6、Γ_r=D_r8−D_r4。F2−F0/F1−F0も同じF0,mを共有し、F0を6独立観測へ複製しない。全体効果は(S4+S8)/2を根内で計算後、8根で平均した。

Γ_N−Γ_C4=D_8(H8)−D_8(H4)=E_refを全条件で照合した。平均距離ではL_a=Y_a(H4)−Y_a(H8)≥0からE_ref=L1−L2。点ごとの距離は入れ子参照で下がるが、群差は上下どちらにも変化する。中央値/p90は枝の統計量差であり、フレーム差の分位点ではない。離散数/角差に距離の単調性を要求しない。この分解は測定関数の有限データ差で、因果媒介効果や説明率ではない。

根cluster bootstrap10,000回、seed1604000001、同じ再標本化を全指標/参照/比較に共有。下位seedを再標本化せず、平均/中央値/範囲/SD/全根値/根除外8平均を保存した。少数seedの雑音を含む8根の探索区間で、多重性調整・確認的有意差・等価性・Cの交差検証ではない。S4/S8は同じブロック番号でも実seedが異なる。

## 6. 主幾何量：全三比較・全四参照

単位Å、各セルは8根平均[探索的95%区間]。ROOT_MEANは同根二段階平均、Γは同根段階差。

{table(full_table, ['参照','比較','S4','S8','ROOT_MEAN','Γ=S8−S4'])}

## 7. 全6連続量・全6離散条件の段階差

F2−F1、4 ns/100 ps。大きい値を一律の科学的改善と数えない。Rg/Q8/角差は物理形状の記述である。

{table(all_metric_table, ['指標','単位']+list(MODES))}

全12時間条件と全3比較は[continuous.csv](continuous.csv)、[discrete-counts.csv](discrete-counts.csv)、[paired-effects.csv](paired-effects.csv)、[root-summary.csv](root-summary.csv)、[全尺度段階差](all-scale-stage-differences.csv)へ追跡できる。ε・τ・burn・prefixによる反転も同じ優先度で保持した。

## 8. 8根ごとの段階差

主平均距離F2−F1 [Å]。同一準備構造に条件付けた8根全てを掲載する。都合の悪い根を除外しない。

{table(root_table, ['根']+[f'{{m}} {{c}}'.format(m=m,c=c) for m in MODES for c in ('S4','S8','Γ')])}

## 9. 評価参照変更の寄与：全尺度

F2−F1、4 ns/100 ps。E_ref=Γ_N−Γ_C4。正負どちらの寄与も保存し、割合へ変換しない。

{table(all_metric_dec, ['指標','Γ_N','Γ_C4','E_ref'])}

全3比較・全窓・8根の恒等式残差は[reference-decomposition.csv](reference-decomposition.csv)、各区間は[reference-decomposition-summary.csv](reference-decomposition-summary.csv)。元参照の問いと共通参照の問いは異なり、一方を都合よく正解と認定しない。

## 10. Top1の歴史的出所と候補集合診断

下表の分母は実選択数で、独立科学反復数ではない。旧/新/validationは訓練窓所属、P4は早期候補所属である。

{table(origin_counts, ['段階','群','選択数','P4内','旧800内','新400内','validation内'])}

全80選択の時刻・区間・所属・座標/モデルSHAは[selected-origins.csv](selected-origins.csv)。同状態同TのF2/F1起点dRMSD/角差、H4距離と実行済み3MDseed平均Δ21は[selection-effect-links.csv](selection-effect-links.csv)。起点は処置後の媒介変数なので、この結合を調整済み因果効果にしない。

{table(lof_counts, ['候補集合','得点操作','診断数','元Top1と同じ','下流NOT_OBSERVED'])}

FULL80 fit、S8のPREFIX4/COUNT_MATCH各40 fit、計160 CPU LOF fit。保存float32 embeddingを固定し、20近傍/Minkowski p2/novelty=False、tieはglobal ID、数値thread1を使用した。FULLは原score/全順位を許容内で再現。F0-repeat16配列も一致した。制限時は全候補scoreを保持する操作と近傍密度を再fitする操作を分けた。潜在座標を別モデル間で直接引き算していない。

新Top1のMD応答はNOT_OBSERVEDであり、座標が近い/別状態で同IDだったことからYを借用しない。元Top1が完全一致する行もOBSERVED_ORIGINAL_ONLYであり、新しい独立観測や方策試験ではない。候補数合わせも密度/構造支持/時間域を同時に変え、純粋な候補数因果効果を識別しない。完全なTop10/100・SHA・順位感度は[pool-selection-diagnostic.csv](pool-selection-diagnostic.csv)。

## 11. 学習乱数とMD乱数

全2×3セルを[paired-effects.csv](paired-effects.csv)、全量の行平均差/MD行内SD/加法残差を[randomness-decomposition.json](randomness-decomposition.json)に保存。主量の全64状態×参照の診断は[main-randomness-diagnostic.csv](main-randomness-diagnostic.csv)。1セル1軌道、2学習seed×3MDseedなので、純交互作用と誤差分散の分離、M0学習seedの一般変動、学習対MDの精密な寄与率を認定しない。根間変動、段階差、根内seed変動を区別する。

## 12. 実費用と実行上の失敗

下表は報告生成前までに完了した工程の実測wall/CPU。1 worker、数値thread1、GPU不可視。後段の最終SHA再監査と報告作成時間は追加の費用証跡で区別する。

{table(cost_table, ['工程','wall s','CPU s'])}

評価実計算{len(eval_costs)}条件、参照同一の240条件は論理aliasとして保持した。評価中最大RSSは{peak/1024**2:.3f} MiB。各条件費用は[evaluation-costs.csv](evaluation-costs.csv)、工程ログは[execution-events.json](execution-events.json)、報告生成費と最終検証は[delivery-costs.json](delivery-costs.json)を参照。これらは評価器のCPU費用で、学習の機会費用やB2純利益ではない。

配備時、Mac AppleDoubleを初回転送manifestに誤登録し、メタデータの転送SHA検査が1回失敗した。実コード/入力を変更せず、メタデータを除いたv2 allowlist6ファイルを再照合した。5境界テストはPASS。科学再現の失敗を隠す修正ではなく、科学解析前の配備修正である。科学処理の停止/失敗はイベント・失敗索引に全件保存する。

## 13. 支持される記述、支持されない記述

四参照で同じ軌道を測ることにより、評価参照変更の数値的寄与とその尺度依存を記述できる。共通参照でも残る差は、この初期条件/MD/CVAE設定での段階条件の組合せに伴う探索的な等MD量差までである。小さい/反転/広い区間も同様に報告する。[事前判定表](decision-criteria.md)を結果に応じて変更していない。

S4/S8では候補数7,800/15,800、訓練時間窓、M0、候補起点、物理履歴が同時に変わる。共通Aだけでこれらの独立原因は分離できない。X/Yの幾何共有、X/W重複、Zの段階間共通支持不足、8根全使用、事後多指標分析が残る。X相関の再探索やC予測器は追加していない。Cが成立した/棄却されたとは判断しない。固定MD量であり、更新コストを引いた固定wall-clock B2純利益でもない。

## 14. 独立資格ゲートとThreats to Validity

物理資格P：unfolded初期構造準備史、プロトン化/pH、GBn2/NoCutoffの適用範囲、十分な初期平衡とburn-in、再最小化/速度reseedが残る。安定した粗幾何や100 ps除外は平衡性や熱力学状態を認定しない。R1はこの設定を変更も資格認定もしない。

学習資格L：200歩/800提示は統制された短い設定で、CVAEの収束/表現有用性の保証ではない。M0は各状態で再構築した学習済みモデルで、継続オンラインモデルとは異なる。loss低下/Top1変化を探索改善としない。P/Lは評価参照の再検証とは別に審査する。

他の限界：一つの蛋白質・初期準備、短い有限非定常軌道、未校正の領域尺度、幾何距離の鏡像不識別、greedy計数の順序依存、近接tieでの角最近傍不安定性、少数根/seed、モデル共通初期化、候補制限後のMD欠測。全root/全尺度を示しても一般HPCシステム効果や生物学的発見へ外挿できない。

## 15. 再現、証拠索引、次の判断

[再現手順](reproduce.md)、[実行カード](execution-approval.md)、[実装](../../p1/r1_cpu_review.py)、[報告生成](../../p1/r1_cpu_report.py)、[原評価ソース](../../p1/server/gq_r2.py)、[原B1仕様](../P1-B1-Expansion/metric-contract.md)、[原B1報告](../P1-B1-Expansion/review-dossier.md)を参照。原入力SHAと出力SHA、承認/実装/生成版を区別する。完全な距離配列・代表ID・embedding・DCD・重みは許可サーバ、GitHubは全可読表・図・監査・索引。旧科学データ/ソース/seedを修正せず、9archiveを保持する。

統計上の根拠：[Grossfield et al., 2018, Best Practices for Quantification of Uncertainty and Sampling Quality](https://pmc.ncbi.nlm.nih.gov/articles/PMC6286151/)の相関・準備条件付き不確実性。LOF操作の根拠：[scikit-learn 1.6.1公式仕様](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)の標本内negative_outlier_factor_とnovelty区別。両資料が本事例の科学的有効性を証明したものではない。

次はChatGPTと研究者による独立科学審査のみ。共通参照での限定主張、残るM0/候補交絡、P/L資格、将来の必要対照を審査し、新しい実験は別承認とする。B2・C予測器・S3を自動開始しない。
'''
    (out/'review-dossier.md').write_text(report)

    # 全12指標を同じ形式で表示する。単位の違う量を合成しない。
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    candidates = [f for f in font_manager.fontManager.ttflist if 'Noto Sans CJK' in f.name]
    if candidates:
        plt.rcParams['font.family'] = candidates[0].name
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(4, 3, figsize=(13, 13), constrained_layout=True)
    for ax, metric in zip(axes.flat, metrics):
        for i, mode in enumerate(MODES):
            r = row(mode, metric=metric)
            mean, lo, hi = map(float, (r['mean'], r['bootstrap95_low'], r['bootstrap95_high']))
            ax.plot([i, i], [lo, hi], color='0.35', linewidth=1.5)
            ax.plot(i, mean, 'o', color='black')
        ax.axhline(0, color='0.7', linewidth=.8)
        ax.set_xticks(range(4), ['当時', '共通H4', '共通H2', '等点数'], rotation=20)
        labels = dict(distance_mean_A='平均dRMSD', distance_median_A='dRMSD中央値',
                      distance_p90_A='dRMSD p90', Rg_mean_A='Rg平均', Q8_mean='Q8平均',
                      angle_to_geometric_neighbor_median_deg='幾何最近傍との角差中央値')
        ax.set_title(labels.get(metric[0], metric_label(metric)), fontsize=9)
        ax.set_ylabel(f"段階差 [{units[metric[0]]}]")
    fig.suptitle('F2−F1の同根S8−S4：全登録指標（4 ns / 100 ps除外）\n8根cluster bootstrap探索区間、指標間の多数決は行わない')
    fig.savefig(out/'all-metric-stage-differences.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for i, rid in enumerate(ROOTS):
        values = [float(root_lookup[(mode, rid)]['S8_minus_S4']) for mode in MODES]
        axes[0].plot(range(4), values, '-o', label=rid, linewidth=1)
    axes[0].set_xticks(range(4), ['当時', '共通H4', '共通H2', '等点数'])
    axes[0].axhline(0, color='.6', linewidth=.8)
    axes[0].set_ylabel('F2−F1のS8−S4 [Å]')
    axes[0].legend(ncol=2, fontsize=8)
    main_dec = [r for r in read_csv(out/'reference-decomposition.csv') if is_main(r) and r['comparison'] == 'F2-F1' and key(r) == main_metric]
    positions = np.arange(8)
    for offset, col, label, shade in [(-.23, 'Gamma_original', '当時Γ', '.25'),
                                     (0, 'Gamma_common_A4', '共通H4 Γ', '.55'),
                                     (.23, 'reference_contribution', '参照寄与', '.8')]:
        axes[1].bar(positions+offset, [float(r[col]) for r in main_dec], .23, label=label, color=shade)
    axes[1].set_xticks(positions, [r['root_id'] for r in main_dec], rotation=45)
    axes[1].axhline(0, color='.6', linewidth=.8)
    axes[1].set_ylabel('幾何距離差 [Å]')
    axes[1].legend(fontsize=8)
    fig.suptitle('8根を保持した参照感度と測定関数の数値分解（因果媒介効果ではない）')
    fig.savefig(out/'root-reference-decomposition.png', dpi=170)
    plt.close(fig)

    handoff = f'''# B1-R1：ChatGPTへのA–G引継ぎ

## A. 現在状態

{stamp}。CPU解析完了、最終不変監査/GitHub交付は別証拠で確定する。承認設計59f97821、CPU実装 `{args.implementation_commit}`、元B1科学生成40a911e。最終同期SHAはGit履歴/最終返信の実在値を参照。8根/16状態/240枝×四参照=960論理条件、欠測0。再現/結果/LOF監査PASS、独立科学審査PENDING、研究者科学受入れPENDING。GPU/MD/学習/モデル推論0。

## B. 確認状態

CONFIRMED：指定設計の限定CPU復核。MEASURED：入力SHA/実行時間/再現検査。DERIVED：四参照の全比較、根区間、参照寄与、候補診断。PROPOSED：将来のM0/候補交差対照や物理/学習資格確認。UNVERIFIED：XのZ/W条件付き価値、B2純利益、P/L資格、一般化。文書/工程完了を科学受入れにしない。

## C. 科学的結果

主平均距離Δ21の同根S8−S4 [Å]：当時参照 {interval(orig)}、共通H4 {interval(common)}、評価参照寄与 {interval(dr)}。統計単位8根、有限seed込みの探索的95%区間。正の根数は当時{orig['positive_roots']}/8、共通H4 {common['positive_roots']}/8。全6連続/6離散尺度は完全報告表7–9で同じ優先度を維持する。指標ごとの逆方向と広い区間を落とさない。

{interpretation}

保存embedding FULLの80再fitは原score/全順位を再現、F0-repeat16一致。候補制限の160行とFULL80行を保存し、新Top1のMD成果はNOT_OBSERVED。選点は処置後の媒介で、選点出所とΔを結んでも因果調整ではない。共通H4のS8は早期履歴からの変化であり、S8時点の未発見領域ではない。

## D. 技術情報

[実装](../../p1/r1_cpu_review.py)、[報告生成](../../p1/r1_cpu_report.py)、[実行カード](execution-approval.md)、[再現](reproduce.md)。原科学ソース/データ/seedは不変。単worker/thread1、GPU不可視。入力15,208 SHA、9archive、原子順504/28Cα、H4 prefix、候補ID、実MD起点、公開凍結時計を照合。原再現PASS後のみ追加参照を実行。bootstrap1604000001の同一8根抽出を全条件で共有、下位seed追加再標本化なし。純交互作用分散は識別不能。

配備のAppleDouble manifest失敗1回はv2 allowlistで解決、科学条件変更なし。実行停止・未実施は失敗索引とイベントを照合する。9archiveはサーバに保持、Mac raw backupはWAIVED_BY_RESEARCHER。

## E. 重点審査点

1. 共通参照の測定対象変更と、元の当時履歴新規度を両立して解釈できているか。
2. 全尺度/全根/seed変動を踏まえ、残る段階条件の組合せの記述をどこまで許すか。
3. 候補数/密度、M0、訓練窓、選点媒介を評価寄与だけで同定済みにしていないか。
4. X/Y表現共有、X/W重複、Z支持不足、全8根観測済みの下でCへ進む前に必要な独立対照は何か。
5. 物理Pと学習Lを別資格ゲートとしてどう判断するか。

## F. 索引

[完全報告](review-dossier.md)、[全連続](continuous.csv)、[全離散](discrete-counts.csv)、[全対応](paired-effects.csv)、[根段階](root-stage-effects.csv)、[根区間](root-summary.csv)、[参照分解](reference-decomposition.csv)、[分解区間](reference-decomposition-summary.csv)、[全感度](all-scale-stage-differences.csv)、[全乱数](randomness-decomposition.json)、[主乱数](main-randomness-diagnostic.csv)、[Top1出所](selected-origins.csv)、[起点と実効果](selection-effect-links.csv)、[LOF診断](pool-selection-diagnostic.csv)、[LOF再現](LOF-full-reproduction.csv)、[入力監査](input-audit.json)、[SHA](input-file-sha256.csv)、[結果監査](result-audit.json)、[元再現](original-reproduction.json)、[費用](delivery-costs.json)、[出力索引](public-evidence-index.json)。raw距離/embedding/DCD/重み/完全ログは許可サーバのみ、GitHubは可読派生表と図/監査。

## G. 次段階

ChatGPTと研究者の独立科学審査で停止する。M0/候補の交差、P/L、C/B2を扱う新計算は全てPROPOSED/未承認。B2・C予測器・S3を自動開始しない。旧S2独立終審INCOMPLETEを維持する。
'''
    (out/'handoff-to-chatgpt.md').write_text(handoff)
    write_json(out/'report-generation-cost.json', dict(wall_s=time.perf_counter()-start,
               CPU_s=time.process_time()-cpu, numerical_results_generated_on_server=True,
               new_MD_training_inference=0, report_source_sha256=report_sha))
    print('日本語報告・全尺度図・A–G引継ぎを生成しました。', flush=True)


if __name__ == '__main__':
    main()
