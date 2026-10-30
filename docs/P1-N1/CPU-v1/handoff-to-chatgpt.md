# P1-N1 CPU評価：ChatGPT引継ぎ A–G

## A 現在の状態

2026-10-30 JST。COMPLETE 272/272、2,048,000frame、未実施承認単位0。基準7fffe2d、実行器b5fd110、集計3aa930b。最終commitはGit履歴と最終返信、回読はremote-readback.jsonで照合。GitHubは完全なcompact表/図/監査/コード、全frame NPZと原データは許可サーバのみ。原9archive保持、Mac raw backup免除。

## B 状態

CONFIRMED：研究者の今回指示でmodel1、28CA proper Kabsch/Å、Q_CA8_M1_G3_LT、原品質/12窓、0.5/2ps CPU評価を承認。MEASURED：272入力/出力と座標・時刻・品質・SHA一致、全native指標。DERIVED：8根対応・bootstrap探索区間・旧幾何相関。PROPOSED：今後の時間尺度/予算・recipeの検討。UNVERIFIED：物理/学習十分性、CのX独立価値、B2正味利益。技術PASSと科学受入れPENDINGを分ける。

## C 重要結果

POST_HOC_EXPLORATORY。主窓4ns/100psのF2−F1最小RMSD差はS4 +0.396619 Å（6根正/2負）、S8 −0.398921 Å（2正/6負）、二状態平均−0.001151 Å（4正/4負）、95%探索区間[−0.204768,+0.216556]。S8−S4 −0.795541 Å。Q平均の二状態差−0.003784で区間は0を跨ぐ。2psも同主窓では同方向。

4ns枝の最良3.614485 Å。履歴best改善枝はF0 22/48、F1 52/96、F2 47/96で、枝数は独立Nでない。native測定信号はあるが安定した更新優位・folding成功を意味しない。全対比/全窓は完全報告とCSVを参照。

## D 技術情報

MDAnalysis2.9.0/NumPy1.26.4、単worker/thread/GPU不可視。固定首2単位合格後に残270。単位wall合計329.994523s/CPU329.934963s、最大RSS182.625MiB、summary2.371534s/RSS281.227MiB。約49MB出力、2h/2GiBに未到達。全原SHA前後不変、CA全点一致、sim.csv時刻とvalid/reasons一致。人工reader9検査PASS、欠損負試験時の既存reader destructor警告を隠さない。失敗/再試行0。全frame NPZはpaired(r,Q)、ID/time/valid/bestを保存。原科学コード不変。新推論/LOF0。

## E 審査論点

S4/S8反転は元実験の候補pool/M0/歴史交絡を含む。Qとrの不一致、sampling依存、相関frame、8既知根の探索区間、多重尺度をどう解釈するか。34参照未実行、物理準備/pH/平衡とL2 KL/表現問題は残る。固定GPU時間・wall-clockでの価値へ外挿しない。C/B2のH600秒案や新モデルrecipeを自動採択しない。

## F 索引

[完全報告](review-dossier.md)、[全索引](README.md)、[実行カード](execution-approval.md)、[全窓](all-windows.csv)、[モデル](model-windows.csv)、[状態](state-windows.csv)、[状態差](state-paired.csv)、[全8根](root-paired.csv)、[全区間](root-summary.csv)、[旧幾何全参照](geometry-native-joined.csv)、[相関](geometry-correlations.csv)、[履歴](history-progress.csv)、[費用](costs.json)、[全単位SHA](unit-audit.json)、[最終サーバ](final-server-audit.json)、[交付監査](delivery-audit.json)、[失敗/未実施](failures-and-missing.json)。モデル/学習seed/MDseed/source frameは[全240系譜](../branch-index.csv)。

## G 次段階

独立科学審査と研究者判断のみ。native信号と不確実性を踏まえ、34NMRや物理・学習資格の追加必要性、C/B2に十分な時間尺度/独立根数を検討する。新MD/train/inference/LOF/C/B2/干渉/物理変更は未承認で、ここで停止する。
