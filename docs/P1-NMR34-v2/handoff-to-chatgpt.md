# NMR34-v2 A–G引継ぎ

## A. 現在状態

2026-10-31 JST、IMPLEMENTATION_AND_SYNTHETIC_TEST_COMPLETE / REAL_QUALIFICATION_PENDING。基準70427b17951ffa3ecc5f0cd228eec816685425d5。人工8test methodsがPASS、実軌跡0/2、全量0/272。最終commitは本ファイルを含むGit履歴と最終返信で示し、内容commitの全文確認はremote-readback.jsonで追跡する。

GitHubはコード・試験・文書・静的SHA。新raw出力なし、サーバに接続せず、原9archiveとMac raw免除の方針を維持した。本輪にサーバ上の実在/SHAを再検査したとは主張しない。

## B. 状態と科学境界

CONFIRMED：コード改良、静的分析、人工試験、資源予算設計、文書同期のみ。MEASURED_ENGINEERING：Mac人工試験の結果。DERIVED：配列容量と全量費用算式。PROPOSED：次の二軌跡資格、近接診断幅1e−6 Å、全量の分割・予算。UNVERIFIED：サーバv2性能、MDAnalysis reader、元時刻/ID/窓全値照合、科学的優位性。

旧N1/v1の定義・入力SHA・結果は変更しない。主model1、28CA、proper Kabsch、strict8Å/gap3、元品質/窓位相を維持する。全量、MD/CVAE/LOF/C/B2の許可なし。

## C. 重要結果

新たな科学数値はない。人工回転/鏡映/単位、scalar精度、Q固定分母/8Å隣接float、argmin同参照Q、24窓×35系列、window phase、ID品質、SHA/lock/再実行拒否を検査した。初回境界testの空native集合エラーとfixture修正を両ログに保全した。

v1実測8.2–9.4時間からv2速度改善率を算出していない。near表は理論上全量21.30GB追加となり得るので2GiBを保証しない。exact quantileを維持する列別集計は再解凍I/Oを伴う。人工testの短時間はサーバコストではない。

## D. 技術情報

[独立adapter](../../p1/nmr34_v2.py)、[人工試験](../../p1/test_nmr34_v2.py)。CAを一度だけcache、34参照/maskを固定、scalar資格mode分離、512点chunk、SHA付きmanifest、sampled/valid ID別保存、同参照Q、near marginを実装。列sliceはcopyしてchunk全行列への参照を解放する。

Timerは非重複wall/CPU、Runはflock/排他startとreceipt、resource_checkは協調的保護。全体orchestratorと外部watchdog/永続総予算は未実装であり、実読取前の次回prerequisiteと明記した。人工seed34、新モデル/MDseedなし。Mac NumPy2.4.4/Python3.14と対象環境差を残す。

## E. 独立審査で確認する事項

- 原時刻とCAキーの正規化、DCDReaderの対象環境API、旧window_statusを実行カードで照合できるか。未供給statusはUNVERIFIED_WINDOW_STATUSと出力し、勝手に再定義しない。
- 工程診断幅はQ判定を変えないか。near巨大ケースの停止/予算が十分か。
- 列別quantileのI/OとCA cacheによるRAM増を実測するまで、最適化完了を科学実行readyと誤解していないか。
- lock/receipt単位機能と、未実装の全batch lock/ledger/外部監視を区別しているか。
- 200/500ps問題は旧ID保持と将来の独立感度設計として扱い、旧結果を修正していないか。

## F. 索引と再現

[技術・差異報告](technical-report.md)、[予算案](budget-plan.md)、[次カード](next-execution-card.md)、[最終人工ログ](synthetic-tests.log)、[初回失敗ログ](synthetic-tests-first-attempt.log)、[静的監査](static-audit.json)。原実SHAは[旧freeze](../P1-NMR34-QA/freeze.json)を参照し再生成しない。

人工試験のみ：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s p1 -p test_nmr34_v2.py -v`。実DCD処理CLIなし。新規依存導入なし、人工一時ディレクトリは終了時削除する。コード/旧証拠不変SHAはstatic-audit.json。

## G. 次の判断

研究者/ChatGPTがコードと未検証項目・予算を審査し、必要なら二軌跡だけの別実行を承認する。二軌跡資格後も全272は別承認。C/B2、MD、学習/推論、LOFは開始しない。本輪交付とGitHub全文回読後に停止する。
