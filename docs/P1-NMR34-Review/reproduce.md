# 既存証拠の検算と再現境界

基準commit：`e9162145d60c4e88b5b147609b2da0ec20542cb7`。新しい統計解析、原軌跡の評価、科学実験の再実行手順ではない。

## 実施した検算

1. manifest/compact SHA索引/delivery-audit/reference-mapと独立scriptを研究者領域の新ディレクトリへ置いた。既存コードはimportしない。
2. 既存FULL output内のanalysis CSVと272個のwindows.jsonだけを読んだ。DCD、PDB座標、モデル、raw archiveは開かない。
3. 原compact285件を事前/事後にhash照合。窓JSONは旧出力索引のSHAと一致することを確認してmetadataだけ転記。
4. 枝→モデル/状態→根→平均/中央値/SD/符号数を別実装で照合。新しいbootstrap・乱数・p値は0。CIは保存範囲チェックとコード審査のみ。
5. 新出力をサーバに保存し、compact附表と実ログだけをGitHub交付用にコピー。転送後SHAを照合する。

公開用のパス変数を使った呼出し形は以下である。実在するパスは研究者のローカル運用情報を参照し、私的接続情報をここへ記載しない。

```sh
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 check_existing_tables.py "$REVIEW_BUNDLE" "$SAVED_FULL_OUTPUT" "$NEW_REVIEW_OUTPUT"
```

`REVIEW_BUNDLE`にはmanifest.json/compact-results-sha256.json/delivery-audit.json/reference-map.jsonが必要。`SAVED_FULL_OUTPUT`にはanalysis/とunits/が必要。`NEW_REVIEW_OUTPUT`は未存在でなければ停止する。本実行はLinux `ulimit -v 2097152`と外部`timeout 120`を用いた。Python3.12.3、標準ライブラリのみ。GPU不可視、単process、数値ライブラリのthread poolは起動しない。

実測：wall17.331735秒、CPU17.331528秒、peak RSS62,296 KiB。これはレビュー検算費用であり、旧FULLの科学wall711.018秒へ遡及加算しない。全出力は数MiBのcompact資料で、raw backup免除は変更しない。共有資源を実行直前にread-only確認し、他者processへ操作していない。科学失敗・再試行0、検算失敗0、工程起動1回。manifestのMD_blockが文字列である点は実行前の静的schema確認で対応した。

## 原成果の不変性

旧科学実装、凍結結果、旧報告は変更しない。新メタデータは情報を追加する別附表であり、古いCSVの数値を修正しない。原9archiveは以前の保存場所に保持し、本レビューで再圧縮・削除・Mac転送をしていない。

再実行は本書の存在だけで承認されたことにならない。主な検算は既に完了しており、次は研究者/ChatGPTの科学審査で停止する。
