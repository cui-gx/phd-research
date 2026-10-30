# N1限定CPU実評価：凍結実行カード

2026-10-30、CONFIRMED：研究者の本輪指示。基準7fffe2d35f170ba3a128077781a74b164a1f9efa。model1 SHA、28CA proper RMSD [Å]、Q_CA8_M1_G3_LT、既存valid/reasonsと12窓を固定。新結果はPOST_HOC_EXPLORATORY。原準備契約は履歴として変更しない。

最初の固定2単位はr01-h1-mdと、原実行順で最初のr01下流r01-s4-F0-t0-m2-md（branch-index execution_order=1）。単位合格後のみ残270を実行する。単worker/数値thread1、GPU不可視、RSS2GiB/新出力2GiB/科学2hで停止。SHA/ID/CA/時間/品質/数値不一致は即時停止、成功単位不変。全272、各0.5ps・既存窓内最初の点から4点毎の2ps感度。履歴2nsに対する4ns窓はINCOMPLETE_WINDOWと記録し、下流4nsと混ぜない。

前後SHA、DCD全frameと既存CA配列の逐点一致、sim.csv時刻・valid=~reasons.any、品質件数、native自己r≈0/Q=1、proper rotationと鏡像、欠測・単位変換を工程検査する。DCD readerのdtは有限精度なのでsim.csv原時刻を主時間とし、DCD時間との差を記録する（工程許容0.001ps、旧科学窓の変更でない）。窓は旧t<=prefix+1e-5psの端点丸めを継承し、burn厳密t>burnを保持。

主表示4ns/100ps。全12窓・両間隔、F2−F1/F1−F0/F2−F0、8根の対応、S8−S4、全符号・陰性を報告。区間は根bootstrap10000回/seed17103001で探索的95%区間、モデル/MD/frameを根としない。追加の有意性選別なし。元幾何との関係は同窓枝/状態/根で記述し、frame相関を独立検定にしない。

34NMRは別費用/未承認で本輪計算しない。したがって参照依存性の定量検証は未完了。hit/dwell、第二Q、新MD/train/inference/LOF/C/B2/干渉benchmark/物理変更なし。全結果/コード/SHA/費用/失敗/日本語報告/A–Gを交付後停止する。
