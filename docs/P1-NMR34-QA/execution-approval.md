# NMR34-QA限定実行・凍結記録

2026-10-30 CONFIRMED：研究者は基準ef0bdd64ca904bfa78afa759d8ebe8077d71105dの契約に従い、r01-h1-md（4000点）とr01-s4-F0-t0-m2-md（8000点）のみを承認した。全272、MD、学習、推論、LOF、GPU干渉、C/B2は未承認。

[元カード](../P1-N1-Review/next-execution-card.md)と[数式契約](../P1-N1-Review/nmr34-contract.md)を継承する。CPU1 worker/数値thread1/GPU不可視、累積科学wall900秒、単工程300秒、RSS2GiB、出力256MiB。SHA確認・人工/参照検査も台帳に含む。成功receiptは排他的作成、run lock、コード/入力/設定fingerprint、不一致即停止。新出力のみ使用し旧科学資料不変。

[freeze.json](freeze.json)に実SHA、原子キー、Python/NumPy/MDAnalysis/psutil版、人工検査と既消費費用を記録した。2026-10-30 20:15/20:18 JSTのread-only資源確認でCPU負荷は低く、約114GiB利用可能、GPU計算processなし。他ユーザのログイン・processは存在する。本人に承認された1CPUだけを使用し、共有予約表の新規取得は行っていない。GPUには触れない。

原200/500ps窓を保存時刻から再現し、ID・件数とM1全frame/全窓値を照合する。入力7ファイル/単位と旧frames/windows、固定2参照のSHAを前後確認する。M1誤差1e−8Å、Q1接触count完全一致。NMR参照自己/回転/鏡映、34×34参照RMSD、全408000組のscalar/chunkを確認する。

出力：各単位frames.npz（R/Q/count N×34、min/argmin、ID/time/valid）、window-ids.json、34参照別windows.csv、immutable receipt、参照接触と幾何、最終費用/入力不変性。大きい逐frameファイルはサーバのみ、GitHubは窓表/監査/報告/SHA。旧archive保持・Mac raw免除。

既存B1環境を再利用、追加インストールなし。終了後に全量へ進まず報告・全文回読後停止する。
