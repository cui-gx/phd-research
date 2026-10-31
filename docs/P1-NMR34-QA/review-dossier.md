# P1-NMR34-QA：固定二軌跡の技術・科学評価器資格報告

実行日：2026-10-30 JST。交付監査：2026-10-31 JST。状態：**限定2単位の数値・入力完全性PASS、計算COMPLETE、独立科学審査PENDING**。証拠分類：server CPU measurement / derived analysis。既存B1の再評価は **POST_HOC_EXPLORATORY**。

## 1. 要旨と研究質問

問いは「固定model1で検証済みの評価を、原子対応と品質・時間窓を保って34参照へ拡張できるか。全量実行の費用を判断する材料が得られるか」である。F2の効果、folding成功、モデル学習の十分性を検定する試験ではない。

事前指定の履歴r01-h1-md（4,000点）と下流r01-s4-F0-t0-m2-md（8,000点）を一回ずつ処理した。12,000点×34参照＝408,000組のRMSD/Qを保存した。両単位で原model1最大絶対誤差5.3291×10⁻¹⁵ Å、Q1接触数完全一致、元窓件数・品質・時刻照合PASS。scalar/chunk最大差7.1054×10⁻¹⁵ Å。凍結と実行の科学wall合計173.215828秒、監視された最大RSS210.480469 MiB、新出力4,890,583 bytesであった。

ただし費用の内訳別計時、8 Å境界近傍pairの専用表、ensemble-minの窓集計は未保存であり、包括的な全量実装資格を宣言しない。単位別費用の外挿は約8.2–9.4時間だが上界でも信頼区間でもない。全272は実行しておらず、別承認を要する。

## 2. 承認、入力および再現性

CONFIRMED：[限定承認](execution-approval.md)、基準`ef0bdd64ca904bfa78afa759d8ebe8077d71105d`。実装・実入力凍結`c33807eec32096d59049bcf48ef3238ffa134906`をGitHubへ送信し、5ファイルの全文を照合してから実行した。独立[adapter](../../p1/nmr34_qa.py)は旧N1純関数を参照し、旧B1/R1/L1/L2/N1コード・出力を変更しない。

[freeze.json](freeze.json)は20入力SHA、34×28のCAキー、設定fingerprint、ソフトウェア版と人工試験を記録する。対象は原7ファイル×2、固定参照2、旧N1のframe/window出力4。Python3.12.3、NumPy1.26.4、MDAnalysis2.9.0、psutil7.0.0、既存環境再利用で新規インストールなし。参照を最新配布版で置換していない。[final.json](final.json)で全20 SHAの前後不変を確認した。

CPU1科学worker、数値thread1、GPU不可視。共有資源は実行直前に確認し、他ユーザのprocessを停止せず利用した。新規予約表の取得は未実施。最終監査では低CPU負荷・十分な空きRAM、GPU計算利用なしを確認したが、他者の予約権限まで保証するものではない。個人・内部ホスト情報は公開記録に含めない。

## 3. 固定数式と単位

28 Cαの対応を固定し、非周期座標をÅで扱う。質量重み、末端除外、反射適合は使わない。

\[
r_k(x)=\min_{R\in SO(3)}\sqrt{\frac1{28}\sum_{i=1}^{28}\|(x_i-\bar x)R-(N_{k,i}-\bar N_k)\|^2}\quad[\mathrm{Å}].
\]

SVDのdeterminant補正でproper rotationのみを許す。MDAnalysisのDCD読取りはconvert_units=True、保存された既存CA座標と全点一致を確認した。人工nm→Å試験は単位変換の算術試験であり、これと実CA照合を合わせて単位資格とする。

\[
C_k=\{(i,j):i<j,\ j-i\ge3,\ \|N_{k,i}-N_{k,j}\|<8\mathrm{Å}\},\qquad
Q_k(x)=\frac{\sum_{(i,j)\in C_k}\mathbf1[\|x_i-x_j\|<8\mathrm{Å}]}{|C_k|}.
\]

Qは無次元、strict <8 Å、sequence gap≥3。接触表のpair番号は0始まり、参照model番号は1始まり。Q1はQ_CA8_M1_G3_LT。全34の同じ**規則**を用いるが、接触集合と分母は参照ごとに異なる。Bhowmik式第二Q、ensemble consensus、hit/dwell閾値は導入しない。

\[
r_{\min34}(x)=\min_k r_k(x),\quad k^*(x)=\min\arg\min_k r_k(x).
\]

同値は保存float64値に対して最小model番号とする。逐frameのR/Q行列とargminから同参照のQを再構成できるが、Q at ensemble-argminの独立列・要約は未出力。別参照のmax Qを組み合わせない。全契約は[事前契約](../P1-N1-Review/nmr34-contract.md)。

## 4. 実行と数値検証

|検査|履歴4,000点|下流8,000点|
|---|---:|---:|
|参照数|34|34|
|M1最大絶対差 Å|5.3290705182e−15|5.3290705182e−15|
|scalar/chunk最大差 Å|7.1054273576e−15|7.1054273576e−15|
|Q1整数count|完全一致|完全一致|
|品質・時刻・frame対応|PASS|PASS|
|旧窓件数・M1要約|PASS|PASS|
|DCD相対時刻と保存時刻の最大差 ps|5.99479e−6|1.20049e−5|
|単位wall s|37.182789|135.570957|
|単位CPU s|45.485924|167.258514|

時刻比較はDCDの原点差を差し引き、凍結コードの0.001 ps条件を満たした。これは8 Åや科学効果の許容幅ではない。全RMSD/Qの有限性、0≤Q≤1、min34≤M1を検査した。全408,000組をscalarとchunkで比較しており、モデル抽出だけの検査ではない。

[参照接触表](reference-contacts.json)に34自己RMSD/Qと全pair、[参照幾何表](reference-geometry.csv)に34×34＝1,156組を保持する。自己RMSD最大2.66375e−14 Å、全Q自己値1。全34の剛体回転/並進、鏡映禁止の実行検査を通過した。参照間の異なるモデル561組のRMSDは0.411960–2.590248 Å。これは同じ構造ensembleの幾何記述であり、native populationや独立561観測の分布ではない。

接触数はmodel1が42、全34の範囲39–49。参照同士の原子chain/residue/insertion/resname/altlocキーは完全一致し、ensembleのmodel1と固定model1座標も一致した。したがって原子・式の一致は支持されるが、異なるQ分母の値を同一の固定接触集合と解釈してはならない。

## 5. 窓と保持された境界問題

[履歴全窓](history-windows.csv)と[下流全窓](downstream-windows.csv)は各816行＝34×12窓×2 sampling条件。0.5 psと、元窓の開始後にstride4で選ぶ2 psを保持する。2 psは全域の別位相グリッドではない。元valid/reasons、frame/global ancestral ID、保存時刻の関係を検証した。frameの一意キーは(task_id,frame_id)。同じglobal IDだけで下流枝を統合しない。

下流4 ns/0.5 psのburn0/100/200/500 ps件数は8,000/7,800/7,601/7,001。履歴の対応は4,000/3,800/3,601/3,001で、4 ns窓は元どおりINCOMPLETE_WINDOWである。200/500 psの理想格子より各1点多い問題を修正しなかった。数値時刻を用いる元選択の再現であり、新しい推奨境界ではない。

元N1は全窓IDリストを独立保存していないため、旧保存time/validから元規則でIDを再構成し、元件数とM1全要約・argminを照合した。独立した元IDリスト同士の比較ではない。この区別をwindow_ID_reproduction=trueの解釈に残す。

全窓でtotal=valid、今回二単位の品質除外0。主下流窓4 ns/burn100/0.5 psのmodel1最低RMSD6.270597 Å、平均Q0.426230。履歴の同じ指定窓は不完全で最低6.732618 Å、平均Q0.348571。異なる長さ・同一祖先の二軌跡の記述であり、更新効果比較ではない。2 psは0.5 psの部分集合なので同じ窓の最小RMSDが改善することはないが、平均Qの大小は一般には制約されない。

## 6. 実費用、保存と全量見積り

[実行台帳](final.json)、[最終byte監査](delivery-audit.json)、[外挿式](cost-estimate.json)を参照。freeze0.125802 s＋run173.090024 s＝173.215828 s。run CPU213.137030 s。CPU時間はwall時間と同義ではなく、監視threadも含むprocess CPUである。科学worker/threadの設定は固定したがOSの1core affinityによる強制制限ではない。

run監視最大RSS220,704,768 bytes＝210.480469 MiB。freezeのpeak_RSS_bytes=0は短い処理でサンプル未取得を意味し、RAM消費ゼロではない。単位receiptのRSSはprocess累積最大であり単位固有の増分ではない。0.1 s監視のため瞬間ピークを保証しない。module import/process起動の費用はmain開始の科学計時に含まれない。

final.json作成前の記録4,886,021 bytesに対し、最終byte監査はfinal自身を含み4,890,583 bytes（4.6640 MiB）。監査0.011046 sは既存出力byte/manifest確認のみで、新しい科学評価ではない。科学900 s、単工程300 s、RSS2 GiB、出力256 MiBを超えなかった。

全32履歴×37.182789＋240下流×135.570957＝33,726.879 s（9.369 h）。混合frame線形は29,540.697 s（8.206 h）。各長さ1単位しかなく、repeat/根間ばらつき未測定のため8.2–9.4 hを信頼区間や上限としない。NPZの`features['ca'][i]`をloop内で読むため、既存CA配列を反復解凍する余分な費用が含まれる。scalar全点検査の費用も含む。これは最適化されたNMR kernelのベンチマークではない。

全量R/Q float64本体1,114,112,000 bytes、count int16本体139,264,000 bytes、合計1,253,376,000 bytes（約1.167 GiB）。ID、時刻、mask、窓、receipt、圧縮時のbuffer等は別。今回圧縮出力の単純frame外挿は約834.659 MB（10進）だが圧縮率の保証はない。2 GiB全量出力枠や2時間枠を自動採用しない。

大きいframes.npzとwindow-ids、成功receiptはサーバの独立出力に残る。全ファイルの相対索引・SHAはdelivery-audit.json。GitHubには全参照窓表、幾何、接触、凍結/実行/監査、報告とコード。原9archiveの存在・byteサイズはmanifest一致、今回の全archive再hashは未実施、過去SHAは過去検証としてのみ引用する。Mac全量raw免除を維持する。

## 7. 失敗、警告、計画との差分

数値失敗0、失敗receiptなし、再試行0、保護停止0。終了後run lock非保持を確認した。MDAnalysis2.9.0 DCDReaderのtimestep copy動作が3.0で変わる旨のDeprecationWarningが端末に出た。frame内容の不一致ではない。stdout/stderrの完全ファイルは作成せず、成功/費用はimmutable JSON receiptで保存した。警告の完全ログ欠落を隠さない。

未完了の詳細記録・実装上の差分：

- 読取/SVD/Q/集約/保存ごとの内訳時間は未保存。単位/全体の実時間だけで外挿した。
- 8 Å近傍pairの独立リストと距離marginは未保存。strict比較と旧Q1完全一致は確認したが、閾値近傍の数値頑健性を全面認定しない。
- ensemble-minとargminは全frame保存済みだがmin34窓要約・Q at ensemble-argmin列は未作成。全量契約が要求するこれらの集計は今後の別実装審査で扱う。
- DCDは512点blockで処理したが、R/Q/countは1軌跡分をRAMに保持して圧縮保存した。memmapではない。二単位のRSS実測は低いが長い軌跡への一般化は未検証。
- 各blockで参照中心化を再計算し、CA比較用NPZも反復解凍する。速度改善案はPROPOSED、今回の凍結コードは変更しない。

従って、ユーザ指定の二単位数値・資源ゲートはPASSとする一方、詳細契約の全実装項目が無欠落で完了したとは扱わない。欠落を埋める目的で追加科学計算を自動実行しない。

## 8. 科学的解釈・妥当性の脅威

MEASURED：原model1再現、34参照対応、計算費用、参照幾何。DERIVED：この入力での数値拡張の実行可能性、暫定全量費用。UNVERIFIED：全272の参照依存、F2−F1、S4/S8の効果、physical/learning qualification、未知根への一般化、CのX独立価値、B2のwall-clock純利益。

min34≤M1は選択操作の性質であり、より小さい絶対値だけで探索改善やfolding成功を認定しない。34参照は独立実験でなく、12,000相関frameは12,000独立標本でない。二単位は同じr01に属し、F1/F2を含まない。根間推論、効果区間、検出力を計算していない。品質filterの一致もMD平衡やGBn2物理妥当性を証明しない。

静的交付検査は[static-check.json](static-check.json)を参照。窓表主キー・行数、接触pair、JSON、相対リンク、旧科学ソースと根README不変を確認した。初回の汎用globはmacOS AppleDoubleをJSONとして読んで失敗したため、本タスクの付随メタデータだけを除去して再検査した。科学計算の失敗・再試行には数えず、元科学ファイルは変更していない。

## 9. 次の判断

PROPOSED：研究者/ChatGPTはまず本数値再現と記録差分を審査する。全量承認の前に、反復解凍の除去、内訳計時、境界pair記録、ensemble集計、同値性確認を含む限定adapter改訂カードを別途検討する価値がある。これは新計算承認ではない。現実装のまま全量を希望する場合も、約9.4 h点見積りと不確実性、分割停止、出力を踏まえて別予算を決める。

全272、MD、学習、推論、LOF、GPU干渉、C/B2/S3は0。独立科学審査・研究者受入れPENDING。原証拠とarchiveを保全し、GitHub全文回読後に停止する。
