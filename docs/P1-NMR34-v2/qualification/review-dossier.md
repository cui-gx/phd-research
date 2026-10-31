# NMR34-v2：固定二軌跡の数値等価性と性能資格

2026-10-31 JST。研究基準eed520fd6b1263dfbb49b599fa80e02c479ff8e2、実行凍結90ed64aed54f961dfb458c6fb257e5b890bc5ade。**限定2単位PASS、科学計算COMPLETE、独立科学審査・研究者受入れPENDING**。

## 要旨と問い

同じ二軌跡を、科学定義・元frame/品質/窓を変更せず最適化した評価器で再現できるか、実費用はいくらかを検査した。既存履歴4,000点と下流F0の8,000点、計12,000点×34参照＝408,000組をqualify=Trueで一回処理した。全参照v1/v2 RMSD最大差は両単位0 Å、Q整数count/Q値・ensemble argmin・元全窓が一致した。scalar/chunk最大差7.10543e−15 Å。

外部監視の科学累計wall17.392948秒、worker CPU16.931123秒、process-tree RSS最大225.367188 MiB。実際の科学worker thread数は観測最大1。旧v1の単位wallとの比は6.73/12.19だが、I/O cacheや監視方式も異なるため厳密な単一因子の高速化試験ではない。

全量272のqualify=True点外挿は約47.42分。scalarを差し引いた約11.78分は反実仮想の算術であり、通常modeの実測ではない。どちらも上界/信頼区間ではない。全量は実行していない。

## 承認と工程資格

[実行承認](execution-approval.md)と[固定設定](config.json)。最新指令は過去のv2未承認記載を本2単位に限り更新する。GPU不可視、CPU1worker/数値thread1、科学900秒、工程300秒、RSS2GiB、出力256MiB。入力/成功出力を上書きしない。

[追加人工試験](../../../p1/test_nmr34_v2_execution.py)と既存人工試験の12 test methodsを対象サーバの既存環境で実行し、すべてPASS。100/200/500psの上側隣接floatを含む有効窓、窓内2ps位相、34固定参照＋ensembleの全24条件についてmin/mean/median/p10/argmin/同参照Qの明示的真値を照合した。SHA不一致、lock、再起動拒否、失敗receipt、wall/stage/RSS/disk門を試験。外部watchdogが人工sleep processを実際に停止する試験もPASS。[全ログ](artificial-tests.log)。

Macの試行はpsutil未導入のため外部監視試験が失敗した。[失敗記録](mac-engineering-attempt.log)を保持し、Macへ追加導入せず既存サーバ環境を利用した。科学失敗と混同しない。

コード・test・実入力設定9ファイルをcommit/pushして全文回読（Git blob SHA/byte長一致）した後に実DCDへ進んだ。[工程回読](engineering-readback.json)。新しい[薄実行器](../../../p1/nmr34_v2_execute.py)はproject領域のglobal flock、0.1秒外部監視、追記fsync累計budget台帳、immutable start/success/failure、config/input/code fingerprint、完全stdout/stderrを実装する。自動復旧・全量拡張は持たない。

## 入力、環境、科学定義

FSD-EY/1FME、28 Cα、原非周期Å座標、固定34 NMR参照。元20入力とv1成果を含む33ファイルの実SHAを前後検査し全一致。元N1/v1科学ソースと結果は不変。全原子キーはchain/resSeq/iCode/resName/altlocを順序ごと照合、固定幅の空白のみstripし、原子を並べ替えない。DCDのCA座標は既存CA cacheと全frame一致、nm→Åの暗黙再解釈はしない。

[CPU/OS記録](hardware.json)、[実行環境とfingerprint](execution-fingerprint.json)：Python3.12.3、NumPy1.26.4、MDAnalysis2.9.0、既存psutil環境再利用、追加インストールなし。GPU不可視/数値thread環境をprocess import前に設定し、OS affinityや共有設定を変更しない。09:52/09:55/09:56 JSTで他者のCPU/RAM/GPUをread-only確認、低CPU負荷・約116GiB空きRAM、GPU計算processなし。他者ログインは存在し、今回許可されたCPUだけを使用。予約表は新規取得していない。

\[
r_k(x)=\min_{R\in SO(3)}\sqrt{28^{-1}\sum_i\|(x_i-\bar x)R-(N_{k,i}-\bar N_k)\|^2}\ [\mathrm{Å}],
\quad C_k=\{i<j,j-i\ge3,d_{ij}(N_k)<8\mathrm{Å}\},
\quad Q_k(x)=|C_k|^{-1}\sum_{C_k}\mathbf1[d_{ij}(x)<8\mathrm{Å}].
\]

proper rotationのみ、float64直接残差、固定分母。min34=min_k r_k、argminは最小model番号、同参照Q=Q_argmin。model1主参照を変更しない。全参照mapping/分母/pair/座標SHAは[reference-map.json](reference-map.json)。原[科学契約](../../P1-N1-Review/nmr34-contract.md)を継承する。

## 数値結果

|項目|r01-h1-md|r01-s4-F0-t0-m2-md|
|---|---:|---:|
|frame数|4,000|8,000|
|全34 v1/v2 RMSD最大差 Å|0|0|
|N1 model1最大差 Å|5.32907e−15|5.32907e−15|
|scalar/chunk最大差 Å|7.10543e−15|7.10543e−15|
|Q/count|完全一致|完全一致|
|ensemble min/argmin|一致|一致|
|同参照Q|一致|一致|
|34固定窓/ensemble窓|816/24|816/24|
|DCD相対時刻最大差 ps|5.99479e−6|1.20049e−5|
|near pair件数|0|0|

N1最大差はv2と保存v1が全値同一であることと、旧N1/v1最大差の実測からのDERIVED値。今回もN1を全点比較し1e−8 Å以内を直接検査したが、N1差の独立最大列は保存していない。[差分CSV](comparison.csv)、[worker結果](worker-final.json)、[scalar実測](history-chunks.json)・[下流scalar](downstream-chunks.json)を参照。

near診断は全eligible pairのmargin=d−8 Åが±1e−6 Å内のものを保存する。今回0件であり、空表は異常ではない。幅は工程診断で接触定義を変更しない。近境界の挙動自体は人工testで確認したが、実軌跡の非空near表は今回検証されていない。

全frame/global ancestral ID・time/local time・valid/reasonsを独立保存し、v1/N1 metadataを完全照合した。window sampled/valid IDを別保存、旧v1 valid IDを全件照合、0.5/2psの抽出位相を維持した。元N1に独立ID一覧がないという履歴上の制約は残る。旧時刻規則から再構成したIDと、旧件数/全統計の一致が証拠である。

下流4ns/0.5psのburn0/100/200/500件数は8,000/7,800/7,601/7,001。履歴は4,000/3,800/3,601/3,001で4ns条件はINCOMPLETE_WINDOW。200/500psの各1点差は修正せず再現した。34固定参照のmin/mean/median/p10/final、Q mean/median/max、RMSD argminと同frame Qをv1窓表へ照合した。ensemble系列も保存v1の全frame min/argminとQを用いる独立集約へ照合した。全[履歴840行](history-windows.json)・[下流840行](downstream-windows.json)を保持する。

## 非重複計時と性能

単位の実wallは5.525454/11.118119秒、CPUは5.525167/11.117590秒。下記wall区間は互いに重ならない。全値とCPUはworker-final.jsonに保存した。

|工程 [s]|履歴|下流|
|---|---:|---:|
|CA cache/metadata|0.027072|0.046224|
|reader/座標照合|0.128149|0.251582|
|Kabsch|0.562123|1.115043|
|Q/margin|0.120267|0.240711|
|scalar資格|4.094247|8.365133|
|ensemble/有限性|0.000430|0.000868|
|圧縮保存|0.055995|0.107040|
|chunk SHA|0.000983|0.002036|
|window ID|0.015928|0.022915|
|window chunk読取|0.255011|0.495940|
|window統計|0.116426|0.139141|
|summary保存|0.007798|0.008258|
|v1/N1/窓対照|0.138795|0.320429|
|単位内residual|0.002227|0.002799|

別途、入力SHA前0.092558秒、参照/自己検査0.124531秒、入力SHA後0.071209秒。worker wall16.933088秒に対しsupervisor science wall17.392948秒で、後者は起動/import/外部監視も含む。各工程のprocess CPUと監視process CPUを混ぜていない。

[外部監視結果](supervisor-final.json)：RSS236,314,624 bytes、thread観測最大1、保護停止なし。0.1秒サンプルなので瞬間ピークの保証ではなく、時間上限到達時の停止には検知粒度・terminate猶予がある。今回は上限から十分離れていた。最終byte監査7,024,697 bytes（科学終了receipt前の監視記録とは数百byte差）、全成功chunk SHA一致、global lock非保持。[最終監査](final-audit.json)。

v1単位wall37.182789/135.570957秒と比べた観測比は6.729/12.194。v1は反復NPZ解凍を含む一方、v2は追加のensemble窓/near診断や外部process監視を含む。実行日、cache、周辺loadも統制していないので、この比を一般的kernel speedupや単一改変の因果寄与と呼ばない。

## 全量予算の更新と限界

[算式JSON](updated-budget.json)：32×5.525454＋240×11.118119＝2,845.163秒（47.419分）、qualify=Trueの点外挿。scalar区間のみ差引くと706.515秒（11.775分）だが、これは通常mode反実仮想であり未測定。両者とも固定前後SHA/起動/全量集計の全費用を保証せず、各長さ1単位だけでCI/上界を作らない。

今回出力のframe線形は約1.199GBだが、window/metadataの固定費と圧縮率の差を無視する粗い点見積り。near0件が全根で続く保証はなく、最悪near表が約21.30GB追加という既報算術は依然有効。RSS2GiB/出力2GiB/2hの全量完了を認定しない。科学時間が短くなっても、全272許可やC/B2への許可は生じない。

## 失敗・保存・主張の境界

科学失敗0、再試行0、argmin分岐0、保護停止0。Mac人工環境の依存不足1件を保持。MDAnalysis DCDReaderの3.0でtimestep copy動作が変わる旨のDeprecationWarningはserver stderr.logに完全保存、stdout.logも空ファイルとして保存。生の完全ログとbudget.jsonl、全chunk、metadata、窓IDはサーバ独立出力に保全し、GitHubはSHA/索引・compact完全結果・報告/コードを保持する。内部パスを含むraw stderrは公開文書へコピーしない。

原9archiveは実在/サイズが既存manifestと一致、今回は再hashせず過去SHA検証と区別する。Mac raw免除を維持。二単位は同じr01由来、片方はF0であり、独立8根やF1/F2効果の検定ではない。12,000frameや34参照を独立標本にしない。数値等価性/工程速度の支持であり、folding、探索改善、物理/学習資格、CのX情報価値、B2純利益は本結果から認定しない。

## 判定と次の承認

**PASS：限定二単位の数値・資源資格**。独立科学審査と研究者科学受入れはPENDING。次は[承認判断資料](next-approval.md)を研究者/ChatGPTが審査する。全272/MD/CVAE/LOF/R0/C/B2を自動開始せず、GitHub全文回読後に停止する。
