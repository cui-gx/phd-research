# P1-B1 Pilot：AIモデル更新の下流効果

2026-10-26。**承認済みPilotの数値計算は完了。新データの安定した上乗せ改善はINCONCLUSIVE。研究者審査待ち。**

## 要旨

FSD-EY/OpenMM/既存CVAE/単一RTX PRO6000で、新しいNoCutoff共通履歴4 nsを作り、F0凍結・F1旧データ更新・F2新旧混合更新を二対応乱数ブロック、各4 ns（下流24 ns）で比較した。F1/F2は同じM0/optimizer/RNGから200歩/延べ800サンプル、全モデル同候補7,800点と無native参照LOFを使用した。

更新は実際の選点を変えた。F2−F1の起点距離は5.913/4.311 Å。下流4 nsの平均幾何新規度差は−0.0478/+0.3588 Åで符号が一致しない。F2−F0の平均差は正でも、離散領域数では第2ブロックで負の尺度がある。全6尺度、全prefix/緩和感度を保存し、都合のよい指標だけを選んでいない。

全48,000下流フレームは粗い品質条件を通過。29成功タスクと1配備漏れ失敗を記録。GPU割当占有時間1505.0798秒、CPU最終評価63.3310秒。固定MD量の診断なので、固定wall-clockの科学純利益やCの追加情報を証明していない。元準備/溶媒/緩和の未確認条件も保持する。

## 審査の入口

1. [教員向け日本語概要](supervisor-summary-ja.md)
2. [事前計画](analysis-plan.md)・[下流前凍結](recipe-freeze.md)
3. [実験設計](experiment-design.md)
4. [歴史とデータ来歴](history-and-data-lineage.md)
5. [モデル学習](model-training.md)
6. [候補選択](candidate-selection.md)
7. [下流MD](downstream-md.md)
8. [物理代理の数式](scientific-metrics.md)
9. [全対応結果](paired-results.md)
10. [実費用](cost-and-runtime.md)
11. [統計・妥当性の限界](statistical-limitations.md)
12. [失敗と修正](failures-and-amendments.md)
13. [再現手順](reproduce.md)
14. [次段階の審査事項](next-stage-recommendation.md)

## 証拠と版

[最終検証](../执行证据/2026-10-26-b1-pilot/validation.json)、[全タスク/時間合法性監査](../执行证据/2026-10-26-b1-pilot/final-audit.json)、[864対応差](../执行证据/2026-10-26-b1-pilot/paired-results.csv)、[完全候補順位](../执行证据/2026-10-26-b1-pilot/candidate-rankings.csv)、[モデル来歴](../执行证据/2026-10-26-b1-pilot/model-provenance.json)、[原データSHA](../执行证据/2026-10-26-b1-pilot/raw-artifact-sha256.json)、[公開SHA](../执行证据/2026-10-26-b1-pilot/public-sha256.json)。大DCD/checkpoint/全配列/原ログは本人サーバとバックアップ（完了状態は検証記録を参照）に保管し、GitHubへ上げない。

計画0c92f6025bcde7a971994d9c515a1184abe83fbeをpush/遠隔回読後に計算した。初版5ef0e03、復元cbe793a、費用修正1358a86、方法4932f3f、保存検査d533389。各段階の正確なソースSHAと修正表を保持する。実装は既存科学関数/ParslのPilot用適応であり、元Colmena全体の再現ではない。

CONFIRMEDは研究者の承認、MEASUREDは測定、DERIVEDは派生解釈、PROPOSEDは今後の案、UNVERIFIEDは未認証条件。実行端の工学完了は研究者受入れや独立科学審査の代わりではない。S2独立終審INCOMPLETEを維持。正式B1/B2/C/S3へは進まず停止する。

## 納品・保管・清掃状況

2026-10-26、完全原データアーカイブ581,720,607 bytesのサーバ/Mac双方SHA-256が一致した（`07acba4d1e973f7eaaf6be55ce3e56cc8d8303a694e9e996654d29678886a90a`）。8 MD軌跡、5モデルcheckpoint、初回失敗、保存ソース、全解析配列を確認した。本人の登録済み一時環境・キャッシュだけを削除し、B1の原データ388ファイル、旧S1/S2 336・GQ 263・R2配列16と既存R2アーカイブを再照合した。原始証拠・モデル・アーカイブは保管する。追加科学計算は行わず、研究者審査を待つ。

[バックアップ検証](../执行证据/2026-10-26-b1-pilot/backup-verification.json)、[清掃検証](../执行证据/2026-10-26-b1-pilot/cleanup-verification.json)。公開SHAの当初39ファイルはそのまま保ち、後から取得した閉鎖記録はdelivery-manifest.jsonで別に照合する。
