# 再現・復旧・保管の境界

研究基準33f6aa9e5071af18d7b841b61367507d2113b834、実行凍結7c24237117c17d2d6c1a629b3ece9ea3529be978。[計画](analysis-plan.md)、[入力行列](manifest.json)、[設定](config.json)と実装SHAを使用する。

内部host名や個人の絶対パスは公開しない。許可projectをP、独立batchをP/artifacts/nmr34-full-20261031-v1、同batchのcode/bundle/outputを使用する。bundleにはmanifest/config、旧freeze、geometry-native-joined.csv、N1-root-summary.csv。既存B1 Python環境を再利用し追加インストールしない。

```text
PYTHONDONTWRITEBYTECODE=1 PYTHON code/nmr34_full.py supervise P BUNDLE OUTPUT
```

この記述は新しい再実行を許可しない。初回から同じOUTPUTへ再起動すると拒否する。復旧は研究者が明示した承認IDを`--resume-approval ID`に渡した場合のみ候補となる。fingerprint/全入力SHA/成功receiptと全出力SHA/累積spentを照合し、成功単位はskipする。部分単位は承認付きでfailed-attemptsへ保持して同条件で再試行する。未確定budget segment、残予算なし、成功SHA不一致では停止する。新規dirやbatch分割で時間枠をリセットしない。

対象rawは常に読み取り専用。全chunk/窓ID/品質metadata/完全stdout-stderr/budgetログと成功receiptは許可サーバへ残す。GitHubには全compact結果、根/状態/モデル/枝/履歴表、図、コードと入出力SHA索引を保存。MacへDCD/モデル重み/全raw archiveを移送しない。原9archiveは削除せず、存在/サイズと実SHA再検証の範囲を報告で区別する。

人工検査は`python -m unittest discover -s CODE -p 'test_nmr34*.py' -v`。実MDを起動しない。geometry相関は旧geometryの0.5ps窓と新native窓の結合であり、geometryの再計算ではない。8根の同じbootstrap drawを全参照へ共有し、参照を追加の独立Nにしない。
