# 図表と本文の点検記録

2026-10-27。DERIVED/技術点検。独立科学審査や原データ外部再現の認定ではない。既存3枚のPNGを目視し、固定版make_figuresの抽出条件と元表、描画対象80点の索引を照合した。PNGを再生成・加工していない。

|既存図|描画点数|元PNG SHA-256|
|---|---|---|
|root-state-effects.png|16|d71476a248255d413259ef6330dab1263928f7df3a3464ad8efe0a7de5409b54|
|feedback-diagnostic.png|16|71b0b907cfc30e73c609f8b934c14f30f34fac06ee033d1797850fe5088d0253|
|multiscale-effects.png|48|c839c2a1bf1aab6b9bd506e8475038506e14421682e8bf617851c8146f6e4d9e|

## 図ごとの解釈と制約

- root-state-effects：state-effects.csvのcomparison=F2-F1、distance_mean_A、burn100 ps/prefix4 ns。16点、根IDごとS4/S8を横に±0.12ずらす。値と符号は[根別表](paired-results.md)に一致。S8のr04/r06は負。error barなしで推定誤差を可視化していない。
- multiscale-effects：同じ主時間条件、added_regions、ε1.5/2/3 Å、**τ5 psのみ**の48点。両時点・全8根を示す。τ0は[全6設定の表](paired-results.md)で必ず併読する。根IDを結ぶ線は時間系列ではない。小さい値や尺度差を隠した証拠として扱わない。
- feedback-diagnostic：同じ幾何効果16点とfeatures.jsonのnew_nonrepeat_fraction_eps2を対応付ける。2panelで縦軸範囲が異なる。各点の根注記は8祖先の識別で、16独立根ではない。回帰・予測性能・条件付きX効果を図から推論しない。

全点の数値は [report-review-statistics.json](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json) のfigure_points、図SHAはfigure_SHA256へ保存した。これは描画ソースの点を照合する監査で、画像pixelから座標を独立に復元した検証ではない。3画像を目視し、ラベル・単位・panel・凡例・負の点・尺度の対応を確認した。図の欠けた不確実性は本文の根bootstrap/乱数表で補足し、存在しないerror barを主張しない。

## 表と根bootstrap

[report-review-cpu-stdout.log](../执行证据/2026-10-26-b1-expansion/report-review-cpu-stdout.log)と [report-review-statistics.json](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json) は、元41,472対応のhigh/low/difference、6,912状態平均、3,456根平均、3,456時間差、432要約の平均/SD/両区間端、9,216ノイズ記録をサーバ単一CPUで再照合した。使用input SHAとコードSHAを同JSONへ保存。相関の最大差1.110223×10⁻¹⁶以外はカテゴリ最大差0。整合したことと方法論が独立に正しいことを区別する。

報告の数値表はサーバ生成値の表示整形で、MacでMD解析・統計推定・新たな図の数値計算は行っていない。四捨五入は原値に遡れる。正/負根数は根平均の符号で、各時点・各seedの正数と混同しない。
