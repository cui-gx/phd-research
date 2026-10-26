# 再現手順

これは新たな実行許可ではない。共有資源調整と最新AGENTS/研究者承認が必要。Macでは科学計算を行わない。

## 入力・版

事前計画commit `0c92f6025bcde7a971994d9c515a1184abe83fbe` をpush・GitHub回読後にGPU計算を開始した。実行初版は5ef0e03、M0配備漏れ復元/解析はcbe793a、失敗費用集計修正は1358a86。原manifestとsource-amendmentに正確なファイルSHAを保存し、古いソース指紋を上書きしない。

既存vendor mdlearn938cb80、DeepDriveMD b18dacba、OpenMM8.5.2、MDAnalysis2.9.0、Torch2.7.1+cu128、sklearn1.6.1、Parsl2025.10.20を本人隔離環境へ復元する。実依存lockは証拠を参照。システムCUDA/driver・グローバルGitを変えない。GPU上の実UUID/driverと環境は私人実行記録に保存し、公開版では不要な識別情報を落とす。

## 隔離環境の復元例（サーバのみ）

以下の`PROJECT`と`ENV`は研究者本人の承認済み領域を指定する。共有システムへインストールしない。Python 3.12.3で作成したvenv内のpip 25.0.1を使用した。実行時のpip初期導入元URL/SHAとinstall.logは完全アーカイブに保存している。新しい環境にpipがない場合、既存の検証済みbootstrapを使い、system Pythonへpipを追加しない。

```sh
"$ENV/bin/python" -m pip install setuptools==75.8.2 wheel==0.45.1
"$ENV/bin/python" -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
"$ENV/bin/python" -m pip install --only-binary=:all: -r "$PROJECT/source/configs/p1-server-requirements.txt" 'openmm[cuda12]==8.5.2' matplotlib==3.10.1 psutil==7.0.0
"$ENV/bin/python" -m pip install --no-deps --no-build-isolation "$PROJECT/source/vendor/mdlearn-938cb80"
"$ENV/bin/python" -m pip check
"$ENV/bin/python" -m pip freeze
```

実験で確定した全バージョンは公開requirements.lock.txtと照合する。mdlearnはPyPI同名パッケージへ置き換えない。全配布wheelのSHAを固定した環境イメージではないので、将来の完全なバイナリ再現は保証しない。現環境の記録と実験ソースを保管することと、将来同じ乱数結果を得ることは異なる。

実行時コードの再監査では、実行当時のcommitまたはアーカイブ内の保存ソースとexecuted-source-sha256を使う。最終公開版では例外メッセージのみを校正しており、そのファイルをそのまま旧manifestへ差し替えない。新規再現runを開始する場合も、新run名・承認・版を登録し、旧runへの再投入はしない。

## 実行

1. 対象1 GPU/CPU/メモリ/予約許可を確認し、入力・固定コードのSHAを照合する。
2. CPUで `CUDA_VISIBLE_DEVICES=-1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 taskset -c 0,1,2 <ENV>/bin/python -B -m unittest discover -s tests/p1 -p test_b1_pilot.py -v` とR2回帰テストを実行する。
3. 既存本人プロジェクト配置のsourceで `<ENV>/bin/python -B -m p1.server.b1_run --stage history`。このPilotは固有のrun名を使う。既存結果を上書きしない。新しい再現runでは、当該承認と出力パスを明示版管理して全条件を同じ条件で生成する。
4. 旧歴史→品質→旧pool→M0→checkpoint新区間→品質→最終pool→state-freezeを確認。学習容量・公開順・原子対応・checkpointSHAが不正なら停止する。
5. 同じ制御入口の `--stage branches`。1worker Parslが既存科学関数を呼ぶ孤立子プロセスを順次実行する。4更新、同一候補の推論/再推論、6下流MDと品質処理。実行途中に学習設定・科学コード・候補を変えない。
6. 全6枝成功後、`CUDA_VISIBLE_DEVICES=-1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 taskset -c 0,1,2 timeout 2400 <ENV>/bin/python -B -m p1.server.b1_analysis`。CPU解析で共通A0全点距離、全感度、対応差、図を作る。大配列はGitHubに置かない。
7. 全入力/weight/optimizer/曝露/選点/軌跡/結果のSHA、全コスト、失敗と修正を照合。原S1/S2/GQ/R2を保護し、本人領域の完全アーカイブと許可済みMacバックアップを照合する。
8. 一時環境・キャッシュ・本人の残プロセスだけを清掃し、日本語報告・小規模証拠をmainへpush/遠隔確認する。次の状態/正式B1/B2/C/S3を自動開始しない。

## 失敗からの復元

最初のM0はヘルパー未配備で学習前に失敗した。同じ条件のM0-attempt2へ対応表で復元した。旧失敗ディレクトリを移動/削除せず、attempt-mapとsource-amendmentで追跡する。成功済みタスクのSHAが一致するときだけ再利用する。修正は同条件の工学修復に限定し、科学条件が変わったら比較を止める。

全trajectory/checkpoint/embedding/完全順位/optimizer/RNGは本人サーバとバックアップ（完了状態は検証記録を参照）に保存する。GitHubはコード・報告・有限表・ハッシュ参照であり、生データの公開配布ではない。

生eventsのtaskは論理名である。失敗M0と復元M0-attempt2は異なるrequest SHAとattempt-mapで区別する。元イベントを書き換えず、監査ではrequest/result SHAと実taskディレクトリを結び付ける。

## 本Pilotの保管・清掃実績

2026-10-26、完全原データアーカイブ581,720,607 bytesのサーバ/Mac双方SHA-256が一致した（`07acba4d1e973f7eaaf6be55ce3e56cc8d8303a694e9e996654d29678886a90a`）。8 MD軌跡、5モデルcheckpoint、初回失敗、保存ソース、全解析配列を確認した。本人の登録済み一時環境・キャッシュだけを削除し、B1の原データ388ファイル、旧S1/S2 336・GQ 263・R2配列16と既存R2アーカイブを再照合した。原始証拠・モデル・アーカイブは保管する。追加科学計算は行わず、研究者審査を待つ。

[バックアップ検証](../执行证据/2026-10-26-b1-pilot/backup-verification.json)、[清掃検証](../执行证据/2026-10-26-b1-pilot/cleanup-verification.json)。公開SHAの当初39ファイルはそのまま保ち、後から取得した閉鎖記録はdelivery-manifest.jsonで別に照合する。
