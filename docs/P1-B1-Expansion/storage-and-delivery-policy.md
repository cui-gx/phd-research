# B1 Expansion：保存先と技術交付の現行方針

2026-10-28、研究者CONFIRMED。変更対象は資料保存・技術交付だけで、研究対象、凍結実装、実験条件、seed、データ、結果を変更しない。

## 保存先と変更履歴

|資料|保存先と検証|
|---|---|
|報告・実装・試験・全行列・完全構造化統計・3図・SHA索引・実行/監査証拠|GitHub cui-gx/phd-research main。実際の遠隔回読とblob/内容照合が必要|
|GitHubに含めないDCD・モデル重み・完全原ログ等|既存許可サーバの8根＋metadataの9archive。元位置で保持し、実ファイルのbyte/SHAを検査|
|Mac原科学archive全量複製|WAIVED_BY_RESEARCHER。旧0/9は正しい歴史で、未達の必須作業ではない|
|Macの未検証103,972,864 bytes断片|残存事実のみ記録。本タスクで伝送・削除・清掃しない|

2026-10-27の文書/JSONのPARTIAL、0/9、双端backup待ち、backup後清掃という記録は、その時点の事実/運用条件として保存する。**2026-10-28以後、Mac全量複製がないことだけを技術交付の阻害条件にしない。** 過去の実測ファイルや凍結計画を遡って修正しない。今後の別実験へ無条件に一般化する規則でもない。

## 独立した状態

|項目|現行の扱い|
|---|---|
|SCIENTIFIC_COMPUTE|COMPLETE：既存8根/16状態/240下流MD・評価、追加計算なし|
|RESULT_AUDIT|PASS：既存の時間/SHA監査とCPU表照合。新しい統計解析はしない|
|GITHUB_EVIDENCE_DELIVERY|実際の検証結果を[delivery-status.json](delivery-status.json)と遠隔回読記録で確定|
|MAC_RAW_BACKUP|WAIVED_BY_RESEARCHER|
|SERVER_RAW_ARCHIVES|RETAINED_SHA256_VERIFIED：9/9、20,223,932,863 bytes|
|INDEPENDENT_SCIENTIFIC_REVIEW|PENDING|
|RESEARCHER_SCIENTIFIC_ACCEPTANCE|PENDING|

サーバarchiveは[今回の完全SHA読戻し](../执行证据/2026-10-26-b1-expansion/storage-policy-server-verification-20261028.json)で全9ファイルの実在/サイズ/SHAが既存manifestと一致した。元[2026-10-27保存記録](../执行证据/2026-10-26-b1-expansion/post-compute-status-20261027.json)のlocal_copy_pendingは旧規則の履歴で、ファイルを修正しない。

## 技術交付の閉鎖条件

1. 指定報告・全既定結果・コード/行列/seed・図・SHA/監査証拠がGitHubへ反映され、実際に回読確認されている。
2. GitHubに置かないrawについて、既存許可サーバの9archiveが実在し、元manifest SHAと一致する。
3. 原収集の退出を確認し、新たなMac転送を開始していない。
4. 原科学条件・結果・凍結コードに変更がなく、0/9の歴史を保ちつつMac要件の取消を明記する。

これらの実検証後、技術交付だけをCOMPLETEにできる。科学的優位性・独立審査・研究者受入れは別で、PENDINGのまま。環境やサーバarchiveの清掃は閉鎖のために勝手に実行しない。科学B2/C/S3を始める許可でもない。

## 退出、再現、同期

[収集退出の確認](../执行证据/2026-10-26-b1-expansion/storage-policy-collector-check-20261028.json)では登録PIDは不在、一致する収集プロセス0。既存のNEEDS_VPNは過去の退出理由であり、今後の「Mac伝送再開待ち」を意味しない。既存archiveを消さず、読み出しが必要な再現は研究者の許可とサーバの共有資源規則に従う。

[再現仕様](reproduce.md)の旧「Macへ保存」「双端検証後清掃」は旧運用履歴として読む。新しい保存先と現行状態は本書、[交付監査](delivery-audit.md)、[固定引継ぎ](handoff-to-chatgpt.md)、delivery-status.jsonを優先する。新しい科学計算やデータ移行は行わない。

## 既存controller終了状態の扱い

サーバの旧 `ANALYSIS_ARCHIVED_AWAITING_LOCAL_BACKUP` は2026-10-27にプログラムが終了した時の履歴であり、今後Mac転送を再開する指示ではない。元run/status・archive manifest・失敗記録を書き換えず、2026-10-28以後の運用判断はdelivery-status.jsonと研究者の最新指示から行う。旧delivery-verification.jsonも前回報告の実際の回読証跡として保存し、本政策の最新回読は別のstorage-policy証跡に残す。
