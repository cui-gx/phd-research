# N1科学審査とC/B2準備

2026-10-30 JST。審査基準 `2d1e8a1a304c669fc6b625dd802d7e1e680d7d3f`。
本作業は**文献・既報表・静的実装の審査と設計のみ**。サーバ接続、新MD、学習、推論、LOF、DCD/NMR34数値評価は行っていない。旧実験の値を変更しない。

**結論（DERIVED）**：N1は固定model1に対する記述的比較として限定的に支持できる。S4/S8の差は追加研究の動機になるが、Xの増分予測価値も固定実時間のスケジューリング利益も未検証である。600秒・4校正根/8未知根・1600歩を確認実験の確定条件にしない。次に提案するのは、事前指定した2軌跡だけのNMR34工程・費用資格であり、まだ実行許可ではない。

|資料|役割|
|---|---|
|[科学審査](review-dossier.md)|数式、集約、全根、陰性結果、因果・統計上の限界|
|[指導教員向け概要](supervisor-summary.md)|結果と次の判断を短く説明|
|[一次文献の照合](literature-evidence.md)|論文の実験、機構、当研究との重複と相違|
|[NMR34契約](nmr34-contract.md)|参照、選択偏り、Q、ストリーミング処理、全量評価の条件|
|[C/B2更新設計](cb2-design.md)|予測価値と方策効果、強いZ/W、データ分割|
|[費用・統計・停止](budget-and-gates.md)|時間尺度、最小実用差、根数、長軌跡の必要条件|
|[資源計量](resource-measurement-plan.md)|独立/並行費用、利用可能時刻と厳密な締切|
|[次の限定実行カード](next-execution-card.md)|未承認の2単位NMR34資格、コピー用指示を含む|
|[A–G引継ぎ](handoff-to-chatgpt.md)|次の審査の固定入口|
|[静的表監査](static-table-audit.json)|既報表44,064算術関係の照合。新推定なし|
|[入力SHA索引](review-input-inventory.json)|旧CPU-v1全30ファイルの読取り時SHA|
|[本文値](reported-primary-contrasts.csv)|主窓の全9指標×3対比×4集約の既報行を転記|
|[全窓F2−F1](reported-all-window-F2-F1.csv)|2間隔×12窓×9指標×4集約。元値そのまま|
|[全根](reported-root-primary.csv)・[相関](reported-primary-correlations.csv)|元CSVの行をそのまま転記|

旧完全表の入口は[N1 CPU-v1](../P1-N1/CPU-v1/README.md)。転記CSVは独立な新結果ではない。静的監査は `python3 docs/P1-N1-Review/audit_existing_tables.py` で再現でき、DCD・モデルを読まず、bootstrapや相関を再計算しない。

新しい文書の完成と研究者の科学的受入れを分離する。外部の独立査読は代替しない。NMR34全量、資源測定、C/B2及び物理系変更は、別の明示承認を必要とする。
