# 品質、完全性、科学資格と保存の判定

2026-10-27。科学計算COMPLETE、研究交付PARTIAL。[実測validation](../执行证据/2026-10-26-b1-expansion/validation.json)は下流240/240 MD・240/240評価、16状態、1,024成功task/科学task失敗0を示す。予定値は削除していない。履歴32区間/64 ns、M0 16、追加学習64、推論96も完了。

## 固定品質規則と結果

504原子/28残基/Cα対応、有限座標・54角、拘束残差≤0.01 Å、隣接Cα2.5–5 Å、ペプチドC–N0.8–2 Å、非隣接残基重原子距離≥0.8 Å、準備構造に対する側鎖手性。全下流8,000×240=1,920,000点が粗条件に合格した。全枝で実投入座標=選択座標、小集合厳密距離と分割計算の差0 Å。[quality.json](../执行证据/2026-10-26-b1-expansion/quality.json)は枝ごとの入力SHA・代表時刻・原配列のSHAを保持する。

合格は粗い幾何破綻の検出結果であり、pH・プロトン化・十分な平衡・自然な動力学集団・生物学的妥当性は認定しない。初期unfolded作成史は依然UNVERIFIED。下流reseedと再最小化による緩和、100 ps除外の十分性、NoCutoff/GBn2への外挿は制約として残す。温度・エネルギー原ログはrawのsim.csvとしてSHA索引に残るが、本輪文書作成で全系列の新たな物理資格判定は実行していない。

## 完全性・時間合法性・表整合

[temporal-and-SHA-audit.json](../执行证据/2026-10-26-b1-expansion/temporal-and-SHA-audit.json)は全16状態のM0→新MD→状態凍結→下流開始の順序とSHAを確認。公開41ファイルを照合、全80checkpointをCPU読戻し。[report-review-statistics.json](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json)は41,472対応、6,912状態集計、3,456根集計、432要約/区間、9,216ノイズ記録の数値を再照合し、誤差最大は相関の丸め1.12×10⁻¹⁶、他カテゴリ0。整合性は独立した科学審査ではない。

保護停止2回は記録し、科学task失敗0に隠さない。復元前は成功入出力と要求SHAを検査し、成功taskを再実行しなかった。公開ログの同名衝突は別名保存、旧証拠は不変。[失敗の全履歴](failures-and-amendments.md)。

## 可用性と未完了ゲート

[public-export-index.json](../执行证据/2026-10-26-b1-expansion/public-export-index.json)は公開ファイルと原論理名、[raw-artifact-sha256.json](../执行证据/2026-10-26-b1-expansion/raw-artifact-sha256.json)はraw相対パスとSHA。raw JSONと脱敏後JSONのSHAは区別する。サーバ9archiveとそのbyte/SHAは [post-compute-status-20261027.json](../执行证据/2026-10-26-b1-expansion/post-compute-status-20261027.json)。Mac完全backup0/9、未検証断片のみ、清掃未実施は [report-backup-status.json](../执行证据/2026-10-26-b1-expansion/report-backup-status.json)。今回転送を再起動しない。

文書作成・工程監査・科学的解釈・独立審査・研究者受入れを分ける。全科学データがGitHub上で復元可能という主張、唯一の確認的評価器資格、B2/C/S3の開始資格はここで与えない。
