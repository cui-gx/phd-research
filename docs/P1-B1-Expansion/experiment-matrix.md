# 実験行列

承認範囲：8根×8 ns=64 ns履歴。各根4/8 nsの16状態、各状態15本×4 ns=60 ns、下流計240本/960 ns。合計1,024 ns。履歴は2 ns×4区間をcheckpointで連続する。M0は16、追加学習64、標準推論80＋F0一致診断16。追加の工程MDは行わない。

[完全240行CSV](experiment-matrix.csv)、[根・状態・種子を含むJSON](experiment-matrix.json)。予定IDを削除せず、成功/失敗/未実行を別記する。F0は各状態3本のみで、T1/T2に共有する。行列は `p1.server.expansion_contract.experiment_matrix` から生成し、実行時に同一ハッシュを照合する。
