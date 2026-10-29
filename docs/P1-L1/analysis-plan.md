# L1：凍結CVAEの表現資格診断・事前固定計画

2026-10-29。研究者が基準6730e493bddce42fb4d86ed93fab05cc88810268からの限定CPU前向評価を承認した。80最終checkpoint全てを使用し、重み/optimizerを変更しない。新訓練/逆伝播/MD/LOF/候補実行なし。数値診断の下記実装仕様は結果を読む前に固定し、研究者による物理的合格閾値の承認とは区別する。

## 入力と集合

先に全80checkpoint・recipe・exposure・result、16 decision-poolのindices/contacts/featuresを原SHAと照合する。各状態の共通200 validation IDをOLD_VALIDATIONとする。RECENT_HELDOUTはb=2/6nsに対して(b+1.7,b+2.0]nsのvalidフレームからID順の等間隔200点（整数index linspace）を選ぶ。全80対応訓練入力と非重複を検査し、実frame ID/時刻/集合SHAを前向評価前にfreezeする。不足や不一致なら停止する。

全点は決定4/8ns以前。M0公開b以後のRECENT_HELDOUTは事後の汎化診断で、M0のオンライン情報ではない。OLD_VALIDATIONもモデル学習レシピ策定後の既存データであり独立外部テストではない。近い同根の時間相関を認め、200点を独立反復にしない。

## 指標と基線

Yは1×28×28 binary contact、モデルはeval/no_grad、z=mu、sigma=exp(clamp(logstd,max10))。sample単位でBCEを算出する。固定掩码はALL=784要素、NONLOCAL=i<jかつj−i≥3の325要素、LONG=i<jかつj−i≥4の300要素。各BCE/フレームは掩码sum、BCE/有効要素はsum/要素数。torch BCE(reduction=none)を利用し、その数値的log clampを維持する。対角/隣接を主な根拠としない。

共通OLD800の接触頻度p=(count+0.5)/(801)と、各臂の実訓練800頻度を同じ評価集合へ適用する。更に同じ評価集合からのleave-one-out頻度p=(他199点のcount+0.5)/200を非展開可能なtransductive参考として併記する。自己ラベルを使わないが相関点/他の評価点を用いる楽観的比較であり、通常のオンライン基線ではない。全て固定の0.5擬似度数、結果に合わせて調整しない。

KL_n=0.5Σ(mu²+sigma²−1−2log sigma)。batch平均にせずsample平均する。潜在各次元のmu平均/母分散、E[sigma²]、KL、共分散固有値を報告。zero潜在decoderのBCEとmu復号BCEの差を入力コード依存の診断とする。KL/分散について恣意的なcollapse合否閾値を作らない。

同一評価200点の潜在Euclidean距離と既存325対Cα dRMSD[Å]を比較する。全非対角対のSpearmanとk=10最近傍の重複率を記述する。raw muを主表示、評価集合内標準化muを感度として併記する（将来候補選択への変更ではない）。物理近傍と時刻近傍/入力contact近傍の重複も参考にする。近接時刻が一致を説明し得る点を残し、相関対を独立検定に使わない。

F1/F2各二学習seedの近傍重複と潜在距離rank相関で表示安定性を比較し、モデル間のmu座標を直接引かない。M0=F0を一度だけ数え、r07-s4-M0と四子モデルを同じ規則で残す。全16状態/全80モデル/二集合/三掩码を公開する。

## 実行・停止

GPU不可視、1 worker/数値thread/CPU affinity、batch32、RSS2GiB監視、出力1GiB監視、累計2時間で停止・再審査。CPU/Torchのvirtual addressはRSSと区別し、巨大仮想mappingだけを実使用としない。環境・共有利用を実行前に点検する。全checkpointのSHA/optimizer/model digest・有限性と前後不変性を確認。forwardを繰返して同CPU条件のbit一致を検査する。

入力・出力非有限、ID漏洩、SHA不一致、資源超過、既定手法の変更が必要な場合は停止して記録する。モデル構築時の初期値は保存重みで全て置換し、optimizerを構築・実行しない。出力は本人領域の新L1ディレクトリのみ。原80重み・9archiveとB1/R1/Q0証拠を保持しMacへ複製しない。

技術的完全性、再構成の基線差、表示の幾何整合/安定性、科学的探索利益を分けて報告。L1の良否から収束・C・B2や物理資格を認定しない。交付後停止しL2/P/O/C/B2へ進まない。
