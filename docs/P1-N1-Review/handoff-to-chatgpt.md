# A–G引継ぎ：N1科学審査と次の限定資格

## A. 現在の状態

- バッチ：`P1-N1-REVIEW-20261030`。基準main/N1交付commit：`2d1e8a1a304c669fc6b625dd802d7e1e680d7d3f`。実行版と今回の文書版を区別する。
- 作業状態：**COMPLETE（文献・文書・静的審査）**。新しい科学計算0、サーバ接続0、MD/訓練/推論/LOF/DCD再解析/NMR34計算0。新たな科学的受入れはPENDING。
- 既報は272/272 MD、240下流/32履歴、8根/16状態/2,048,000frame。今回の達成件数をこれらの再実行と表現しない。
- 静的確認：既報全9 CSV/JSON、30ファイルの読取り前後SHA、44,064算術等式を確認。最大差2.665e−15、bootstrap/相関の再計算なし。[確認時刻JSTと結果](static-table-audit.json)。
- 内容commit：`307054b61b65c20dd9a88705d42b96dd6d87fc26`。28変更ファイルの全文602,861 bytesをGitHubから回読し、各Git blob SHAとサイズ一致を確認した。最終検証記録版は下記の版管理規則に従う。
- GitHub：本ディレクトリの全文、原行抽出CSV、コード/文献索引・監査と共有記録。同期の実在commit、本文照合数と最終時刻は[遠隔回読記録](remote-readback.json)およびそのファイルを追加したGit commit/最終返信で照合する。自己のcommit SHAを自己文中へ再帰的に埋め込まない。
- サーバのみ：DCD、model/optimizer、全ログ、N1全frame NPZ、9原archive。今回実在/SHAを再照合していない。N1時のarchiveは存在/サイズ検査、直近の全archive SHAは別のB1/R1保存記録。Mac raw backup免除は継続。原archiveを削除しない。

## B. 状態ラベルと確認事項

|状態|内容・根拠|
|---|---|
|CONFIRMED|研究者の本作業承認は独立審査・既報読取り・文献・設計・日語文書・同期だけ。科学計算禁止。旧結果/コード/原archive保持|
|MEASURED（既報）|N1の272軌跡、約330秒CPU、42 native contacts、原SHA監査。[旧実行証拠](../P1-N1/CPU-v1/unit-audit.json)|
|DERIVED|根対応の算術整合、以下の既報解釈、コード上の窓境界/再開保護の指摘。独立した実軌跡再現ではない|
|PROPOSED|NMR34最初の2単位900秒、R0 15単位、C/B2新根・H・主成果・予測法・費用門。全て未採択|
|UNVERIFIED|nativeの安定的進捗、一般的学習十分性、MD準備/平衡、Xの独立情報、B2純利益、必要H/n/最小実用差|

## C. 主要科学結果と反対証拠

主4 ns/burn100 ps、0.5 ps、独立8根。RMSDの差は負が差の第1条件群に有利。

|既報尺度|S4 F2−F1|S8 F2−F1|同根二状態平均|S8−S4|
|---|---:|---:|---:|---:|
|枝別最小RMSD [Å]|+.396619|−.398921|−.001151|−.795541|
|枝内平均RMSD [Å]|+.161105|−.258517|−.048706|−.419623|
|平均Q|−.017404|+.009835|−.003784|+.027239|

最小RMSD平均の探索95%区間は[−.204768,+.216556]、段階差は[−1.436161,−.237645]。平均RMSDとQの段階差区間は0を跨ぐ。F2−F0 Q平均は−.021517 [−.040517,−.004217]、F1−F0も−.017733 [−.036774,−.000816]。全比較、多重性未調整、事後評価を保持する。[全数値](reported-primary-contrasts.csv)、[全窓](reported-all-window-F2-F1.csv)、[全根](reported-root-primary.csv)。

最良3.614485 Åはfolding成功判定ではない。履歴best更新はF0 22/48、F1 52/96、F2 47/96で、独立二項標本ではない。幾何とnativeの相関は尺度依存で、COMMON_A2の平均RMSD相関+.420197、Q相関−.451724もある。全てを「無関係」とまとめず、絶対指標の周辺相関と更新の対応効果・予測情報を区別する。

S4/S8では候補、親モデル、学習窓が同時変化する。固定model1でも差が残ることは評価A0だけの説明を弱めるが、XがZ/Wを超えるとはまだ言えない。B1等MD量をB2固定実時間へ外挿しない。

## D. 技術情報・再現境界・不具合

原式は28CA proper Kabsch/Å、j−i≥3のnative8Å未満42対Q。F0共有3枝、F1/F2各2学習×3MD、根内S4/S8対応。root bootstrap10,000/seed17103001を既報から読み、今回再実行しない。

静的再点検は `python3 docs/P1-N1-Review/audit_existing_tables.py`。標準ライブラリだけで既報CSV/JSONの算術・件数・SHAを読み、新ディレクトリへ原行を転記する。サーバ/モデル/DCD/NPZを開かない。科学式・原表・旧生成コードは変更しない。[入力SHA](review-input-inventory.json)。

**窓境界の所見**：4 nsのburn100は7,800点で主条件と整合するが、burn200/500は7,601/7,001点。累積floatの厳密`>`境界により理想格子より1点多い。旧結果は保持し効果の大きさは未計算。NMR比較では旧IDを再現し、格子修正と参照変更を混ぜない。

**将来adapterの改善条件**：複合frameキー、mask付きbest系列、原時刻offset、非重複cost ledger、explicit例外、run lock、再開fingerprint、phase別不変receipt。旧time guardは完了receiptと現process経過の二重加算で早期停止し得るが、既報単位費用や主値の誤りを意味しない。[詳細審査](review-dossier.md)。

最終的な既報表の算術不整合は0。交付検査器の初回はAppleDoubleメタデータを本文として読むエラーがあり、対象除外を修正して再点検した。PyYAMLの存在確認は失敗したが導入せず、標準ライブラリのみ使用した。これらは科学計算の失敗ではない。既報の失敗/保護停止、L2の巨大有限KL、学習/LOF不安定性は旧資料を保持し、報告都合で除外しない。新しい科学値や95%区間を作らなかった。

## E. ChatGPTに重点審査を求める論点

1. 最小RMSDだけの段階反転を「更新価値の状態依存」とどこまで記述できるか。Qの不利な結果を同じ重みで扱っているか。
2. model1を主のままNMR34 minを感度にする契約、可変参照Q、34モデル非iid、旧mask継承が適切か。
3. 新2単位に900秒/1e−8 Å/全34内部幾何という工程案を採択するか。全量272の資格ではない。
4. 現CVAE recipe/LOFの不安定性と、MD準備・reseed・短時間緩和に関し、次の用途でどの限定を受容し、何を別実験にするか。
5. 強ZWに既存の物理Wを残した上でX1に共通支持があるか。4根校正で多変量モデルを成立したことにしていないか。
6. 600秒、最小実用差δ_R/δ_pred、n=8は未決。C校正36、C未知32、B2別未知80の費用案を縮小/段階化する判断。148本一括実行を勧めていない。
7. 学習stepを競合演出のため増やさず、Cの情報価値とX費用込みB2の締切成果を分ける設計でよいか。

## F. 資料索引

|資料|用途|
|---|---|
|[完全審査](review-dossier.md)|数式、統計、全根、陰性、実装所見、科学判断|
|[原文献](literature-evidence.md)|Bhowmik/Ma/DeepDriveMD/Colmena、版と実験境界|
|[NMR34契約](nmr34-contract.md)|参照・式・保存・偏り・首2/全量の分離|
|[C/B2設計](cb2-design.md)|推定対象、強ZW対照、共通支持、新根/seed、情報境界|
|[費用・判定](budget-and-gates.md)|600秒/4ns/効果精度/n/未識別要因|
|[資源測定](resource-measurement-plan.md)|単独/並行を分離、実時間・公開deadline・費用内訳|
|[次カード](next-execution-card.md)|未承認の最初の2単位だけ、転記可能Prompt|
|[指導教員向け概要](supervisor-summary.md)|助言と既報の慎重な日本語要約|
|[静的監査](static-table-audit.json)、[入力SHA](review-input-inventory.json)|今回の確認日時・44,064等式・原ファイル不変|
|[主比較](reported-primary-contrasts.csv)、[全窓F2−F1](reported-all-window-F2-F1.csv)、[全根](reported-root-primary.csv)、[相関原行](reported-primary-correlations.csv)|新推定ではなく元表の完全な該当行|
|[N1旧全証拠](../P1-N1/CPU-v1/README.md)、[全272索引](../P1-N1/branch-index.csv)|元値、集約、原入力、実行/環境、保存索引|
|[B1](../P1-B1-Expansion/review-dossier.md)、[R1](../P1-B1-R1/review-dossier.md)、[Q0](../P1-Q0/review-dossier.md)、[L1](../P1-L1/review-dossier.md)、[L2](../P1-L2/review-dossier.md)|科学系譜、負面、物理/学習/参照の未解決事項|
|[Post-R1資格](../P1-Post-R1-Qualification/qualification-review.md)、[先生助言](../研究打合せ/2026-10-30-速水先生-差別化と科学評価.md)|物理系の範囲と相談背景|

原実装は[純関数](../../p1/n1_native_metrics.py)、[reader](../../p1/n1_cpu_evaluate.py)、[集約](../../p1/n1_cpu_summarize.py)。本作業の入力・ソース・文献索引は[追加出典manifest](review-source-manifest.json)、文書リンク/不変性検査は[交付検査](delivery-check.json)、push後の全文一致は[回読記録](remote-readback.json)で追跡する。

## G. 次段階と停止

推奨する次の判断は**NMR34最初の2単位資格の採否のみ**。採択しなければ現資料の審査/修正で停止する。採択して2単位がPASSでも、全量NMR/R0/新MD/学習/推論/LOF/C/B2/S3を自動開始しない。

資格の最小範囲を通過し、科学的意味・費用・共通支持・学習/物理条件を採択してから、校正の新承認を求める。研究者の科学的受入れとChatGPTの次段階判断を本書が代行することはない。
