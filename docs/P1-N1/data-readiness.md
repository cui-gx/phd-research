# 既存N1データ・計算準備チェックリスト

本輪は数値的な軌跡再評価ではない。byte SHAとDCDのCORD/NSET header、PDB CA文字列対応だけを読んだ。[メタデータ監査](metadata-audit.json)、[272ファイル表](MD-file-audit.csv)。

## 全対応

- [branch-index.csv](branch-index.csv)：原B1行列から240行を転記。root/state/F0–F2、training block/seed、MD block/seed、原実行順、model task/checkpoint/親SHA、起点座標SHA、source global frameと元DCD、状態凍結SHAを含む。新native列はNOT_EXECUTED、用途POST_HOC_EXPLORATORY。
- [state-index.csv](state-index.csv)：16決定状態のM0/二学習seed/三MDseed/共通履歴の対応。
- [history-index.csv](history-index.csv)：8根×4連続2ns=32履歴。S4は最初の2段、S8は4段。計64ns。同根状態は相関する。
- 各stateの下流F0は3本、F1/F2は各2学習seed×3MDseed=各6本。16×(3+6+6)=240本、合計960ns。F0には追加training seedがなく、model_seedはM0生成seed。F0を2回複製して独立データにしない。
- 既報の2,048,000保存frameは32×4000＋240×8000というheader/既存メタデータに基づく数であり、今回座標から科学値を得た数ではない。

## 実在とSHAの準備点検

272 MDの原result/request、DCD/initial.pdb byte SHA、28CA key対応とheader frame数は一致。80model checkpointはbyte hashだけでload0。96ranking.npzもbyte hashのみ。9archiveの存在/sizeを確認し、全量archive SHAを今回再計算したとはしない。元状態・branch quality・old time filteringの科学監査はB1/R1/Q0の既存証拠を継承し、N1再実装で再度対応確認する必要がある。

[参照監査](reference-static-audit.json)：model1、全34model、unfoldedに各28CA。全34の文字列CA keyは同じ。coordinate geometry・native pair数・NMR間RMSDはNOT_MEASURED。元N0の「34参照未入手」という残件は、既存固定ファイルの静的確認についてのみ解消した。最新版RCSBとの全座標一致や原著native referenceの同一性は未確認。

## 保存潜在データの利用可能性

|用途|存在|本輪で行ったこと|新たな承認が要ること|
|---|---|---|---|
|B1 decision候補→固定M0/F1/F2潜在|96 ranking NPZ（16 F0-repeatを含む）、sourceでembedding/frame_ids保存確認|byte SHA・ソース静的確認。配列を開かない|native評価承認後のID join/作図。NPZ各frame対応の最終点検|
|240下流frameの潜在|一括推論結果は未保存|存在すると推測しない|全下流の色付きlatent図には新forwardが必要。今回不可|
|L2候補潜在|別experimentの156endpoint|既報参照だけ|旧B1modelへ流用不可。全新Top1のMDはNOT_OBSERVED|
|旧幾何指標|B1/R1全CSV・距離/品質/時刻配列|CSV索引と旧契約を維持|native指標とのjoin/相関を実行する新CPU承認|

## 環境・資源

既存runtimeのmetadata照会：OpenMM8.5.2、MDAnalysis2.9.0、Torch2.7.1+cu128、NumPy1.26.4、sklearn1.6.1、mdlearn0.0.10a1。importlib.metadataで確認し、GPU/CVAEをloadしない。接続時低負荷、RAM約116GiB以上available、home空き約826GiB、GPU compute processなし。本輪はGPU使用0で、空き状態を将来予約済みの証拠にしない。予約表を直接新たに確認したとは言わない。

## 未完了ゲート

N1 scientific evaluatorのDCD reader/quality join/all windows/ensemble batch処理は未実装・未実行。今回の純粋関数と人工22testsはその数式部分だけの工程資格で、実軌跡の原評価再現や科学合格ではない。L2レシピ採択、P物理準備、hit/dwell、第二Q参照集合、将来policyの承認は残る。
