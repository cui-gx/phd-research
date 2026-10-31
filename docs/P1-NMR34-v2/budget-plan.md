# 全量272の予算・分割案（PROPOSED / 未承認）

2026-10-31。2,048,000frame、32履歴×4,000、240下流×8,000。v2実測は0。v1の混合線形8.206h／層別9.369hは比較シナリオであり、最適化後の速度・上界ではない。

## 時間の算式と不確実性

T_total＝T_start/inputSHA＋32T_h4000＋240T_d8000＋T_global_audit。各TをCA cache、DCD/座標照合、Kabsch、Q/margin、ensemble、圧縮、SHA、window read/aggregation/save、residualに分ける。CPU秒、wall秒、CPU/wall比、read/write bytesと実RSSを記録する。二単位ではI/O共有負荷・根間ばらつきを推定できず、bootstrap CIや「十分高速」を主張しない。

全量を別途認める際も最初の層別小batchで速度を再測定し、枠内の予測残時間と安全余裕を研究者が確認する。単位300秒またはscience累積2hに達した場合は停止・報告する案であり、残時間の自動追加はしない。900秒の次回資格予算は全量枠ではない。

## RAMと保存

R/Q/countの無圧縮本体は1,253,376,000 bytes。CA cacheは最大8,000×28×3×8＝5,376,000bytes（float64の場合）、chunk512のR/Q/count本体313,344bytes。SVD/residual/距離matrix/近接表/NumPy内部copyが別に必要。512×34×28×3×8の直接残差だけで11,698,176bytes。これらは算術上の配列容量でありRSS測定ではない。RSS2GiBの適合は未検証。

34参照付近のnear表は最悪全eligible pair/frameとなる。gap≥3のeligible数325、二整数pair＋frame＋marginをint64/float64で記録すると1frame最大10,400bytes、全量で約21.30GB追加し得る。したがって2GiB出力を一般的上限とはできない。near件数の実測と圧縮率が必要で、上限時は停止し、対象pairや不利枝を削らない。

通常nearが疎であることも未検証。全量の必要予算＝chunk全配列＋near実測外挿＋ID/品質＋24窓×35系列×272＋SHA/ログ＋一時出力＋監査余裕。圧縮率の保証はしない。chunkごと直接保存し、全軌跡の二重圧縮ファイルを作らない。既存raw9archiveと新出力を別に保全、Macへraw全量移送しない。

## 分割と停止

実行順・全272行列を事前凍結し、1workerで順次実行。各単位に入力/参照/コード/config fingerprintと成功receiptを置く。batch開始前に他ユーザ占有・予約/許可、CPU/RAM/ディスクを再確認。全体lockと単位lock、不可変manifestで二重起動を防ぐ設計が必要。単位成功は前後入力SHAと全出力SHAの一致後にのみ認定する。

現在は数値coreと単位保護libraryを実装し、全体orchestrator/外部watchdog/永続累積budget ledgerは未実装である。全量開始の必須prerequisiteに残す。途中停止後は成功単位を上書きせず、inputSHA/configを照合した承認済み復旧手順だけで継続する。
