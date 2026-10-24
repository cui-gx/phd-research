# 科学任务适配器：来源、接口与验证边界

2026-10-22；代码准备属于 `derived analysis`。本页本身不声称 CUDA、MD 或 CVAE 已运行成功；实际执行以每次任务 `result.json` 和根阶段报告为准。

## 复用的实现

1. [DeepDriveMD Colmena implementation](https://github.com/ramanathanlab/deepdrivemd/tree/b18dacba46f079644e4ee66191675375581955c3)，固定 commit `b18dacba46f079644e4ee66191675375581955c3`。本工作区已有原始源码和 MIT LICENSE：`literature/p1-concrete-2026-10-19/source-snapshots/`。
2. MD 力场构造逐字复用该版本 `deepdrivemd/apps/openmm_simulation/app.py::_configure_amber_implicit`。轨迹的 Cα 接触图和参考 RMSD 逐字复用 `MDSimulationApplication.analyze_simulation`。适配器先核对文件 SHA-256，再用 Python AST 只提取这两个已审查函数，注入原来的 OpenMM、MDAnalysis、NumPy 依赖；不导入上游旧版 Colmena/Pydantic 编排层，不从网络执行源码。对应源码 SHA-256 为 `9e744c4a4628a7833c57666d43ccca14b58e1842e796846c5761b566b17a15ba`。
3. [mdlearn SymmetricConv2dVAETrainer](https://github.com/ramanathanlab/mdlearn/blob/938cb80ac3ebe33498dbcb2780f97f81ec80e0f8/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)，固定 commit `938cb80ac3ebe33498dbcb2780f97f81ec80e0f8`。每次执行检查所装 trainer 源文件 SHA-256 `df099022af7e38162371eff5abd607ccc31bba22b5f714838b6ea96d0ac4297a`，调用 `fit(X, scalars, output_path)` 和 `predict(X, inference_batch_size)`。RMSD 是绘图/记录标量，不是训练监督标签。
4. 推理与选点按上游 `apps/cvae_inference/app.py`：CVAE 潜在表示 → scikit-learn `LocalOutlierFactor` → LOF 最小的前 N 个 → 参考 RMSD 升序。复用科学方法，不声称此适配器发明模型或选点算法。

这是对已核对源码的工程复用，不能替代科学领域专家对分子对象、轨迹长度或评价指标的确认。与 IPDPS 2022 论文的 TensorFlow/Keras 实验、硬件和规模也不等同。

## 明确的工程改动

- CUDA 请求必须只看见一张明确分配的 GPU；OpenMM 强制 CUDA，PyTorch 验证恰好一个可用设备，不接受 CPU/OpenCL 静默回退。CPU 仅在 `purpose=cpu_functional` 时允许。
- MD 固定 PDB-only AMBER14/GBn2 路径、不传 Amber topology。接触图 8 Å 截断与力场 1 nm 非键截断是不同参数。
- 官方folded PDB含34个MODEL；本包明确使用MODEL 1作为参考，原始ensemble保留。展开结构链标记P、参考链标记A，按唯一链内28个残基的有序残基名/编号对应，不要求任意链字母相等。
- 原上游 `configure_simulation` 没有完整冻结种子，且允许自动换平台。本适配器设定积分器种子后重建 Context，并明确初始化温度速度。所有策略使用一致处理；不保证跨 GPU/版本位级可复现。
- 轨迹步数/报告间隔使用十进制整数关系校验，禁止截断；检查完整帧数、所有坐标有限、最终能量有限、Cα 原子映射一致。
- 接触图按上游稀疏 COO 形式保存，但规范外层为一维 object array，避免恰好等长接触图被 NumPy 自动变成二维。对象 `.npy` 只从本项目已经验证 SHA-256 的本地产物加载，不能装入未知来源的 pickle 文件。
- 每次训练从头开始；完整深拷贝数据清单，保留 snapshot/model/ranking ID、文件哈希和训练数据版本。推理数据清单与模型训练清单分别记录。
- 非有限 embeddings 直接失败；没有沿用上游 `nan_to_num` 把 NaN 修为零的行为。LOF 不够 21 个样本时失败，不静默缩小 `n_neighbors=20`。
- LOF/RMSD 相同分数用 result ID/frame 显式稳定排序，防止未定义的并列顺序。改变并列规则是公开工程差异。
- 无 DataLoader 子进程时 `prefetch_factor=None`，兼容现代 PyTorch；约束 mdlearn `_set_num_threads` 遵守 runner 分配的固定 CPU 线程数，关闭外部日志和训练绘图。模型结构和损失不改。
- 当前 `configs/p1_server_science.json` 是 **20 ps / 0.5 ps 报告间隔 / 40 帧 / 1 epoch / batch 4 的工程功能配置**。它不能产生论文正式比较结论。历史提案 10 ns / 10 ps / 20 epochs / batch 64 需在领域和机器资格检查后另行冻结。
- `run_request` 不启用 `purpose=formal`。正式门槛、科学评价、样本量和资源额度尚未确认。

## 请求接口

```text
python -m p1.server.science REQUEST.json RESULT.json
```

所有任务公共 JSON 字段：

```json
{
  "task_type": "simulation",
  "task_id": "md-0001",
  "seed": 1234,
  "device": "cuda",
  "purpose": "qualification",
  "cpu_threads": 4,
  "output_dir": "/approved/run/tasks/md-0001",
  "science_config": "configs/p1_server_science.json",
  "inputs": {
    "initial_pdb": "/approved/input/1FME-unfolded.pdb",
    "reference_pdb": "/approved/input/1FME-folded-model1.pdb"
  }
}
```

`science_config` 也可直接传完整 dict；不得只传部分字段。runner 负责独立子进程的 `CUDA_VISIBLE_DEVICES`、CPU affinity（若实验室允许）、总时间/磁盘限额，以及任务退出后的资源释放。适配器不联系服务器、不改变 GPU 模式、不申请远程资源。

- `simulation`：初次输入如上；反馈重启将 `inputs.restart` 设为之前推理的 `selections[i]`，保留 `reference_pdb`。restart 至少带 `pdb_path,dcd_path,frame,ranking_id,model_id,training_snapshot_id`。返回 `result_id,contact_map_path,rmsd_path,pdb_path,dcd_path,artifact_sha256,frames` 和参考哈希、帧时间、RMSD 单位、实际平台。
- `train`：`inputs={"results":[所有本次训练采用的成功 simulation 完整结果]}`。返回 `model_id,model_weight_path,model_weight_sha256,training_snapshot_id,training_result_ids,loss_curve`。
- `inference`：`inputs={"results":[本次推理数据],"model":成功 train 完整结果}`。返回 `ranking_id,training_snapshot_id,training_result_ids,inference_snapshot_id,inference_result_ids,selections`。每个 selection 记录结果 ID/帧、模型和排名版本，能作为下一 MD 的 restart。

成功 `status=success,valid=true`；失败 `status=failure,valid=false` 并保存 `failure.txt`。`output_dir` 必须不存在，任何现存目录都会拒绝覆盖。每次任务保留请求、结果、版本和耗时；训练保留快照与 loss，推理保留 embeddings/选点。CPU 功能结果显式 `engineering_only=true`；所有结果 `evaluation_ready=false`。

## 验证范围

不依赖科学库的 unittest 覆盖：MD 单位、整数步数、禁止正式运行/CPU 伪装 CUDA、快照深拷贝和文件篡改拒绝、固定源哈希、有效输入门槛、GPU 单卡绑定、LOF→RMSD 两阶段顺序和 NaN 拒绝。

另需真实软件环境检查完整链：一个小 MD → 训练/保存 → 加载/推理 → 选点 → 一个重启 MD。CPU 小测试只证明适配接口能连起来；明天仍必须在获准的实际 RTX PRO 6000 上分别验证 OpenMM CUDA 和 PyTorch CUDA。依赖版本由根 run pack 的安装配置和执行后环境锁记录；GPU 架构支持不能从测试通过或依赖文件存在推断。


科学开发前还需检查上游接触图分析使用的box/dimensions与隐式溶剂非周期模型的一致性；功能检查通过不替代这项科学设定审查。若须改为非周期距离，必须公开修改、升版并跨策略一致，不能混用已产出的快照。
