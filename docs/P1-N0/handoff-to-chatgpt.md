# P1-N0：ChatGPT・CodexへのA–G引継ぎ（設計のみ）

## A. 現在の状態

2026-10-30 JST。**N0文書・評価契約案と差別化比較表を作成**。基準L2確定commit `65fb2acc8f99774269671ceca25a411ac9ce15cd`。速水先生の共有メールは [打合せ記録](../研究打合せ/2026-10-30-速水先生-差別化と科学評価.md) に原文を保持している。今回のN0はMD/訓練/推論/LOF/DCD数値読取りを行わない。**SCIENTIFIC_REANALYSIS_NOT_APPROVED**。

## B. 資料と分離すべき状態

- **CONFIRMED**：1FMEは28残基・solution NMR34モデル。リポジトリのnative reference model1の既知SHAは`a5276b2752cd95555f7ca078c512c68f89b50893519e99347a1986fa63c82dc8`（旧manifest由来）。B1は240×4nsのF0/F1/F2下流枝、L2の36chain/156endpointは計算終了。
- **ADVICE_RECORDED**：速水先生はDeepDriveMD/Colmenaとの差別化と、native RMSD・latent分布・低RMSD構象を効率よくサンプリングする評価を勧めた。FSD-EY使用を肯定し、陰溶媒の限界と原研究との条件一致を指摘。
- **PROPOSED**：native model1 Cα RMSD（proper Kabsch、28個）をB1事後の主診断候補に、native QとNMR34感度・hitと持続性を補助にする。G_Rは依然未採択の参考探索尺度で、事後変更しない。
- **UNVERIFIED**：実際の新native数値とfolding hit、同一wall-clockでの方策価値、科学XのZ/W増分、DeepDriveMD/Colmenaに対する十分な新規性、物理P、L2の一般化・収束。

## C. 核となる研究判断

Colmenaにはモデル陳腐化/再訓練待機とresource steeringの先行議論がある。AI更新を判断すること単独は差別化ではない。単共有GPUでMD継続と更新を競合行動とし、決定前Xの追加情報とnative折り畳み進捗を実wall-clockの同一制約で比較する**限定された検証可能な仮説**として扱う。

## D. 技術的境界

元のB1`Q8`は全300組の接触割合で、NMR定義の`Q_native`と異なる。既存内部距離型dRMSDとproper-aligned native Cα RMSDも異なる。B1元の等MD量効果は現存下流軌道で再評価できるが、旧ログからオンライン実時間反実仮想を補完しない。L2の新LOF Top1はすべて下流`NOT_OBSERVED`。

## E. 次レビューの優先事項

1. 1FME native model1の主評価が可比性と参照任意性のバランスを満たすか。論文実装のRMSD reference/atom selectionを調べる。
2. NMR34感度の具体的用途、native contact Q母集団と閾値/継続の非恣意的な固定、既存DCDのframe ID/dtを確認。
3. 先行研究の更新ルール・資源制約と本研究の新規性の本当の交差部分を照合。
4. どこまで新CPU事後評価を承認するか。研究者承認が出る前に実行しない。

## F. ファイル索引

- [N0入口](README.md)
- [評価契約案](native-evaluation-contract.md)
- [先行研究差別化](related-work-differentiation.md)
- [承認ゲート](decision-gates.md)
- [速水先生の原文](../研究打合せ/2026-10-30-速水先生-差別化と科学評価.md)
- [L2技術完成](../P1-L2/review-dossier.md)
- [B1科学報告](../P1-B1-Expansion/review-dossier.md)

## G. 次の行動と停止

研究者とChatGPTがN0契約・差別化案をレビューし、方法の修正・採択、限定CPU実行を**別途承認**する。今回の文書作成は、新たな研究実験の承認でもB1/L2科学的受入れでもない。原9archive保存、Mac原rawバックアップ免除を継続。作業が終了したらGitHub commit／実体readback後に停止。
