# P1-N1：ChatGPT独立審査の入口（A–G）

2026-10-30 JST。[準備報告](preparation-report.md)、[指標契約](native-metric-contract.md)、[C/B2案](cb2-minimal-design.md)を読み、既存の確認結論と新しい提案を混ぜずに審査してください。

## A. 現在の状態

N1-PREP-20261030：**COMPLETE_PREPARATION_ONLY**。基準main73b93ed224b45b3f62e99e92447241e9af096d8a、L2基準65fb2acc8f99774269671ceca25a411ac9ce15cd。N1科学評価0、C/B2実行0、未完了の承認科学単位0。方法の採択・実科学実行はNOT APPROVED。本文・コードを含む39ファイルのGitHub全文回読済み内容commitは`8f5ba10bb49e5245a3265d780eeaa85246a84149`。受領記録の最終commitはGit履歴と最終返信で確認する。最終チェックのJSTとGitHub実在内容commitは[交付検証](delivery-validation.json)、[回読](remote-readback.json)とGit履歴/最終返信で確認する。自分を含む未来の最終SHAを事前に作らない。

GitHubは日本語資料、全240/32対応、272ファイル監査、候補64行列、pure functions/test、SHAとcompact evidenceを保存する。原DCD・モデル・ranking arraysと9archiveは許可サーバに保持。新しい論文PDF/原著XML・公開codeの参考コピーはlocalのみ、URL・SHA・確認範囲を共有する。Mac raw全量backup免除を保持する。

## B. 状態を区別した確認事項

- **CONFIRMED**：研究者は文献・方法設計・静的審査・data inventory・人工testだけを承認。対象・物理系を変更せず、新MD/train/推論/DCD科学評価/LOF/benchmarkをしない。
- **ADVICE_RECORDED**：速水先生は差別化、native RMSD/latent/効率、条件整合と溶媒近似の限界を指摘。詳細参照/τ/新計算を承認した意味ではない。[原記録](../研究打合せ/2026-10-30-速水先生-差別化と科学評価.md)。
- **MEASURED_METADATA**：272 DCD/PDBのbyte SHA/頭部/CA key、80checkpoint byte hash、96ranking hashを確認。model load0、DCD座標decode0。固定PDBはmodel1/34NMR各28CA。[receipt](metadata-audit.json)、[参照](reference-static-audit.json)。
- **MEASURED_ENGINEERING**：人工22test、失敗/error0。[test](synthetic-test.json)。実native値の正しさや実DCD evaluatorの完成ではない。
- **DERIVED**：先行研究と大きい重複。Q定義/情報条件をそろえない成果対比は不可。
- **PROPOSED**：model1 r/Q主候補、34感度、未定τ、64rollout案、H600秒、新根/feature/資源計量。未採択。
- **UNVERIFIED**：B1のnative進捗、P/L十分性、XのZW超過価値、同wall純利益、singleGPU干渉、論文独立新規性。

## C. 科学的に重要な結果と未結果

今回の新native科学値は**0**。B1をnativeで事後評価する時はPOST_HOC_EXPLORATORY。元B1/R1の結果・L2の巨大KL/部分支持を不変に保つ。

原文照合で重要だったのは、DeepDriveMD2022が12h×10回のnative比較を既に行い、良い成果はnative-guided selectorを含む点。固定時間という条件自体は新規ではない。MaのBBA最小4.44Åは成功閾値でない。Lee2019のexplicit未fold例はVHPで、FSD-EY全般へ拡張しない。

Bhowmik Qの8Å/75%/1.1Å条件をmodel1単一参照や34NMR共識と同一視しない。Q_CA8_M1_G3_LTと、参照集合依存のQ_CA8_BASIN75_G3_LE_PROPOSEDを明確に分け、後者の忠実再現は未確認。実native pair数も未計算。

## D. 技術情報と再現の境界

[全240対応](branch-index.csv)と[32history](history-index.csv)にroot/state/seed/親SHA/選点frame/元DCD/実行順を保存。各state F0=3、F1/F2=各2学習×3MD。F0共有、8独立random roots（同一準備構造条件付き）、S4/S8反復という階層。

[pure functions](../../p1/n1_native_metrics.py)は対応済みarrayだけ、[metadata](../../p1/n1_metadata_audit.py)はbyte/header/stringだけ。原科学コード変更なし。N1 DCD reader、quality join、全窓/34参照の本体は未実装。保存candidate embeddingはあるが下流全frameの潜在はなく、新forwardなしでは全下流図は作れない。

metadata wall8.725239s/CPU8.095469s/RSS26.473MiB、人工tests wall0.058995s/RSS37.793MiB。起動/転送の全費用ではなく、科学評価costの予測にも使わない。GPU不可視、数値thread1、既存環境版をmetadataだけ確認。原archive存在/sizeは確認、9全量hash再実施なし。テストソースSHAと実配備一致を照合する。

取得制限・誤ID除外・公開code branch確認・PDF抽出警告を[報告](preparation-report.md)と[sources](sources.json)に記録。新しい科学計算・科学失敗はない。独立科学審査は未実施。

## E. 優先的に審査すべき論点

1. model1のr/Q1を近似物理モデル内の主進捗としてどこまで使うか。34-min、Q75の別定義/未確定集合とτをどう採択するか。
2. nativeをpolicyへ渡さない条件で先行法と比較する意味。native-guidedを同情報baselineと誤認していないか。
3. 既存Wは物理summaryを含む。X3/X4の冗長性と強ZWを維持しても、X1等に共通支持・追加情報があるか。
4. 4calibration/8blind案では高次元fit・powerが足りない可能性。Cの単一乱数V_obsを真の期待価値と扱っていないか。
5. CONTINUEは連続checkpoint、他policyはreseed。policy差は複合行動差。強ZW対Xの方が直接増分対照である。
6. 決定後Hと全campaign予算の違い、atomic公開とdeadline tail、未測のGPU干渉・実costを先に資格測定すべきこと。
7. P/Lの準備・pH/平衡・KL/seed問題と新版recipe採択をN1から自動承認していないこと。

## F. 証拠索引

[README](README.md)が全資料入口。[準備報告](preparation-report.md)、[native契約](native-metric-contract.md)、[先行行列](related-work-matrix.md)と[CSV](related-work-matrix.csv)、[data readiness](data-readiness.md)、[C/B2](cb2-minimal-design.md)、[64行候補](future-experiment-matrix.csv)、[費用/公開](resource-and-timing.md)、[判定](decision-and-stop.md)、[証拠境界](evidence-boundary.md)、[指導教員向け概要](supervisor-summary.md)。

実証拠は[branch](branch-index.csv)、[history](history-index.csv)、[16state](state-index.csv)、[MD SHA/header](MD-file-audit.csv)、[metadata](metadata-audit.json)、[reference](reference-static-audit.json)、[22test](synthetic-test.json)/[log](synthetic-test.log)、[入力保護SHA](evidence-input-sha256.json)、[source log](sources.json)、[出力SHA](output-sha256.json)、[交付検証](delivery-validation.json)、[GitHub回読](remote-readback.json)。原ログ・trajectory/modelはサーバ原領域、GitHubへrawを上げない。

## G. 次の一段階と停止

研究者/ChatGPTが本設計を審査し、修正・採択・限定N1 CPU実行カードを別途判断する。今回の同意では実N1/C/B2/資源benchmark/追加model/MD/物理体系変更を実行できない。残りの科学資格・閾値・recipe・予算を実装者が黙って決めない。交付・回読後に停止する。
