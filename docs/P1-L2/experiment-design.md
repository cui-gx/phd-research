# 固定行列、学習系譜、乱数の分離

本案の全数値・seedはPROPOSED。研究者の実行承認前に確定する。行列は[36chain](experiment-matrix.csv)と[156評価点](checkpoint-matrix.csv)。

## 1. 学習系譜と歩数

~~~mermaid
flowchart LR
  I["独立初期化 i1/i2/i3・step0"] --> M["M0：OLD800\n200 → 400 → 800 → 1600"]
  M200["保存M0-200\n重み＋optimizer"] --> F1["F1：OLD800\n追加200 → 400 → 800 → 1600"]
  M200 --> F2["F2：OLD400＋NEW400\n追加200 → 400 → 800 → 1600"]
  M -. "200歩snapshotのみ" .-> M200
~~~

各状態で3初期化×3chain。全4状態で36chain、各1600歩、計57,600新規optimizer steps、230,400サンプル提示。1epoch=800 unique ID/4=200歩。checkpointは1/2/4/8epoch。各chain内の提示数800/1600/3200/6400を記録する。M0 step0を12個保存し、未学習アーキテクチャ対照とする。

M0のchain_stepsはlifetime_stepsに等しい。子のchain_stepsは追加量で、lifetime_steps=200+chain_steps、従って400/600/1000/1800。F1/F2のstep0はM0-200のaliasで、新たな24独立モデルにしない。F0はM0-200固定を意味し、M0-1600を後からF0へ置換しない。144学習済みendpoint＋12未学習endpoint=156モデル評価、各OLD/RECENTで計312モデル集合条件。

旧[Post-R1案](../P1-Post-R1-Qualification/minimal-design.md)にはM0歩数を診断から選んでから子を分岐する選択肢があった。本L2では**親をM0-200に事前固定する変更案**とし、最良親選択による交絡を避ける。旧案・旧証拠は上書きしない。長く学習したM0を親とする効果/交互作用は未識別として残す。

## 2. 乱数と更新の対応

|stream|値|用途|
|---|---|---|
|init i1/i2/i3|1700000101 / 1700000102 / 1700000103|M0の重み初期化のみ。同じiを全4状態で使う|
|M0 optimization|1701000001|初期化の後に再設定するdropout・reparameterization等の乱数|
|M0 permutation|1701000001|独立したNumPy Generatorの8epoch順序。optimization RNGとは別object|
|F1/F2 optimization|1702000001|親復元後に同じ乱数状態で開始する。3初期化間でも同じstream|
|F1/F2 permutation|1702000001|各epochで同じ800位置の並べ替え。内容は臂で異なる|

`init_seed`と`optimization_seed`を単一のseed列に潰さない。M0を構築・初期化した後でoptimizationを再seedし、全初期化で初期optimizer空状態と学習順序を一致させる。F1/F2は同一M0-200のmodel/optimizer/scheduler（存在する場合）をstrict復元し、同一乱数開始状態を確認する。初期化間では親optimizerも学習で変わるため、「子の重みだけの直接効果」ではなく初期化に起因する学習履歴の条件付き影響である。

epoch間はRNGを継続し、毎checkpointでseedを戻さない。permutation generatorを8回順次呼び、全800位置を各epoch一回ずつ使用する。旧200歩の単一passを繰り返すだけの固定順序とは区別する。実際の8epoch順序とRNGstateは将来の実行前凍結・保存対象である。本輪では乱数列を生成していない。

3初期化×1更新streamは、固定した最適化雑音の下で初期化を比べる最小案である。L1の旧二更新seed結果は既報対照として保持するが、新初期化との交差セルではない。初期化×更新seedの分散分解を要求するなら2番目の更新streamでF1/F2を追加する必要があり、24追加chain/38,400歩となる。**その追加は今回の行列外で、別承認が必要。**

## 3. 維持する仕様

[Q0実recipe](../P1-Q0/model-recipes.json)、[固定学習実装](../../p1/server/b1_science.py)、[mdlearn](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)に一致させる。

- 入力1×28×28、binary contacts、cutoff8 Å、残基/原子順は原データを使用。
- convolution filters=16×4、kernels=3×4、strides=1,1,1,2、affine128、dropout0.5、latent_dim3。
- RMSprop、lr0.001、weight_decay0.00001、gradient clipping norm10、lambda_rec1、batch4、num_workers0。その他optimizer既定値と全param_groupsは原環境の実値を記録し、変更しない。
- 訓練損失は既存のALL784 BCE batch総和＋KL batch平均を維持。評価でNONLOCAL/LONGを使っても、訓練maskや重みは変えない。KL annealing、early stopping、lr scheduler、学習率探索、標準化やaugmentationを新設しない。
- 旧自動random splitは使わず固定membershipと共通評価IDを使用。保存モデルを読む診断はCPU/eval/no_grad、batch32、z=mu。CPU評価は訓練chainから分離しRNGを消費しない。

## 4. 順序・比較・不変性

状態順はr01-s4、r01-s8、r02-s4、r02-s8、各状態i1→i2→i3。各初期化でM0を1600まで計算・保存した後、固定M0-200から子を実行する。F1/F2実行順は状態index（0始まり）と初期化indexの和が偶数ならF1先、奇数ならF2先。途中の良否で順序を変えない。親依存は順序と独立にSHAで確認する。

M0を1600まで学習しても、子に渡すのは既に保存した200時点の完全snapshotである。modelのmutable参照を使い回さない。全子の親SHA・開始model/optimizer digest一致を監査する。

新36chainは原80モデルの置換でも再現試験でもない。初期化/streamが異なるため、旧B1の200歩と新200歩の差を「歩数だけの効果」としない。旧L1値は背景、新chain内の対応差がL2の推定対象となる。

全候補はS4=7,800、S8=15,800で、原indicesのcandidate順序・IDを固定する。評価点156個全てにFULLのembedding/LOFを用意する案である。未学習対照も同じ候補数を使う。候補や密度集合の縮小・native RMSD選別・下流成果による選点は行わない。
