# 資源資格と真のwall-clock計量案

本書の将来測定は未承認。現在確認した費用は[metadata](metadata-audit.json)と人工[test](synthetic-test.json)だけ。先行実測は[L2](../P1-L2/runtime-summary.json)と[B1費用](../P1-B1-Expansion/cost-and-runtime.md)。一枚GPUだから強い競合があるとは仮定しない。

## 1. 将来の資格測定ゲート

|ゲート|最小測定案|進む条件／不成立|
|---|---|---|
|R0 直列|同recipeのMD単独、train単独、inference単独、CPU LOF単独、data prep/起動を固定入力で各3反復|実cost分布と記憶量、科学レシピ・入出力一致が把握できる。各反復自体が新計算で別承認|
|R1 干渉|MD+train GPU同居、MD+CPU inference/LOF、同じ仕事量の直列総和と各3対|メモリ・遅延・公平なCPU割当・科学条件の保全を確認。空きGPU%だけで同居可としない|
|R2 終了/公開|締切近傍の安全checkpoint・DCD flush・品質判定・atomic publishと失敗復旧|deadline後frameを無償で使わないこと、台帳と出力対応の工程test|
|R3 必要性|cost割合ρ=(train+infer+LOF+prep+switch)/(MD+同費用)と干渉によるslowdownを報告|小さい費用・弱い干渉ならそのまま報告。学習量を増やして都合のよいbottleneckを作らない|

単GPU直列は現在の可実行基準。MPS/MIG、driver/system変更、他userを含む負荷注入は行わない。並行は別承認と専用資源区間がある場合のみ。各process単独/同居のVRAM・RSS・CPU/thread・power/clock（取得可の場合）・GPU utilizationを計時し、kernel active時間とprocess wallを区別する。2process同時のRAM合計は各RSSとは別。現GPU96GBを理由に性能非干渉を仮定しない。

## 2. イベントと費用schema

全eventはrun/root/policy/task/attempt、host monotonic_nsとUTC/JST、input SHA、model version、parent、stream/seed、resource allocation、状態遷移を記録する。同一hostのmonotonicで差を取り、wall時計の時刻変更をdurationへ混ぜない。

`t_data_ready → feature_start/end → decision → dispatch → worker_start → compute_start/end → data_flush_end → quality_end → atomic_available` を保存する。推論とLOFは別span、前処理/transfer/serialize/deserializeも別span。GPU共有待ち、dependency待ち、reservation待ち、起動/import、失敗attempt、checkpoint/recoveryを別status/理由にする。`available`以前の結果をpolicyへ渡さない。

|量|定義・単位|
|---|---|
|MD|初期化、最小化/速度再標本化、積分+reporter、checkpoint/I/Oを分記 [s]。nsは別列|
|train|load/data、fit、validation、saveを分記 [s]。steps/framesは別列|
|inference|loadとembeddingを分記 [s]|
|LOF|density fit、score/order、selector出力 [s]|
|launch/transfer/wait/failure/recovery|互いのevent境界と原因を定義 [s]。GPU利用率で逆算しない|
|end-to-end|time0から最終available/締切 [s]。並行時はspanの和でなくinterval union/critical path|
|resource work|CPU-seconds、GPU process-residency seconds、VRAM peak。GPU active kernel seconds未測なら未測|

直列sumの残差は「その他/未分離」と報告し、純scheduler overheadと命名しない。並行時の有効wait/overlapは二重計上を防ぐ。失敗しても消費資源を台帳から除かない。

## 3. 締切、機会費用と打切り

主候補のH=600秒はdecision後の実時間。現既存runnerはtask完了後公開なので、まず同じatomic task-publicationを採用する案。H以前に最小化しただけの起点、未公開DCD、H後に終わったtaskの成果を無料で数えない。残時間と保守的cost上限でtask admissionを行い、終端のstrandと有効MD量もpolicy結果として報告する。

安全に止められるcheckpoint/flush粒度と停止遅延の上限はR2で実測して事前凍結する。超過tailは全額記録し、厳格な同一資源結果と予算逸脱を分ける。late taskを無償drainして更新policyだけ評価時間を延ばさない。外部共有資源による停止は、root blockの欠測/再試行規則を事前設定し、結果を見てpolicyを再実行しない。

同状態U/Sに実Hを与えた成果差が機会費用込みVである。単に`train秒×推定MD進捗`を引いた量はモデル計算であり実測反実仮想と区別する。オンラインXの計算・追加I/Oも課金。資格診断L2の全156 FULL分析時間を一回更新の費用へ代用しない。

天然RMSD/Qの最終評価はH後に隔離CPUで同じ固定規則を適用し、利用可能時刻だけで対象frameを切る。policyへ結果を返さず、後評価費用も報告する。オンライン品質処理は公開前に必要なのでHに含める。

## 4. 予算と停止案

N1限定CPU評価を後日承認する場合、最初に固定history1本＋branch1本で実cost/shape/元quality照合を測る。数式の人工testとは別の科学計算承認が必要。主model1は2,048,000 frame、全34感度は最大69,632,000 frame-reference組。byte SHA監査の8.7秒をこの科学cost予測へ使わない。SVDやQのthroughputは未測である。

提案保護は単worker/thread、GPU不可視、RSS2GiB、追加出力2GiB、2h再審査点。全34感度をbuffer全量へ載せず1024程度のchunk streamingとし、frame表/34列arrayはサーバ、GitHubは全branch/root/window集計・図・SHAのみ。chunk数/圧縮方式も実装版で凍結する。追加依存を共有systemへ導入しない。

C/B2案は64rollouts×600秒=38,400秒（10.67時間）のpost-decision wall上限。12根×4ns履歴の費用は既報約52秒/nsなら約2,496秒だが、これは概算であり新測定ではない。初M0/feature/I/O、校正・停止資格・再試行・後評価と共有待機を別途積み上げる。GPU占有はwallと同義でなく、同居案ではさらに違う。R0–R2費用は未測、上限と件数を別カードで決める。残余予算を自動的な追加許可にしない。

本輪はこの予算を使用しない。MD chunk長、H、初モデル/更新steps、閾値、policy係数、根数・power、停止仕様は全て研究者審査が要る。
