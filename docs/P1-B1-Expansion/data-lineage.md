# データ系譜と情報時刻の最終照合

2026-10-27、MEASURED/DERIVED。全8根、16状態、240下流枝を完了。凍結定義は[data-lineage-plan.md](data-lineage-plan.md)で、原データを報告に合わせて変更しない。

## 祖先と連続性

各根r01–r08は同じ準備unfolded構造から異なる乱数で開始し、0–2→2–4→4–6→6–8 nsを完全OpenMM checkpointで連続する。履歴seedは1600000100+r。区間継続で再最小化/再速度生成をしない。S4とS8は同根、S8はS4の下流枝を読まない。下流240枝は選択座標から再最小化し、対応MDseedで速度を再生成する。根内の履歴継続と、下流の座標reseedは異なる物理操作である。

## 全状態共通の固定窓

|状態|M0より前の旧学習800 [ns]|時間分離検証200 [ns]|M0より後の新400 [ns]|候補/A0|
|---|---|---|---|---|
|S4（境界b=2 ns）|(0.1,1.6]|(1.7,2.0]|(2.0,3.6]|(0.1,4.0]の7,800点|
|S8（境界b=6 ns）|(4.1,5.6]|(5.7,6.0]|(6.0,7.6]|(0.1,8.0]の15,800点|

旧800から偶数位置400をF2旧成分へ使う。各窓は等間隔の異なるframe IDで抽出し、同座標や重複IDで不足を補わない。境界の時刻丸め漏洩を防ぐため、新側ID≥b/0.5 ps、旧側ID<b/0.5 psと元2 ns区間を併用する。原時刻は不変。候補と訓練の重なりはオンライン設定の一部で、汎化試験の独立splitではない。

## 監査と公開の境界

[temporal-and-SHA-audit.json](../执行证据/2026-10-26-b1-expansion/temporal-and-SHA-audit.json)は16/16状態でM0が新MD生成前、特徴が枝実行前、freeze SHA一致を確認し、結果SHA不一致0。[all-histories-readback-01.json](../执行证据/2026-10-26-b1-expansion/all-histories-readback-01.json)は連続checkpoint、全M0、対応訓練・F0再推論の工程読戻し。イベントのqualifiedはMD特徴の品質確定を示し、別task kindのfalseを科学的不合格としない。

各raw入力・出力のSHAは [raw-artifact-sha256.json](../执行证据/2026-10-26-b1-expansion/raw-artifact-sha256.json)、公開JSONのSHAと原JSONのSHAは脱敏により別物で、[public-export-index.json](../执行证据/2026-10-26-b1-expansion/public-export-index.json)が公開論理名と保存名を対応付ける。全DCD/indices/recipe/exposure/重みは許可保管先の根archiveとmetadataに残り、GitHubには全フレームを複製していない。Mac完全archiveは0/9、[保存状態](cost-and-runtime.md)を参照。
