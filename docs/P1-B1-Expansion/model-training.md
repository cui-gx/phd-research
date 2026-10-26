# M0と対応更新

既存mdlearn938cb80のCVAE/損失/RMSpropを使用する。ネットワークは28×28二値8 Å接触入力、filters16×4、kernel3×4、stride1/1/1/2、dense128、dropout0.5、latent3。lr0.001、weight decay1e-5、clip10。学習された標準化器は使わない。

全状態のM0は未学習の同一seed1600000001で初期化し、旧800をbatch4/200歩で学習する。初期weight/optimizer digestを根横断で検査する。F1/F2はそれぞれ同じM0/optimizerを復元し、各Tの同初期RNGと800位置のpermutation、200歩/延べ800提示を使う。F1旧800、F2旧400＋新400で容量を揃える。時間分離した検証200は診断のみ。

各step loss、サンプルID/提示順、初期・最終model/optimizer/RNG digest、checkpoint SHAと実費用を保存する。保存checkpointは終了時CPUで読み戻し、内容digestと全optimizer param_groupsを確認する。loss低下は科学探索の改善を示さない。訓練不足/学習設定の一般性は本実験の限界として残す。

[最終実機前検証](implementation-and-preflight.md)。本輪の全80学習結果の集計は実行完了後に記録する。
