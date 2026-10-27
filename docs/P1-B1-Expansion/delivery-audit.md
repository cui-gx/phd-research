# B1 Expansion：文書交付の点検

2026-10-27。技術点検であり、独立科学審査・研究者受入れではない。最終の機械点検とSHAは[交付点検JSON](../执行证据/2026-10-26-b1-expansion/report-delivery-audit.json)、同期はpush後のGit履歴と[回読証跡](delivery-verification.json)を参照する。回読証跡は実際の成功後にのみ登録する。

## 18要件とA–G

[完全報告](review-dossier.md)の節1–18は交付要件の番号と一対一対応する。

|要件|報告内の場所と補足資料|
|---|---|
|1 目的/境界、2 Pilotとの差、3 凍結/実行|節1–3、analysis-plan、failures-and-amendments|
|4 完了数、5 モデル/データ/seed、6 時刻/祖先|節4–6、data-lineage、model-training、全行列|
|7 候補、8 代理定義、9 全配対|節7–9、candidate-selection、scientific-metrics、paired-results|
|10 根/状態、11 乱数、12 X/Z/W|節10–12、randomness-analysis、state-dependence-analysis|
|13 実費/失敗/保存、14 正負/不一致|節13–14、cost-and-runtime、全6離散設定|
|15 仮説の支持、16 妥当性|節15–16、statistical-limitations、data-quality|
|17 進行条件、18 研究者判断|節17–18、reproduce、next-stage-recommendation|

[引継ぎ](handoff-to-chatgpt.md)のA–Gに、版/状態、ラベル、主要値、技術/seed、審査問題、全索引、未承認案を記載した。最終SHAを実行版SHAで代用せず、回読済み版を同期証跡とGit履歴に残す。

## 今回の確認

- 既存CSV/JSONの表整合はサーバCPUでPASS、全入力と新コードのSHAを登録。MD/訓練/GPU推論の新規実行0。
- 既存3図を目視し、元CSV/特徴と描画80点を照合。図を事後加工せず、τ0非掲載・軸範囲・不確実性未表示も開示。[図表監査](figure-and-table-audit.md)。
- 18節・A–G、全主要比較、8根の値、全6離散条件、乱数・陰性・尺度不一致、X/W重複、時点間A0変化、モデル年齢の名称訂正を保持した。
- 新規公開文書/コード注釈は日本語。原科学データ、既存41公開証拠、凍結科学ソース、seed、行列、指標を変更しない。ルートREADMEの既存並行変更はcommit対象外。
- 相対リンク/画像の実在、元公開SHA、報告用CPU出力のSHA、Git差分の空白を点検する。秘密鍵/接続情報/内部ホスト/個人資源名を追加しない。
- 科学計算COMPLETEと研究交付PARTIALを分ける。Mac完全backup0/9、環境未清掃。VPN復旧後も今回転送再開0。独立審査/研究者受入れPENDING、S2独立終審INCOMPLETE、B2/C/S3未承認。

## 残件と停止

保存の閉鎖は未完了。次の判断は①独立科学審査、②バックアップを別途再開するか、③次の問いと新しい限定仕様を承認するか。現在の文書作成許可では追加計算/転送を行わない。点検合格は科学的優越性や全研究段階PASSを意味しない。終了後に停止する。
