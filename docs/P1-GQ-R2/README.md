# P1-GQ-R2：局所構造探索評価器の審査資料

2026-10-26。**工学的納品PASS、唯一の科学成果指標としてはNOT READY。研究者・計画側の審査待ち。**

## Executive Summary

承認済み範囲で、既存16 ns NoCutoffの全32,000フレームをサーバCPUだけで解析した。新規GPU計算、MD、CVAE学習/推論、B/C効果比較、S3は実行していない。科学目標は物理的に意味のある局所構造の多様性であり、折り畳みや準安定状態の発見ではない。

増分ε領域と固定参照庫を実装し、事前登録の1,536条件、負対照、全点品質検査、9プログラム試験と日語科学図を保存した。粗い幾何警報は0。2 Å/5 psの代表差に主鎖角変化はあるが、ε/持続条件の非単調性と固定庫の代表性不足が明確であり、唯一の閾値を科学的に確定するには独立資料が不足する。現在の値は探索的な操作量に限る。

主要実行は失敗を含め152.139秒。原R1の263ファイルはSHA不変。全科学値と図はサーバで作り、Macは開発・資料整理・伝送・照合だけを行った。原データや重みをGitHubにアップロードしていない。

## 読む順序

1. [教員向け概要](supervisor-summary-ja.md)
2. [事前分析計画](analysis-plan.md)
3. [数式と未来C/Bの入力契約](metric-definition.md)
4. [全点品質・緩和・科学リスク](physical-quality.md)
5. [領域評価とA/B比較](novelty-evaluation.md)
6. [閾値と識別不能性](threshold-calibration.md)
7. [負対照と失敗](negative-controls.md)
8. [統計・独立性・妥当性の限界](statistical-limitations.md)
9. [コスト・計算量](cost-and-complexity.md)
10. [B1資格判断](B1-readiness.md)
11. [再現手順](reproduce.md)
12. [修正履歴](amendments.md)

## 証拠と実装

[小規模証拠](../执行证据/2026-10-26-gq-r2/)、[検証要約](../执行证据/2026-10-26-gq-r2/validation.json)、[全感度CSV](../执行证据/2026-10-26-gq-r2/sensitivity.csv)、[公開証拠SHA](../执行证据/2026-10-26-gq-r2/public-sha256.json)。実装は `p1/server/gq_r2.py`、監督は `gq_r2_run.py`、証拠整理は `gq_r2_publish.py`、試験は `tests/p1/test_gq_r2.py`。

計画commit `94d96bc24c8c35dca7f08452809b2a35239a9da3`、実装初版 `0c8ecf6`、空分布修正と証拠整理 `90b3dca`。品質実行時ソースと失敗時ソースは実行SHAを分け、本人領域のアーカイブに保存する。最終報告commitはGitHubの履歴と交接記録で追跡する。報告から将来の研究結論をCONFIRMEDへ昇格させない。

## 状態ラベル

CONFIRMED：研究者が確認した範囲/目標。MEASURED：実際の測定。DERIVED：その計算・解釈。PROPOSED：未承認の尺度や今後の候補。UNVERIFIED：未確認の科学条件。プログラムのPASSと科学のPASSは別。S2補充独立終審INCOMPLETE、B1/B2/C/S3未承認。完了後停止する。

本タスク指定の推奨はSol High。自動のモデル/推論設定切替や並列エージェント委任は行っていない。これは過去に未完の独立最終審査を代替するものではない。
