# B/C共通データ契約（设计稿，未实现）

2026-10-25｜PROPOSED。字段表用于未来批准后的实现，不是可运行配置。本次没有新增科学数据。

## 1. 六张表

| 表与主键 | 必需字段 | 约束 |
|---|---|---|
| campaigns：root_id | preparation_id/sha、source_lineage、base_model_sha、protocol_sha、software_manifest_sha、approval_id、seed_root、split_id | 共享来源关系显式；prepared structure共同但随机独立须注明条件独立范围 |
| states：state_id | root_id、parent_task_ids、milestone、snapshot_sha、old/new_pool_sha、candidate_pool_sha、model/optimizer_sha、rng_sha、U_initial、X/Z/W及单位、feature_cost、availability时间 | 分支前不可变；缺项不能用后续结果补 |
| branches：branch_id | state_id、arm、seed_block、train_seed、MD_seed、h或q、recipe_sha、run_order、output_manifest_sha、status、failure_class | B1/B2必须显式分开；缺失臂保留 |
| events：(branch_id,event_seq) | monotonic_elapsed_s、UTC、kind、task_id、input/output_hash、resource_lease_id、result_qualified | 顺序严格单调非递减；MD采用已发布模型和ranking |
| labels：(state_id,comparison,seed_block,h/q) | evaluator_sha、initial_coverage、arm_outcomes、paired_difference、eligible_result_ids、late_result_ids、actual_costs、derivation_code_sha | 标签在分支后产生；只引用截止内合格输入；保留完整单位 |
| splits：source_group_id | ancestral_data_ids、model_training_ancestry、calibration/development/test role、freeze_commit、assigned_before_outcome | 祖先相连来源不能跨开发/测试；公共外部冻结模型例外需显式声明 |

主键以不可变逻辑ID表示，不含服务器账号/IP。浮点值保留完整精度和展示舍入规则；NA缺失附原因，不自动填0。训练sample manifest记录每batch帧ID和曝光数，预处理顺序、数据划分及RNG恢复可复现。

## 2. 派生规则

1. 状态特征表、拆分表先冻结并提交版本，之后才允许生成标签。若分析计划改变，另存版本及修改原因，不覆盖旧版。
2. B1配对必须相同state/q/selector/reseed，F1/F2相同初值、K、b、曝光。B2配对必须相同state/h/公共续行语义，实际MD量允许不同且需要记录。
3. 非物理/未资格帧保留原始证据，但依预声明资格函数不进入成果；排除数与原因单列。
4. 数据可用时间来自实际事件，不从MD内部物理时间换算。任务完成后才可用的整批数据共用批次边界。
5. B2差值标签只能由配对实际结果计算；缺臂返回MISSING_PAIR，不插补成零。B1标签不能直接作为B2净价值标签。
6. 相同输入、同seed复跑生成新branch_id和attempt_id，不能覆盖失败run；报告纳入/排除依据。

## 3. 必须能生成的审查表/图

- 根级配对差散点、不同状态/h的全部结果；不以帧数产生误差条。
- 实时成果阶梯图及共同截止线，另列H后排空区间。
- 完整成本分解、GPU占槽/CPU/有效ns账；嵌套计时不重复加。
- X对Z/W的共同支持图、数据祖先与split交叉审计。
- m₀/m₁留出预测误差及每根差值；开发和确认分开。
- 失败/无效结构/缺失标签表，阴性结果与事前偏差记录。

## 4. 可复现与验收

未来实现测试包括：未来checkpoint/未发布数据拒绝、SHA变更拒绝、同源跨split拒绝、截止后帧排除、F1/F2曝光匹配、配对缺失不产数值标签、同集合重复不增覆盖、B1/B2单位不可混用。这些属于批准后的测试清单，本次没有声称已实现或通过。

每张派生表都能追溯到源码commit、输入SHA与事件文件，报告中的数字从表生成而非手填。GitHub保留紧凑派生表与manifest，原始轨迹/权重另存且经哈希核验；路径存在不等于已备份。
