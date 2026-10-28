# 図表の定義と表示監査

2026-10-28 JST。図の数値生成はサーバ、最終表示確認はMacで行った。図を画像として開き、日本語glyph、軸名、単位、8根の表示、区間、legend、余白・文字切れを目視確認した。両図とも表示上の欠損なし。これは独立科学審査のPASSではない。

- [全尺度の段階差](all-metric-stage-differences.png)：6連続量・6離散条件を全参照で示す。元は[全尺度表](all-scale-stage-differences.csv)と[根要約](root-summary.csv)。横軸の単位は各panelの定義に従い、Å、degree、無次元Q8、離散領域数を混同しない。離散条件のεはÅ、τはps。探索的区間は8根の配対bootstrapで、保存フレームの標準誤差ではない。
- [根別参照依存](root-reference-decomposition.png)：事前指定100 ps除外/4 ns、主平均幾何距離のΔ21=F2−F1に対するΓ=S8−S4 [Å]。元は[根段階表](root-stage-effects.csv)と[参照分解](reference-decomposition.csv)。共通H2の不一致と8根のばらつきを含める。参照寄与は数値的恒等分解で、Xの因果寄与ではない。
- 小型閲覧表は[compact-view-audit.json](compact-view-audit.json)のfilter/columns/SHAで完全表へ遡れる。全12時間条件は完全表に残し、事前指定の主表示以外を捨てない。小型表での統計再推定は0。

画像SHAと元CSVのSHAは[最新索引](public-evidence-index.json)に記録した。報告編集時も[editorial-audit.json](editorial-audit.json)によりCSV/PNGの不変性を検査した。結果の正負や見やすさを理由に軸・閾値・評価ルールを変更していない。
