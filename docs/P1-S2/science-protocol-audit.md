# S2-A：FSD-EY / 1FME 科学协议审计

日期：2026-10-24。证据类型：`derived analysis`（源码/来源审查）与 `local CPU/GPU measurement`（实际系统实例检查）。本文件不宣布物理采样或生物学有效性通过。

## 已核实的输入

固定 DeepDriveMD 提交 `b18dacba46f079644e4ee66191675375581955c3`；输入URL和SHA-256见仓库 `inputs/p1-fsd-ey/manifest.json`。原始 folded PDB 包含34个NMR模型，当前参考为确定性提取的MODEL 1；不是取所有NMR模型作为训练数据。RCSB记录确认1FME是28残基FSD-EY的溶液NMR结构，不能把单个MODEL 1等同唯一真实构象。[RCSB记录](https://www.rcsb.org/structure/1FME)。

实际两个单模型输入均504原子、253个氢、28残基，残基序列一致：EQYTAKYKGRTFRNEKELRDFIEKFKGR。参考链A、unfolded链P；根据顺序/残基名匹配Cα。无HETATM水或离子。unfolded含46.599 Å立方CRYST1记录；提取的参考文件没有盒子。

`unfolded`是上游提交附带文件，不是本项目新生成；固定版本完整文件树中1fme目录仅folded PDB、system目录和unfolded PDB。该目录及已查README没有提供unfolded生成脚本、升温/展开过程、初始速度或平衡日志。**生成方法UNVERIFIED**，不能写成“已按某温度充分展开并平衡”。上游可复现文件身份与其物理制备历史是不同问题。

## 实际数值与物理设置

来源：固定 `deepdrivemd/apps/openmm_simulation/app.py::_configure_amber_implicit`，本项目 `p1/server/science.py::_simulation`，安装的OpenMM 8.5.2 XML及系统序列化。系统审计在CPU上仅建模、不积分；运行平台另测CUDA。

| 项目 | 当前实际值 / 语义 |
|---|---|
| 拓扑 | PDB解析；无prmtop；504粒子，253个约束；createSystem成功匹配模板，不自动补氢或修复缺失原子 |
| 力场 | `amber14-all.xml` + `implicit/gbn2.xml`；实际安装XML哈希另存审计JSON，不将Amber14标签当完整版本证据 |
| 溶剂 | GBn2隐式溶剂，ACE非极性项；solute dielectric=1、solvent=78.5、kappa=0默认；无显式盐离子，净电荷约+4e |
| 非键相互作用 | CutoffNonPeriodic，1.0 nm；GB力同为非周期1.0 nm；无PME；系统periodic=false |
| 约束 | HBonds；约束容差1e-5；系统另有CMMotionRemover（默认频率，XML为准） |
| 积分/温控 | LangevinIntegrator，2 fs；目标300 K、摩擦1 ps⁻¹；无barostat |
| 初始处理 | 设置随机种子后重建Context，再设置PDB坐标；每段均minimizeEnergy（OpenMM默认10 kJ mol⁻¹ nm⁻¹、maxIterations=0），再按300K和任务seed重新生成速度 |
| 平衡 | 无独立升温/平衡段、无预先定义的burn-in剔除；所有reporter帧进入当前工程分析 |
| 保存 | 每0.5 ps保存坐标DCD及step/time/potential/total energy/temperature；首帧为0.5ps，无t=0帧；S2仅改变片段长度 |
| CVAE输入 | 原上游Cα接触图8Å，包含对角及对称条目；CVAE结构/损失/优化器未改变；1epoch/batch4为PILOT |
| restart | 从选中DCD帧写PDB（坐标舍入），再次最小化、重新生成速度；不是保存速度/积分器/随机状态的checkpoint continuation |

## 风险及处理边界

1. **高：分析的周期语义可能不一致。** 非周期OpenMM系统仍携带PDB盒子；上游分析在参考对齐后将`atoms.dimensions`传给contact_matrix，可能人为采用最小镜像。S2诊断将比较保存接触图与无盒/有盒计算，不悄悄改变训练输入。正式探索前需要确认采用非周期接触图；这是待批准的科学数据处理修正。
2. **高：参考结构参与实际选择。** 现有链为CVAE embedding→LOF最异常N=100→reference RMSD升序。若候选数≤100，LOF完全不淘汰候选；最终top1可能完全由参考RMSD决定。S2记录LOF-only与实际排序两层，LOF-only仅诊断，不切换运行规则。
3. **高：物理预备历史与平衡未验证。** unfolded文件身份可追溯，但生成/质子化过程、热力学平衡、采样收敛无法据此认证。成功匹配力场模板不等于pH/质子化科学适宜。
4. **中：隐式溶剂1nm截断。** OpenMM官方建议隐式溶剂截断通常应比显式更大，2nm常为可用选择；当前1nm是上游复现值，不能以复现成功宣称截断误差可忽略。改为2nm/NoCutoff仅为PROPOSED，需审批。[OpenMM说明](https://docs.openmm.org/latest/userguide/application/02_running_sims.html#implicit-solvent)。
5. **中：最小化和重采样。** 帧继承可证明科学反馈被调用，但每次reseeding改变速度且重新最小化；不能将各段拼成一条连续动力学轨迹、时间相关性或动力学速率证据。
6. **中：短轨迹相关性。** 多帧不等于独立重复；当前成本配对种子和两个重复仅用于描述性PILOT，不支持探索显著性结论。

## 开始有界成本测量的门槛

静态审计已完成、系统可实例化，以上假设已显式记录；允许在已批准S2范围内对**原协议**做资格/成本PILOT。先20ps，再200ps与1ns，每长度2个配对seed；逐任务检查退出状态、帧数、所有坐标和日志数值有限。总计最多12任务、GPU计算段墙钟上限900s、单任务180s、进程树采样RSS4GB、输出1GB、单GPU/最多3逻辑CPU。异常立即停止，不扩大到正式性能实验。动态稳定性和周期接触图诊断待实测后追加。

## 动态实测补充（MEASURED）

6段MD均成功，累计2.44ns、4880帧；所有坐标与记录的能量/温度有限，无崩溃或约束求解异常。两段1ns的平均温度分别300.9906K与300.4046K；观测范围219.7856–346.9572K及207.5552–340.2134K。初期温度偏低和瞬时波动如实保留，不凭平均接近300K认定充分平衡；Langevin恒温体系也不应以总能量严格守恒作验收要求。

**周期接触图风险在这批数据中未出现实际差异**：4880/4880帧保存接触图同时等于有盒与无盒计算（全部28×28条目比较）。盒子确实传入上游分析，潜在语义问题仍存在，但不能将其写成本批数据已被污染。不同构象/盒子下是否产生差异仍UNVERIFIED；正式协议建议明确非周期特征处理，待审批。

本阶段没有重跑完整restart闭环；S1已验收的选中DCD帧→后续initial.pdb对应关系误差≤0.001Å继续作为输入继承证据。源码审计确认随后再次最小化、按任务seed生成新速度。因此只认证坐标来源与reseeding语义，不认证动力学状态连续或无偏平衡采样。

机器软件版本、实际XML哈希、每段温度/势能范围、CPU/GPU条件和失败见 `docs/执行证据/2026-10-24-s2/`。初次审计记录脚本有单位转换错误，第二次修正后成功；未因此修改物理设置。
