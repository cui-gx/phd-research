# N1天然構造指標契約案 v0.1

2026-10-30。**PROPOSED / 実軌跡NOT EXECUTED**。N0を具体化した案で、旧主要指標や結論の遡及変更ではない。天然構造への接近を有限時間の構造進捗として扱い、平衡population、folding速度定数・経路の物理的正しさを認定しない。

## 1. 入力・原子対応・参照

主候補は既存`1FME-folded-model1.pdb`、SHA-256 `a5276b2752cd95555f7ca078c512c68f89b50893519e99347a1986fa63c82dc8`。34 NMR構造を含む既存folded PDBは`f9c5de680c00ee2629634fb6c7f621e2e1e2664e92b2e4b51b236d5e483b436b`。[静的参照監査](reference-static-audit.json)。RCSBは34 submitted conformers、28残基と記載する。既存ファイルは固定DeepDriveMDデータ由来であり、今回最新版RCSB座標へ交換していない。

Cα28個の `(chain,resSeq,iCode,resName,altLoc)` を明示的に一対一対応させる。配列順はPDBの既存対応を保持し、欠測・重複CA・代替位置・residue identity違いでは停止。原子全504個とNMR原子全体を一致と仮定しない。末端を結果に合わせて除去しない。文字列対応の静的確認は完了したが、nativeと実DCDのRMSDを計算した意味ではない。

座標単位Å、非周期、質量なし等重み。OpenMM内部nmを直接渡すことを禁止する。DCD読込み側はMDAnalysisのÅ規約と版を確認する。PDB box/minimum imageを適用しない。原データをcenter/fitして保存し直さず、新配列を生成する。

## 2. Native Cα RMSD：`R_CA28_M1_SO3_A`

行ベクトルX,N∈R^(28×3)、Xc=X−mean(X)、Nc=N−mean(N)、H=Xc^T Nc=U S V^T。

$$R=U\,\mathrm{diag}(1,1,\det(UV^T))V^T,\quad r(X)=\sqrt{\frac1{28}\sum_i\|(X_cR-N_c)_i\|^2}\quad[\mathrm{\AA}].$$

det(R)=+1で鏡映を禁止し、スケール調整を行わない。fit原子と評価原子は同じ28CA。重みなし、部分fitなし。`proper_rmsd`の人工検査許容誤差1e−12 Åは小さいdouble人工点に対する工学判定で、実科学の等価幅ではない。rank不足ならrotation非一意性を記録し、距離の解釈に注意する。

34参照では各モデルkへ独立にproper fitしてr_kを全保存し、`R_CA28_NMR34_MIN_A=min_k r_k`、argmin k（同値は小model番号）を感度にする。min34≤model1だが、34倍の独立実験数ではない。モデル1より小さくなる選択機会があるため主指標と混ぜない。RMSD最小モデルkのQ_kを共同感度にし、別モデルのmaxQと一つの擬似構造を作らない。

## 3. 二つのnative-contact Qを区別する

### 3.1 主候補 `Q_CA8_M1_G3_LT`

P3={(i,j):i<j,j−i≥3}、325対。d_ijはCA非周期距離[Å]。

$$C_1=\{(i,j)\in P3:d_{ij}(N_1)<8\},\quad Q_1(X)=\frac{\sum_{(i,j)\in C_1}1[d_{ij}(X)<8]}{|C_1|}.$$

無次元[0,1]、境界8.000…Åは非接触。C1を参照だけで固定し、trajectory/条件群/結果ごとに分母を変えない。C1空なら停止。原定義を変えない限りnative自身でQ1=1。325対はeligible数で、native接触数そのものではない。**今回C1を実座標から計算・件数測定していない**。非native接触数と旧Q8を別列で残し、高Qが非native密集を排除しないことを示す。

旧B1 `Q8=Σ_P4 1[d<8]/300`（P4:j−i≥4）は全接触率でnative fractionではない。新Qへ改名しない。

### 3.2 Bhowmik関連の操作的感度案 `Q_CA8_BASIN75_G3_LE_PROPOSED`

[Bhowmik 2018](https://doi.org/10.1186/s12859-018-2507-5) Results冒頭はCA距離8Å以下、75%の構象、nativeから1.1ÅのRMSD条件を述べる。しかしnear-native集合の具体的出所、reference、sequence exclusion、境界・解析コードを本資料だけでは一意に復元できない。N0の「34NMRの75%共識」と同じ規則ではない。引用先[Savol & Chennubhotla 2014](https://doi.org/10.1021/ct500361w)とも数値を混同せず、原実装未取得を残す。Savol原文の定義はCA<10Å、native ensembleの65%以上、配列上7残基未満の接触を除外（本文のcontact定義）で、Bhowmikとパラメータも異なる。引用先をそのままBhowmikの実装仕様にしない。

明示的に**当研究の解釈案**として、独立に凍結した参照集合Lに対してB={z∈L:r(z,N1)≤1.1Å}、

$$C_{75}=\{(i,j)\in P3:|B|^{-1}\sum_{z\in B}1[d_{ij}(z)\le8]\ge0.75\},\quad Q_{75}(X)=|C_{75}|^{-1}\sum_{(i,j)\in C_{75}}1[d_{ij}(X)\le8].$$

と定義できる。L、proper fit、P3追加は当研究側の指定なので**Bhowmik忠実再現と呼ばない**。L/B/C75が未凍結、B空、C75空ならNOT_DEFINEDとし、本B1の将来枝からLを作らない。34NMRをLとするなら別名`Q_CA8_NMR34_CONSENSUS75_G3_LE`で別感度にし、Bhowmik原論文の式と称さない。全34の無条件共識と、RMSD条件付きsubsetも別である。Q75(N1)=1は保証されない。実装はboolean共識maskの一般関数までとし、本輪に実参照でfit/接触率を作らない。

**採択提案**：N1の最小実評価はmodel1のrとQ1を先に審査する。第二Qは上の未解決を解決し別凍結した場合だけ実施する。勝つ定義を結果後に選ばない。

## 4. 原品質・時間窓・枝要約

B1の元valid mask（有限・拘束・CA/CN・重原子・手性規則）、sampling interval、global IDとbranch local IDを継承する。[原契約](../P1-B1-Expansion/metric-contract.md)。品質を新native値で変更しない。全frame記録0.5ps、既報集計の2psサンプリングも併記する。N1連続native主案は保存全frame0.5psで、従来2psだけの旧指標を上書きしない。両間隔でbestの機会数が異なることを感度として示す。

主表示候補はprefix4ns・除外100ps、既存の除外0/100/200/500ps×prefix1/2/4nsを全12窓で保持する。端点はelapsed t∈(burn,prefix]、MD frame0は最初のreport frameで、minimized初期PDBを新規サンプルに数えない。時刻の浮動小数誤差への選別は既存segment/global ID規則で行い、閾値を都合よく拡張しない。100ps除外は平衡証明ではない。

各枝・窓でN_total/N_valid/N_excluded、min r、best-so-far min、argminのID/時刻、rのmean/median/p10/final、Qのmean/maxと各argID、min r時のQ、Q/Rの全対応点を保存する。tieは最初の元ID。空集合はNA+理由とし、0Å/Q=1に補完しない。無効点はbest更新しない。minと平均を混同しない。全時間曲線と最終bestを併記し、一過性の最小値だけでfoldedとしない。

Q/R共同分布は同一frame・同一参照の(r,Q)。主成果は連続値で、図はまず散布/経験分布とする。固定binが必要ならnative評価前にbin境界を契約へ追記して凍結し、未確定のbinで閾値依存の結論を作らない。

### 4.1 元B1の幾何新規度を補助対照として保持する

同状態の元品質適格履歴A0と、非局所325対の距離vector f(x)を用い、

$$m_{A0}(x)=\min_{h\in A0}\sqrt{\sum_{(i,j)\in P3}(d_{ij}(x)-d_{ij}(h))^2/325}\ [\mathrm{\AA}]$$

の既報mean/median/p90をそのまま補助として用いる。大きいほど当時履歴からの幾何的隔たりで、native RMSDが小さいことと同義ではない。元のε1.5/2/3Å×τ0/5ps、2psサンプルの追加領域数と全12窓も保持する。5ps持続は離散2ps観測で最短6psという元意味を維持する。

N1の0.5ps native値と旧2ps幾何表を比較する際はglobal/local frame IDの共通2ps点でjoinし、旧原配列・平均値を書き換えない。必要ならN1の両sampling列を併記する。R1のORIGINAL_HISTORY/COMMON_A4/COMMON_A2/MATCHED_COUNTの相違・陰性も残し、nativeに好都合な旧参照だけを選ばない。G_Rは新しい採択済み主要尺度ではない。新nativeとの関連/再集計自体も本輪未実行である。

## 5. 閾値・first hit・滞在

τ_RMSD、τ_Q、必要持続時間τ_dwellは**UNSET / NOT_ADOPTED**。文献4.44Åは観測最小値でfolded閾値ではない。Bhowmikの1.1Åは参照集合規則で、B1到達の成功閾値へ自動転用しない。NMR内部距離分布はまだ計算しておらず、そこから生物学的閾値が自動決まるとも言わない。

承認された場合に限りhit_i=valid_i∧(r_i≤τ_R)（共同版はQ_i≥τ_Qも必要）、first sampled hit=min{t_i:hit_i}。連続観測episode [a,b] の観測滞在はt_b−t_a、単点0ps、無効/欠測点で必ず分割。積分時刻間の連続状態は不明であり、sampling間隔を跨ぐ滞在の真値ではない。hit0ならright-censored、観測終端と有効観測量を残す。τが未定なら本系列を実行しない。枝のlocal MD psとpolicy wall-clock first usable hit秒を混同しない。

## 6. 潜在可視化・情報遮断

元B1の保存`ranking.npz`はframe_ids/embedding/LOF/orderを含み、固定モデルと同decision候補に対応する。96ファイルには16 F0-repeatも含むため80 unique model conditionと区別する。nativeラベルをIDでjoinするだけの図は、将来native評価承認後に保存embeddingで作れる。下流240枝の全frame embeddingは保存されていない。新forwardが要る図をこの許可に紛れ込ませない。[棚卸し](data-readiness.md)。

各モデルの3軸を別図で示し、共通色範囲・同ID・同samplingを全条件で統一。raw3Dまたは固定2軸を主図とし、t-SNEの自由なseed/perplexityで結論を選ばない。可視化での群分離は構造状態・熱力学重み・学習十分性を保証しない。

天然reference/r/Q/未来の下流Yはオフライン評価器だけが読む。オンラインpolicy featureのschemaを許可リスト化し、native/真の効果/更新後の測定をdispatch前の無料情報へ混入させない。元DeepDriveMDのnative-guided条件は別のnative-informed対照であり、このblinded policyと同一情報条件ではない。

## 7. 統計と将来wall-clock成果

B1新評価は**POST_HOC_EXPLORATORY**。8根、同根S4/S8、F1/F2各2学習seed×3MDseed、共有F0各3本を保持。各状態F2/F1は2×3を等重み平均、F0をtraining blockごとに複製せず1回平均し、同根対応差と全根値を報告する。Δ21=best(F2)−best(F1)[Å]は負がF2に有利。共有F0との比較の共分散を保持する。全尺度・窓を公開し、frame/branch/NMRモデルを独立根にしない。

将来オンライン主候補は共通決定状態を公開した時刻0からH秒以内に**利用可能になった**品質適格新frameと共通履歴の最小rである。

$$B(H)=\min_{x\in A_{common}\cup A_{new}:available(x)\le H}r(x),\quad G(H)=B(0)-B(H).$$

共通履歴が同じなので、reseedで既知構造を再選択するだけの見せかけの改善を防ぐ。Hまでに新frameがなければB(H)=B(0)。これはdecision後の条件付き予算で、履歴生成まで含む完全campaign予算とは区別する。一次成果採択、H、公開粒度、物理/モデルrecipeは別の研究者承認が要る。[計量](resource-and-timing.md)に従う。
