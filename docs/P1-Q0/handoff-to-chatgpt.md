# ChatGPTへの引継ぎ：P1-Q0

## A. 現在の状態

2026-10-29 JST。Q0限定CPU監査COMPLETE。80/80モデル、272/272 MD（32履歴+240下流）、2,048,000ログ行を検査した。基準3b8b7b25da85c5d5da055b093ee4c79f6ff850b7、初版計画9c360a9aa2fb92c4e15534789b8b74ddbebc9f42。本文版8d01f6b2efc3e4e2cb6800059832b4619fcf7640の40交付ファイルはGitHub独立副本で全文SHA一致を確認済み。最終commitは本資料のGit履歴と最終返信で取得する。科学生成版は40a911e。GitHubは派生表/図/コード/監査、原DCD・重み・ログ/9archiveと初回Q0版は旧許可サーバ。Mac raw backup免除を維持。

## B. 確認事項

CONFIRMED：ユーザーによるQ0のみのCPUログ監査。MEASURED：80/272記録・主入力1,328 SHA一致、追加旧品質記録一致。DERIVED：曲線/窓/根別の記述。UNVERIFIED：学習収束、準備/pH/平衡、表現と科学利益。PROPOSED：次のL/P資格項目の審査。新計算と研究者科学受入れは未承認/PENDING。

## C. 主要結果

r07-s4-M0の単歩total最大130,942,008、全値は有限。M0全16、F1の31/32、F2の32/32で末尾20歩平均が冒頭20歩より低いが、収束証拠ではない。逐歩はtotalのみ、BCE/KLは未保存、validationは末尾のみ。BCE/枚診断はtrain/4、validation/50。sample重み付きvalidation KLは復元不可。

MD task平均温度は履歴299.610683–300.696067K、下流299.549310–300.922948K。温度/勢能の窓差と全根を[完全報告](review-dossier.md)に公開し、平衡合格とはしない。原入力504原子/28残基253H・水0、末端HT1–3/OT1–2。pH/準備コマンドは未判明。損失と温度だけで科学資格を認定しない。

## D. 技術情報

主監査と補助処理は単CPU、GPU不可視、2GiB制限内。コード・ログ索引は[README](README.md)。model/optimizer/RNGはログdigestと親checkpointバイトの照合であり、重み再loadなし。保存frame ID/800提示/200歩/32対応blockを照合した。

初回のresultパス誤読を訂正。Q0初版窓の浮動小数点境界重複をreport indexで修正し、taskごとの窓行数総和を元行数と照合した。旧Q0版は保持し、B1/R1は不変。[失敗](failures.json)。修正版主監査wall9.791941s、CPU9.789135s、峰RSS84.258MiB。旧passも計上し、一つの中間補助passの正確な時間は未保持と明記した。精密全累積wallを報告できるとはしない。

## E. 重点審査

1. 有限でも大きいM0尖峰をどう扱い、どのL資格が最小限必要か。
2. 未保存分項・一回の検証しかない状況で何が言えるか。
3. 根ごとの勢能変化とreseed、履歴継続を区別した説明は妥当か。
4. 元端基名・253HからpHを推定していないか。分子分野教員に必要な準備情報は何か。
5. Q0完全性とP/L十分性、C/B2仮説を混同していないか。

## F. 資料索引

[完全報告](review-dossier.md)、[モデル完全表](model-loss-summary.csv)、[逐歩](model-loss-per-step.csv)、[モデル系譜](model-lineage.csv)、[提示](model-exposures.csv)、[272task](md-task-diagnostics.csv)、[根別](md-root-diagnostics.csv)、[窓](md-window-diagnostics.csv)、[時系列](md-timeseries-10ps.csv)、[準備](preparation-inventory.json)、[SHA](input-sha256.csv)、[品質/保管](supplemental-input-audit.json)、[原品質](existing-quality.csv)、[履歴品質](history-existing-quality.csv)、[費用](costs.json)、[補助費用](supplemental-costs.json)、[図費用](figure-costs.json)、[前pass](prior-pass-costs.json)、[数値要約](descriptive-summary.json)。[出力SHA](output-sha256.json)はサーバ派生証拠、後付け本文の配送はGit commit/遠隔回読で検証する。

## G. 次段階

次は研究者/ChatGPTの独立科学審査だけ。L/Pのどの新計算が必要か、現体系をどの限定範囲で採用するかを判断する。O参照庫、C予測器、B2、S3、新MD/訓練/推論は自動開始しない。
