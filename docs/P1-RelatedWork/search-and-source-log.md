# 检索、版本与证据可追溯记录

## 范围与方法

检索/核查日期：2026-10-25（JST）。当前档案起点：main `1dc4f85d6fae311b6ac8d56c3533c2ec981272c3`。目标是检验P1的机会成本、有限时域和反馈状态主张是否被已有研究覆盖，不是寻找可支持既定故事的论文集合。

采用用户指定5篇为种子，结合公开网络检索、出版者/会议/作者原文、前后引用线索和已有本地文献库。检索优先近5年，补入科学基础与元决策经典。没有使用私有订阅数据库的全面导出，没有预注册穷尽检索方案，没有PRISMA筛选流量统计，不能称“覆盖所有相关研究”。

纳入：原始科学反馈系统、同资源模型重训决策、有限预算学习和计算价值理论，且能帮助判断至少一个明确的P1主张。排除主要证据用途：单纯云租赁费用/DAG makespan、无学习反馈的通用排队、与本任务无关的LLM token路由、营销/博客/专利摘要。综述可作索引，不替代原文实验。缺文不被排除成“无关”，而单列风险。

## 实际使用的查询族与追踪

下表保留实际用过的查询关键词/组合，合并重复查询；不是逐次搜索引擎排名日志。没有保存搜索结果总命中数，不能据此量化召回率。

| 查询族 | 使用过的文本/组合 | 结果处理 |
|---|---|---|
| 用户种子 | 五篇完整题名；DOI；1FME / DeepDriveMD / Colmena | R01–R05；出版年份/版本核查 |
| 固定预算与科学工作流 | `"budget" "retraining" "scientific workflows"`；`"budget-aware" "scientific" "learning" workflow scheduling`；`"scientific utility" scheduling learning workflow` | 未以无搜索结果推断无先例；追踪Colmena原应用 |
| 剩余时域 | `"deadline" "retraining" "Ekya" OR "ORRIC"`；`"model retraining" "remaining budget" scientific workflow` | R06/R07；跨领域功能等价比较 |
| 自适应模拟 | `"adaptive sampling" "molecular dynamics" "learning" "computational cost" 2025 2026`；`"Budget" "adaptive sampling" "molecular dynamics"`；`"adaptive simulation" "training cost" scheduling` | R08/R09；区分采样动作和更新资源动作 |
| 更新理论 | `"Online Resource Allocation" "Retraining" ORRIC`；`"How to Retrain Online Models Optimally with Few Updates"`及OpenReview限定查询 | R07/R12；不把二手录用标签当正式证据 |
| 计算价值 | `"value of computation" rational metareasoning Hay Russell 2012`；`"Selecting Computations: Theory and Applications" paper` | R10；确认2012原文/2026再发布 |
| 异步组织 | `"Asynchronous" "DeepDriveMD" Pascuzzi 2023` | R11；识别stress代理与真实科学实验差异 |
| 采样基线 | `"REAP" "reinforcement learning" "adaptive sampling" 2018` | R09原作者稿及正式DOI |
| 高风险缺文 | `"DynaGene" "Adaptive" scheduling`、`"DynaGene" "IPDPS"`、`"DynaGene" "Xuxuan"`、`"DynaGene" "Zhuozhao"` | R13仅元数据；保留全文风险 |

引用追踪：R03→R01/R02，R05→R03及科学采样文献；Ekya/ORRIC→受限资源重训；REAP与计算价值理论提供不同邻近层。搜索中的数据库主动学习（如SIGMOD 2020 *Active Learning for ML Enhanced Database Systems*）属于尚未深读的外围线索，未计入12篇原文审查、未用于证明没有等价目标。并未穷尽全部Bayesian experimental design、anytime算法、adaptive sampling和在线学习文献。

## 所读版本、具体深度与原始入口

“有原文”表示取得全文并核查相关核心部分，不表示所有附录、证明、源码、数据均逐行审查。详细节/图/式见矩阵。表内文件相对工作区根目录，**仅存本地**；GitHub提供本报告、来源URL与SHA-256，不包含这些原论文副本。

| ID | 实际版本 / 阅读边界 | 本地文件 | 原始入口 |
|---|---|---|---|
| R01 | Publisher PDF; Methods, BBA analysis, Fig.7, Discussion; full main text accessible; no raw trajectory replication | `literature/p1-novelty-2026-10-25/bhowmik2018.pdf` | [source](https://link.springer.com/content/pdf/10.1186/s12859-018-2507-5.pdf) |
| R02 | Academic lab-hosted original article; main text and Fig.1 image checked; full supplement not obtained | `literature/p1-novelty-2026-10-25/lindorff2011.pdf` | [source](https://www.schroderlab.org/material/517.full.pdf) |
| R03 | Existing local arXiv v5; methods/scientific and system evaluation/limitations checked; no artifact run | `literature/first-part/papers/P03-DeepDriveMD.pdf` | [source](https://arxiv.org/pdf/2104.04797v5) |
| R04 | arXiv v1; architecture, application, evaluation and future-work checked | `literature/p1-novelty-2026-10-25/colmena2021.pdf` | [source](https://arxiv.org/pdf/2110.02827v1) |
| R05 | Existing author PDF; formal publisher HTML sections 4-7 additionally checked; final PDF blocked | `literature/first-part/papers/P02-Colmena.pdf` | [source](https://arxiv.org/pdf/2408.14434v1) |
| R06 | Official proceedings; objectives/methods/physical versus simulation evidence/ablations checked | `literature/first-part/papers/P06-Ekya.pdf` | [source](https://www.usenix.org/system/files/nsdi22-paper-bhardwaj.pdf) |
| R07 | Existing author v1; model, algorithm and experiments checked; no complete proof re-derivation | `literature/strategy-portfolio-2026-10-09/papers/FB04-ORRIC-2024.pdf` | [source](https://arxiv.org/pdf/2405.16029v1) |
| R08 | Existing v1; Algorithm 1 and scientific/CPU resource evaluation checked; publication status unverified | `literature/strategy-portfolio-2026-10-09/papers/FB03-AL-Queue-2025.pdf` | [source](https://arxiv.org/pdf/2509.25538v1) |
| R09 | Author v2; method and evaluation boundary checked; all supplements not reviewed | `literature/p1-novelty-2026-10-25/reap2018.pdf` | [source](https://arxiv.org/pdf/1710.00495v2) |
| R10 | PMLR reissue of UAI 2012; metalevel definitions/deadline extension and claims checked; no full proof audit | `literature/p1-novelty-2026-10-25/hay2012.pdf` | [source](https://raw.githubusercontent.com/mlresearch/r10/main/assets/hay12a/hay12a.pdf) |
| R11 | Existing conference author manuscript; sections 4-6, surrogate workload/platform and tables checked | `literature/p1-paper-viability-2026-10-19/Pascuzzi-JSSPP2023.pdf` | [source](https://jsspp.org/papers23/Pascuzzi.pdf) |
| R12 | Existing author preprint dated 2026-01-29; framework/assumptions/main claims checked; full proofs and acceptance not verified | `literature/strategy-portfolio-2026-10-09/papers/FB05-Retrain-few-updates-2026.pdf` | [source](https://www.cs.purdue.edu/homes/spa/papers/retrain2026.pdf) |
| R13 | Metadata ONLY. No original abstract, methods, figures, conclusion or full text obtained | `literature/p1-novelty-2026-10-25/dynagene-metadata.json` | [source](https://api.crossref.org/works/10.1109%2FIPDPS65963.2026.00103) |

补充：R05还核对了[出版者正式HTML](https://journals.sagepub.com/doi/10.1177/10943420241288242) §4–7，最终卷年2025，online为2024。旧本地文件名P02-Colmena不是2021论文；与FB01的重复PDF哈希相同，计一项。R03作者稿v5为2022，不以arXiv最早2021年混淆会议年份。R10是2012论文在PMLR 2026重新发布，非2026新成果。R12作者稿虽有后续索引线索，但正式录用状态未确认，不写ICLR已发表。

## 获取失败与解释限制

| 来源 | 实际结果 | 替代 / 结论限制 |
|---|---|---|
| SAGE R05正式PDF | HTTP403 | 正式HTML可读；作者稿PDF保留，不能声称下载正式PDF |
| Science R02出版者 | HTTP403 | 学术实验室公开原文副本可读；Fig.1图像确认µs单位，完整补充材料未取得 |
| R02另一个KIAS镜像 | TLS证书问题/网页502 | 未关闭证书校验；采用另一个可读学术镜像 |
| REAP NSF副本 | 下载超时 | 作者arXiv v2可读；未将失败当正文缺失 |
| DynaGene IEEE入口 | JavaScript/访问校验，未取得正文 | Crossref确认题名、作者、IPDPS2026、页码、DOI；其记录没有摘要。不能按题名推测策略/指标/结果 |
| Few Updates OpenReview | 页面访问校验 | 作者Purdue PDF可读；不根据二手检索结果认证录用 |
| 原始轨迹、学习权重与artifact | 本次未获取/未运行 | 文献数值是作者报告；未独立重复科学结果 |

DynaGene当前连原摘要、结论和图也未取得，故无法按“先摘要结论图”降级核查。完成本次有界报告不意味着该缺口已关闭。正式首创/方法差异主张前，应取得可合法访问的原文或作者稿并重新审查；本次不联系作者或教授。

## 原文算术和引用的谨慎处理

Colmena 2021原文同时出现“平均63个在等待期间提交”“总537个”及“15%”的说法；简单63/537约11.7%，统计聚合口径未足够解释。这份报告不重复15%作为自行核验的比例，只使用57min延迟及原文明确的5%/10%相对结果。R05部分结果引用R03/R04，不计独立复现实验。图示、合成测试、离线标签回放和真机科学运行在矩阵分别说明。

## 可复核方式

1. 从[书目](references.bib)或上表取得相同版本；遇出版者重打包需记录新哈希而非声称字节相同。
2. 以[source-manifest.json](source-manifest.json)验证本地PDF的SHA-256和字节数。哈希是版本一致性证据，不是科学正确性证据。
3. 按[矩阵](comparison-matrix.md)指定的节/图/式核查主张；先查R03、R04、R05，再查R06/R07/R10。
4. 检查[当前证据边界](literature-review.md)和[反驳条件](reviewer-critique.md)，不可将PROPOSED实验解释为MEASURED结果。

检索日志是本次有限范围的可追溯记录，仍可能遗漏非英文来源、未索引新稿和其他领域的等价方法；正式投稿前需更新。
