# 再現手順と証拠の所在

この手順は新しい計算許可ではない。再実行には共有資源の調整が必要。GPUを使わず、既存16 nsのみを解析する。

1. GitHub mainのAGENTS・全体記録・交接と本輪の事前計画を読む。事前計画commitは `94d96bc24c8c35dca7f08452809b2a35239a9da3`。計画push/遠隔回読の後に解析した。
2. 本人プロジェクト内の隔離環境にPython 3.12.3、NumPy1.26.4、SciPy1.15.2、MDAnalysis2.9.0、OpenMM8.5.2（CUDA追加packageなし）、matplotlib3.10.1、psutil7.0.0を復元する。完全なlockも参照。システム/グローバル環境を変更しない。
3. GQ-R1原データ、R1 analysis-final-v2の8特徴配列、公開したR1のSHA manifestを用意する。大DCDと配列はGitHubに含まれない。本人領域の論理ID `runs/gq-r1-20261026` と `artifacts/gq-r1-20261026/analysis-final-v2` に対応する。原子対応は504原子/28残基、325距離、54角。
4. サーバで `CUDA_VISIBLE_DEVICES=-1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 taskset -c 0,1,2 <CPU環境>/bin/python -B -m unittest discover -s tests/p1 -p test_gq_r2.py -v`。境界テストは科学的有効性の証明ではない。
5. 本人領域の構成に合わせ、`<CPU環境>/bin/python -B -m p1.server.gq_r2_run --project <PROJECT> --phase quality`。続いてcalibration、evaluate、controls、figuresをこの順に個別起動する。監督プログラムはCPU使用率・メモリ・GPUプロセス数を各段階前に読取り、CPU0/1/2、数値スレッド2、2400秒/RSS16GiBの上限を適用する。GPUを不可視にし、OpenMM SystemのXMLを読むだけでContextを作らない。
6. 出力済み段階は上書きしない。失敗JSON/標準エラーを保存し、修正は記録する。別環境への再現では、新しい明示的出力先を使うよう監督側の論理パスも版管理する。
7. 入力SHA、ソースSHA、実行記録、全感度CSV、全負対照、科学図を照合する。大配列は本人領域と許可済みローカルバックアップに保存し、Macでは科学値や図を生成しない。
8. 原R1 manifest全件の再照合、出力とアーカイブSHA照合、環境/キャッシュのみの限定清掃、他人のプロセスに触れていないことを確認し、GitHubに小規模証拠と報告を同期する。

数値APIの根拠：[MDAnalysis 2.9.0の二面角解析](https://docs.mdanalysis.org/2.9.0/documentation_pages/analysis/dihedrals.html)。この資料は角度の計算と原子選択を説明するが、本輪の経験的品質閾値やεを推奨するものではない。OpenMM拘束は保存Systemの実値を読み取る。

証拠整理用 `gq_r2_publish.py --project <PROJECT>` は最終版では `public-v2` に出力する。public-v1は私人ディレクトリを含むログの公開前草稿として本人領域に保持し、GitHubにはpublic-v2の脱敏版だけを置いた。原ログと初回失敗JSONはアーカイブに残す。公開SHAは脱敏後ファイルに対する値であり、原ログSHAと混同しない。

## 最終保存・清掃

224,340,738 byteのR2全証拠アーカイブはサーバと許可済みMacバックアップでSHA-256 `e81b85eaffec8356fd502b918726eb9bcc1162ec88e34d11fe6d8dda5b8d4ffc` が一致した。207のエントリに初回失敗、全配列、精確なソース版を含む。原R1の大DCDは別の検証済みR1アーカイブに保持する。

[バックアップ確認](../执行证据/2026-10-26-gq-r2/backup-verification.json)と[清掃確認](../执行证据/2026-10-26-gq-r2/cleanup-verification.json)はアーカイブ後の独立した閉鎖記録である。`public-sha256.json` はサーバで生成した公開解析材料のmanifestで、この二つの後付け閉鎖記録まで含む自己参照manifestではない。本人のR2環境と指定キャッシュだけを削除し、原データ/配列/ログ/アーカイブを残した。
