# GQ第一轮复现与证据边界

2026-10-26。此文是本轮已批准实施的复现说明，不能自动授予新的60分钟或重置账本。重新运行需要研究者授权和实验室资源协调。

## 1. 执行源码与计划

计划：7185e98edfd13214e7c1789968e16c558df5a14f，首次科学计算前已推送并由GitHub connector回读。GPU worker/controller：18e3fe934389d9edc78521cede07cafbc500436f。CPU分析后续修订见amendments与最终执行源码哈希，不把分析修订当改变MD配置。

复用固定DeepDriveMD b18dacba、mdlearn938cb80及既有p1/server科学组件。新文件gq_control是本轮资格测试的预算监督，不代替已有Parsl工作流。gq_science构造相同力场候选及完整checkpoint续算；gq_analysis只在服务器计算物理诊断，不调用CVAE进行科学成果评分。

## 2. 环境与输入

保存实际服务器Python、OpenMM distribution/build、CUDA driver/runtime、Torch、MDAnalysis、NumPy、mdlearn等版本和pip lock。旧S2环境已清理，按旧安装记录恢复本人项目内隔离环境；pip bootstrap wheel SHA核验，不改全局软件。新增绘图matplotlib3.10.1和预算监控psutil7.0.0只装隔离环境。

科学输入与来源见analysis-plan及原inputs/p1-fsd-ey/manifest.json。原始S1/S2先生成before哈希表，结束后逐项复核；任何旧文件改变都会阻断交付，不修写旧记录。

## 3. 运行顺序

1. GitHub同步，读最新批准范围；确认实验室预约与实际资源，每次会话/启动复查。
2. 在本人项目恢复隔离依赖并保存lock；只传审阅白名单源码，逐文件SHA核对。
3. 服务器运行`python -B -m unittest discover -s tests/p1 -p test_gq.py -v`，核查失败也扣预算、pending阻断、阶段不能借额度等4项测试。
4. 用私有lease记录本轮已确认资源；该文件不提交GitHub。固定唯一round根，持久budget-ledger不能随目录/进程重启重置。
5. 每项执行使用`python -B -m p1.server.gq_control --root <唯一round目录> --name <唯一task> --stage <gq1/gq2/gq3/reserve> --request <冻结JSON> --lease <私有许可> --timeout <本次上限>`。worker请求与执行记录为精确参数来源，禁止复制命令后擅自增加任务。
6. GQ1固定坐标→3×100ps→服务器分析并写准入依据；GQ2按seed顺序4×1ns→分析；只有预定条件满足才进行GQ3续算。
7. 服务器CPU分析：`python -B -m p1.server.gq_analysis --root <round> --output <新的不可覆盖分析目录>`，固定最多3逻辑CPU、2数值线程；该进程不持有GPU上下文。保留每次新分析及旧失败。
8. 必要AI成本测试使用原有science.run_request接口，对固定已有S2池匹配输入与初始checkpoint；结果仅资格/耗时，不从选中构象启动MD。
9. 结束检查预算、缺失、SHA和原始证据，输出JSON/CSV及图，远端保留大文件并做授权本地备份，双端SHA核验。

## 4. 文件类型

GPU原始：request、stdout/stderr、process、execution、GPU遥测、occupancy、DCD/PDB/checkpoint、system XML和科学result；物理固定坐标力数组另存npz。CPU派生：逐轨迹特征、二面角、quality、grid-sensitivity、shape-alias、固定库映射、invariance、物理分项比较及图。

GitHub仅放报告、代码、紧凑派生表和脱敏manifest，不上传DCD、大权重、lease、用户进程详情、SSH信息。报告里的路径使用逻辑artifact ID；具体私有存储映射由执行证据维护。GitHub有manifest不等于原始数据在GitHub。

## 5. 计算与统计解释

全部力/结构数值和图在服务器计算，Mac只进行文件/JSON组织、传输、SHA和文档完整性检查。frame非独立重复、续算非新根。四个速度/噪声流共用同一准备结构，只条件于该结构；校准/留出不代表外部科学验证。所有阈值是本次探索候选，正式协议尚未合格。
