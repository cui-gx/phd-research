# L2指標契約

version L2-design-v1、2026-10-29、PROPOSED。以下は追加診断前に固定する規則で、実験結果ではない。閾値・mask・集合をB1の下流効果に合わせて選ばない。モデル間で同一評価IDを使い、全4状態・3初期化・全歩数・OLD/RECENTを公開する。

## 1. 接触再構成

入力Y∈{0,1}^{28×28}、決定的な潜在平均z=μ(Y)、復号確率p=D(z)。mask Mを

- ALL：784要素（対角・対称重複を含む、補助）。
- NONLOCAL：i<jかつj−i≥3、325要素（主再構成診断）。
- LONG：i<jかつj−i≥4、300要素（必須感度）。

とする。LONGは本計画の配列上の長距離接触という操作的名称で、一般的なタンパク質分類基準と同一視しない。

$$R_M(Y,p)=-\sum_{(i,j)\in M}\{Y_{ij}\log p_{ij}+(1-Y_{ij})\log(1-p_{ij})\}.$$

単位はnats/フレーム。R_M/|M|をnats/有効要素とする。有効要素は全正例・負例を含み、予測が当たった接触だけではない。L1と同じTorch BCE(reduction=none)の数値処理を維持し、別epsilonを導入しない。集合平均は200枚の等重み。正接触/非接触の寄与と個数も別列にし、片方が0ならその条件付き平均はNAとして分母を保存する。

### 頻度基線

各要素の訓練頻度はp^train_ij=(n_ij+0.5)/(800+1)。共通OLD800と臂別実訓練800を別々に保持する。epochを重ねても同じIDを使うため頻度は変わらない。主差は

$$A_{train}=\overline{R_M(Y,p^{train})}-\overline{R_M(Y,D(\mu(Y)))}.$$

正は当該頻度基線よりBCEが小さいことだけを意味する。F2の新分布への適応を誤って情報抽出と呼ばないため、共通OLDとの差より臂別頻度との差を優先する。

同一評価集合200点のleave-one-out頻度 p^LOO_n=(他199点のcount+0.5)/200 もL1同様に報告する。これは相関した他の評価点を用いるtransductive参考で、オンライン利用可能な公平基線でも合否基準でもない。

## 2. 再構成が個別の入力情報に依存するか

同じ200点に対して、以下を全モデルで固定する。平均値だけでなく、セルごとの符号・分布を保持する。

1. **平均コード対照**：bar z=(1/200)Σ_n μ(Y_n)、全てD(bar z)で再構成。A_mean=mean R(Y,D(bar z))−mean R(Y,D(μ(Y)))。bar zは評価集合に依存するtransductive診断で、未来候補を予測するモデルではない。新しいdecoder forwardが必要。
2. **対応入替え対照**：時刻・global ID順の200点について、π_o(n)=(n+o) mod 200、o∈{1,17,53,97,149}。A_perm,o=mean R(Y_n,D(μ(Y_π(n))))−mean R(Y_n,D(μ(Y_n)))。全5offsetを保存し、最大差だけ選ばない。保存reconstructionがあれば新forwardなしで算出できる。
3. **zero-code対照**：D(0)をL1との連続性のため残すが、zeroとの差だけを入力依存性の証明にしない。
4. **未学習対照**：各独立初期化のM0-step0に同じ評価を行う。childのstep0はM0-200のaliasである。学習済みモデルと各自の同init未学習モデルの差を示し、ランダム特徴でも得られる幾何を区別する。

平均コード/対応入替えは情報理論的な相互情報の推定ではない。offset1には特に時間相関が残り、入替えは交換可能な独立サンプルの置換検定ではない。局所的に似た入力なら差が小さくても完全な無情報とは結論できない。各入力の構造とコードの対応が復号に利用されるか、という有限集合上の診断である。

## 3. KL、潜在分散、退化

固定実装はlogstdを最大10でclipし、σ=exp(logstd)とする。[mdlearn VAE](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/model.py)、[VAE原著](https://arxiv.org/html/1312.6114v11)の対角Gaussianの場合に対応する。

$$K_n=\tfrac12\sum_{l=1}^{3}\{\mu_{nl}^2+\sigma_{nl}^2-1-2\log\sigma_{nl}\}\quad[\mathrm{nats/frame}].$$

全体および各次元の平均KL、μの平均、入力間母分散Var(μ_l)、E[σ_l²]、μ共分散（母分母N）の3固有値を報告する。μ各列のmin/max、距離のzero率、非有限数も保存する。KLの大きさは入力情報量そのものではなく、事前分布からのずれも含む。

非有限値は工学FAIL。厳密に一定のμによる距離rank未定義はNAと理由を報告する。小さいKL、低分散、一部固有値の縮小はposterior collapse/次元退化のリスク所見として扱い、既存根に合わせた任意の「KL<α」合格閾値は作らない。良い再構成だけでcollapse不存在を認定しない。

## 4. 潜在幾何と物理構造

f(x)をNONLOCAL325対のCα内部距離[Å]とし、既存featuresを使用する。

$$d_{phys}(x,y)=\|f(x)-f(y)\|_2/\sqrt{325}\quad[\mathrm{\AA}],\qquad d_z(x,y)=\|\mu(x)-\mu(y)\|_2.$$

潜在距離は無次元。主はRAW μ、補助は同評価集合内で各次元を標準化したμ（標準偏差0の除数は1）である。補助標準化をLOF選択規則へ反映しない。

各点の自己を除く10近傍N_z(n)、N_phys(n)を定義し、K10=(1/200)Σ_n |N_z(n)∩N_phys(n)|/10 [0,1]を主幾何診断とする。同距離はglobal IDで解決する。全19,900非対角上三角距離対のSpearmanを併記し、p値を出さない。距離が一定ならNAで、0に補完しない。

基線は同NONLOCAL binary接触のEuclidean距離、および絶対時刻差。高次元接触と3次元潜在には容量差があり、接触基線を上回ることを最低合格の必要条件にしない。ただし劣っていることを隠さず「同等」とも表現しない。時刻基線が強い場合は短いblockの時間相関による一致の可能性を明示する。未学習step0も同じK10とSpearmanを測る。

内部距離は剛体変換に不変だが鏡映を区別せず、側鎖や水素・溶媒を含まない。これは構造の一側面の診断で、遷移速度/自由エネルギー/反応座標の資格ではない。

## 5. 初期化間・checkpoint間安定性

同状態・同臂・同stepについて3initの全3対で、潜在距離rank相関と潜在10近傍重複を報告する。μ座標の直接差は回転/置換等に依存するため主指標にしない。全3対は同じ3モデルを共有し、3独立標本ではない。

歩数変化は各chainの200→400、400→800、800→1600および200→1600。A_train、A_mean、全A_perm、BCE、K10、Spearman、KL/分散を同じ列で示す。再構成改善と幾何改善の符号表を作るが、少数・相関checkpointの相関係数を一般法則としない。OLDの保持悪化とRECENT改善を平均で隠さない。

## 6. LOF順位とTop1

全156endpointのRAW μを、状態内で固定した同じFULL候補集合Eと同じ密度fit集合D（E=D）へ適用する。S4=7,800、S8=15,800。CPU単thread、sklearn固定版、n_neighbors20、minkowski p2、novelty=False。各fitのnegative_outlier_factor_を小さい順、同値はglobal IDで順位付けする。[公式API](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)

全score/rankを保持し、同一候補集合のモデル対に対してscoreのSpearman、Top10/Top100重複率（共通数/10または100）、Top1一致、Top1同士のd_phys[Å]を報告する。Top1時刻・OLD/NEW/その他の由来、最小2scoreの差も記録し、微小差で選点が変わる可能性を可視化する。異なる密度fit間のscore絶対差を校正された不確実性と呼ばない。

比較は、同chainの全4 checkpoint間6対、同臂/stepの3init間3対、同init/追加stepのF2−F1、各子対固定F0=M0-200、未学習対照との比較。S4/S8の異なる候補集合を直接全順位相関で比較しない。状態差は同状態内対比を並べるだけとする。

全ての新候補は下流結果 **NOT_OBSERVED**。旧B1と同じframe IDが選ばれても本L2でMDを実行した意味ではなく、旧下流値を自動結合しない。順位変化を科学利益・C成立・B2固定時間純利益としない。

## 7. loss記録と単位

将来の新実装は各stepのraw total、BCE総和、KL平均、実batch数、gradient norm、finite flagを別列で保存する。raw total=BCE_sum+KL_batchmeanの既定目的を変更しない。診断列BCE/frame=BCE_sum/b、BCE/element=BCE_sum/(b×784)、KL/frame=KL_batchmeanを併記する。正規化合計は実際の最適化目的ではないため、raw totalと混同しない。

保存endpointの検証は200点のsample重みで集計し、batch32と末尾8を等batch重みで平均しない。訓練時dropout/潜在サンプリングとeval時z=μの差を残す。旧Q0の未保存BCE/KLを新規ログから補完して過去の値を書き換えない。
