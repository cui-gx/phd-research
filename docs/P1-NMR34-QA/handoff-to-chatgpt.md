# P1-NMR34-QA — ChatGPT独立審査への引継ぎ

## A. 現在状態

- バッチ：nmr34-qa-20261030-v1。科学実行2026-10-30、最終サーバ監査2026-10-31 09:25:36 JST。
- 実行COMPLETE、2/2軌跡、12,000/12,000frame、408,000/408,000参照組。全272はNOT APPROVED / NOT EXECUTED。
- 数値・入力・制限の二単位ゲートPASS。詳細記録の欠落は下記E。独立科学審査・研究者科学受入れPENDING。
- 科学基準ef0bdd64ca904bfa78afa759d8ebe8077d71105d、実装凍結c33807eec32096d59049bcf48ef3238ffa134906。交付内容commitと全文照合は[remote-readback.json](remote-readback.json)、最終交付SHAは本ファイルを含む最終Git commitと研究者への最終返信で特定する。自分自身のSHAをファイル内に埋め込まない。
- GitHub：コード、全窓表、参照幾何/接触、SHA、実行/監査、費用、報告。サーバのみ：逐frame34列のNPZ、window-ID、immutable receipt等。[全索引](delivery-audit.json)。原9archive存在/サイズ一致、今回全archive再hashなし、Mac raw免除。

## B. 確認状態

CONFIRMED：固定2単位、既存N1窓、34参照、900 s/300 s/RSS2 GiB/出力256 MiB/単CPU/GPU不可視。許可済み計算は完了し再実行しない。

MEASURED：全20入力SHA前後不変、原子/座標/品質/時刻照合、M1再現、全scalar/chunk、費用。

DERIVED：この二単位での数値拡張の適合、暫定全量費用。PROPOSED：別adapter改訂資格と全量予算審査。UNVERIFIED：全272参照依存、更新利益、物理/学習十分性、C/B2。技術PASSを科学受入れと混同しない。

## C. 主要結果

両単位M1 RMSD最大絶対差5.3290705182e−15 Å（許容1e−8 Å）、Q1整数count完全一致、全scalar/chunk最大差7.1054273576e−15 Å。34自己RMSD最大2.66375e−14 Å/Q自己1、参照接触数39–49（M1=42）。異参照561組のRMSD0.411960–2.590248 Å。

科学wall173.215828 s、run CPU213.137030 s、監視最大RSS210.480469 MiB、出力4,890,583 bytes。原200/500 ps境界の各1点差と不完全な履歴4 ns窓はそのまま保持。下流主窓M1最低6.270597 Å・平均Q0.426230は単一F0枝の記述であり、F2効果ではない。

統計単位は同じr01由来の2軌跡。34参照・相関frameは独立標本でない。全量8.2–9.4 h点外挿はCI/上界でなく、現実装の反復NPZ解凍を含む。folding成功、CのX独立価値、B2純利益は結論できない。

## D. 技術情報

[再現手順](reproduce.md)、[adapter](../../p1/nmr34_qa.py)、[freeze](freeze.json)、[最終receipt](final.json)。Python3.12.3/NumPy1.26.4/MDAnalysis2.9.0/psutil7.0.0。新学習seedなし、人工tensorのみseed34。既存科学seed・重み・データは変更しない。

DCDは512frame block。全R/Q/countを軌跡ごとに保存、proper Kabsch/strict8Å/gap≥3。flock、fingerprint、排他的成功receipt、0.1s資源監視。正常終了、lock非保持、failureなし、再試行0。成功出力の上書き・再実行を禁止する。

## E. 遺留事項・審査点

1. 詳細契約の内訳別計時、8Å近傍pair表、ensemble-min窓集計・Q at argmin列は未保存。逐frame行列はあるが、追加処理を自動実行していない。
2. 原N1の窓ID独立リストはない。旧time/validからIDを再構成し旧件数・M1要約を照合したという証拠範囲を維持する。
3. CPU単worker/数値thread設定と1core affinityは別。監視threadを含むCPU時間がwallより長い。freeze RSS=0は未取得、0メモリではない。
4. 参照ごとのQ分母差、min34選択による下方変化、1根/F0のみの一般化制限を確認する。
5. 圧縮率/全量費用ばらつき・環境変動は未知。反復解凍除去等は数値同値性と独立承認が必要。
6. MDAnalysis警告は端末で観測、完全stderrファイルは未保存。receiptとSHAは保存済み。原物理/学習資格の問題は本QAで解決しない。

## F. ファイル索引

|資料|内容|
|---|---|
|[review-dossier.md](review-dossier.md)|数式、全結果、費用、限界、未実施を含む完全報告|
|[execution-approval.md](execution-approval.md)|研究者の限定許可と凍結|
|[freeze.json](freeze.json)|入力SHA、CAキー、版、fingerprint、人工検査|
|[final.json](final.json)|2成功receipt、前後SHA、全体費用|
|[delivery-audit.json](delivery-audit.json)|出力全索引/SHA/byte、lock、原9archive存在/サイズ|
|[history-windows.csv](history-windows.csv)、[downstream-windows.csv](downstream-windows.csv)|各816行、全34参照×24条件|
|[reference-contacts.json](reference-contacts.json)|34接触集合、分母、自己検査|
|[reference-geometry.csv](reference-geometry.csv)|34×34 proper RMSD|
|[cost-estimate.json](cost-estimate.json)|単位別/混合外挿、出力本体算式|
|[reproduce.md](reproduce.md)|論理パスと再現/保管境界|
|[static-check.json](static-check.json)|表・JSON・リンク・旧証拠不変の静的検査|
|[remote-readback.json](remote-readback.json)|交付commit全変更ファイルの全文確認|

## G. 次段階

研究者/ChatGPTが本報告の限定PASSと未保存項目を審査する。全272の承認、必要なら最適化adapterの限定再資格、予算・分割方法を決定する。いずれもPROPOSEDであり、この引継ぎを新実行許可としない。全量NMR34、MD、訓練/推論、LOF、R0、C/B2/S3を開始せず停止する。
