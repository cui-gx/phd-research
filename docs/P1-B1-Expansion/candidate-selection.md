# 候補選択と物理的な機構診断

S4は100 ps以後の0–4 ns、S8は同じ根の0–8 ns合格履歴全体を使う。候補数は自然に異なるためZへ保存し、増加を科学フィードバックXだけの効果としない。同状態全モデルは同候補SHA。

既存CVAE predict batch64/seed2026102671、LOF neighbors20・Minkowski p2・novelty=False・n_jobs2。negative_outlier_factor_昇順、同点はglobal ID昇順。Top1を選び、Top10/100・全順位/score/embedding・実checkpoint SHAを保存する。native RMSDを使わない。

F0は同状態で二度推論して全配列一致を検査する。F1/F2は同Tで初期model/optimizer/RNG/step/提示数を検査する。実際の原DCDから全原子起点を抽出し、分枝MD投入配列と照合する。ID差、Top-k共通数、起点dRMSD[Å]、周期主鎖角差[度]を分けて報告する。定数scoreの相関はnullとする。

同起点でも計画を変更せず全予定seedを実行する。共有起点は独立構造発見の増加ではない。選点変化と下流成果の優劣は別の問いである。本輪の結果は完了後に集計する。
