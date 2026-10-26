# データ系譜と公開時刻

本輪は実行中。確定済み方法は[data-lineage-plan](data-lineage-plan.md)とcommit40a911e以前の事前記録を参照する。S4のM0は0–2 ns品質確定後、新2–4 nsの生成前に構築する。S8のM0は4–6 ns旧窓から、新6–8 nsの生成前に別途構築する。M0初期化規則/200歩は共通で、連続8 nsのAIオンライン更新履歴を再現したとは主張しない。

4区間は同じMD checkpointの継続で、8 ns状態は4 ns分枝結果を読まない。global IDと元2 ns区間/local IDを維持する。時刻の累積浮動小数誤差で旧側末尾フレームを新側へ移さないよう、元区間IDで排他的に制限する。原時刻は保存する。

各状態はM0/optimizer、候補/特徴、歴史checkpoint、全DCD、X/Z/WのSHAと公開時刻を保存する。特徴は状態分枝より前に凍結される。`temporal-and-SHA-audit.json`は最後にイベントと保存ファイルを独立再読する。監査が未完了/不合格なら科学的解釈を確定しない。

イベントの`qualified`はMD特徴生成の品質確定を示す。モデル/pool等の別種タスクのfalseを科学的不合格と読み替えず、task kind・status・依存関係と共に読む。
