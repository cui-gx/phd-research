# P1-N0：native-RMSD/Q評価契約案と先行研究との差別化

2026-10-30 JST。基準：L2最終科学交付 `65fb2acc8f99774269671ceca25a411ac9ce15cd`、速水先生の助言記録 `docs/研究打合せ/2026-10-30-速水先生-差別化と科学評価.md`。

**現在の状態：DESIGN_ONLY / SCIENTIFIC_REANALYSIS_NOT_APPROVED / NEW_MD_NOT_APPROVED**。本輪でMD・CVAE・推論・DCD読込・LOF・科学数値の再計算は実施しない。旧B1/R1/Q0/L1/L2の指標・コード・結果・原archiveは不変である。

目的は二つ：(1) FSD-EY/1FMEでnative RMSD・native contacts Qを既報と比較可能な有限のfolding-progress診断として厳密に定義すること、(2) DeepDriveMD／Colmenaに対するHPC研究問いの差別化と必要な比較方策を明示すること。

- [native-RMSD/Qの評価契約案](native-evaluation-contract.md)：構造原子対応、主参照、観測窓、統計、漏洩・失敗、事後B1と将来確認試験の区分。
- [先行研究と本研究の差別化表](related-work-differentiation.md)：Bhowmik 2018、Lee et al. DeepDriveMD 2019、Ma et al. FSD-EY 2020、Ward et al. Colmena 2021/2025の既知部分と未検証部分。
- [科学・承認ゲート](decision-gates.md)：どこまで設計固定でき、どの作業に別途計算承認・教師相談が必要か。
- [A–G交接](handoff-to-chatgpt.md)：次レビューの入口。

**実験上の重要な制限**：現在のB1は同一MD量での比較であり、native指標を事後に測っても同一wall-clockでのオンライン調度方策価値を測定したことにはならない。L2は2既知根の学習資格診断で、native hitの実測はない。DeepDriveMD/Colmenaの既知の再訓練・資源制御の範囲と重なる部分を新規性として主張しない。

本契約の選択は実験結果を見る前の**分析方法案**であり、研究者の批准があるまでB1の新たな確証的primary endpointへ昇格しない。B1に適用した場合は必ず post-hoc exploratory と表示する。
