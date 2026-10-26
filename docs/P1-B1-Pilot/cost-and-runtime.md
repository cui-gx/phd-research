# 計算費用と時間境界

本輪は固定MD量であり、固定壁時計の方策評価ではない。GPU合計の人為的時間上限は設けず、承認範囲を8 MD（共通2本＋下流6本）、M0/4更新、統一推論と必要CPU評価に限定した。単体timeoutは異常保護で、追加実験の許可ではない。

## 費用を分ける

- 共通準備：旧2 ns、品質/旧pool、M0、新2 ns、品質/決定pool。三臂に重複加算しない。
- 臂別更新：F1/F2の200歩とcheckpoint/validation。F0は追加学習0。
- 選点：各モデルの推論/LOF/出力、F0の再推論は再現性診断として別記する。
- 下流：各4 nsのContext初期化/最小化/速度生成、積分＋同期reporter I/O、checkpoint/final I/O、結果hash/公開、CPU品質・指標評価。
- 工学失敗：最初のM0の1.736253秒を含める。F2不利は失敗として再実行しない。

## 時計と測定法

GPU占槽はGPU指定子プロセスの起動から完全回収までの壁時計。CPUでのデータ処理/導入やCUDA初期化もこの予約区間に含まれ、GPUカーネル活動時間の積分ではない。GPU不可視の品質/指標タスクはGPU占槽に含めない。`execution.json`が実境界である。

worker内部は`time.perf_counter`と`time.process_time`で測る。MDのintegrationはreporter I/Oを含む。学習のfit、checkpoint、validationを分けるが、その合計とGPU占槽は同じ境界でない。導入・import・プロセス生成/回収・hash・公開を含む残余を「純粋なscheduler overhead」と呼ばない。

CPU時間はworkerのprocess_time。Parsl制御・監視・driver CLI等の全ノードCPU時間を完全分離していない。CPU占有の設定は制御0、worker1/2、数値スレッド2。RSSはworkerのru_maxrssと監督のprocess-tree samplingを区別する。単体RSS16 GiB/保存25 GiBの保護を行う。

campaignの経過壁時計はhistoryとbranchesの間に操作者による確認/修復/文書作業を含む。タスク時間合計、段階内の串行依存経路、操作者の間隔を区別し、全経過を自動実行系のクリティカルパスと称さない。B2を行う場合に初めて固定h内の利用可能成果と機会費用を評価する。

最終のcosts.csv/jsonには成功/失敗全タスクと分項値を記録する。共通歴史や初期モデルの費用をゼロ扱いせず、同じ費用を三臂に三重計上もしない。
