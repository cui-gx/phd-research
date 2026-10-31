# NMR34-FULL：実行前固定計画

2026-10-31 CONFIRMED：研究者は本チャットで272軌跡CPU分析と7200秒/工程300秒/RSS2GiB/新出力2GiB停止門を明示承認した。基準33f6aa9e5071af18d7b841b61367507d2113b834。全量計算完了後、Astra Extra Highの独立科学審査を待つ。新MD/CVAE/LOF/R0/C/B2は未承認。

## 入力・順序・数値抽査

[manifest.json](manifest.json)：原N1の272単位SHA監査とB1 branch-indexから作成。task_id文字列昇順に固定、32履歴/240下流/8根/16状態/元学習・MDseedと親モデルを保持。全2,048,000frame。各7原入力＋N1 frames/windowsの計2,448ファイルSHAを実読取前に照合する。参照2ファイルSHAも固定する。

[config.json](config.json)：既資格v2批量kernel、qualify=False。各軌跡のframe0、floor(N/2)、N−1に固定して全34参照のscalarを抽査する（計816frame×34＝27,744組）。結果で選択しない。全frameのM1は旧N1にabs1e−8Å、Q1整数count完全一致、元時刻・品質・ID・全窓を照合する。near±1e−6Å記録を保持しQのstrict8Åは変えない。

## 集計契約

旧28CA proper Kabsch/Å、固定参照別Q、12窓×2 sampling、200/500ps境界を不変とする。34固定参照＋min34/same-argmin-Qの35系列、9原native指標全てを保持。主窓は4ns/100ps/0.5ps、他23条件を省略しない。model1主系列を置換しない。

各状態はF0の3MDseed、F1/F2各2学習seed×3MDseed。学習seedごとに3MDを平均してから2seedを平均する（均等行列では6枝平均と同値）。共有F0を学習seed分複製しない。根ごとにF2−F1、F1−F0、F2−F0を作り、S4/S8/二状態平均/S8−S4を計算。8根の対応を維持し、root mean/median/SD/min/max/符号数を提示。元N1と同じseed17103001、10,000回の根bootstrap（全参照/条件に同じdrawを共有）で95%探索区間を出す。多重比較の確認的p値や独立34参照の検定を行わない。

主質問はF2−F1の最小RMSDで「S4正/S8負」が全固定参照で保たれるか。全参照の値・範囲・符号と根級結果、Q等の不一致も同じ透明度で報告。参照範囲はCIでなく、min34の値低下は選択操作の性質。M1−min34の数値差は因果寄与ではない。

旧幾何との関係は原R1の4参照・12窓・0.5psのdistance_mean_Aに対するabsolute native endpointの記述的Spearmanを各NMR系列で計算。相関branchを独立標本としたp値を出さず、更新効果の相関やXの独立予測価値と呼ばない。2ps幾何の再計算はしない。

## 制御・保存・停止

独立full wrapper、project領域global flock、単科学worker/数値thread1/GPU不可視。外部監視は0.2秒周期、wall/RSS/disk/工程を追記fsyncし、永続budget-stateへ累積時間を保存する。batch終了後もspentを引き継ぎ、別途明示されたresume承認IDと同一fingerprintがなければ再開しない。未確定segmentは不足時間を推測せず停止する。成功receiptと全出力SHAを検査してからだけskipする。部分単位を自動上書きしない。全量の復旧が必要なら失敗原因・残予算・非上書き新attempt設計を審査する。

科学計時は起動/全入力SHA/参照/全単位/集計/図/最終監査を含む。7200秒または工程300秒、RSS2GiB/出力2GiBで自分のprocessだけ停止し、枠を自動拡大しない。全stdout/stderr、資源/失敗を保持。原9archive保持、Mac raw免除、旧結果不変。成功結果は不可変dirとreceiptで保持し、GitHubには全compact表/コード/図/SHAと報告、rawchunkと完全ログは許可サーバへ保全。
