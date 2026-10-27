# native参照なしの候補選択と実MD入力

2026-10-27、MEASURED/DERIVED。候補同一性と物理的起点差を確認した。これは候補の科学的最適性や折り畳み性能の認定ではない。

S4は100 ps以後の履歴7,800点、S8は15,800点。同状態全臂は同じ候補SHA。既存CVAE predict（batch64、seed2026102671）→LOF（neighbors20、Minkowski p2、novelty=False、n_jobs2）→negative_outlier_factor_昇順→同点global ID昇順でTop1を選ぶ。folded/native RMSDは使わない。全順位/埋込み/score、Top1/10/100、原DCDとのID対応は許可保管先に保存し、GitHubには比較表とSHAを置く。

|比較|Top1相違 / 比較数|起点dRMSD平均 [Å]（範囲）|角RMS平均 [度]|Top10 / Top100共通数の平均|
|---|---|---|---|---|
|F2-F1|32/32|3.7035 (1.3766–6.4094)|49.6380|0.3750 / 7.6875|
|F2-F0|31/32|3.3812 (0.0000–6.4094)|47.1590|0.2500 / 7.0625|
|F1-F0|29/32|2.5184 (0.0000–4.8908)|39.0602|1.0938 / 12.4688|

Top-kは共通IDの**個数**で、Jaccard率ではない。比較数32=16状態×2T。F0を2Tで対照に使っても独立F0候補を増やさない。F2−F0の1比較、F1−F0の3比較はTop1が同じでdRMSD=0。異なるIDでも同等構造かどうかは物理距離で別に読む。今回F2−F1の全32対はIDと構造に差があり、最小dRMSD1.3766 Åだった。

F1/F2各15/16状態で学習seedによってTop1が変わった。F0の反復推論16状態は同条件で一致を工程読戻し済み。全240下流枝について選点から抽出した全原子座標と実MD初期配列の完全一致、粗品質8,000/8,000点を確認した。同点や同起点を理由に枝を再選択しない。

証拠：[selection-comparisons.csv](../执行证据/2026-10-26-b1-expansion/selection-comparisons.csv)、[quality.json](../执行证据/2026-10-26-b1-expansion/quality.json)、[all-histories-readback-01.json](../执行证据/2026-10-26-b1-expansion/all-histories-readback-01.json)、[report-review-statistics.json](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json)。LOF scoreのSpearmanは同CSVにあり、定数は欠損扱い。順位や起点が変わっても、下流幾何探索の正負は[対応結果](paired-results.md)の独立な問いである。温度・乱数再播種・再最小化も下流応答に関与する。
