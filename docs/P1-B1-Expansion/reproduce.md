# 今回の報告統計だけを再照合する手順

2026-10-27。今回実行したのはGPU不可視の既存表CPU照合だけである。下のMD起動手順は歴史的な全実験復元方法であり、現在の追加計算許可ではない。転送や全実験を自動再開しない。

```sh
CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1   <ENV>/bin/python -B p1/report_review_audit.py   --input-dir <PUBLIC_V1> --output-dir <NEW_REVIEW_OUTPUT>
```

`<PUBLIC_V1>`は許可保管先の既存公開表一式、出力は必ず未存在の新領域。共有CPU/メモリ/GPU占有を先に読み取り専用で確認し、許可されたCPUへ制限する。インストール、MD、学習、GPU推論は呼ばない。コード版4771d2197af3e90609375ff3f8708cc2d3797395、使用入力/コードSHA、Python/NumPy版、全照合数は[report-review-statistics.json](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json)にある。既存432要約の全区間も同じbootstrap乱数で復核する。結果が不一致なら元表を変更せず失敗ログを残す。

Macではこの数値照合を代行せず、取得ファイルのSHA/リンク検査と表示整形のみ行った。raw全体は0/9Mac完全複製で、standaloneな原データ外部再現を認定しない。

## 以下は既定科学実験の復元仕様（履歴・別承認が必要）

# 再現・途中再開

これは新しい実行許可ではない。最新AGENTS、研究者の範囲承認、共有資源調整を先に確認する。Macで科学計算を代行しない。

1. 元計画060c72e、実装c79b79a、初回GPU前の境界明確化40a911eと完全行列を照合する。実行当時の保存ソース/実依存lockを使い、後のコードを旧manifestへ差し替えない。
2. 本人隔離環境でPython3.12.3、Torch2.7.1+cu128、OpenMM8.5.2/cuda12 plugin、MDAnalysis2.9、mdlearn938cb80、Parsl2025.10.20等を復元する。Pilotの[環境手順](../P1-B1-Pilot/reproduce.md)と本輪lockを参照する。system/driver/global Gitを変更しない。
3. CPU/GPU占有と実許可、空き容量を再検査する。新規runを作るときは別承認/別run IDを明示する。既存runは成功出力のrequest/SHA一致時のみ復元する。
4. `CUDA_VISIBLE_DEVICES=-1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 <ENV>/bin/python -B -m unittest discover -s tests/p1 -p 'test_b1*.py' -v` とR2回帰をサーバで行う。合成fixtureを実MDに数えない。
5. 本人source内で `<ENV>/bin/python -B -m p1.server.expansion_run --phase all`。controller自身はCPU/GPU不可視、子だけ実UUIDへ拘束する。実行コマンド/環境/コードSHAは私有実行記録に保存する。二重起動せず、最初のlockと本人PIDを確認する。
6. first/remaining/finalは同じ固定runの段階入口。`all`は先頭の予定枝を検査後、全行列、解析、公開証拠、根別archiveまで進む。成功出力を再計算せずSHAを照合する。途中失敗は原attemptを保ち、原因を確認して同条件の新attemptを登録する。科学条件が変わるなら停止する。
7. `status.json`、原イベント、root/state/task IDとGPU診断を見る。SHA/公開順序/資源競合/容量違反を無視して続行しない。接続失敗時はVPNを依頼し、別原因や別ホストを推測しない。
8. 完了後、raw DCD/model/配列/原ログは本人serverと検証済みMac backupへ保管する。公開JSONでは不要なパス/UUIDを除くため、raw SHAは私有原ファイルに対する参照であり脱敏後JSONのSHAではない。public manifestは公開版自身のSHAを示す。
9. 双端backup検証後に登録環境/キャッシュのみ清掃し、全結果/失敗/日語報告/交接記録をGitHubへ通常push・遠隔回読して停止する。B2/C正式予測/S3へ自動的に進まない。

## 既存資格資産への依存

現在の適応は既存GQのNoCutoff `system.xml` と、R2の固定幾何テンプレート `synthetic-source.npz`（SHA53bd1ca4f33765a9382a605edacec9c6ce4e8dcd660b7848e0ca85bef6dd3d50）を照合に用いる。後者の元座標を取り除き、原子対応/拘束/手性の定義だけを再利用する。旧MDを本輪の学習やA0へ混ぜることとは異なる。

新規環境では旧GQ/R2の検証済みarchiveからこれらの依存資産も復元する必要がある。本輪の新しいコードだけをcloneすれば全入力が自動取得できる、というstandalone公開artifactの資格はまだ主張しない。旧資産は保管・SHA照合を続け、公開配布の整理は別作業とする。
