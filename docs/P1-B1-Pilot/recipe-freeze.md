# 下流開始前の配方凍結

2026-10-26。旧2 ns→M0→新2 ns（完全checkpoint継続）の順で実行を確認した。M0は新データの生成前に完了。旧800独特ID、新400独特ID、検証200、共通候補7800。M0実測200 optimizer steps/800曝光、loss有限、最終weight/optimizer/RNGを保存。配方不足による変更なし。

M0 checkpoint SHA：`571a46a91646c469699b93cdac559639cdc18d8a44e602c32943a0ad00dd7a79`。

F1/F2の800容量、400/400構成、K200、batch4、二つの学習seed/MDseed、推論/LOF、全6尺度・感度/prefixは事前計画を維持する。最初のM0は配備漏れによる学習前失敗として別attemptで復元。時間splitや科学条件を結果に合わせて変更していない。

[共通状態凍結](../执行证据/2026-10-26-b1-pilot/state-freeze.json)、[M0実測](../执行证据/2026-10-26-b1-pilot/M0-result.json)。これは配方の実行可能性であり科学的な探索改善の証明ではない。
