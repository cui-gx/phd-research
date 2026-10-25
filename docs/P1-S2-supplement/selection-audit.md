# B：不使用天然参考的候选选择及匹配更新对照

2026-10-25 JST；`MEASURED` 指本机CPU测量，科学解释限定为同一数据对上的决定变化。无新增后续MD，无调度收益实验。

## 规则与公平性

同一有序800候选池=md-200ps-r0/r1各400帧，输入SHA和snapshot ID见[manifest](../执行证据/2026-10-24-s2-supplement/selection-manifest.json)。不读取folded/native RMSD。CVAE embedding后在全池用sklearn1.6.1 LOF(k=20, Minkowski p=2, novelty=False)，按negative_outlier_factor_升序（越小越离群），并列按result_id字符串、frame整数升序。只拒绝非有限分数，不事后筛除“噪声构象”。[官方接口](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)；[固定mdlearn源码](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)。

选中对象是原始result_id+0基frame，不是重新生成结构。F0旧checkpoint的SHA256为`32f1a9887ec6dbb980862a00977bc48c710b0a74c1476c714efb10f61a4344e3`。每臂从共同模型、buffers和RMSprop状态深拷贝恢复，核验摘要；训练前重新设定Python/NumPy/Torch RNG。优化种子2026102411/12/13，统一推理种子2026102404。

| 臂 | 数据/曝光 | 真正optimizer.step | 用途 |
|---|---|---:|---|
| F0 | 冻结，不训练 | 0 | 既有模型决定 |
| F1-old | 旧400每帧2次，共800曝光 | 200，batch4 | 仅继续训练 |
| F2-mix | 旧400+新400各1次，共800曝光 | 200，batch4 | 用新帧替换一半重复旧曝光 |

两个更新臂用相同800位置排列和配对种子，复用vendor `_train`的损失、梯度裁剪和优化器，未采用公共fit的80%随机划分或按epoch猜步数；没有验证集选优。公共初始checkpoint未被优化器状态别名污染（恢复后摘要与测试均核实）。结构/学习率等配置沿用[科学配置](../../configs/p1_server_science.json)，本补充仅设备改CPU、workers0；损失值不作为科学效果评价。

J_k=|A_k∩B_k|/|A_k∪B_k|；overlap_k=|A_k∩B_k|/k；Spearman在相同800ID顺序上比较连续LOF分数，包含并列平均秩。所有k=1/10/100均保存。训练及推理为本机墙钟，不是目标GPU成本。

## 结果与反例

F0重复推理两次逐分数相同。6个更新臂均完成200步、800曝光，共同初始模型/优化器一致。下表是全部三个优化随机性配对，无挑选最佳seed。

| seed末两位 | F1 vs F0 top100交集 | F2 vs F0 top100交集 | F2 vs F1 top100交集 / Jaccard | F2 vs F1 Spearman | F2 vs F1首选dRMSD (Å) |
|---|---:|---:|---|---:|---:|
| 11 | 24 | 19 | 23 / 0.12994 | 0.14713 | 2.69749 |
| 12 | 20 | 17 | 28 / 0.16279 | 0.32340 | 5.38435 |
| 13 | 21 | 18 | 28 / 0.16279 | 0.17574 | 3.04724 |

F2 vs F1三对top1均不同，top10交集均0。F1本身也明显改变F0排序，因此不能把“更新对比冻结”的全部差异归因于新数据。F0首选旧轨迹frame53；F1三seed依次旧轨迹161/54/161；F2依次新轨迹65/旧轨迹315/新轨迹0。完整result_id映射、Rg/Q/Ree和全部分数见[比较](../执行证据/2026-10-24-s2-supplement/selection-comparison.json)、[训练臂记录](../执行证据/2026-10-24-s2-supplement/matched-arms.json)和同目录`scores-*.json`。

6臂训练墙钟0.8545–0.8794s，包含恢复与数据准备在内的臂训练区间，不是纯GPU kernel时间；每臂推理/LOF/写盘约0.2439–0.2474s。F0首次/重复推理0.2952/0.2525s，缓存/启动不同。B进程整体14.7406s含导入、检查、恢复、训练、推理和文件操作。不能用这些CPU成本计算单RTX PRO6000上的MD机会损失。

历史CUDA frozen vs updated的LOF-only top100交集19，J=0.10497、Spearman≈0.12015、首选旧轨迹53→138；参考引导原实际选择仍是新轨迹340→365。两类选择不是同一规则，旧结果完整保留；历史更新的步数/曝光并未匹配，不用于纯新增数据因果证据。[历史复算](../执行证据/2026-10-24-s2-supplement/historical-lof-only.json)。

## 可支持及不可支持

本数据和模型下，无天然参考LOF-only规则可可靠执行；固定优化更新量后，训练数据组成干预仍改变排序和原始构象选择。只支持**条件性决定差异**。新数据的分布、独特构象数、来源轨迹seed一起变化，不能独立识别抽象“新数据数量效应”；三优化seed不是三个独立MD数据集。模型仅有初步训练，选择不稳定可能源于表示未收敛；LOF极端离群可能是非平衡异常，而非有价值科学状态。

没有后续MD验证，不支持探索改善、更新值得付出GPU时间、优于无AI或调度算法有效。正式规则仍`PROPOSED`，不替换原工作流；下一步需要研究者批准科学资格、选择规则及公平预算协议，而不是继续训练直到出现有利结果。
