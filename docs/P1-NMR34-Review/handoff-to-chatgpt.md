# P1-NMR34-FULL科学審査：A–G引継ぎ

## A. 現在状態

状態：**REVIEW_COMPLETE / WAITING_RESEARCHER_AND_PLANNING_REVIEW**。審査基準 `e9162145d60c4e88b5b147609b2da0ec20542cb7`。本輪は既存272単位の保存表・原実装・文献・監査証拠の照合で、新しい科学単位0、旧272件の再実行0。最終確認は2026-10-31 JST。[table-audit](evidence/table-audit.json)は11:21:54、read-only lock観測は11:23:53。

最終交付commitは本ファイルを含むGit履歴と最終返信で確定する。[remote-readback.json](remote-readback.json)には内容commitと全文照合を保存する。自己参照するSHAをファイル内へ捏造しない。

GitHub：日本語完全審査、全主窓/根/全窓の保存値抜粋、228,480窓metadata、272元JSONのSHA、検算script/ログ、費用、指摘・出典・次判断。サーバのみ：旧raw trajectory/checkpoint/全frame chunk/原ログ/9archive。Mac raw全量backupはWAIVED_BY_RESEARCHER。

本審査は同じ研究作業環境からの独立再照合で、外部研究者による盲検査読ではない。研究者科学受入れとChatGPT/領域教員の独立判断はPENDING。

## B. 状態ラベル

- **CONFIRMED**：研究者は全量終了後の独立科学審査を依頼。新実験へ進む許可はない。既存の原証拠保存・日本語・GitHub同期・Mac raw免除を継承。
- **MEASURED**：本輪285compact SHA前後一致、2,419,200算術照合、最大差6.21725×10⁻¹⁵、228,480metadata転記、17.331735秒、RSS62,296 KiB。元272件の科学測定は既存receiptを審査したもので本輪の再測定ではない。
- **DERIVED**：限定された34参照内のS4正/S8負の平均方向は支持。総合利益・X識別・固定wall-clock利益の主張には不足。
- **PROPOSED**：参照感度課題を一区切りとし、用途別資格/成果定義/最小R0カードを文書で収束させる。
- **UNVERIFIED**：物理的準備・pH/十分な平衡、普遍的な表現資格、元thread別帰属、監査末尾の厳密wall、C独立価値、B2利益。

## C. 主な科学結果

全てPOST_HOC_EXPLORATORY、独立単位は同じ準備に条件付けた8乱数履歴根。

|主窓F2−F1最小RMSD|model1 Å|34固定参照の範囲 Å|
|---|---:|---|
|S4|+0.396619|+0.352999〜+0.456842|
|S8|−0.398921|−0.441402〜−0.354038|
|二状態平均|−0.001151|−0.039509〜+0.046956|
|S8−S4|−0.795541|−0.842465〜−0.749708|

全24条件の平均方向も34/34で保持。主窓S4のCIが正なのは24/34、S8/交互差は34/34で負、全体は34/34で0を跨ぐ。参照は独立反復ではない。model1平均CI[−0.204768,+0.216556]は利益の不存在も証明しない。

model1の平均Q：F2−F1平均−0.003784 [−0.014724,+0.006674]、F2−F0平均−0.021517 [−0.040517,−0.004217]。F2−F0最大Qも−0.033978 [−0.067956,−0.003224]。最小RMSDだけで総合優位としない。一方最大QのF2−F1交互差は正の探索区間を持ち、Qの全尺度に信号がないとも言わない。

model1のS4は6根正/2負、S8は2正/6負。min34のS4は5正/3負。個々の状態での予測法則ではない。F0は旧モデル選点からのreseedであり、連続MD対照ではない。

## D. 技術・再現情報

元のproper Kabsch/28CA/Å、固定Q、全12窓×2間隔、品質・seedを維持。元コードは変更しない。bootstrapは元seed17103001/10,000根drawsであり、新規再標本化は実施していない。

新[script](scripts/check_existing_tables.py)は標準ライブラリだけで保存CSVを再集約し、旧windows.jsonからmetadataを転記する。CPU単process、GPU不可視、外部120秒・仮想メモリ2GiB保護。Python3.12.3、実行1回、失敗0。

元CSVにはwindow_status/total/valid/argmin_frameがなかった。新附表で全228,480行を補った。歴史4 ns窓8,960行はINCOMPLETE_WINDOW、下流201,600行はCOMPLETE。全窓valid=total。元200/500 ps境界差を保持。argmin_frameは0始まりlocal ID、時刻や参照k*とは区別する。

元のlock=falseは固定出力で観測値ではない。今回read-only lslocksでは対象非掲出、budget閉。本輪の観測で過去を正当化しない。元台帳713.663秒には監査末尾記帳の厳密時間が含まれず、未測留保。元OS thread2の帰属も未確定。いずれも現在の主統計を覆す不整合は示していない。

## E. ChatGPTが重点審査すべき点

1. 限定参照頑健性を受け入れた上で、未立証な総合利益とC/B2を明確に分けられているか。
2. 最小値の平均、履歴bestを超える進展、deadlineに利用可能な成果を混同していないか。
3. 8根に条件付けられた探索CIと、34参照/24窓の非独立性を十分に限定したか。
4. Q対F0の負面、各根の反転、旧幾何との相関の限界を公平に扱っているか。
5. 窓附表の追加で審査資料の可読性は満たされるか。旧CSVの単独解釈には注意が必要。
6. P/L資格を無限の事前検査にせず、現実的なHPCベンチマーク用途の受入れ条件を定義できるか。
7. 次のR0/成果契約が採択された場合にだけ実行カードを出す、という停止境界を維持すること。

## F. ファイル索引

[完全審査](review-dossier.md)、[指導教員概要](advisor-summary-ja.md)、[指摘と判定](findings.md)、[出典/読了範囲](sources-and-scope.md)、[検算再現](reproduce.md)、[証拠説明](evidence/README.md)、[算術監査](evidence/table-audit.json)、[全主窓](evidence/main-all-contrasts.csv)、[全根抜粋](evidence/main-root-extract.csv)、[全窓方向](evidence/all-window-direction-extract.csv)、[全metadata](evidence/window-metadata.csv.gz)、[元JSON SHA](evidence/metadata-source-sha256.json)、[転送SHA/lock観測](evidence/transfer-manifest.json)、[次の判断](next-decision.md)。

元の[科学報告](../P1-NMR34-FULL/review-dossier.md)、[全結果SHA索引](../P1-NMR34-FULL/compact-results-sha256.json)、[raw出力SHA索引](../P1-NMR34-FULL/delivery-audit.json)は変更せず参照する。

## G. 次段階と停止

研究者/ChatGPTの科学審査を待つ。新しい資格条件、主成果、学習recipe、時間予算、根数の採択を助手が代行しない。[次回文書限定Prompt](next-decision.md)は提案であり、R0/C/B2/MD/CVAE/LOF/NMR再実行を承認しない。

内容commit・最終遠隔検証はremote-readback.jsonとGit履歴を参照。最終SHAを返信後、実行せず停止する。

内容commit `42d520829782d0133095f47e97db20b771fcba02`：29ファイル/2,530,306 bytesをGitHub connectorで全文取得し、復号したbyte数と独立Git blob SHA-1が一致した。圧縮metadataもbinary全文を検証済み。[回読証拠](remote-readback.json)。本receiptを含む最終commitはpush後に別回読し、最終返信でSHAを報告する。
