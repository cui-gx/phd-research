# 証拠附表の読み方

すべて2026-10-31の既存成果照合。新しい座標評価・bootstrapはない。

- [table-audit.json](table-audit.json)：285成果SHA、全階層算術、行数、接触分母、実CPU費用。
- [main-all-contrasts.csv](main-all-contrasts.csv)：35系列×9指標×3対比×4段階=3,780行。原主窓の保存値を転記。CIは再推定していない。
- [main-root-extract.csv](main-root-extract.csv)：model1/min34の全根・主窓・全3対比。共有F0の階層を保持。
- [all-window-direction-extract.csv](all-window-direction-extract.csv)：全35系列×24条件×4段階のF2−F1最小RMSD保存要約。
- [window-metadata.csv.gz](window-metadata.csv.gz)：272既存windows.jsonからの全228,480行転記。
- [metadata-source-sha256.json](metadata-source-sha256.json)：上記272元JSONの相対出典、byte長、実SHA。旧delivery-audit索引と一致。
- [transfer-manifest.json](transfer-manifest.json)：サーバから移した附表とscriptのSHA、取得時のread-only lock一覧観測、Python版。
- [check.stdout](check.stdout)・[check.stderr](check.stderr)：照合実行ログ。stderrは0 byte。旧科学実験のログではない。

## metadataの結合契約

旧結果のディレクトリ番号をreferenceへ変換する。`results/1`は`1`、`results/NMR34_MIN`は`NMR34_MIN`。キーは `(task_id, reference, window)`。history.csvまたはbranches-s4/s8.csvへ1対1で結合する。window文字列をfloat時刻で丸め直さない。

`total`は窓/抽出位相で選ばれた点数、`valid`はさらに元品質maskを適用した点数。`window_status`は既存N1から継承したCOMPLETE/INCOMPLETE_WINDOW。`argmin_frame`は**0始まり・軌跡内のframe ID**で、global frame IDでもpsでもない。時刻は元のmetadata.npzまたは旧N1 frames.npzからIDで参照する。整数frame×0.5という式で元float時刻を置換しない。本輪はそれらNPZをdecodeしていない。

35系列で同じ品質maskを共有していても、各系列のargminは異なり得る。min34のargmin_frameは軌跡内の最小時点であり、同時点のNMR参照番号k*とは別の変数である。k*の逐frame配列は元chunkに保存済みで、本附表に新たなargminモデルを推測して追加していない。

2 ns歴史の4 ns窓には数字があるがINCOMPLETE_WINDOWである。完全4 ns軌跡の成果・滞在時間とは扱わない。元コードでは下流効果の集計から歴史行が分離されている。全転記窓でvalid=totalという観測は、元品質規則の通過を意味するだけである。
