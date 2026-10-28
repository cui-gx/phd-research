# CPU復核の実行進捗：最終記録

2026-10-28 JST。CPU_REANALYSIS=COMPLETE、RESULT_AUDIT=PASS。独立科学審査・研究者の科学的受入れはPENDING。GitHub交付の確定値は実際の最終commitと遠隔回読証跡で示す。

- CONFIRMED：設計59f97821の限定CPU復核。原B1/元データ/seed/科学条件は変更しない。
- MEASURED：15,208原ファイル、9archiveのSHA/実在、8根/16状態/240枝の原子順・frame ID・凍結時計・実起点・系譜を検査しPASS。終了時再照合もPASS。
- ORIGINAL_HISTORY：240/240 PASS、17,280連続値と全フレーム最小距離の実測最大誤差0、整数/ID完全一致。不一致を修正して通した事例はない。
- 四参照：全960論理条件（720実評価＋240同一参照alias）、11,520連続/69,120離散行、全12時間窓、欠測0。
- 対応差165,888行、状態27,648行、根段階13,824行、8根要約6,912行、参照分解3,456行、乱数36,864記録。共有F0を独立複製にしない。
- 保存embedding：FULL80再fit＋subset80 fit、全240診断行。FULL全score/順位再現、F0-repeat16一致。新Top1の未実行下流はNOT_OBSERVED。
- 科学段階wall合計6,999.449662 s、CPU6,996.298536 s。報告生成wall5.824955 s/CPU5.808943 sは別記。ピークRSS307.621 MiB、単worker/thread1、GPU不可視、GPU/MD/学習/モデル推論0。
- 初期境界検査5件/追加境界・階層検査9件PASS。科学停止/失敗0。AppleDouble配備manifest失敗1回と、派生証拠伝送完了前のEOFErrorは[交付失敗記録](delivery-notes.md)に保持した。科学条件・数値変更なし。
- [完全報告](review-dossier.md)、[A–G引継ぎ](handoff-to-chatgpt.md)、[全表索引](README.md)、2図、[実誤差](original-reproduction-accuracy.json)、[最終入力監査](final-integrity.json)、SHAと再現コードを作成した。

DERIVED：主平均距離のΓは共通H4 +0.679662 Åだが共通H2 −0.101443 Åと不一致。全6離散尺度の区間は0を含み、全体F2−F1優位は未確認。XのZ/Wを超える価値、B2純利益、物理P/学習L資格は未識別・未確認のまま。

科学終了は15:54:23 JST。以後は文書整備・SHA/構造・伝送検証のみ。実行器/監視器は自然終了し、新バッチを起動しない。9原archiveと既存環境は保持、Mac原archive転送0。本輪を閉じ、研究者・ChatGPT審査を待つ。B2/C予測器/S3へ自動進行しない。
