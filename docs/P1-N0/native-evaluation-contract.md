# P1-N0 評価契約案 v0.1：native-RMSD、Qと有限時間の折り畳みサンプリング

**文書作成日：2026-10-30 JST。状態：PROPOSED / NOT EXECUTED。** 過去のB1/R1の凍結主要指標を置き換えない。速水先生の助言を評価方法へ翻訳した当研究側の提案であり、先生がこの詳細計量を承認したわけではない。

## 1. 目的と評価対象

操作的研究目的：「同じFSD-EY準備と固定物理モデルに条件付け、許可された有限計算資源で、天然構造に近い構象をどれほど効率よくサンプリングできるか」。平衡分布、速度定数、熱力学的自由エネルギーの正しさ、実験折り畳み経路の再現はこの指標だけで主張しない。

**B1既存データの事後診断**：8歴史根、S4/S8の16状態、下流240×4ns、各状態のF0/F1/F2、学習seed／MDseedの既存対応を保つ。新指標で再評価する場合は post-hoc exploratory、未来の確認実験の事前登録ではない。**L2の新checkpointのTop1は下流NOT_OBSERVED**なので、既存B1軌道を自動で結び付けない。

**将来の確認試験**：戦略・MD品質・力場・最初の構造、実時間締切、意思決定時点、モデル・候補・データ公開規則を凍結した新しい独立根でのみ固定wall-clockを主張する。

## 2. 天然参照の取得と固定

実験参照は PDB **1FME**（FSD-EY、28残基、solution NMR、34構象）。[RCSB 1FME](https://www.rcsb.org/structure/1FME)。既存リポジトリ [inputs/p1-fsd-ey/manifest.json](../../inputs/p1-fsd-ey/manifest.json) には最初のMODELを抽出した `inputs/p1-fsd-ey/1FME-folded-model1.pdb` と、その保存済みSHA-256 `a5276b2752cd95555f7ca078c512c68f89b50893519e99347a1986fa63c82dc8` が記録されている。

**提案する事後B1の主参照：既に固定済みの1FME model 1**。旧入力参照を結果後に別のNMR構象へ交換しないためである。モデル1が特定原著のRMSD用referenceと一致するかは原論文のMD解析スクリプトから未確認。**感度**：公開34モデルすべての同一原子対応が確認できる場合だけ、各軌道frameから34参照へ個別にfitした最小RMSD `min_NMR34` と、構象別一覧を別表にする。複数構象の最小値は単一モデルRMSDより小さくなり得るため、モデル1主指標と混ぜない。NMR34の収集、実SHA、chain/atom完全性は未実施であり、事後CPU解析前のゲートである。

**準備仕様**：参照とMDの28残基の配列、residue番号・挿入コード・chain、CA座標、欠測/altLoc、原子順を明示的に検査。既存シミュレーション504原子とNMR PDBの原子集合を直接全原子一致と仮定せず、同じ28個のCαをアミノ酸対応で突き合わせる。1つでも対応不整合なら黙って短縮せず停止・報告。非周期のÅへ統一。参照座標も正式取得版とSHAを残す。

## 3. native Cα RMSD（Å）

全28個の対応Cα座標 `X=(x_i)`、固定native model1 `N=(n_i)` に対し、中心を引き proper Kabsch 回転 `R∈SO(3)`（det R=+1、鏡映は禁止）を最適化し

```text
RMSD_CA(X,N) = min_R sqrt( sum_i ||R(x_i-mean(X))-(n_i-mean(N))||^2 / 28 ) [Å].
```

**主要の事後診断候補**：各下流MD枝で、品質合格かつ最初の100psを除外したフレームの `best_RMSD = min_t RMSD_CA(X_t,N_model1)` を算出。単枝単位の全値を保持。B1と同じ除外窓0/100/200/500ps、観測先頭1/2/4nsは感度として全条件を報告する。B1元の内部幾何距離は別の距離であり、同じ「RMSD」と略記しない。

平均/median/p10のRMSD、最低値に到達したframe IDと物理時刻、最終値、native-NMR34感度、根/条件群の全ペアを保持。平均RMSDとbestは別々の推定対象であり、幸運な単frameだけでfoldedと記さない。各枝の評価可能frame数・品質除外率を併記。

**持続性／到達**：first hitの閾値 `tau_RMSD` は原論文の4.44Åを機械的に採用しない。候補閾値群は既知データを見る前に参考NMR ensemble内距離と比較用途から定義・承認し、各閾値の全結果を表示。事後B1については枝**内部**のfirst-hit simulation time［ps/ns］だけを算出する。240枝は並行・条件付きreseedなので、合計MD nsに時系列順を仮装した global first-hit wall-clock を作らない。持続時間も固定窓の別提案として較正後に凍結。

## 4. fraction of native contacts Q（無次元）

モデル1の28Cαから`P={ (i,j): 0≤i<j<28, j−i≥3 }`（325対）を定義。参照上で `distance_CA(i,j) < 8 Å` のものを `C_native` とする。原B1の8Å二値接触と閾値方向を揃え、ちょうど8Åは非接触として扱う。native pairがゼロなら停止し、恣意的に分母1を置かない。

```text
Q_native(X) =
 [sum_(i,j in C_native) 1{distance_CA_X(i,j) < 8 Å}] / |C_native|.
```

Qが高いことはその定義のnative contactが多いことを意味するが、同時に余計なnon-native contactが多くても高くなり得る。非native接触数、構造健全性、native Cα RMSDとの共同分布を必ず併記。旧B1の`Q8`は全300組の二値接触割合で**native contact Qとは異なる**。過去のQ8を新Qとして再命名しない。

**NMR集合感度（提案）**：各pairが34モデルの≥75%で接触の場合だけ「ensemble consensus contact」とする別Qを作る。これをBhowmikのnative-contact定義と同一と呼ばず、当研究独自の感度として書く。34構象と完全対応が取得できない場合は `NOT_MEASURED`。Qもref nativeのみ評価用で、当時のCVAE/LOF選点に与えない。

## 5. latent samplingをどう診断するか

既存M0/F1/F2で保存済みモデルと既存評価IDに対応したembeddingがある場合はその系譜と時刻を保持し、天然RMSD/Q色付き3D latent scatter、2D投影、RMSD/Q分位群別の分布を作る**案**。新しいforwardが必要か、保存embeddingのみで済むかを実行前にinventoryで明記する。異モデルのlatent軸を直接同一物理座標とみなさず、モデルごとに色付けし、固定入力ID上の近傍rank／選択差を比較。

潜在分布の変化、Top1の変化、BCE・K10の改善は、foldingの実際の到達や機構を証明する量ではない。rank/Top1とnative関連Yの関係を見る場合も、未来のYを使ったモデル・閾値の採択は禁止。native参照構造がML学習/オンラインLOFへ露出したら情報漏洩と記録して別実験扱いにする。

## 6. 公平な集計と統計階層

B1は同一歴史根 r01..r08の S4/S8、条件群 F0/F1/F2、更新学習seedとMDseedの階層を保持する。F0共有出力は複製して独立反復としない。主要の探索的比較は**同根・同状態の対応したF2−F1**とF1−F0、F2−F0に加え、root単位のstage差を示す。8歴史根は同じ初期unfolded準備に依存した8乱数系列であり、8独立分子構造ではない。

観測frame数や枝数を独立根のNに使わない。NMR34モデルも34独立の生物学的実験ではない。best-of-manyはサンプル数依存なので臂間同数のMD分量・枝数を固定して比較する。閾値でhitが0ならゼロ件として報告し、有利な閾値へ変更しない。探索区間は事後解析と記し、多重指標・閾値を確認的p値として扱わない。

**時間の区別**：既存B1では枝ごとのMD simulation ns/psと保存されたtask wallを報告できるが、これだけでMD/学習/待機の競合下の実オンライン政策の同一deadline反実仮想を再構成できない。未来のB2/Cでは最初の投入から全train/infer/MD/排他待機/reseed/品質判定/データ公開までの実wall-clock［s］と、決定時点までに実際に入手できた入力をtimestampログにする。集計の時刻は物理nsと秒を混ぜない。

## 7. 先に実装で検査すべき不変性と安全性（CPU実行は未承認）

1. 同じ座標を平行移動・proper回転してもRMSD変化なし。鏡像はproper回転で完全一致にしてはいけない。完全一致native→RMSD0。
2. model1から34モデルへ感度を拡張した場合 `min_NMR34 <= RMSD_model1`（同原子集合で成り立つ）を確認。mainとensemble-minを足し算／恣意的選択しない。
3. Native Qが0–1の範囲、native参照で1、旧Q8とは違う母集団であることをユニットテストする。
4. フレーム時刻・座標・品質規則とDCDの対応がB1の元SHA/アトム順と一致。新しい出力だけ保存し、旧ファイル書換えなし。
5. 全branch×全mask/窓で欠測理由を明記。reseed最小化だけを新成果に含めず、初期100ps除外を平衡の証明と言わない。

## 8. 必須の未決事項

- 1FME model1／34モデルの実体SHA・原子対応、参考論文が採用したRMSD参照とfit atom selectionの確認。
- 低RMSD閾値・持続時間・複数NMR感度の合理的な校正と研究者承認。主軸は単一の連続best-RMSDとし、閾値を結果を見て決めない。
- B1既存DCDの読取り・CPU計算に関する新たな明示承認。保存embeddingの実状態と前向推論要否を先に棚卸し。
- 未来オンライン比較における予算と全時刻の固定、DeepDriveMD/Colmena既知トリガとの具体的方策整合。
- Pの物理準備・暗黙溶媒の局限と、助言を踏まえた最小受容基準。明示溶媒実験は新版本・別承認。

**文献**：[RCSB 1FME](https://www.rcsb.org/structure/1FME)；[Bhowmik et al. 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6302667/)；[Ma et al. 2020](https://journals.sagepub.com/doi/10.3233/APC200023)。
