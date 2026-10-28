# CPU復核の実行進捗

2026-10-28 JST / RUNNING、交付PARTIAL。設計59f97821、実装e703b69。

- 共有CPU/メモリ/ディスク確認済み。GPU不可視、worker1/thread1。
- サーバ小規模検査5/5 PASS。
- 入力：15,208 raw SHA一致、8根/16状態/240枝のshape/有限性/atom順/選点/凍結時刻/seed一致、9archive SHA一致。監査wall63.118034 s、CPU62.749205 s。
- ORIGINAL_HISTORY：実行中。全枝PASS前に他参照を実行しない。
- COMMON_A4/A2/MATCHED_COUNT、LOF、階層集計、最終不変監査：未実施。
- 配備時にMac AppleDoubleメタデータをmanifestへ誤登録して転送SHA検査が1回失敗。実コード/入力は不変で、メタデータを除いたv2 allowlistを全6実ファイルで検査して修正。科学結果の修正なし。

最終科学結論・独立審査・研究者受入れは未完了。B2/C予測器/S3へ進まない。
