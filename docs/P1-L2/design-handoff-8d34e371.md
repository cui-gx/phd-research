# P1-L2：独立審査向け引継ぎ

## A. 現在の状態

- 批次：P1-L2-DESIGN-v1。最終文書点検日2026-10-29 JST。**DESIGN COMPLETE、SCIENTIFIC EXECUTION NOT APPROVED**。
- 基準main：`83bac631c007366d1492330fe3355677d4f5eeaf`。Q0は`6730e493bddce42fb4d86ed93fab05cc88810268`、Post-R1設計は`3b8b7b25da85c5d5da055b093ee4c79f6ff850b7`。
- 今回の作業は資料・固定版ソースコードの読取り、日語設計、既存ID転記、行列作成、静的点検とGit同期だけ。新MD/訓練/前向推論/LOF/科学再解析/サーバ接続はすべて0。
- 提案行列36chainの実施数は**0/36（未承認）**、156評価endpointの実施数0/156。未実施を失敗や完了としない。計算の独立審査・科学受入れも未通過。
- GitHubには設計本文、予定行列、既存ID転記、入力SHA、静的監査を保存する。サーバ原DCD/80重み/配列/9archiveの状態は既報を参照し、今回再確認していない。Mac原archiveの免除を維持する。
- 本文版 `f5aaeca5a26d5a415fbf2e1b5f92d6ce7de1ee90` の配送24ファイルはGitHubから独立取得し、全文・SHA-256・Git blobを照合済み（2026-10-29 JST）。[交付検証](delivery-validation.json)に記録する。自己参照commitを捏造せず、最終配送commitは本ファイルを含むGit履歴と研究者への最終返信で確認する。

## B. 確認状態の分離

|状態|内容|
|---|---|
|CONFIRMED|研究者は既存4工程状態、4段階の歩数、3以上の独立初期化を考慮するL2設計を依頼。今回の新計算は禁止、原証拠保持|
|MEASURED（既報）|L1の80モデル完全性、各種BCE/潜在/幾何/seed診断、Q0系譜・ログ。新L2測定ではない|
|DERIVED|旧200歩・同一初期化系統だけでは学習量と独立初期化を識別できない。RECENTの改善だけで個別構造情報とは断定できない|
|PROPOSED|固定M0-200から分岐する36chain、具体seed、ablation、全156 FULL順位診断、判定/資源保護|
|UNVERIFIED|L2結果、収束/一般化/学習十分性、物理資格、探索価値、CのX追加情報、B2純利益|

## C. 科学的動機と現在の数値

既報L1のNONLOCAL RECENT平均BCEはF0=105.3166、F1=107.0408、F2=44.3003 nats/枚。F2の共通旧頻度基線は100.0909だが、臂別訓練頻度は51.7919で、臂別優位は20/32。RAW物理10近傍保存F2は0.1221、接触/時刻基線は0.3458/0.3466。全16状態の既報要約であって、今回4状態の新しい統計ではない。[L1完全報告](../P1-L1/review-dossier.md)

この不一致から、学習量、初期化、分布頻度への適応と入力固有情報、局所潜在幾何を分ける。loss低下やTop1変更を科学利益と見なさない。L2の提案規模は4状態×3初期化×3chain=36、57,600歩、144学習endpoint＋12未学習対照。2歴史根しかなく、checkpointやフレームを独立標本にしない。

## D. 主要技術仕様

- 既存mdlearn938cb80、28×28 binary contact、latent3、同RMSprop/batch4/構造/目的関数を維持する。訓練maskの変更なし。
- 3新init seedとoptimization/permutation streamを別名・別stateにする。M0学習曲線と、固定M0-200親からの追加学習曲線を分離する。子の追加1600は累計1800歩である。
- OLD/RECENTはL1の同じ200+200 ID。4状態の転記1,600行、訓練membership9,600行。既知の開発データ、M0のRECENTは事後汎化診断。
- 頻度/平均コード/5対応入替え/未学習/接触/時刻を固定対照とする。RAWが主、標準化は補助。LOFは状態内FULL同集合・k20・novelty=False、下流NOT_OBSERVED。
- 旧科学ソースコードは変更していない。静的交付検査では新CSVのCRLFが末尾空白として検出され、新CSVだけをLFへ正規化した。原CSVと全field値は不変で、科学実行の失敗はない。新実装入口は[script-design](script-design.md)の設計に留まる。実サーバ入力SHA・実乱数列・初期重みSHAの新検証は実行承認後に必要。
- 旧B1費用からfit約243秒、起動等込み粗見積り約366秒。ただし全候補前向1,840,800枚とCPU診断/LOFは別。L1比例約2.1時間は仕事差がある未校正の規模目安。2時間復核点で停止する提案。

## E. 独立審査で確認してほしい点

1. 親M0-200固定は、旧案の結果から親を選ぶ交絡を避ける一方、成熟M0の更新効果を残す。L2の最小目的として妥当か。
2. 3初期化×1更新streamで条件付き初期化差を測る範囲で十分か。全面分散分解を求めるなら別途追加24chainが必要である。
3. 平均コードと対応入替えによる非自明性検査が、時間相関を残す短いblockに対して何を主張できるか。zero-codeのみの旧検査からの改善と限界を確認する。
4. 本案のPASSは有限集合上の限定支持であり、全般的な学習十分性は未認定とする。実用同等幅のない安定性/plateauを誤認していないか。
5. 全156endpointのFULL順位を行う費用が情報価値に見合うか。削減するなら実行前の別版として固定する必要がある。
6. E0の保存配列診断だけを先に承認するか、36chain案を承認するか、なお文書修正だけに留めるか。

## F. 索引

[README](README.md)を入口として、[analysis-plan](analysis-plan.md)、[experiment-design](experiment-design.md)、[metric-contract](metric-contract.md)、[decision-criteria](decision-criteria.md)、[cost-and-scope](cost-and-scope.md)、[script-design](script-design.md)、[risks](risks-and-unidentified.md)、[sources](evidence-and-sources.md)を読む。

完全な条件表は[experiment-matrix](experiment-matrix.csv)、[checkpoint-matrix](checkpoint-matrix.csv)。実行前固定用IDは[training-membership](training-membership.csv)、[evaluation-ids](evaluation-ids.csv)。元文書/CSV/ソースコードSHAは[evidence-input-sha256](evidence-input-sha256.json)。交付/旧証拠不変性は[delivery-validation](delivery-validation.json)。将来依頼案は[proposed-execution-prompt](proposed-execution-prompt.md)。

## G. 次の判断と停止

研究者が設計採択・必要な修正・E0または最小L2の計算範囲を別途決める。方法の重要変更時はAstra Extra Highで再審査し、固定後の実装はSol Highを推奨する。モデル指定は研究者のUI選択で、自動変更したとは主張しない。

本輪は文書交付後に停止する。新MD、L2訓練/推論/LOF、P/Oの新計算、C予測器、B2、S3を自動開始しない。既存B1/R1/Q0/L1の科学的受入れ状態も変更しない。
