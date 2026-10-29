# Q0：保存済みログの限定資格監査

2026-10-29。研究者の明示承認、基準3b8b7b25da85c5d5da055b093ee4c79f6ff850b7。80モデルと272 MDの既存ログだけを読む。GPU不可視、単CPU/数値thread1、追加RAM2GiB、出力1GiB、累計2時間で再審査。新MD/学習/モデルload・推論/LOF/DCD処理・成果再評価なし。

原SHA索引とrequest/result/recipe/exposure/loss/checkpointバイトを照合する。モデルの親・optimizer・RNGは既存digest記録の照合であり、テンソルを復元しての再証明ではない。逐歩totalをそのまま保存し、未保存BCE/KLはNOT_SAVEDとする。訓練BCEを4、検証BCEを50で割った1枚当たり診断列を別記する。sample重み付き検証KLは集約値から回復不可。

MD sim.csvの有限性、0.5ps/250stepの報告連続性、checkpoint時刻接続を検査する。0–100/100–200/200–500/500ps以後の登録窓および10ps表示用集約を報告する。新しい物理合否閾値、平衡認定、独立フレーム統計は作らない。8根を最上位単位とし、元品質記録を独立再計算と呼ばない。

入力不一致・欠落・資源超過時は停止して証拠を保存する。旧データ/ソース/結果は不変、新出力のみ。Mac原backup免除、9archive保持。計算完了後日本語報告・全CSV/SHA/費用/A–G交付、GitHub回読後停止。P/L/O/C/B2へ進まない。
