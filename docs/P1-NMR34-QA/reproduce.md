# 再現と保存の境界

実装凍結commit：c33807eec32096d59049bcf48ef3238ffa134906。承認基準：ef0bdd64ca904bfa78afa759d8ebe8077d71105d。旧科学実装は変更せず、既存の純関数を読み取り専用で複製して独立adapterから参照した。

実行環境と全入力SHA/原子キーは[freeze.json](freeze.json)。データの論理的rootをPROJECT、出力をPROJECT/artifacts/nmr34-qa-20261030-v1/outputとする。内部hostや個人の絶対パスは公開資料へ記録しない。

```text
python code/nmr34_qa.py freeze PROJECT BUNDLE OUTPUT
# freezeをcommit/pushし、全文のGit blob SHAを確認してから次へ進む。
python code/nmr34_qa.py run PROJECT BUNDLE OUTPUT
```

BUNDLEのunit-audit.jsonはN1 CPU-v1の固定版。PROJECT/runs/b1-expansion-20261026とPROJECT/artifacts/n1-cpu-20261030-v1/outputをread-onlyで参照する。成功出力の存在時や失敗後は同じOUTPUTへ再実行しない。独立run lock、コード/純関数/入力/保護値のfingerprintを照合する。実行許可の再利用を意味する手順ではない。

CUDA_VISIBLE_DEVICES=-1、OMP/MKL/OPENBLAS/NUMEXPR threads=1。watchdogは資源監視用threadであり科学計算workerは1。0.1秒毎のprocess-tree RSSと出力サイズを確認するため、瞬間ピークに対するOSの厳格なメモリ割当上限ではない。全計算は小blockで進め、時間・メモリ・ディスクの超過でSIGTERMを自身へ送って停止記録を残す。他者のprocessは操作しない。

各frames.npzはN×34のfloat64 RMSD/Q、int16接触count、ensemble-min、1始まりargmin、frame/global ancestral ID、時間、validを含む。下流のglobal IDは単独で全実験一意ではなく、(task_id,frame_id)を主キーとする。window-ids.jsonは元品質と窓条件で選んだID、windows.csvは全34参照/24条件の要約を保持する。全frame原配列はサーバのみ。GitHubにはそのSHA、参照幾何/接触、窓表、receipt、報告を置く。

原7ファイル/単位、N1のframes/windows、M1/NMR34の入力は実行前後でSHA確認する。原9archiveは保持し、今回再圧縮・Mac raw移送・全archive再hashを行わない。既存環境は共通研究資産として保持し、新環境や背景監視サービスは作らない。
