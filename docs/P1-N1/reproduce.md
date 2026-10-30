# N1準備の再現と未実施範囲

本書は新科学計算を許可しない。全旧資料を読み取り専用で使い、新しい出力先でのみ監査する。

## 資料・対応表

基準73b93ed224b45b3f62e99e92447241e9af096d8aのB1 experiment-matrix.csv/json、task-manifest.json、models.jsonから、branch-index240行/history-index32行/state-index16行を生成した。model taskはF0→M0、他はF1-t1/2・F2-t1/2へ対応し、requestのmodel SHAとmodels.jsonを照合する。これは既存メタデータの転記で、科学量の新解析ではない。[入力SHA](evidence-input-sha256.json)。

## 人工単体検査だけを行う場合

既存のNumPy1.26.4環境とrepository rootでGPU不可視/単threadを指定し、`python -m unittest discover -s tests/p1 -p test_n1_native_metrics.py`を実行する。実データを使わない22testであり、原DCD evaluatorの受入れではない。今回実行では専用folderに同じ3ソースを配備し、importlibで純粋関数を登録して同じtest suiteを実行した。配備SHAは[人工test receipt](synthetic-test.json)と[transfer verification](server-transfer-verification.json)。共有環境へpip installやsystem変更はしない。

## メタデータ監査

`p1/n1_metadata_audit.py PROJECT TASK_MANIFEST NEW_OUTPUT`は、PROJECTの既存B1原領域を読む。CUDA_VISIBLE_DEVICES=-1、OMP/MKL/OPENBLAS threads1、PYTHONDONTWRITEBYTECODE=1を指定した。出力は新規作成専用で、成功directoryを上書きしない。

読み取るものはrequest/result JSON、DCD byte/hashと最初100bytes header、initial PDBのCA文字列、checkpoint/rankingのbyte SHA、archiveの存在/size、importlib.metadataのversion。DCD座標、NPZの科学array、torch checkpointのloadを行わず、MDAnalysis/OpenMM/MLを実行しない。300秒/RSS2GiB保護で停止する。[metadata](metadata-audit.json)。今回は8.725秒で完了した。ファイルhashはchunk1MiBで読んだ。科学評価の計算費用をこの秒数から外挿しない。

## 次の科学実装に残すもの

native契約が採択されても、新しい限定実行承認が必要。DCDからのÅ/atom/frame/time/quality対応、native全表・34感度・全窓・根統計・latent-label join/作図、cost測定、出力SHAを独立したN1 scientific adapterへ実装する。今回そのreader/実行器を作っていない。原科学コードを改変しない。

staticな公開検査は`research-workflow/n1-static-validate.py`。旧404SHA、索引件数、全対応、未承認状態、相対リンク、実配備source/転送SHAを検査する。native科学値を出さない。全原archive保持、Mac raw複製免除。最終report/sourceは内容commitとGitHub回読の受領記録で特定する。

CSVは転送元のCRLFとbyte SHAを保ち、`.gitattributes`でN1 CSVだけを指定する。初回のGit空白検査はCRLFを行末空白として報告したため、この限定属性で扱いを明示した。CSV本体の正規化や旧証拠の変更は行っていない。
