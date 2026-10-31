# P1-NMR34-FULL：A–G独立科学審査引継ぎ

## A. 現在状態

2026-10-31 JST。バッチnmr34-full-20261031-v1、COMPUTE/ANALYSIS COMPLETE、272/272（履歴32/下流240）、2,048,000frame、34固定＋min34。全入出力・数値監査PASS、独立科学審査/研究者科学受入れPENDING。

基準33f6aa9e5071af18d7b841b61367507d2113b834、実行凍結7c24237117c17d2d6c1a629b3ece9ea3529be978。最終commitは本ファイルを含むGit履歴と最終返信で確定する。[工程回読](engineering-readback.json)、最終全文回読はremote-readback.json。

GitHubはコード、全35系列の枝/履歴/学習モデル/状態/根/区間/幾何相関、図、入力manifestと全出力SHA、報告。サーバのみ：全逐frame chunk、ID/品質、窓ID、完整stdout/stderr/budget、成功receipt。全パス/SHAは[delivery-audit.json](delivery-audit.json)。原9archive存在/サイズ一致（今回全archive再hashなし）、Mac raw免除。計算と監視は終了、global lock非保持。

## B. 確認区分

CONFIRMED：研究者がチャットで全272・科学7200秒/工程300秒/RSS2GiB/新出力2GiBを正式承認。元28CA/参照/Q/quality/12窓×2間隔/元seedを保持。新MD/CVAE/LOF/R0/C/B2は未承認。

MEASURED：CPU計算・資源・成功件数、入力SHA不変、全出力実SHA、M1再現誤差、観測OS thread最大2。DERIVED：34参照での段階方向、8根統計と探索区間、min34感度、参考間数値範囲。PROPOSED：Astra Extra Highの次回独立科学審査。UNVERIFIED：thread IDごとの厳密な帰属、物理/学習十分性、XのZ/W超過価値、B2純利益。

## C. 主な科学結果

全てPOST_HOC_EXPLORATORY。主窓4ns/burn100ps/0.5ps、F2−F1最小RMSD：

|段階|model1 Å|34固定参照の範囲 Å|min34 Å|
|---|---:|---:|---:|
|S4|+0.396619|+0.352999〜+0.456842|+0.386003|
|S8|−0.398921|−0.441402〜−0.354038|−0.405062|
|平均|−0.001151|−0.039509〜+0.046956|−0.009529|
|S8−S4|−0.795541|−0.842465〜−0.749708|−0.791065|

34/34固定参照でS4正/S8負、他23条件でも同方向。主窓S4は24/34の探索区間が正、10は0を跨ぐ。S8と交互差は全34で負、平均は全34で0を跨ぐ。34参照や24条件を独立反復としない。

主窓平均QのS4点差は全参照負、S8は全参照正だが、S4/S8/平均の全区間は0を跨ぐ。model1のF1−F0平均最小RMSD+0.151541Å、F2−F0平均+0.150390Åも保持し、普遍的更新優位を認定しない。全対比・全指標を省略していない。

model1根級S4は6正/2負、S8は2正/6負。min34のS4は5正/3負となる。集約方向の頑健性は個別根での成立や更新価値の予測可能性ではない。候補pool/M0/訓練window/状態履歴の交絡は未解消。

## D. 技術・コスト・再現

[実行器](../../p1/nmr34_full.py)、[全量集計](../../p1/nmr34_full_analyze.py)、[成果監査](../../p1/nmr34_full_audit.py)、[人工tests](../../p1/test_nmr34_full.py)。既存v2 numerical kernelは変更せず、全2448入力＋固定参照/集計入力SHAを最初に検査した。frame0/midpoint/last×全34の事前指定抽査、全frame M1/整数Q1/時刻/元全窓を照合した。

M1全frame最大誤差8.88178e−15Å、scalar抽査最大7.10543e−15Å、M1根要約2592行最大差5.32907e−15。工程16人工tests PASS。[コード/行列設定](config.json)、[再現](reproduce.md)。新学習/MDseedは発生しない。

科学・集計wall711.018489秒＋成果監査2.644697秒＝累計713.663186秒。全単位CPU641.449572秒、集計CPU45.185347秒。peak process-tree RSS297.375MiB、出力1,225,163,390bytes、near100件。科学失敗/再試行/保護停止0。原200/500ps境界を保持し元N1結果を変更しない。

数値thread設定1、OS process thread観測最大2。Matplotlib3.10.1のfont cache Timerと整合するsourceを保存、新process OpenBLAS各1threadを確認。ただし元workerのthread別ID/CPU時間ログがないため帰属はUNVERIFIED。隠さず独立審査へ渡す。[ソフト証拠](software-evidence.json)。

## E. 独立審査で重点確認する事項

1. 「参照model1だけで段階符号が生じた説明を弱める」という限定主張は妥当か。候補/M0/訓練window交絡を除去したと過大解釈していないか。
2. 全体最小RMSD・Qの区間が0を跨ぐ事実、F1/F2対F0、不利な根と他尺度を公平に扱ったか。
3. 34参照、相関frame/窓を独立Nとせず、共有F0・学習/MDseed階層と8根対応を保ったか。
4. min34の自明な絶対値低下、同argmin Qの固定集合との差を正しく限定したか。
5. 幾何相関はabsolute成果であり、更新効果/X独立情報価値の証拠と混同していないか。
6. thread観測2の資源留保、既存物理/学習資格、事後性/小N/多重尺度を十分に明示したか。

## F. 正確なファイル索引

[完全報告](review-dossier.md)、[主結果JSON](scientific-summary.json)、[主窓全対比](results/main-reference-sensitivity.csv)、[全窓感度](window-sensitivity.csv)、[図](results/reference-sensitivity.png)、[manifest](manifest.json)、[config](config.json)、[全成果SHA/費用](delivery-audit.json)、[監視終了](supervisor.json)、[計算終了](compute-complete.json)、[集計終了](analysis-complete.json)、[人工ログ](artificial-tests.log)、[M1統計再現](results/M1-root-reproduction.json)。

各固定参照はresults/1〜results/34、ensembleはresults/NMR34_MIN。全dir共通ファイルはhistory.csv、branches-s4.csv、branches-s8.csv、models.csv、state.csv、root-paired.csv、root-summary.csv、geometry-correlations.csv。[model1根表](results/1/root-paired.csv)、[model1要約](results/1/root-summary.csv)、[min34根表](results/NMR34_MIN/root-paired.csv)、[min34要約](results/NMR34_MIN/root-summary.csv)。M1−min34の枝数値差は[0.5ps](results/M1-minus-min34-0.5.csv)と[2ps](results/M1-minus-min34-2.0.csv)。

## G. 次段階

研究者指定のAstra Extra Highで独立科学審査を行う。次の研究実験・採択結論・正式C/B2は研究者が判断する。本タスクはGitHub全文回読と交付後に停止する。原9archive保持、Mac raw免除を継続し、未使用予算を新しい計算許可としない。
