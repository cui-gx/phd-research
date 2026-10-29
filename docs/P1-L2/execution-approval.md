# L2-design-v1限定実行カード

2026-10-29 JST、CONFIRMED。研究者は設計commit `8d34e3714e246afb0bd74fe6943abeafd8f89c5b` を審査し、固定36chain/57,600新規steps、156評価点を明示承認した。設計原本・CSVのNOT_APPROVEDは設計時の歴史として保存し、本カードで当該行列の実行許可を更新する。E0や追加24chainを含めない。

入力凍結： [108原ファイル実SHAと時刻/ID/Cα順](input-freeze.json)。既存4状態のPDB16件、pool12件、対応20モデルのcheckpoint/recipe/exposure/result80件を検査した。原80系譜は既報索引を維持し、未使用60weightの新ロード/全archive再監査とは主張しない。

工程資格：[人工tensorチェック](engineering-check.json)。固定CVAE/RMSpropで連続6stepと3step+保存/復元+3stepを比較しmodel/optimizer/RNG bit一致、eval反復一致・親不変を確認。人工optimizer12stepであり、科学57,600stepには含めない。CPUだけ、実MDなし。入力監査と人工testの[費用1](input-freeze-cost.json)、[費用2](engineering-cost.json)。

独立実装は[l2_engineering](../../p1/l2_engineering.py)、[l2_train](../../p1/l2_train.py)、[l2_evaluate](../../p1/l2_evaluate.py)。旧B1/R1/Q0/L1実装は変更しない。GPU訓練とCPU評価は別process、全successを上書きしない。旧保存原archive保持、Mac原backup免除を維持する。

接続時CPU/RAM/disk/GPUを確認し、GPU process0、RAM約120GiB available、disk約828GiB availableを確認した。研究者の今回実行指示と以前の継続的共有利用調整を根拠に使用し、古い失効済みsmoke leaseを本輪の予約・資源許可へ流用しない。計算直前にも再点検する。

科学計算前にこの入力/実装をcommit/pushして遠隔全文を照合する。首M0とFULL評価実費を測定し、予定保護値を超える見込みなら次セルへ進まず停止。RSS2GiB、GPU8GiB、出力2GiB、科学工程累計2時間、単工程300秒の復核点。異常・不一致で停止し、結果の良否で行列を選別しない。B2/C/S3や新MDを行わない。

現在は工程資格PASS、科学訓練0/36。実行状態はexecution-progress.jsonで追跡する。本文の工程合格は学習十分性/科学探索価値の認定ではない。
