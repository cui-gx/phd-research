"""確定済みR1結果を変更せず、反対結果と解釈限界を報告の入口へ追記する。"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import time


def main():
    """数値の再推定は行わず、既存CSVから値を転記する。"""
    p = argparse.ArgumentParser(description='R1の全尺度を踏まえた日本語解釈の追記')
    p.add_argument('--output', required=True)
    args = p.parse_args()
    out = Path(args.output)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise RuntimeError('GPU不可視を維持してください。')
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    os.nice(10)
    start, cpu = time.perf_counter(), time.process_time()
    if (out/'editorial-audit.json').exists():
        raise RuntimeError('文書編集の既存証拠を上書きしません。')
    with (out/'root-summary.csv').open() as f:
        summaries = list(csv.DictReader(f))
    with (out/'main-randomness-diagnostic.csv').open() as f:
        randomness = list(csv.DictReader(f))

    def pick(mode, estimand='STAGE_DIFFERENCE'):
        return next(r for r in summaries if r['reference_mode'] == mode and
                    r['comparison'] == 'F2-F1' and r['metric'] == 'distance_mean_A' and
                    float(r['burn_ps']) == 100 and float(r['prefix_ns']) == 4 and r['estimand'] == estimand)

    def ci(r):
        return f"{float(r['mean']):+.6f} [{float(r['bootstrap95_low']):+.6f}, {float(r['bootstrap95_high']):+.6f}]"

    four, two, count, overall = pick('COMMON_A4'), pick('COMMON_A2'), pick('MATCHED_COUNT'), pick('COMMON_A4', 'ROOT_MEAN')
    seed = next(r for r in randomness if r['reference_mode'] == 'COMMON_A4' and r['state_id'] == 'r07-s4')
    headline = f'''**反対結果・不確実性も併記する。** 共通H2の主幾何段階差は **{ci(two)} Å** で、共通H4と一致しない。全6離散尺度の段階差の探索区間は0を含む。共通H4の全体効果（同根S4/S8平均）は **{ci(overall)} Å** で、F2の一般的優位を確認していない。主復核H4の指定を結果に応じて変えず、これらの補助条件と陰性結果を同じ重みで審査する。'''
    discussion = f'''# 結果を統合した方法論的読取り

2026-10-28 / DERIVED。これは確定済みの表の読み方を明確化した追記であり、解析方法・閾値・seed・軌道・候補選択・数値を変更していない。研究者の科学的受入れや独立査読の代替ではない。

## 1. 何を弱め、何を残したか

共通H4の平均幾何段階差は{ci(four)} Å。元の当時参照と比べた数値寄与は完全報告表9に示す。したがって「S4/S8でA0が違ったからだけ」という説明は、この主指標・共通H4の範囲では不十分である。しかし、候補数・M0・訓練窓・起点はそのままなので、差の原因をXに特定していない。

**共通H2では{ci(two)} Åである。** 同じ過去参照を使えば必ず同じ段階信号になる、という結果ではない。H2はより早い履歴からの変化、H4は4 nsまでの履歴からの変化を測る。双方は合法な過去参照でも異なる測定対象であり、結果を見て一方を正解へ格上げしない。H4の結果を維持したまま、参照の時間域・支持構造への依存を主な制限として扱う。

点数合わせの段階差は{ci(count)} Åで、登録された一つの間引きに対して主幾何量の方向・規模は保たれた。しかし、点数だけの純因果効果を除いたことにはならない。間引きは密度と構造支持も変える。p90の参照寄与と平均の寄与も同じではなく、平均だけを根拠に参照効果を無視できるとは認定しない。

## 2. 尺度の不一致と更新全体の効果

全6離散尺度の段階差の区間は0を含む。平均/中央値/p90の連続幾何量で見える信号を、「新しい物理領域が確実に多く見つかった」という主張へ置き換えない。RgとQ8の参照寄与が厳密に0であることは実装の負対照であり、科学的成果が0だったという意味ではない。

共通H4のF2−F1全体効果は{ci(overall)} Å。これはΓ=S8−S4とは異なる推定対象である。段階差が正でも更新の全体優位は未確認であり、逆に区間が0を含んでも無効果・等価性を証明しない。全12時間条件・全3比較・逆方向の根は元の完全表から追跡する。

## 3. 候補と乱数について分かったこと

S8の実Top1がP4に含まれる数はF1 3/16、F2 7/16だった。モデル更新後の起点は処置後の媒介であり、この差を因果調整に使わない。候補をP4へ制限したとき、全候補score固定では元Top1と同じ15/40、LOF再fitでは7/40。候補の許可と近傍密度の再計算を分ける必要がある。新Top1にMDがなければNOT_OBSERVEDのままとし、制限後のF2−F1科学効果を埋めない。

元報告でも例示したr07-s4について、共通H4の状態平均は{float(seed['mean']):+.6f} Å、学習行平均のT2−T1は{float(seed['training_mean_difference']):+.6f} Å、各TのMD内SDは{seed['MD_SD_by_training']} Åだった。これは少数seed変動が状態平均より大きい場合があることの記述である。2×3各セル1本から純交互作用分散や学習/MDの一般的寄与率を推定しない。全64状態×参照の主量診断と全36,864乱数記録を併記する。

## 4. 事前判定表との対応

|ラベル|本輪の根拠|主張の上限|
|---|---|---|
|TECHNICALLY_REPRODUCIBLE|原240枝、全連続/離散条件、元根要約、FULL80順位を再現。実誤差表とSHAがある|技術整合。物理・学習資格や科学受入れではない|
|STAGE_BUNDLE_SIGNAL_REMAINS|共通H4で主幾何Γと探索区間が正側、7/8根で正|この準備/MD/CVAE条件の組合せに伴う探索的な等MD量差|
|REFERENCE_SENSITIVE|共通H2とH4が不一致。指標間で参照寄与も異なる|測定対象の依存を報告。唯一の絶対評価器や「参照影響なし」としない|
|INCONCLUSIVE|全体F2−F1と離散6尺度の広い区間、有限root/seed|全体優位・厳密無効・等価性はいずれも未認定|
|NOT_IDENTIFIED|M0/候補/訓練窓の単独効果、新Top1の下流、XのZ/W超の情報、B2純利益|別の対照/独立審査が必要。Cの成立も棄却も宣言しない|

物理Pと学習Lは独立資格ゲートのままである。次はChatGPTと研究者の審査で停止する。新MD・再学習・推論・B2・C予測器・S3を自動開始しない。
'''
    names = ['review-dossier.md', 'handoff-to-chatgpt.md', 'public-evidence-index.json', 'output-sha256.json']
    snapshots = {}
    for name in names:
        src = out/name
        dest = out/(src.stem+'-server-v1'+src.suffix)
        if dest.exists():
            raise RuntimeError('保存先snapshotが既に存在します。')
        dest.write_bytes(src.read_bytes())
        snapshots[name] = hashlib.sha256(src.read_bytes()).hexdigest()
    report = out/'review-dossier.md'
    text = report.read_text()
    text = text.replace('共通H4で負の段階差となる根：', headline+'\n\n共通H4で負の段階差となる根：', 1)
    text += '\n\n## 16. 結果を統合した読取り\n\n'+discussion.split('\n', 2)[2]
    report.write_text(text)
    handoff = out/'handoff-to-chatgpt.md'
    text = handoff.read_text().replace('保存embedding FULLの80再fit', headline+'\n\n保存embedding FULLの80再fit', 1)
    text += '\n\n追加審査入口：[統合した読取り](interpretation-and-review.md)。初回server-v1報告とSHA索引を別名で保全し、今回の編集は既存表の転記・解釈だけである。\n'
    handoff.write_text(text)
    (out/'interpretation-and-review.md').write_text(discussion)
    notes = '''# 交付過程の失敗と復旧

科学実行の停止/失敗は0。原入力、凍結条件、seed、元結果の変更は0。

1. 科学実行前の初回配備：Mac AppleDoubleをmanifestへ誤登録し、転送メタデータのSHA照合が失敗した。実ファイル6件だけのv2 allowlistを検査して解決。初回bundleとsnapshotを保持した。
2. 科学実行後の派生証拠伝送：ローカル取込を伝送完了前に試み、getmembersでEOFErrorとなった。展開前に停止し、伝送完了後に11,620,528 bytesとSHA-256を照合、全53ファイルを正常に取り込んだ。原9archiveではなく、許可された小型派生表/図/報告だけの伝送である。科学再実行、原データ修正、未観測Y補完はしていない。

server-v1の報告、引継ぎ、索引は別名で保全した。その後の編集は、共通H2の反対結果、離散尺度の不確実性、起点/乱数の読み方を明示したもので、数値表・図・評価規則を変えていない。科学的受入れはPENDING。
'''
    (out/'delivery-notes.md').write_text(notes)
    audit = dict(status='PASS_DOCUMENT_ONLY', prior_server_v1_sha256=snapshots,
                 source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 scientific_tables_changed=False, figures_changed=False,
                 MD_training_inference=0, CPU_s=time.process_time()-cpu, wall_s=time.perf_counter()-start)
    (out/'editorial-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
    hashes = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(out.rglob('*')) if p.is_file() and
              p.name not in ('output-sha256.json', 'public-evidence-index.json', 'run.lock', 'pipeline.lock')}
    (out/'output-sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')
    old_index = json.loads((out/'public-evidence-index-server-v1.json').read_text())
    for entry in old_index['files']:
        if Path(entry['path']).suffix in ('.csv', '.png'):
            if hashlib.sha256((out/entry['path']).read_bytes()).hexdigest() != entry['sha256']:
                raise RuntimeError('科学表または図のSHAが変わっています。')
    public = [dict(path=p.name, bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
              for p in sorted(out.iterdir()) if p.is_file() and p.suffix in
              ('.md', '.json', '.csv', '.png', '.log', '.txt') and p.name != 'public-evidence-index.json']
    (out/'public-evidence-index.json').write_text(json.dumps(dict(status='SERVER_GENERATED_WITH_EDITORIAL_REVIEW',
         files=public, scientific_tables_and_figures_unchanged=True, raw_arrays_included=False), ensure_ascii=False, indent=2)+'\n')
    print('既存の全数値表/図のSHA不変、反対結果を含む文書追記を保存しました。')


if __name__ == '__main__':
    main()
