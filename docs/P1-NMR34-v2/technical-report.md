# NMR34-v2：評価器最適化と全量実行準備

2026-10-31。基準`70427b17951ffa3ecc5f0cd228eec816685425d5`。CONFIRMEDはコード・静的点検・人工試験・予算設計のみ。実DCD評価、全272、MD、学習/推論、LOF、C/B2の新計算は0。サーバ接続も行っていない。証拠分類は人工データによるlocal CPU engineering testであり、科学結果ではない。

## 目的と実装範囲

独立[adapter](../../p1/nmr34_v2.py)を追加し、[v1](../../p1/nmr34_qa.py)・N1純関数・入力SHA・原科学結果を維持した。v2はライブラリ形式で、実データを自動探索・処理するCLIを持たない。実行担当の薄いorchestratorと対象環境のreader資格は次の承認段階で必要となる。全量本番readyとは認定しない。

|項目|v1|v2実装／制限|
|---|---|---|
|既存CA照合|逐frame NPZ反復解凍|load_ca_onceでzip容量事前検査、1軌跡1回。長さ上限は別カード|
|参照|blockごと中心化|Referencesで34×28 float64、中心化、mask、整数mask、分母を一回固定|
|Kabsch|scalar全点とchunk同時|qualify=Trueのみscalar照合。通常は批量のみ。実等価性未測定|
|保存|軌跡全R/Q/countをRAM保持|最大512frameごとexclusive NPZ、SHA付きmanifest|
|集計|固定参照のみ|34固定参照とensemble-min、12窓×2 sampling。exact quantileを維持|
|ensemble|逐frame min/argmin|同一argminのQ、M1−min差も逐frame保存|
|8Å境界|専用表なし|eligible i<j/gap≥3の全pairについてmarginとchunk内frame番号を保存|
|窓ID|再構成valid ID|sampledとvalidを別保存、窓内stride位相を固定|
|時間|全体・単位|reader/座標検証、Kabsch、Q/margin、scalar、ensemble、圧縮保存、SHA、窓読取、窓集計等の非重複wall/CPU|
|失敗保護|lock/fingerprint/監視thread|lock/排他的receipt/入力SHA/fingerprint、協調的資源callback。次資格では外部監視必須|

単worker/数値thread1と実CPU核心使用は別である。数値thread環境をimport前に設定するが、すでに別ライブラリが初期化したprocessでは効果を保証しない。新processを起動しthreadpoolとprocess-treeの実態を記録する必要がある。affinity、共有OS、ドライバ等を本実装は変更しない。

## 数式と科学出力

RMSDは28 Cαの等重みproper Kabsch [Å]。直接残差のfloat64を維持し、反射をdet補正で除外する。trace差分による近似やfloat32への保存変更はしない。Q_kは参照kの固定集合C_k＝{i<j, j−i≥3, native距離<8 Å}に対する現在距離<8 Åの整数count/|C_k|。主参照model1を固定し、ensemble-minは感度系列とする。[元契約](../P1-N1-Review/nmr34-contract.md)の科学定義は不変。

argmin同値はfloat64保存値で最小model番号。Q_at_RMSD_argminは同じ参照のQであり、max Qではない。ensemble窓のQはこの条件付けられた系列の要約。異なる固定native集合と同じ意味とは呼ばない。export_referencesはmodel、0始まりpair、分母、座標byte SHA、M1とのRMSDを独立保存する。

margin_A＝d−8 Å、strict比較は変更しない。near出力の幅1e−6 Åは工程診断のPROPOSED既定値であり、科学接触の許容幅ではない。参照のmask所属はreference-mapから追跡できる。chunk-local番号＋manifest.startが軌跡内frame IDになる。近接pairが多い人工ケースでも上限28×28のeligible部分のみを記録し、必要保存量を予算に含む。

archive_metadataで元frame/global ancestral ID、time/local time、valid/reasonsを独立保存する。原N1は独立窓ID一覧がないため、旧time/valid・規則から再構成し元件数/値と照合する証拠範囲を維持する。200/500 psの境界を丸めない。将来の理想格子感度は別出力・全枝同一規則・主結果不変での設計案にとどめる。

## 計時・メモリ設計

Timerは区間の入れ子を拒否する。readerのnext呼出しがDCD decodeと座標照合を含み、Kabsch/Q/圧縮等と重ならない。NPZ cache準備とメタデータ検査は呼出側でinput_preparation区間に入れ、全process wall・CPUとの差をresidualとして残す。窓集計は1参照列ずつ各chunkから読み、exact median/p10を計算する。近似quantileは使わない。

この集計はchunk NPZを35回読むため再解凍費用を伴う。1列ずつにより全軌跡×34行列のRAM重複を避ける設計上の取引であり、最速とは主張しない。long trajectoryでもCA cacheとID/時刻配列、1列分の集約が軌跡長に比例する。無限長の一定メモリstreamingではない。将来の各単位frame上限とRAM余裕の事前検査が必要である。

協調的resource_checkは区間境界のRSS/時間/ディスクを検査する。圧縮やSVDの途中を即時中断するOS hard capではない。次回は全process監視で300秒/900秒/RSS2GiB/出力256MiBを保護し、signal停止とreceipt監査を組み合わせる。部分chunkは残して成功と混同せず、同じ出力への再実行は拒否する。障害後の再開は新dir・成功receipt/SHAの再検証と別承認を要する。

## 人工試験・既知の失敗

[試験コード](../../p1/test_nmr34_v2.py)、[最終ログ](synthetic-tests.log)、[初回ログ](synthetic-tests-first-attempt.log)。8 test methodsを実行し全PASS。座標seed34、34人工参照、chunk長1/3/13、scalar許容1e−12 Å、exact8 Åと隣接float、Q分母差、argmin同値、24窓×35系列、品質除外/stride位相、SHA不一致、lock競合、再実行拒否、失敗receipt、cache容量・人工停止を確認した。

初回の境界testは一つの人工参照が接触0となり、空native集合保護で意図せず停止した。保護を弱めず、別の固定接触を追加して境界の検証条件を成立させた。科学データ・実装閾値は変更していない。

人工試験はMac/Python3.14/NumPy2.4.4で行った。既存サーバPython3.12.3/NumPy1.26.4/MDAnalysis2.9.0と異なる。test時間をサーバv2速度や科学costに転用しない。DCD readerのMDAnalysis API、atom-key正規化、旧窓全値再現、実RSS、輸送/ファイルI/OはUNVERIFIEDである。人工試験が通ったことだけで科学実装全面PASSとしない。

## 次の判断

[限定二軌跡カード](next-execution-card.md)と[予算案](budget-plan.md)を審査する。既存9archive保持、Mac raw免除、旧結果不変。全量実行・C/B2の判断を技術最適化から自動的に導かない。
