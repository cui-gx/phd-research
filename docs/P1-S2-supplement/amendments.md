# S2-SUPPLEMENT 技术修订与偏差登记

## 2026-10-25 JST，结果分析前：隔离环境位置与安装上限

**状态：技术修订；科学分析尚未开始。** 事前计划仍是 Git commit `0ae3d092659be6c32b176ab8fa17612a833f49f9`、SHA-256 `dbdd38d7153570dc81318351639877a4a17254fe479c3faa249f668d5f5fff42`，不改写原文件。修订前尚未读取任何新的 A/B/C 结果；只有既有 S2 元信息、实现与工程测试。

2026-10-24 第一次在外置盘 `.runtime/P1-S2-SUPPLEMENT-20261024/venv` 安装依赖时主动中止。日志保留于该登记目录 `install.log`。当时外置盘按文件系统分配块统计约 5.51 GB，超过预定 5 GB 安装空间；同一文件集逻辑大小约 0.534 GB。外置盘对约 40,614 个小文件的块分配造成明显膨胀。安装在 `Installing collected packages` 阶段中止，未通过 `pip check`、未作正式环境版本确认；不能描述为依赖安装成功。本次安装与空间超限作为失败保留。

**本次可逆实现调整**：把已停止的隔离环境迁移到登记的本机临时目录 `/private/tmp/doctoral-hpc-P1-S2-SUPPLEMENT-20261025`；保留原 `.runtime/P1-S2-SUPPLEMENT-20261024` 入口为指向该环境的符号链接，以维持虚拟环境脚本绝对路径。迁移前后核对文件内容与环境导入，再只补齐确实缺失的固定版本依赖，不重装已可用软件。新的环境准备恢复窗口最多 30 分钟，迁移过程瞬时占用上限 8 GB 十进制；完成后实际运行环境目标不超过 5 GB 十进制。若边界再失败，保留错误并停止，不无限重试。详细峰值、命令、包版本、失败和剩余空间将写入资源收据。

**科学协议不变**：FSD-EY/1FME、原始 4,880 帧和 800 候选池、所有 A/B/C 数学定义/参数/种子/拆分/失败门槛、A 600s、B 900s、C 300s、科学计算累计 1,800s、2 CPU 线程/4 GB RSS/1 GB 派生输出均不变。没有 GPU/MPS、没有 MD 积分、没有 S3 授权。首次依赖失败不计为科学计算时间，因为未计算科学结果；任何后续 A/B/C 失败与合法重试必须累计记账。

**恢复收据（分析前）**：停止安装的文件集以 `rsync -a` 迁移，`rsync -a -c -n` 核验内容相同（只剩根目录修改时间差异）；迁移峰值约为外盘原分配 5.51 GB 加本机目标不足 0.5 GB，低于 8 GB。原路径改为符号链接；只清除目标环境内 21,065 个 `._*` 文件系统侧车，原科学输入未改。补齐 MDAnalysis、scikit-learn、h5py、pydantic、psutil 后发现第一次中止留下的 torch 包缺 `libtorch_global_deps.dylib` 且无安装元数据，随后仅重新安装固定 `torch==2.7.1`。隔离环境现 `pip check` 为 `No broken requirements found`，上述包均可导入；`torch.backends.mps.is_available()` 为 False，后续所有训练仍显式设置 CPU。恢复日志 SHA-256 分别为 `install-recovery.log:70ad949b86572fb4cb7c9d040ad6c4243be6313d6959ed95390789b872e64611`、`install-torch-recovery.log:7b4e93a785305c30420ce2ebe6008f4cfc4c7970a0f845455e3ddcbb1a98a8b7`，原失败日志 `install.log:0c89d7139bc8994b865db60240ce458dd8697c91ad86844e5b3cc9e0b4ef2fab`。恢复后目标目录文件逻辑大小 875,882,355 bytes、实际分配约 947,892,224 bytes，均低于 5 GB。日志和环境暂留登记的本机临时目录供独立审查。
