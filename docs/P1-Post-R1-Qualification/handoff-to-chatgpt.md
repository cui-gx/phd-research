# ChatGPTへの引継ぎ：R1後の科学資格審査と次段階設計

## A. 現在の状態

- 作業ID：P1-POST-R1-QUALIFICATION-20261028。実行状態：**COMPLETE（文書審査・設計）**。科学計算の完了を表すものではない。
- 基準main：d43e606755b83ddb9e71399860ef27e550662c57。入力B1：e7f438c074d02452d57b7602bba810173b22f9b1。R1設計：59f97821ae6ffe283c371f710546abf84f691642。
- 六つの依頼事項を[資格審査](qualification-review.md)、[成果指標](outcome-definition.md)、[最小設計](minimal-design.md)で完了。新しいMD/学習/推論/LOF/CPU科学再解析は0、サーバ接続0。未完了実験を完了扱いしていない。
- 最終配送確認日は2026-10-29 JST（クライアント日付）。本輪に関する独立科学審査・研究者の新提案採択はPENDING。
- 本文版commit `9bbd1e984c758c2e0cc39e3bae086d6d6860a163` の配送対象16ファイルは、GitHub接続から全文を回読し、byte数・SHA-256・Git blob SHAを照合済み。最終配送SHAは本ファイルを含むGit commitから取得する。自己参照SHAを捏造しない。push後の検証済み本文版と証拠は[交付検証](delivery-validation.json)に記録し、最終配送commitは研究者への返信とGit履歴で確認する。
- GitHubには本資料と小型証拠索引。原DCD、モデル、全loss/MDログは旧サーバarchiveに保持。現存/SHAはR1最終監査の既報に依拠し、今回の再確認ではない。MAC_RAW_BACKUP=WAIVED_BY_RESEARCHERを維持。

## B. 確認済み事項と未確認事項

|状態|内容|
|---|---|
|CONFIRMED|本輪は資格審査・設計・日語文書・Git同期のみ。固定対象/単GPU、原証拠保持、新計算禁止|
|MEASURED（既報）|8根/16状態/240下流MD、80モデル、原評価再現、9archive保持・SHA監査|
|DERIVED|同じH4でも残る幾何段階差は、A0切替だけの説明を弱める。ただしH2と不一致で、M0/候補/学習窓/初期準備の影響は未分離|
|DERIVED（今回の静的所見）|BCEはbatch総和、KLはbatch平均、train/valはbatch4対64。報告total lossは直接比較不可。evalの潜在値はmu|
|PROPOSED|独立固定参照への被覆距離改善G_R、Q0/P/L/Oゲート、E×DとM0×U対照、共同支持下の最小C問題|
|UNVERIFIED|unfolded準備・pHの妥当性、局所緩和の十分性、CVAE収束/表現の有用性、Rの代表性、Xの追加価値、固定wall-clock利益|

研究者が本輪を依頼したことは、提案した数値・方法・後続計算を承認したことではない。「R1終審後」という題名から、記録のない科学的PASSを推測していない。

## C. 重要な科学的結果と解釈

下流4ns/先頭100ps除外、平均最小dRMSDのF2−F1に対するΓ=S8−S4、8根単位：

|参照|Γ [Å]|既報探索的95%区間 [Å]|
|---|---:|---|
|ORIGINAL_HISTORY|+0.699065|[0.333987,1.068522]|
|COMMON_A4|+0.679662|[0.284963,1.090307]|
|COMMON_A2|−0.101443|[−0.553137,0.302143]|
|MATCHED_COUNT|+0.698041|[0.335141,1.067481]|

[元数値表](../P1-B1-R1/main-root-summary.csv)。H4の全体F2−F1は−0.023775 [−0.216596,0.199295]Å、主窓の六離散尺度の段階差区間は全て0を含む。r06はH4段階差が負。新データ更新の一般優位を述べない。

H2⊂H4の各点距離は減少するが、臂間差やその段階差の方向は固定されない。H2→H4ではS4/S8両方の「何が既知か」が変化する。本文に測定関数変更の恒等式を記し、物理機構と区別した。H4を有意だから選ぶことは禁止する。

P資格は用途別に分けた。同一入力の条件付き比較は残るが、初期準備・プロトン化・reseed後緩和の未検証は科学的外挿を制限する。L資格も対応制御と学習十分性を区別した。lossの集約尺度に新しい注意点があるが、F1/F2の対応実験を無効と認定したわけではない。

## D. 技術情報と再現の境界

- 科学実装は[expansion_science.py](../../p1/server/expansion_science.py)、[b1_science.py](../../p1/server/b1_science.py)、[固定mdlearn trainer](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)。今回変更なし。
- M0はold800で200歩。F1/F2は同じ親/optimizerから旧800対旧400+新400を200歩で更新。三潜在次元、RMSprop、既存batch/architectureを維持。モデル初期化seedと更新学習seedを別扱いにする。
- 80 loss.jsonのハッシュは[models.json](../执行证据/2026-10-26-b1-expansion/models.json)にあるが、今回その原本文を新規取得していない。lossの値・収束は未判定。Q0案はその小型証拠を整えるもの。
- LOFはnovelty=False。将来E/D対照ではE⊆Dを守る。新しい候補の下流結果はNOT_OBSERVED。ソースを読むこととモデルを実行することを区別した。
- 原MDは非周期NoCutoffの固定条件、履歴checkpoint継続と下流座標reseedは異なる。原archiveの絶対パスや内部ホスト情報を本資料へ載せていない。
- 科学実行は行っていない。文書作成時の一度のpatch構文エラーは適用前に停止し、内容を修正して正常作成した。存在しない設定ファイル名の読取りは実在するp1_server_science.jsonへ訂正した。静的点検器は一度AppleDoubleの._*.mdを誤読してUnicodeDecodeErrorで停止したが、通常のMarkdownだけを対象に変更し再検査した。科学出力への影響なし。文献PDFの一部取得timeout/recaptchaは索引に読取範囲を明記した。

## E. 独立審査をお願いしたい点

1. 限定した非平衡局所探索という対象に対して、P資格の要求が不足/過剰になっていないか。どの準備情報を領域教員へ確認すべきか。
2. lossのBCE/KL/batch集約とtrain/eval差の説明は固定コードと一致するか。学習不足を証拠なしに断定していないか。
3. G_Rは有限参照構造の被覆という対象を正しく表すか。未知領域の過小評価、参照の偏り、鏡映/局所構造の縮退を許容できるか。これは未承認案である。
4. E⊆Dを守る交差対照、M0とoptimizerを一体とする対照は、識別したい効果に合っているか。
5. Xの選択を既報相関で正当化していないか。Wとの情報重複と支持外予測をどう扱うか。新8根の工程案を確認的Cと誤認しないか。
6. 等MD量の効果ラベルと固定締切の更新価値を分けた順序は適切か。小さい更新費用という陰性の可能性を保持しているか。

## F. ファイル索引

- [README](README.md)：全資料の入口。
- [qualification-review.md](qualification-review.md)：MD/CVAE/R1、未識別要因、支持・不支持主張。
- [outcome-definition.md](outcome-definition.md)：指標比較、G_Rの式、参照分離、失敗/安全性。
- [minimal-design.md](minimal-design.md)：因子対照、Cの共同支持・根/seed・未知テスト・機会費用。
- [cost-and-gates.md](cost-and-gates.md)：既報秒数、例の件数/費用、未確定項、停止境界。
- [supervisor-summary.md](supervisor-summary.md)：指導教員向け日本語概要。
- [evidence-and-sources.md](evidence-and-sources.md)：E1–E13、L1–L9の正確な出典と読取範囲。
- [proposed-q0-prompt.md](proposed-q0-prompt.md)：未承認の次回依頼案。
- [delivery-validation.json](delivery-validation.json)：文書静的照合・旧証拠不変性・配送状態。
- [R1全結果](../P1-B1-R1/README.md)、[B1原資料](../P1-B1-Expansion/README.md)、[原SHA索引](../执行证据/2026-10-26-b1-expansion/raw-artifact-sha256.json)：本輪で複製・上書きしない。

## G. 次の判断

推奨はQ0の保存済みログ監査だけを先に検討すること。Q0の採否、物理準備を維持/別版化する方針、学習資格の最小カード、有限参照被覆という成果目標の採否は研究者が決める。N1/N2/C-Fの件数は費用検討用で、新しい計算許可ではない。

本輪は文書交付後に停止する。B2・正式C予測器・S3、新MD/学習/推論/CPU科学再解析を自動実行しない。
