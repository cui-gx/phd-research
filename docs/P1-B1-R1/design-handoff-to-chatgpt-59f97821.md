# P1-B1-R1：ChatGPTへの引継ぎ

## A. 現在の状態

2026-10-28 JST。**設計文書COMPLETE、CPU再解析NOT APPROVED / NOT RUN。** 読取基準commitは`e7f438c074d02452d57b7602bba810173b22f9b1`、科学実行版は`40a911e1f36d1365fc5ee7d8753a7feb1edd964d`。本交付の最終SHAはpush後のGit履歴・最終返信で確認する。自分を含むcommit SHAを事前に捏造しない。

既存B1の240下流MD・1024成功科学taskは完了済み。本R1では新task0、サーバ接続0、科学数値再計算0、GPU使用0、旧報告更新0。GitHubへ追加するのは日本語設計・静的入力目録/点検、研究協作規則と交接のみ。rawは元サーバarchive、Mac全量複製はWAIVED_BY_RESEARCHERのまま。

## B. 状態を分ける

- **CONFIRMED**：研究者はR1の設計・文書・必要な静的点検とGit同期のみを承認。旧科学資料を保護し、終了後に停止する。
- **MEASURED（既存）**：B1の実行/保存事実は[現行交付状態](../P1-B1-Expansion/delivery-status.json)とその証拠による。今回の新測定ではない。
- **DERIVED（方法上）**：同じ枝の評価参照だけを変更した差は計算的に分離可能。候補/M0の生成効果は同時には分離できない。
- **PROPOSED**：COMMON_A4主再検証、A2/等点数感度、保存embeddingのLOF診断、全指標/8根統計、CPU費用枠。
- **UNVERIFIED**：共通参照での段階差、制限集合でのTop1、その下流効果、物理/CVAE資格、C/B2の成立。

## C. 主要な科学的論点

既報主幾何Δ21の同根S8−S4は平均+0.699065 Å、8/8根で正。一方全体Δ21は−0.014074 Å、探索的95%区間[−0.209151,+0.210466] Å。出典は[既存8根×3比較（24行）](../执行证据/2026-10-26-b1-expansion/report-main-root-effects.csv)と[既報統計](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json)。本輪は数値を再生成していない。

評価参照はS4=H4、S8=H8で、H8が増えると各枝の最小距離は下がるが、群差Δ21は上下どちらにも動ける。共通H4で両段階を測り直すことにより、ΓN−ΓC4=D8(H8)−D8(H4)を求める設計とした。ただしH4基準のS8成果は「S8でまだ未知だった領域」ではなく「早期履歴からの変化」である。

候補集合制限は保存embedding上の選択機構だけを検査する。新Top1に実行済みMDがあるかを推測せず、未観測Yを作らない。全6連続量・全6離散尺度・元12時間窓を保持する。角指標は参照依存、Rg/Q8は参照不変である。

## D. 技術情報

元データのスキーマ・論理パス・SHAを[data-index](data-index.md)と[input-inventory.json](input-inventory.json)に登録した。下流特徴は`{branch}-md-prep/science/features.npz`、順位は`{state}-infer-{label}/science/ranking.npz`。公開CSVだけでは別参照への最近傍を復元できない。

実装案は別CPUモジュールで旧ソースを保護する。科学seedは不変、解析bootstrapは元1604000001を提案。8根を再標本化し、同根S4/S8・全指標・参照法・共有F0を束ねる。学習/MDseedのブロック番号が同じでも段階間の実seedは異なる。1セル1本の2×3設計から純交互作用分散を主張しない。

## E. 審査を依頼する点

1. 共通H4への問いの変更と、当時H_sに対する新規度の問いを並列に保つことに同意するか。
2. A2と等点数の補助条件は十分か。結果を見て後から有利な参照を選ばない固定条件として妥当か。
3. 候補の出所・LOF診断を機構記述に留め、反実仮想のYやX因果効果を作らない境界が十分か。
4. MD物理資格とCVAE学習十分性をR1とは別審査にすること、既存8根を未見最終テストにしないことを確認する。

## F. 全資料への入口

[README](README.md)／[計画](analysis-plan.md)／[データ索引](data-index.md)／[スクリプト設計](script-design.md)／[判定表](decision-criteria.md)／[費用](cost-and-scope.md)／[未識別交絡・別資格](unidentified-confounders.md)／[出典](sources-and-review-notes.md)／[入力目録](input-inventory.json)／[静的検査](static-checks.json)／[未承認の次回依頼案](proposed-execution-prompt.md)。元B1報告は[こちら](../P1-B1-Expansion/review-dossier.md)。

## G. 次段階

唯一の次の行動は研究者・計画側によるこの設計の審査。採用する場合は別途「CPU再評価を実行してよい」と明示承認し、対象版/条件/運用枠を確定する。単なる本設計の受取や文書COMPLETEを実行許可にしない。B2・C予測器・オンライン方策・S3、新MD/学習/推論は含まない。独立科学審査PENDING、研究者科学受入れPENDINGを維持して停止する。
