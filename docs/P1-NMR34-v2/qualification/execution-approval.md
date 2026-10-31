# NMR34-v2限定二軌跡資格の凍結

2026-10-31 CONFIRMED。基準eed520fd6b1263dfbb49b599fa80e02c479ff8e2。研究者は固定2軌跡/12,000frame/34参照/28CA、qualify=True、M1/v1/全窓/argminの一致と性能計量のみ承認した。全272/MD/CVAE/LOF/R0/C/B2は未承認。

[config.json](config.json)は旧20入力とv1成果のbyte SHA、現在の3実装SHA、900s/300s/RSS2GiB/出力256MiBを固定する。1科学worker/数値thread1/GPU不可視。12人工test methodsは既存サーバ環境でPASS、Macのpsutil欠落試行も保全する。

実入力のSHA確認から科学台帳を開始する。外部processで0.1sごとのprocess-tree RSS、出力、累積時間/工程時間を監視し、異常時は自分のworkerだけ停止する。監視の時間粒度/停止猶予の限界を記録する。project領域のglobal flock、追記fsync台帳、排他startと成功receipt、完整stdout/stderrを使用する。同出力の再起動を拒否し、原成功物を上書きしない。近接診断幅1e−6Åは接触のstrict8Å定義を変更しない。

実読取前に実装・人工test・configをcommit/pushし全文を照合する。資源は09:52/09:55 JSTにread-only確認、CPU低負荷、約116GiB空きRAM、GPU計算なし。他者ログインあり、占有/予約の横取りをしない。新規予約表取得は未実施、研究者が今回許可したCPUだけ使う。原9archive保持・Mac raw免除。資格後に停止する。
