# CVAE学習と復元条件

既存mdlearn938cb80のSymmetricConv2dVAETrainerを再利用した。ネットワーク、再構成損失/KL、RMSprop、勾配clippingを変更しない。入力28×28の二値8 Å Cα接触をCOOで表す。非周期のMDAnalysis contact_matrixを使い、天然構造への整列/RMSDは選点に不要なので実行しない。学習された正規化器は使わない。

構成：filters16×4、kernels3×4、strides1/1/1/2、dense128、dropout0.5、latent3。RMSprop lr0.001、weight_decay10⁻⁵、λ_rec=1。損失は元実装のL=λ_rec L_recon+L_KLで、値の尺度/バッチ集約も既存関数のまま。

M0は旧800を1回、200 optimizer steps。F1/F2も800容量を1回ずつ、200 steps×batch4=800曝光。既定fitのrandom80% splitを避け、明示時間splitのDataLoaderを元`_train`へ渡す最小適応である。未学習モデルと同じM0から始まる対照を混同しない。validation200は全臂共通の診断で、停止/配方選択/モデル選別には使わない。

checkpointにはweight、optimizer、epoch/追加歩数、torch CPU/CUDA RNG、Python RNG、NumPy RNGを保存する。モデル/optimizerの内容digestとファイルSHAは別概念である。F1/F2は同じM0 weight+optimizerを回復した後、ブロックの同じRNGへ再seedして対応させる。親RNGをそのまま継続したとは書かない。

学習前のweight/optimizer/RNG digest、各stepのloss、実step数、全曝光IDと800位置のpermutation、最終checkpointSHAを保存する。loss記録は既存損失値を観測し、損失を再実装したり無意味な学習を追加して費用を増やしたりしない。

M0の200歩は実測済みで[凍結資料](recipe-freeze.md)に記載。F1/F2の実測対応は最終証拠表を参照する。loss低下や候補の変化だけでは科学的探索改善を証明しない。1回曝光の学習が十分かどうかも本Pilotの結論範囲に含めず、陰性結果を一般的なAI無効論にしない。

固定版の追加既定値：ReLU、decoder末端Sigmoid、clip_grad_max_norm=10、train/valid_subsample_pct=1、schedulerなし。optimizerの全param_groups（alpha/eps/momentum等を含む）は保存checkpointから読み戻して公開モデル来歴表に記録する。checkpointをCPUに読戻し、weight/optimizer内容digestの一致も独立の保存検査として実行する。
