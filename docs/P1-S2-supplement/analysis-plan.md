# P1 S2-SUPPLEMENT：结果分析前承诺（v1）

日期：2026-10-24 JST。基线：`8f09fc02975a8736254925b7f7e69b23443cbe68`。本文件由第一阶段独立方法学审查形成；编写时只读已有 S2 报告、代码、输入/任务元信息及一手来源，**没有执行补充结果计算**。已有 S2 结果并非盲态；本计划只对尚未执行的补充分析构成事前承诺，不得称整个研究已经前瞻预注册。

**CONFIRMED**：S2 CONDITIONAL PASS、S2-SUPPLEMENT APPROVED；FSD-EY/1FME、单 RTX PRO 6000 96GB、构象探索目标不变。**S3 NOT APPROVED，evaluation_ready=false**。以下尺度、警告阈值和对照实施参数均为 **PROPOSED：本次内部方法检验预先固定值**，不是研究者批准的正式科学协议，也不是文献验证过的物理容差。

执行顺序：先提交并推送本文件和 `methodology-review.md`，回读远端记录完整 commit SHA；再建立补充实现 commit 和运行 manifest。结果 manifest 引用计划 SHA 与文件 SHA-256。不得先计算后补填预注册时间。任何修改须追加 amendment、说明原因及已经看过的结果；不覆盖原计划、不将修改后分析称为同一个事前检验。

## 1. 有界执行卡与问题

| 项目 | 固定范围 |
|---|---|
| 数据 | 成功批次 `results/raw/remote/2026-10-24-P1-S2/runs/s2-pilot-02`，6个MD任务、4880帧、累计计算2.44ns；不合并失败批次 |
| A | 固定物理表征、完整先验尺度网格、整seed隔离、采样敏感性和负对照 |
| B | 固定800帧候选池，已有frozen/updated LOF-only审计；CPU可行时追加匹配更新量的三臂比较 |
| C | 输入来源/物理语义审查；11个预选构象、3种非键设置的非积分CPU能量/力敏感性 |
| 不做 | 新MD积分、后续候选收益MD、GPU训练、S3策略campaign、替换正式科学参数、论文显著性声明 |
| 资源建议 | 本地隔离CPU环境；科学计算最多2线程、一个子进程串行，RSS上限4GB、派生输出1GB；不用GPU/MPS |
| 成本上限 | A 600s；B全部含训练/推理900s且每训练臂90s；C 300s；总科学计算1800s，不自动追加预算；依赖安装另限15min/5GB，超限保留设计与失败 |
| 停止 | 超时/资源超限/非有限量/血缘不匹配停止对应模块并保留失败，其他独立只读工作可完成；禁止换GPU补跑 |

研究假设不是预期成功承诺：A1检查物理投影能否避免一帧一状态且不过度塌缩；A2检查固定校准中心库能否赋予内部留出轨迹可解释的覆盖/库外距离；B检查不使用native参考时模型/训练数据组成是否改变决定；C检查当前1nm相互作用设置对既有坐标的能量/力敏感性。上述均不能检验“更新提高后续探索”或“调度更优”。

## 2. 数据血缘、统计单位与拆分

1. 原始数据只读；核对 `checksums.json` 的203个实际数据文件（排除AppleDouble元数据），报告未核验/缺失项。保留既有成功2.44ns/4880帧、800帧候选池及原始LOF+参考RMSD输出的身份与值。失败批次不进入本分析分母，仍在失败登记中。
2. 所有派生行至少保存 `run_id, task_id, result_id, seed, frame_id_0based, physical_time_ps, input_sha256, analysis_commit, plan_commit, parameter_id`。DCD按原504原子拓扑读取；A取拓扑次序28个 `protein and name CA`；C取全部504原子。记录链/残基/原子序号映射，不能靠字符串排序重排残基。Å为A单位，转换到OpenMM时明确 `1 Å = 0.1 nm`。
3. **整seed划分**：`2026102401`（r0，所有20/200/1000ps任务）为 calibration；`2026102402`（r1，所有长度）为内部 holdout。主A校准只用 `md-1000ps-r0`，主A留出只用 `md-1000ps-r1`，每条2000帧；20/200ps仅作前缀/长度敏感性附表。禁止把同seed短段放校准、长段放留出，禁止随机拆帧伪造独立性。
4. 六个任务都从同一unfolded坐标、按两个重复seed重新初始化。各长度同seed可能是相同/近似前缀；OpenMM相同seed不保证逐位一致，**也不能据浮点不一致推断独立**。先对同seed重叠物理时刻比较：原坐标逐值相同率、Cα dRMSD min/median/max、`<=10^-6 Å`与`<=10^-3 Å`近重复比例，并记录是否整体漂移/转动。不同seed也做同类诊断，不因相似而悄悄删帧。主A只取每seed最长轨迹，避免重复累计；全4880帧并集仅历史对应附表。
5. 有效独立性上限是**两个seed组**，不是6个独立轨迹，更不是4880个样本；共同初始构象进一步限制外推。只有一个校准seed、一个内部留出seed，且旧S2已公开汇总，不能称外部独立验证。不给frame bootstrap CI、p值或策略显著性；描述每条轨迹，不汇报伪精确的独立样本标准误。
6. 主分析不删初期帧，明确“含初始化松弛，未建立平衡”。只按预定敏感性额外报告 `physical_time_ps > 20` 和 `>100` 的最长轨迹；这些切除不称合格burn-in，不能从结果挑一个当正式平衡时长。

## 3. A1：两个固定低维物理表示

对第i个Cα位置 `x_i∈R³`（Å），`n=28`，采用非周期欧氏距离 `d_ij=||x_i−x_j||₂`，不用盒子、不进行native对齐。

### 3.1 公式与物理含义

- Cα回转半径：`x̄=(1/n)Σ_i x_i`，`Rg_CA=sqrt[(1/n)Σ_i ||x_i−x̄||²]`（Å）。是等权Cα几何紧致度，不是全原子质量加权Rg。
- 长程接触比例：`P_long={(i,j):1≤i<j≤28,j−i≥4}`，`|P_long|=300`；`Q_long(r)=Σ_(i,j)∈P_long 1[d_ij<r]/300`，无量纲，取值[0,1]。这里Q不是native contact fraction，分母不来自参考结构；等于r不算接触。附原始整数接触数。
- 端到端距离：`R_ee=||x_28−x_1||₂`（Å），是链首尾Cα间距。
- 表示A1a=`(Rg_CA,Q_long)`；A1b=`(Rg_CA,R_ee)`为互补诊断。不能把这些二维格子称为独立亚稳态或全部可达空间的覆盖率。

### 3.2 冻结尺度网格与计数

所有组合全部报告，不根据模型/seed有利结果删选：

| 参数 | 先验网格 | 指定展示基准（不代表科学最优） |
|---|---|---|
| 接触r | 7,8,9 Å | 8 Å |
| Rg箱宽 | 0.5,1,2 Å | 1 Å |
| Q箱宽 | 0.02,0.05,0.10 | 0.05 |
| R_ee箱宽 | 1,2,4 Å | 2 Å |
| 分箱原点敏感性 | 0与半个箱宽 | 0 |

定义 `b_Δ,o(z)=floor((z−o)/Δ)`，格子键为两个整数的有序对。原点0是主表；半箱移位对两轴同时使用 `o=Δ/2`。边界严格左闭右开，不按观测min/max拟合范围，不截断超出历史范围的数据；Q=1保留它的合法bin而非丢失。负Rg/负距离、Q不在[0,1]或非有限值为实现/数据失败。

截至合格帧集合F的覆盖计数 `U(F)=|{b(x):x∈F}|`（格子个数），无“总构象数”分母。报告单轨迹 `U(n)`、`U(t_phys)`、visit-frequency、单次占用格比例、邻帧转换率 `Σ1[b_t≠b_(t−1)]/(N−1)`、连续停留长度（帧/ps）。单帧观察跨度为0，连续k帧的首末间隔为`(k−1)×0.5ps`，不能把k×0.5ps称精确停留时间；进入/离开时刻有采样区间删失。

### 3.3 压力测试、失败与警告

- 完整重复同一集合2×，最终U必须相同；置换顺序后最终U相同，但累计发现曲线允许变化，不能要求每个时间点不变。
- 预定刚体变换：绕z轴90°并平移`(10,−7,3)Å`。距离/Rg应在绝对`10^-6 Å`内相同；格子标签若因原值距边界≤该容差而变化，单列边界敏感性，不用未报告的rounding“修复”。非边界翻转为FAIL。
- 时间抽稀固定frame起点0，stride `1,2,4,10`，对应0.5/1/2/5ps；抽稀集合是原集合子集，最终U不可增加。报告各stride最终U和相对全帧的保留比例，**不要求真实不同采样密度覆盖数严格相同**。
- 描述Rg/Q/R_ee自相关：`ρ(k)=Σ_(t=1)^(N−k)(z_t−z̄)(z_(t+k)−z̄)/Σ_(t=1)^N(z_t−z̄)²`，最长轨迹lag=1…min(200,floor(N/4))，单位lag×0.5ps；常量序列标NA，不伪造0。非平稳松弛时不把ρ换算为可信独立样本量。
- 预定内部退化旗标：任一最长轨迹 `U/N≥0.8` 为近“一帧一状态”；`U≤1`为塌缩警告；转换率≥0.8且停留run中位数为1帧为抖动警告；stride10最终U/stride1最终U<0.5为强采样敏感警告。阈值是保守诊断规则，**不具有物理验证地位**。任一旗标不能通过换参数隐藏；所有网格全旗标时A1科学适用性NOT READY。无旗标也不等于指标已验证。

## 4. A2：固定中心库上的Cα距离RMS差

沿用旧A特征对 `P_d={(i,j):j−i≥3}`、m=325，`f(x)=(d_ij(x))`。定义 `D(x,y)=sqrt[(1/m)Σ_(i,j)∈P_d(d_ij(x)−d_ij(y))²]`（Å），称本项目非局部Cα dRMSD。不是对齐坐标RMSD，不含native参考，不对维度拟合标准化；刚体旋转平移不变，但镜像和不同构象投影可能不可区分，不能独立证明物理合理。

先验半径网格 `ε∈{1,2,4}Å`，2Å仅指定展示尺度。只从calibration最长轨迹frame `0,10,20,…,1990`（200候选，5ps间隔）构建中心库：按frame升序，第一个为中心，其后仅当到所有已有中心最小D严格大于ε时加入。每个ε独立建库，保存中心原frame ID、特征和SHA。**先保存/冻结库，再分析r1；不反向重拟合、不用holdout补中心**。

留出帧映射至最近中心（相同距离以中心frame ID升序打破并列），最近距离≤ε才记该中心被访问；否则标OUT_OF_LIBRARY。报告访问中心数、访问比例 `visited/K`（只相对于这个有限校准库）、库外帧比例、到库最小D的median/p90/max。库外不能每帧算一个“新态”，也不能统统计作一个可靠新态。另列每格内dRMSD分布以说明低维混叠，不按此回调A1。

重复/刚体/置换最终访问集合不变，抽稀访问集合不扩大。K=1为塌缩警告，K/200≥0.8为中心库过细警告，holdout库外比例>0.5为库代表性不足警告；全部为内部诊断阈值。全网格不良时结论是需独立校准数据，不再扩大ε网格直至“通过”。本方法只建立内部候选，库及半径均尚不能直接冻结为正式S3评价器。

## 5. 时间轴的可审计口径

`physical_time_ps=(frame_id+1)×0.5`来自reporter步数，准确代表任务内部模拟时刻；2.44ns是六次实际计算的长度之和，不是2.44ns独立连续动力学，也不是去重后的探索量。

现有 `StateDataReporter` 只写step/模拟time/能量/温度，没有逐帧墙钟。`result.json`的任务started/ended时间与component offset不是逐帧到达日志。**禁止按积分总耗时对帧均匀插值，再画成MEASURED逐帧wall-clock覆盖。**

优先从现有controller事件找可验证的数据发布/消费时刻；若有可靠task publication事件，以该事件为全任务帧的批次可用时间，画阶梯覆盖 `U(t)=|∪_{j:a_j≤t} states(task_j)|`，包括先前初始化/训练/推理/检查及空隙，不仅累计MD时间。若只有worker `ended_unix_s`，只标“worker结束代理，尚不含最终序列化/返回延迟”；起点取首个有记录worker开始并明确它不是完整controller t0。若可得真实controller起点则另报该口径。

缺乏可验证的统一时钟或发布时刻时，交付按任务顺序的覆盖表、已测总217.439157s及缺口，不强造端到端曲线。可将帧产生时刻表示在任务积分起止区间内；任何估计单独标MODELLED且不作主结果。本阶段报告应明确是否满足了“端到端墙钟”要求及未满足原因。

## 6. B：固定候选池与无native选择审计

### 6.1 已有模型的离线比较（必要）

精确沿用 `infer-frozen-r0/science/snapshot.json`顺序，两条200ps轨迹各400帧；核实其他推理快照身份相同。已有scores/embedding为原始证据，不能覆盖。LOF-only规则：对全部800嵌入使用sklearn1.6.1 `LocalOutlierFactor(n_neighbors=20,metric='minkowski',p=2,novelty=False)`，按 `negative_outlier_factor_`升序（更小、更离群），并列以 `(result_id字符串, frame_id数值)`升序；不使用RMSD、不改为novelty=True、不按结果设置额外过滤。非有限值拒绝整个受影响结果，不修成0。

所有模型共同报告top-k，k=`1,10,100`；交集、`J=|S_a∩S_b|/|S_a∪S_b|`、重合比例`|intersection|/k`、800分数Spearman（平均秩处理并列；常量分数NA）、top1是否变化、top1对间上述dRMSD（Å）、Rg/Q/R_ee值及训练/推理实耗。LOF分数不是概率、模型之间绝对分值无校准，主要比较排序；选择变化没有预设“必须成功”的门槛。

保留旧LOF→native RMSD与reference-only结果作标签明确的历史诊断，不混入新选择函数。保存已有两个重复推理的逐值一致事实；新增CPU推理重复是平台内控制，不能要求与历史CUDA逐位一致，也不能把平台变化归因到新数据。

### 6.2 CPU三臂实验（有界可行才执行，否则DESIGN ONLY）

| 臂 | 共同初始状态 | 更新输入/样本曝光 | 更新步数 |
|---|---|---|---|
| F0 | `train-before` checkpoint完整模型状态 | 不更新 | 0 |
| F1-old | 同一checkpoint模型+optimizer状态的独立深拷贝 | 旧400帧每帧2次，共800项 | 200×batch4 |
| F2-mix | 同一checkpoint模型+optimizer状态的独立深拷贝 | 旧400+新400各1次，共800项 | 200×batch4 |

本补充明确匹配**训练样本曝光总量、batch大小及真实optimizer.step次数**，不只匹配epoch。两臂唯一训练数据处理差异为一半重复旧样本被新样本替代；unique构象数与分布变化正是此干预的一部分，不能称已单独估计纯“新数据数量效应”。不是复现S2的80%随机split训练，也不直接与旧updated权重差解释因果；历史F0/updated另表保留。

为限制实现，不改CVAE结构、损失、RMSprop超参数与梯度裁剪；用固定vendor模型和训练步逻辑、显式长度800的索引序列、batch4，无drop_last损失、无early stopping/validation驱动选择、无学习率调参。既有标量RMSD仅可保留为历史诊断，**新训练与选择无需载入它**。此处全部800曝光用于更新，没有声称独立验证集或模型泛化。若原checkpoint含scheduler状态且它会改变此更新，应完整保留并给两臂同样step规则；无法证明一致则不跑。

配对训练随机种子固定为 `2026102411,2026102412,2026102413`（最多3对、6训练）。每对F1/F2从同一个保存的CPU RNG状态开始，NumPy/Python/torch RNG及线程数固定；使用同一800位置的排列，把F1第二份old对应替换为F2 new；记录每个batch原帧ID以核查曝光数。共同初始化包含所有model buffers、optimizer momentum/step等张量。不要让F2接续F1的结果。保存初始状态digest，模型.train/eval模式、实际step计数、batch哈希和最终权重哈希；随机初始化之后再次恢复共同RNG起点，避免加载操作消费随机数的差异。

每个新模型只在固定800候选池上推理；F0在同CPU代码路径下推理。统一推理seed `2026102404`；至少F0重复一次确认平台内可复现。相同seed的F2−F1反映这次匹配更新量下数据组成干预的决策差异；F1−F0显示仅额外训练也能否改变决策；3个训练seed不是3个独立MD数据集，不能声称总体统计效应。CPU实耗单独记为CPU，**不得代替RTX PRO6000成本或更新机会成本**。

先执行一对作为资源可行性门：每臂≤90s，B累计≤900s、两线程/4GB；超限停止B训练，不删失败挑快的seed，不减少steps继续声称匹配试验成功。可完成的完整配对结果描述性报告；不足配对或无法复现optimizer控制时明确DESIGN ONLY/INCOMPLETE，不要求重跑GPU。所有阴性结果（无变化、F1变化大于F2、排名不稳定）都是有效结果。

## 7. C：同坐标、非积分物理敏感性

### 7.1 原始来源与输入资格

区分RCSB实验结构记录与DeepDriveMD处理后输入。RCSB1FME为28残基/34个提交NMR构象；当前网页251原子不是上游504原子含253H的制备证明。MODEL1抽取、H/端基/质子化、unfolded制备历史分别查证；上游固定文件哈希只证明身份，不补写热展开或平衡过程。未见来源保持UNVERIFIED。

### 7.2 预选构象、参数与重复

固定11构象：原 `1FME-unfolded.pdb`（不最小化），及 `md-1000ps-r0/r1` 各frame `[0,19,199,999,1999]`，分别0.5/10/100/500/1000ps。按ID选择，不按异常能量/覆盖/LOF或native RMSD挑结构；保留早期非平衡性质。缺失任一不自动替换，报告缺失。

固定OpenMM8.5.2、同输入拓扑/全部504坐标/力场XML及其他参数，用 `ForceField.createSystem`独立构建3系统：`CutoffNonPeriodic 1.0nm`、`CutoffNonPeriodic 2.0nm`、`NoCutoff`。检查NonbondedForce与GB力的方法/截断及dielectric/kappa/SASA等，**不得只改其中一个force**。记录每个system XML、XML哈希、实际force列表与版本；不采用周期最小镜像。

仅CPU `getState(getEnergy=True,getForces=True)`，不 `step`、不重新最小化、不速度采样、不改坐标、不进行constraint projection。创建Context所用integrator只是API容器，步数必须记录为0。每系统每构象1次warm-up＋3次相同状态获取；共132次请求（99次计时重复），只3个Context，串行释放。将系统/Context创建与每次setPositions/首次获取/重复获取分开计时；重复可能缓存，不能外推MD步耗时。C≤300s/2线程/4GB，任一不支持组合保留报错并停止该比较，不偷偷换版本。

### 7.3 数学与解释

记录 `E_c(x)`（kJ mol⁻¹）、`F_c,i(x)`（kJ mol⁻¹ nm⁻¹）；NoCutoff只是同力场内无截断比较基准，**不是真实物理真值**。

`ΔE_c=E_c−E_NC`；另报相对首个unfolded的差分 `[E_c(x)−E_c(x₀)]−[E_NC(x)−E_NC(x₀)]`，避免仅把势能整体零点差当构象排序改变。逐原子 `δF_i=||F_c,i−F_NC,i||₂`，报告全部504原子的median/p95/max和 `F_RMS=sqrt[(1/504)Σ_i δF_i²]`；相对量 `R_F=sqrt[Σ_i δF_i² / Σ_i ||F_NC,i||²]`，基准分母为0则NA而非加任意epsilon。总力可被键合大力掩盖，尽可能另外输出非键/GB分项，分项不可得则明确限制。禁止把所有原子力向量平均相消后称误差小。

三次相同状态获取是技术重复，先报告逐次值/时间，汇总median与min/max；它们不增加科学样本数。任何非有限能量/力为FAIL；同坐标重复出现相对差>10^-5（能量按max(1kJ/mol,|E|)，力按max(1kJ/mol/nm,||F||)归一）为数值重复性警告，报告实际值，不自动更换精度调到通过。`R_F>0.10`为预定强敏感性旗标，不是小于此数即可认证1nm；所有构象/3种方法全部报告。缺少领域认可误差容限时，科学充分性仍UNVERIFIED。

## 8. 完成标准与S3边界

交付 `coverage-methods.md`、`selection-audit.md`、`science-readiness.md`、一页日语 `supervisor-summary-ja.md`、总 `supplement-report.md`，CSV/JSON、复现脚本/环境锁、所有输入与计划/代码SHA、失败和amendment表。原始/派生/MEASURED/PROPOSED/UNVERIFIED清楚分开；大轨迹/权重不上GitHub。

执行验收是：正确实现已登记规则；报告全部网格与负对照；完整血缘/时钟/更新预算/物理差异；失败不隐藏。**不要求指标“好看”、模型必有变化或cutoff误差小。** 如果无独立校准、物理来源仍缺、中心库失效或训练对照仅设计，报告CONDITIONAL/NOT READY及缺口，不虚构结论。

仅在未来研究者确认独立校准/冻结指标、无参考选择、科学初始化/溶剂/截断/reseeding协议、统一真实发布时钟、等墙钟预算及独立campaign重复设计后，才有资格提请S3。本文不是这些批准。补充完成后更新交接、正常同步并回读远端SHA，停止等待研究者审查。

## 9. 执行端可直接复制的Prompt

> 读取GitHub main最新AGENTS、博士研究全局总档案、协作交接记录、已批准S2补充规格，以及本analysis-plan.md和methodology-review.md。先确认本计划已在结果分析前commit/push并远端回读，记录其SHA；保留用户README修改和全部原始S1/S2。仅实施本计划A/B/C：以现有4880帧及800候选池为输入，whole-seed隔离、固定全部尺度网格、固定中心库、严格负对照，禁止逐帧墙钟均匀插值；B只有在本地2线程/4GB/900s内可靠实现共同checkpoint+optimizer+RNG与相同200步×batch4时执行，失败如实设计交付；C11个预定构象、3种系统、零积分，300s上限。不给新MD、GPU长训练、S3或正式参数审批。实现后先做数学/单位/血缘/边界/更新步数测试，再按冻结manifest运行；全量记录未通过、所有参数、原始与派生关系、软件/代码/输入SHA和时间。提交上述8节全部报告及日语概要，说明支持和不支持结论、P0/P1缺口、最小未来授权需求。结束时更新交接、fetch核对并合并、按用户身份commit/push、远端回读报SHA，停止等待审查。任何需要改变计划的情况先写带时间/已见结果的amendment，不事后替换主结果。

## 10. 一手依据（本轮已查看）

- OpenMM **8.5.2固定tag**用户指南，Implicit Solvent节：允许的非键方法、通常更大截断及2nm的一般建议；不是对本1FME的误差保证：[源码文档](https://github.com/openmm/openmm/blob/8.5.2/docs-source/usersguide/application/02_running_sims.rst#L620-L645)。`latest`当日显示8.6，不能充当运行版本依据。
- OpenMM **8.5.2** `LangevinMiddleIntegrator.h`，seed语义：不同seed随机力序列不同；相同seed不保证同轨迹：[固定源码](https://github.com/openmm/openmm/blob/8.5.2/openmmapi/include/openmm/LangevinMiddleIntegrator.h#L93-L103)。`LangevinIntegrator.h`该版本为其子类。
- sklearn **1.6.1** LOF属性定义，negative_outlier_factor越小越离群：[官方文档](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)。
- [RCSB 1FME](https://www.rcsb.org/structure/1FME)，Experimental Data/entry v1.4，实验身份与34模型；不证明上游unfolded制备。
- 本地固定DeepDriveMD `b18dacba46f079644e4ee66191675375581955c3` 科学函数、`inputs/p1-fsd-ey/manifest.json`；mdlearn `938cb80ac3ebe33498dbcb2780f97f81ec80e0f8` `symmetric_conv2d_vae.py`的fit/_train与`data/utils.py`；项目`p1/server/science.py`、`qualification.py`、`qualification_analysis.py`。源码审查不等于执行验证。
