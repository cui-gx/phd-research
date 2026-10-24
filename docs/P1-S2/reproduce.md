# S2 复现范围与运行入口

在研究者批准、设备已分配且共享占用检查通过的个人Linux项目副本执行。不要将示例替换成共享系统安装或未经授权的GPU；正式实验尚未启用。

1. 获取本次Git提交的源代码、固定输入及vendor目录。无需新建研究项目或原生Colmena重写。
2. 记录本人目录、资源许可和当前CPU/内存/GPU进程/使用记录；使用 `p1.server.bootstrap --directory .runtime/<唯一S2目录>` 创建一次性Python3.12环境。实际命令、软件锁和安装日志保存在对应运行证据；不改变驱动/CUDA系统安装。
3. `taskset -c <2个允许CPU> <venv>/bin/python -B -m p1.server.qualification audit --output <新的审计目录>`，检查audit.json与system.xml，先读科学风险报告。audit不运行积分。
4. 小规模测试：设置`P1_TEST_TMPDIR`为本次runtime/tmp，再运行`python -B -m unittest discover -s tests/p1 -v`。准备微型PyTorch CUDA计算，确认OpenMM CUDA平台；不能用仅导入成功代替真实计算验证。
5. 使用 `configs/p1-server-lease.template.json`记录**已经获得的**许可、GPU UUID、3个逻辑CPU编号、覆盖900s的截止窗口；该文件不能授予许可，真实记录不提交GitHub。每次安装/启动/重试都重新检查占用。
6. `taskset -c <3个允许CPU> <venv>/bin/python -B -m p1.server.qualification run --output <全新run目录> --lease <私有许可记录> --manifest configs/p1-server-s2-pilot.json`。
7. 运行器沿用Parsl单worker及原execute_task，六段MD依次从20ps到200ps到1ns；CPU模型控制进程与科学子进程分开绑定；无任务重叠。每任务前保存占用检查。出现他人进程/不明显存占用即停止；对于已退出己方任务的尾随利用率，最多3秒复查，必须读到空闲才继续。
8. 所有任务完成后，`<venv>/bin/python -B -m p1.server.qualification_analysis --run <run目录> --output <新分析目录>`。此步只做CPU分析；先核查共享CPU/内存。校验全部原始哈希后生成costs.csv/json、stability.json、model-comparison.json、coverage-computability.json、validation.json。不要修改原始checklist来掩盖错误。
9. 归档输入清单、源代码指纹、环境锁、原始run、失败和GPU遥测；取回后核查SHA-256。仅清理本次登记runtime/cache/tmp/己方进程，保留源代码和证据。推送精简报告/证据，不上传大型轨迹、权重、真实许可、主机地址或凭据。

MD试测根种子配对为2026102401/2026102402，各长度相同种子不等于独立campaign。模型种子2026102403、推理种子2026102404。PILOT参数定义见manifest。模型对照使用两段200ps的共同800帧池：旧模型先训练第一段400帧1epoch，冻结其checkpoint；更新模型恢复同一权重与优化器，用800帧继续1epoch；两个模型各推理两次检查同seed重现性。保持LOF k=20、shortlist100与参考RMSD排序。更新对照混合了额外训练和新数据，不分离“仅新数据”的因果贡献；不宣称科学收益。

计时口径：worker内部各组件为不重叠wall-clock分区，checkpoint写出嵌在fit中不能重复加；CUDA在训练/嵌入边界同步。派发到返回另测；其与worker时间的差包括启动/导入/序列化/轮询/回收/Parsl，不能称纯调度成本。DCD/log I/O包含于MD积分reporter；本阶段没有完全隔离纯I/O、结果序列化或纯切换耗时。每次任务是新进程，但没有清空OS/驱动缓存，不能称严格冷缓存实验。
