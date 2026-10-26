# B1 Expansion：独立履歴と更新効果の探索的検証

2026-10-26。研究者承認済みの実験範囲を登録する。**18:19 JSTに実科学計算を開始した。実行中、全結果は未確定。** Sol Highを手動選択して継続し、自動変更しない。

8根×連続8 ns、各4/8 nsで16状態。F0は3 MD、F1/F2は各2学習seed×3 MDseed、各4 ns、下流240本/960 ns、履歴64 ns。合計1,024 ns。F0を二つの学習ブロックへ複製して独立数を増やさない。B1の等MD量と、未承認のB2固定壁時計を区別する。

[事前計画](analysis-plan.md)、[全行列](experiment-matrix.md)、[乱数](randomization-plan.md)、[指標契約](metric-contract.md)、[データ系譜](data-lineage-plan.md)、[資源と復元](resource-and-recovery-plan.md)を最初の科学GPU実行前にpushし、遠隔回読する。生物学的最適値の認定ではなく、承認範囲内の実行用パラメータ固定である。

Cの前置診断として決定前X/Z/Wと効果・ノイズを記述する。正式C予測器、B2/オンライン方策/S3、独立準備構造の追加は実行しない。陰性、不一致、欠損も保存して終了後に審査を待つ。旧S2独立終審はINCOMPLETEのまま。

## 実装と審査資料

[実機前検証](implementation-and-preflight.md)、[データ系譜](data-lineage.md)、[学習](model-training.md)、[候補選択](candidate-selection.md)、[物理代理](scientific-metrics.md)、[品質](data-quality.md)、[統計上の限界](statistical-limitations.md)、[再現](reproduce.md)、[教員向け概要](supervisor-summary-ja.md)、[修正記録](failures-and-amendments.md)。結果・費用・ランダム性の集計は完了後に追記する。開始時刻は実制御器記録で、完了を意味しない。

[最新の実行進捗と収集境界](execution-progress.md)。全行列・最終科学審査の完了とは異なる。

重要：[モデル年齢フィールドの名称訂正](implementation-errata.md)。原データと凍結数値は変更しない。
