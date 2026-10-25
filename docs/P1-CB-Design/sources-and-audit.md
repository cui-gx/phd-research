# 来源、证据范围和设计自审

2026-10-25。本设计是作者侧审查，不代替尚未完成的Astra独立终审。没有本次新增实验结果。

## 1. 权威输入

本轮研究者完整指令《P1博士研究：科学反馈状态C主线与更新净收益B联合研究设计》；共享main `950c4a2315847bab07e502552a9aa97d59801008`。已读AGENTS、总档案、交接、P1-RelatedWork入口/矩阵/空白/形式化/审稿反驳及2026-10-25规划审查、S2补充报告/独立审查/批准规格。当前优先级更新覆盖旧文献审查中的“先B、若有增量再考虑状态”的研究方向建议，但不撤销科学资格与标签的执行依赖。

现有实测引用均来源于[S2](../P1-S2/qualification-report.md)、[补充报告](../P1-S2-supplement/supplement-report.md)及其证据目录，本次未复算轨迹或权重。补充代码版本`656df0cf2677affaf362ed631b662545321f80e3`，事前计划`0ae3d092659be6c32b176ab8fa17612a833f49f9`。48段/56ns/15.84小时等是设计算式，不是实测。

## 2. 研究先例

R编号沿用[13篇矩阵](../P1-RelatedWork/comparison-matrix.md)，完整书目和原文哈希在既有审查，不重复下载版权全文。

| 来源 | 原始链接与定位 | 支持的事实/本次用途 |
|---|---|---|
| R01 Bhowmik et al. 2018 | [BMC论文](https://doi.org/10.1186/s12859-018-2507-5)，Methods/BBA/Fig.7 | 同对象CVAE及外部长轨迹背景；不认证当前隐式短轨迹 |
| R02 Lindorff-Larsen et al. 2011 | [Science](https://doi.org/10.1126/science.1208351)，Fig.1–3 | 快折叠蛋白背景；既有审查未取得补充方法 |
| R03 DeepDriveMD 2022 | [固定v5](https://arxiv.org/abs/2104.04797v5)，§III–VI、Table II | 同对象反馈/采样，科学参数与执行资源差异必须承认 |
| R04 Colmena 2021 | [固定v1](https://arxiv.org/abs/2110.02827v1)，§IV-C2 | 已有共享资源下科学机会成本实例，不是本项目原创概念 |
| R05 Colmena 2025 | [正式论文](https://doi.org/10.1177/10943420241288242)，§5.2/Fig.6 | 旧模型与等待更新取舍；示意图不是隔离实测曲线 |
| R06 Ekya 2022 | [USENIX](https://www.usenix.org/conference/nsdi22/presentation/bhardwaj)，§3–6 | 成本/未来利用时间/强消融的先例 |
| R07 ORRIC 2024 | [作者稿](https://arxiv.org/abs/2405.16029v1)，§III–V | 有限时域学习权重，不直接适用MD集合效用 |
| R08 AL-Queue 2025 | [作者稿](https://arxiv.org/abs/2509.25538v1)，Algorithm 1、§VI | 选点与资源动作分开；cheap-learning区间 |
| R09 REAP 2018 | [原论文](https://doi.org/10.1021/acs.jpcb.8b06521)，算法/Results | 状态引导采样不是全新概念 |
| R10 Hay et al. 2012 | [PMLR](https://proceedings.mlr.press/r10/hay12a.html)，§2 | 计算价值一般框架；不包装本设计公式为新理论 |

既有原文阅读深度/局限详见[来源日志](../P1-RelatedWork/search-and-source-log.md)，本次复核现有证据与设计对应，不宣称重新逐页阅读全文。DynaGene只有元数据和规划侧二手摘要线索，仍UNVERIFIED；不能用缺文作为无重叠证明。

## 3. 本次新增一手方法来源

- **Grossfield et al.** “Best Practices for Quantification of Uncertainty and Sampling Quality in Molecular Simulations [Article v1.0]”，Living J. Comp. Mol. Sci. **2019, 1(1), 5067**。[出版者PDF](https://livecomsjournal.org/index.php/livecoms/article/download/v1i1e5067/913/2595)，DOI 10.33011/livecoms.1.1.5067。本次读取/定位§4、§5、§6、§7.3相关段（PDF pp.7–17范围），涉及独立重复、松弛、相关性与适用条件；未逐条验证全部参考文献。PMC入口返回浏览器验证，改用出版者原PDF成功，未绕过访问控制。该文不认证本项目具体阈值或力场。
- **Athey & Imbens (2016)** “Recursive partitioning for heterogeneous causal effects”，PNAS 113(27):7353–7360，DOI 10.1073/pnas.1510489113。[正式HTML](https://www.pnas.org/doi/10.1073/pnas.1510489113)，重点阅读Significance/Abstract、Honest Splitting/Estimation/Cross-Validation段。用于区分选择模型与独立效果评估的原则；未复查全部证明，不采用其因果树作为本项目已定方法。PMC入口验证阻断，正式HTML可读。
- **D. E. Shaw Research资源页**：[官方入口](https://www.deshawresearch.com/resources.html)，核对2011快折叠论文条目等。只是数据来源追查入口，本次没有取得/核准外部轨迹文件、下载许可或HP35具体变体，不列为已拥有数据。

## 4. 自审修正与仍然开放的问题

| 风险 | 本设计处理 | 尚待验证 |
|---|---|---|
| X预测普通MD产出不等于更新价值 | C标签使用同状态动作差，控制W/时间/成本 | 独立根数据尚不存在 |
| 条件化本次实际训练成本造成事后变量偏差 | 主条件为决策前估计成本，实际成本另报 | 成本估计误差需真机 |
| 历史净收益不可在线观测 | 最小特征不使用反事实历史收益 | 未来独立历史实验库需单独成本/许可 |
| 预算h相同却排空不同 | 评价窗口和资源硬上限分开，实际占槽必报 | 严格同占用时间需要另设计/批准 |
| 早晚状态与训练量混杂 | 固定里程碑、配方/容量、同h、跨根检查支持 | 可能仍缺共同支持，必须承认不可识别 |
| 4根不够C验证 | 明确只诊断，最终样本量待精度/支持规划 | 不预承诺统计功效 |
| D同时改变数据和时机 | 主D冻结训练快照，fresh另标复合；pool路径效应披露 | 不称纯延时干预 |
| 以新体系/更多epoch制造竞争 | 先科学资格、实测成本与负结果；替换另审 | FSD-EY是否存在非平凡区间尚未知 |
| 领域/指标风险未解决 | 独立资格优先，具体咨询问题和阻断卡 | 不把文档交付称科学PASS |

本次工程交付检查仅覆盖文件完整性、相对链接、哈希、状态标签、预算算术、Git变更范围；不是数值实验，也不是独立科学审查。实际提交SHA在远端核验后由执行端报告。
