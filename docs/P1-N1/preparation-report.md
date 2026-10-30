# P1-N1 完全実験準備報告

2026-10-30 JST。**準備交付：技術的に完了。科学評価・新実験：未実行、未承認。独立科学審査・研究者採択：PENDING。**

## Executive Summary

研究者が承認した文献、方法設計、静的コード、資料・SHA棚卸し、非科学的単体検査の範囲でN1を準備した。最新main `73b93ed224b45b3f62e99e92447241e9af096d8a` を取得し、N0・速水先生の助言を読み、旧L2最終版65fb2accと旧科学資料を保護した。

天然構造を最終評価にのみ使う条件で、model1の28Cα proper RMSDと明示的なnative Qを主候補に整理した。34NMR感度、全窓、RMSD/Q共同分布、潜在着色、未定のhit/dwell、元幾何新規度との比較まで定義した。**実際のnative値は一つも計算していない。**

原研究には固定wall-clockでのnative成果、nativeを選点に使う方法、周期再学習と旧model再利用、非同期/資源pool制御が既にある。差異は単なるAI+MDや更新時機でなく、固定された強ZWを超える決定前Xの情報と、同資源・同情報条件での実成果という未実証仮説に限定した。

## 1. 指導助言の解釈と修正点

[原記録](../研究打合せ/2026-10-30-速水先生-差別化と科学評価.md)は研究者から共有されたメールで、具体閾値・参照・実験許可の承認ではない。FSD-EY継続とnative進捗/latent評価の提案を尊重しつつ、物理健全性・情報条件・研究差別化を省略しない。

重要な照合結果：

1. Bhowmik2018のQは距離8Å、75%の構象、1.1Å近傍の条件を伴う。N0のmodel1ハード接触や34NMR共識と同じとは言えない。引用先Savol2014も10Å/65%/sequence exclusionという異なる条件を使う。主Qと解釈的第二Qを明確に命名し、未取得の忠実実装はUNVERIFIEDとした。
2. DeepDriveMD2019のexplicit solventで完全foldしなかった例はVHPの限られたsamplingであり、FSD-EYの全explicit条件や一般的失敗の証拠ではない。
3. DeepDriveMD2022は12h×10回のnative比較があり、良い結果はnativeによる選点絞込みも使う。同時間成果自体を新規としないし、native非可視の現案と情報条件を揃えず数値優劣を言わない。
4. 現行公開pipelineのretrain_freqと旧checkpoint再利用、Colmenaのslot再配分を固定commitで確認した。これは当環境での全上流workflowの忠実実行成功ではない。

[文献行列](related-work-matrix.md)、[版・SHA・確認範囲](sources.json)。Maの2020出版書誌は確認、全方法値は2019著者版に帰属し、出版版全文との差は未確認とした。第三者の要約だけから同一性を保証しない。

## 2. 現在の科学境界

FSD-EY/1FME、OpenMM、現mdlearn CVAE、DeepDriveMD科学関数とParsl適応層、単RTX PRO6000 Blackwell Max-Q96GBを維持する。B1は等MD量・8乱数履歴根/16状態/240下流枝で、native事後評価しても旧確認結論やwall-clockの反実仮想に変換できない。L2新選点にはMDがない。

今後のnative接近は近似物理モデル内の構造進捗で、熱力学正しさ、folding kinetics、native ensembleの確率、蛋白一般性を保証しない。unfolded準備/pH/平衡・GBn2近似・座標reseedと連続MDの違いは旧Pリスクを保持する。先行研究との溶媒/力場/温度/摩擦/モデル・訓練量の違いを変えずに直接性能比較しない。

## 3. 完成した静的準備と実測

|項目|実施と結果|証拠|
|---|---|---|
|branch対応|240行のroot/state/条件群/二学習block×三MDblock・F0共有、親model/起点SHA|[全branch](branch-index.csv)|
|共通履歴|32×2ns、8根/16状態への祖先関係|[全history](history-index.csv)|
|天然参照|固定model1/全34/unfoldedのSHA、全modelに28CA文字列key|[reference audit](reference-static-audit.json)|
|サーバMD入力|272 DCD byte SHA、initial PDB SHA/CA順、CORD/NSET header一致。座標decode0|[全MD](MD-file-audit.csv)、[receipt](metadata-audit.json)|
|元model/潜在保存|80checkpoint byte SHA、96ranking NPZ SHA一致。model load0/NPZ科学配列読取0|[metadata receipt](metadata-audit.json)|
|archive|原9個存在・size一致。新規全量hash/移送/削除なし|[metadata receipt](metadata-audit.json)|
|数学単体|人工22test、失敗0/error0。反射、atom順序、8Å境界、空集合、欠測とcensorを含む|[test receipt](synthetic-test.json)、[log](synthetic-test.log)|

サーバmetadata監査wall8.725239s/CPU8.095469s、peakRSS26.473MiB。人工test実行wall0.058995s/CPU0.078913s、RSS37.793MiB。後者wallはimport後のtest計時、CPUはprocess累積なので直接wallと割合比較しない。接続/コピー/importの全process費用を含む精密な全準備費用ではない。GPU実行0、実座標科学値0。[費用計量案](resource-and-timing.md)。

## 4. 指標・実装の完成範囲

[契約](native-metric-contract.md)は数式、Å/ps/s、原子対応、proper rotation、mask、二Q、NMR感度、全12窓、best/argmin、共同分布、hit/censor/dwell、情報漏洩、統計階層を定義した。数値選択はPROPOSEDで、将来採択commitが必要。

[純粋関数](../../p1/n1_native_metrics.py)は対応済みarrayにだけ作用し、DCD/PDB/modelを読むAPI/実科学CLIを持たない。[metadata audit](../../p1/n1_metadata_audit.py)はbyte/hash/headerと文字列を扱い、MDAnalysis/OpenMM/Torchの科学処理をimportしない。原科学コードは変更しない。

実DCD evaluatorのstreaming reader、quality/global-ID join、34参照のbatch処理、全窓/根統計、可視化の実行器は**未実装・未実行**。pure functionsの22testで実軌跡評価器全体が完成したと称さない。候補latentの保存はあるが、下流全frameの潜在図には別の新forward承認が要る。

## 5. 最小オンライン案と識別限界

[設計](cb2-minimal-design.md)はCの同状態UPDATE_NOW/STALE_NOWの観測価値差とB2の複数decision政策効果を分離した。開発は既存8根、校正は新4根、blindは新8根という最小候補、C24rollout＋B2 40=64行。全て未生成・未実行。8根はpower保証ではなく、4校正根では強ZWを条件付けるには不足し得る。共通支持/分散/モデル複雑さが成立しなければ停止し、件数を無断増やさない。

H600sはdecision後の費用計算案。共通prefixを無料で共有した条件付き実験を完全campaignの実end-to-end予算と称さない。最終採択は必要。C holdoutを見てB2を変えるなら新しいholdoutが要る。全policyを同じcandidate実現へ強制せず、生成規則を同じにする。B1の未来native値や更新後結果をXへ入れない。

## 6. 不確実性・陰性・Threats to Validity

- 本輪には新native科学値がなく、既存B1がnativeへ近づくか未確認。閾値未定を勝手に補完しない。もし今後全hit0でもそれを消さない。
- Qはdegenerate、RMSD最小はサンプル数/参照選択の機会に依存。34最小やbestの改善は平衡samplingの改善と異なる。元全指標/窓・品質除外を保持する。
- 8元根も12新根案も同一準備構造・物理モデル由来。frame/seed/checkpoint/NMRを独立根としない。
- L2は巨大KL・局所幾何/seed/LOF不一致があり全面PASSでない。新モデルrecipe未決を実装者が採択しない。
- CONTINUEとreseed型selectorの差は複合政策差。更新に関する直接対照は同じselectorのZW対ZW+X。C新2action案はF1追加訓練対照を欠くため新data単独の効果ではない。
- 元Wに物理summaryがあること、X3/X4との冗長性を開示する。弱いbaselineへの改名でXの利益を作らない。
- 並行/競合は未測。一枚GPU・空きGPU・大きいVRAMから深刻な競合や無干渉を推論しない。
- 論文版差・Bhowmik Qの実装不明、原著referenceのatom fit選択、Leeの個別MD長表記差を残した。全文不足を断定的空白へ変換しない。

## 7. 取得・準備失敗と監査

文献検索で不一致arXiv ID2204.10732を開いたが別論文だったため採用せず、正しいDeepDriveMD2104.04797v5を確認した。PMC/ACS一部のweb閲覧とMa DOIの本文redirectは制限され、固定PDF/著者版・EuropePMC原文を使用した。Colmenaのmain指定は422で、APIのdefault_branch=master確認後に固定commitを取得した。これらは文献取得の失敗で、科学データの失敗・原結果修正ではない。

DeepDriveMD PDF抽出にxref修復警告があったため重要箇所をarXiv HTMLで対照した。上流codeの静的挙動確認はしたが、依存を入れて上流workflowを実行していない。SHA不一致・atom不一致・科学単位失敗は今回なし。最終[静的交付検証](delivery-validation.json)は旧保護SHA/索引/リンク/テストソースと結果を照合し、独立科学審査ではない。

## 8. 交付判断・次の一段階

**準備技術交付PASS／科学採択PENDING**。研究者/ChatGPTが契約・情報条件・P/L・費用ゲートを審査し、最初に限定N1-CPU評価を承認するか判断することが唯一の次行動。MD/train/inference/LOF、資源benchmark、C/B2、溶媒変更を自動開始しない。全原archive保持、Mac raw免除は継続する。

[指導教員概要](supervisor-summary.md)、[A–G](handoff-to-chatgpt.md)、[原文索引](sources.json)、[最終GitHub回読](remote-readback.json)を参照。実在する内容commitと最終commitは別に記録し、自身の未来SHAを捏造しない。
