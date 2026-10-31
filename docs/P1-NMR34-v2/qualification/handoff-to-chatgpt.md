# NMR34-v2限定二軌跡資格：A–G引継ぎ

## A. 現在状態

2026-10-31 JST。バッチnmr34-v2-qualification-20261031-v1、COMPLETE、2/2軌跡、12,000/12,000frame、408,000/408,000参照組。限定数値・資源ゲートPASS。独立科学審査/研究者科学受入れPENDING。最終監査時刻は[final-audit.json](final-audit.json)、最終交付SHAは本ファイルを含む最終Git commitと研究者への最終返信で特定する。

基準eed520fd6b1263dfbb49b599fa80e02c479ff8e2、実行凍結90ed64aed54f961dfb458c6fb257e5b890bc5ade、工程9ファイル全文回読PASS。[工程証拠](engineering-readback.json)。最終報告の全文回読はremote-readback.jsonで追跡する。

GitHub：完全窓表1,680行、差分CSV、worker/監視/実装SHA/参照対応/全出力索引、報告。サーバのみ：全逐frame chunk、ID/品質配列、元窓ID、完全stdout/stderr/budget台帳、成功receipt。元9archive存在/サイズ一致、本輪archive再hashなし、Mac raw免除。計算と監視は終了しglobal lock非保持。

## B. 確認状態

CONFIRMED：今回限定2軌跡/qualify=True/元定義/900s/工程300s/RSS2GiB/256MiB/単worker/thread/GPU不可視。MEASURED：全34 v1/v2一致、Q/countとargmin完全一致、全窓、実費用、33入力SHA前後不変。DERIVED：全量点外挿、scalar差引き、旧N1最大誤差の継承。PROPOSED：全量のmode/予算/別wrapper。UNVERIFIED：全272の科学効果/費用上界、物理・学習資格、C/B2。

## C. 主要結果

[完全報告](review-dossier.md)、[差分CSV](comparison.csv)。RMSD最大差0 Å、Q/count完全一致、argmin完全一致。scalar/chunk最大差7.10543e−15 Å。各840窓行（34固定×24＋ensemble×24）を全件保持。near±1e−6 Å内0pair、200/500psの元1点差は再現。

supervisor科学wall17.392948s、worker CPU16.931123s、RSS225.367188MiB、thread観測最大1、出力7,024,697 bytes。単位wall5.525454/11.118119s。v1の37.182789/135.570957sとの比6.73/12.19は周辺I/O/cache等を統制した単一改変ベンチマークではない。

全量qualify=True外挿2,845.163s（47.42分）、scalar差引き706.515s（11.78分）は通常mode実測ではない。CI/上界なし。12,000frameは独立標本でなく、同じr01の履歴とF0のみ。探索利益/F2優位/C/B2を認定しない。

## D. 実装・再現

[薄実行器](../../../p1/nmr34_v2_execute.py)、[v2数値core](../../../p1/nmr34_v2.py)、[追加人工test](../../../p1/test_nmr34_v2_execution.py)、[固定config](config.json)、[実環境](execution-fingerprint.json)。CA cache一回、34参照中心化、qualify scalar、512frame chunk、同参照Q、ensemble/全窓、near表。atomキーは固定欄空白のみstrip、元時刻/品質/原子順を保持。

人工12testsはサーバ既存Python3.12.3/NumPy1.26.4/MDAnalysis2.9.0環境でPASS。Mac試行のpsutil欠落は保存。新訓練seed/MDseedなし。project global flock、不可変receipt、外部watchdog、fsync累積台帳、完整ログ。再実行を拒否する。

論理PROJECTをP、バッチをP/artifacts/nmr34-v2-qualification-20261031-v1とし、既存環境のPythonで`code/nmr34_v2_execute.py supervise P BUNDLE OUTPUT`を使用した。実行済みOUTPUTへの再起動は禁止。再現記述は再実行許可ではない。

## E. 審査点と限界

- 二軌跡の数値等価性と全量科学結論を分離する。
- 0.1s監視は瞬間ピーク保証でない。OS affinity未変更、CPU時間/数値thread/コア使用を区別する。
- near非空の実データcaseは未観測、全量near容量を保証しない。
- 全量mode変更・累積復旧wrapperは未承認/未実装。固定2IDの強制を無断解除しない。
- 全量のcounterfactual費用を通常mode測定として扱わない。
- 旧200/500ps問題を不利結果除外や主参照変更で処理しない。

## F. ファイル索引

[完全報告](review-dossier.md)、[config](config.json)、[人工tests](artificial-tests.log)、[Mac失敗](mac-engineering-attempt.log)、[worker結果](worker-final.json)、[外部監視](supervisor-final.json)、[全byte/SHA監査](final-audit.json)、[参照](reference-map.json)、[履歴全窓](history-windows.json)、[下流全窓](downstream-windows.json)、[履歴chunks](history-chunks.json)、[下流chunks](downstream-chunks.json)、[差分CSV](comparison.csv)、[予算算式](updated-budget.json)、[実環境](execution-fingerprint.json)。大きいrawの全相対パスとSHAはfinal-audit.json。

## G. 次段階

[次の承認判断](next-approval.md)を研究者/ChatGPTが審査する。全272を選ぶ場合は別manifest/mode/資源枠/非上書き復旧を明示した承認が必要。本報告から全量、MD、CVAE、LOF、R0、C/B2へ自動進行しない。全文回読後停止。
