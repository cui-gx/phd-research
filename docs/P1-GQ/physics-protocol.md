# FSD-EY物理协议与准备资格

2026-10-26。已执行的GQ1为MEASURED；NoCutoff只是本轮探索候选，正式科学协议尚未冻结。

## 输入与准备史

固定DeepDriveMD提交`b18dacba46f079644e4ee66191675375581955c3`的1FME-unfolded输入，SHA256 `8cb0382cb19e24c1159eb672b236bc1a6642fc8025e6c5cb8200c3c4c435d2b3`。保留504原子/28残基及原有氢、端基；不默默添加氢或改变质子化。PDB读取、原子顺序、每残基原子、氢和电荷另由服务器inventory记录。折叠参考只核对拓扑，不参与本轮候选或覆盖评分。

上游文件来源已知不等于制备过程已知。展开构象生成方法、制备动力学、pH/质子化选择、充分平衡均UNVERIFIED。此次不重建科学体系，也不能凭一份PDB认证这些条件。

## 三候选的实际含义

共同参数：Amber14-all+GBn2隐式溶剂；300K；Langevin摩擦1/ps；2fs；HBonds约束、tolerance1e-5；非周期；CUDA mixed与DeterministicForces=true。每候选重新创建System，而非只更改现成GB对象的cutoff属性。保存System XML与实际force属性。

- 1nm：CutoffNonPeriodic，历史参照。
- 2nm：CutoffNonPeriodic，较长截断候选。
- NoCutoff：不施加非键距离截断的比较候选，不视为物理真值。

固定8.5.2的[GBn2脚本](https://github.com/openmm/openmm/blob/8.5.2/wrappers/python/openmm/app/data/implicit/gbn2.xml)将NonbondedForce的reaction-field dielectric设为1，并构造相应GB项。[GB实现](https://github.com/openmm/openmm/blob/8.5.2/wrappers/python/openmm/app/internal/customgbforces.py)的`_createEnergyTerms`中cutoff还进入GB成对能量表达式。故三个配置的不同并非单一属性开关，绝对能量偏移不直接证明哪个构象更稳定。

当前[官方指南Implicit Solvent](https://docs.openmm.org/latest/userguide/application/02_running_sims.html)给出NoCutoff/非周期截断的使用背景，并建议隐式溶剂通常采用较长截断；这是一般背景，不是本蛋白的精度认证。固定8.5文档入口本次未能访问，实际执行依据安装源码、XML和版本哈希。

## GQ1实测发现

5个预定结构×3候选×4技术重复（首次热身）×4force组，共240个状态请求，0积分步。组定义为total、普通NonbondedForce、CustomGBForce、其余项，分别比较同组力，单位kJ/(mol·nm)。ΔF相对L2=sqrt(Σ||F_method−F_NC||²/Σ||F_NC||²)，各组使用自己的分母。技术重复先求同一致聚合再比较；原始力、能量和坐标约束校正量保留。

| 相对NoCutoff力差 | 1nm，5结构范围 | 2nm，5结构范围 |
|---|---:|---:|
| total | 0.1711–0.2171% | 0.01288–0.02128% |
| 普通非键合项 | 13.48–18.23% | 2.958–4.018% |
| GB项 | 23.60–30.03% | 4.895–7.010% |

总量和分项的分母、不同项的抵消/主导作用不同，不能用小总力比例认证非键近似。这里也没有研究者/领域专家确认的可接受力误差阈值。普通非键合项与GB项是数值分解，不是分别可观测的真实溶剂力。

随后三候选各100ps、同seed2026102601。平均温度分别300.557/298.515/299.323K；当前Cα相邻、肽键C–N、非局部重原子距离与侧链手性检查未发现明显严重异常。它们只是短时筛查，尚不能认证长时动力学或充分平衡。不同配置轨迹分叉不当失败处理。

NoCutoff该短段内部7.655s（初始化2.316s），依据事前优先级及保守1ns成本门槛进入GQ2。没有按哪条覆盖更多选择配置，也没有把更低的绝对势能作为选择标准。完整约束距离残差在新增服务器分析中复核；初次报告未测该项，不追认先前已检查。

## 最小化、局部松弛与续算

首次启动默认容差10kJ/(mol·nm)、最多1000次最小化迭代，再按seed生成300K速度。1ns总段前100ps作为局部松弛排除候选，另查排除0/200ps敏感性；这不是已证明的充分burn-in。原始全部帧保留，不能把删去初始大变化当平衡证据。

延长若获本轮条件准入，加载同System/软件/设备的完整OpenMM checkpoint，恢复时间、坐标、速度及内部状态，不再次最小化或生成速度。与原工作流坐标reseed（新建动力学初值）分别命名；续算前缀不成为新的独立重复。

## 当前判断边界

GQ1支持使用NoCutoff进行本轮有界探索，揭示只看总力的不足。不能据此宣称已得到正确折叠途径、平衡分布或正式合格力场。准备史、质子化、结构变化尺度、采样资格及独立评价器仍须结合本轮轨迹、领域意见和后续审查。

## 结束时证据补充

输入审核为504原子、253氢、28残基，模型净电荷约+4e；端基原子完整保留，不能从电荷倒推制备pH。首次固定坐标240个状态请求，reserve内另240个同范围复核；合计480个能量/力状态请求、0MD积分步。最终分项表来自physics-recheck-01，保存原始和投影后坐标，首次数据不覆盖。60组总量/分项和式核对最大能量残差1.5143×10⁻⁴kJ/mol、力绝对残差0.001344kJ/(mol·nm)、归一化力L2残差9.18×10⁻⁸；这是mixed精度/分组计算的数值核对，不能称严格逐位一致或溶剂精度认证。
