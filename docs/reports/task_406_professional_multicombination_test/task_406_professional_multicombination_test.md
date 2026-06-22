# Task 406C - Professional Multi-Combination Continuation Test

## Quant Expert Report
### Data And Identity Integrity
- Exact `lifecycle_id` labels only.
- Unlabeled lifecycles are preserved and not treated as negatives.
- Combination assignment uses entry-time state only.

### Decision
task_406c_verdict,evaluation_status,predeclared_combo_count,assigned_combo_lifecycle_rows,combo_with_labeled_rows_count,fallback_used_count,unlabeled_treated_as_negative_count,best_positive_combo_id,best_positive_combo_avg_net_return,label_used_for_assignment_flag,inferred_matching_used_flag,leakage_audit_pass_flag,deployment_claim_flag,strategy_acceptance_status
COMPLETE_PASS,PROFESSIONAL_MULTICOMBO_EXACT_LABEL_DIAGNOSTIC,26,26688,23,0,0,C11,0.001651131455658375,0,0,1,0,DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

### Quality
professional_combo_id,professional_combo_name,combo_type,lifecycle_count,add_scale_success_rate,false_positive_rate,entry_reduce_failure_rate,avg_net_return_from_entry,compounded_net_pnl
C01,broad_leader_early_clean,positive_selection,514,0.2782101167315175,0.7217898832684825,0.35019455252918286,-0.0013746181145024197,-0.5949919660323988
C02,broad_leader_momentum_clean,positive_selection,138,0.13043478260869565,0.8695652173913043,0.38405797101449274,-0.0015650066756871307,-0.24638683554655583
C03,broad_leader_momentum_expansion,positive_selection,79,0.20253164556962025,0.7974683544303798,0.34177215189873417,-0.0020342883784621934,-0.17263954320444708
C04,broad_leader_pullback_clean,positive_selection,179,0.2346368715083799,0.7653631284916201,0.3240223463687151,-0.0015127222903102175,-0.2780000350952905
C05,broad_participation_early_clean,positive_selection,969,0.19607843137254902,0.803921568627451,0.33126934984520123,-0.0026916859418860896,-0.943582464155295
C06,broad_participation_momentum_clean,positive_selection,318,0.12264150943396226,0.8773584905660378,0.34591194968553457,-0.003581652476686932,-0.7028917099357068
C07,broad_participation_momentum_expansion,positive_selection,124,0.20967741935483872,0.7903225806451613,0.3225806451612903,-0.002365838763763704,-0.276938553625768
C08,broad_leader_early_neutral_cost,positive_selection,445,0.2202247191011236,0.7797752808988764,0.3775280898876405,-0.003394761076136316,-0.8126557205988232
C09,broad_leader_momentum_neutral_cost,positive_selection,124,0.13709677419354838,0.8629032258064516,0.3951612903225806,-0.003720169707172909,-0.3815958849463643
C10,mixed_leader_early_clean,positive_selection,618,0.22330097087378642,0.7766990291262136,0.3592233009708738,-0.004324796469646438,-0.940415464406685
C11,mixed_leader_momentum_clean,positive_selection,180,0.17222222222222222,0.8277777777777777,0.28888888888888886,0.001651131455658375,0.23064399032813054
C12,mixed_leader_pullback_clean,positive_selection,243,0.1646090534979424,0.8353909465020576,0.30864197530864196,-0.0034892687829539385,-0.5985058965446349
C13,narrow_leader_early_clean,selective_watch,28,0.14285714285714285,0.8571428571428571,0.35714285714285715,-0.008845356367298125,-0.22478302975188014
C14,narrow_leader_momentum_clean,selective_watch,3,0.0,1.0,0.6666666666666666,-0.0136650759046277,-0.040487982426005376
C15,broad_isolated_pullback_clean,selective_watch,4,0.25,0.75,0.0,-0.005079255565618225,-0.02053687983373731
C16,mixed_participation_early_clean,selective_watch,794,0.16750629722921914,0.8324937027707808,0.336272040302267,-0.0038239698216296636,-0.9607868397610337
C17,mixed_participation_momentum_clean,selective_watch,244,0.14344262295081966,0.8565573770491803,0.3401639344262295,-0.0019802653855975523,-0.4109788739554462
C18,broad_leader_mixed_entry_expansion,selective_watch,24,0.2916666666666667,0.7083333333333334,0.20833333333333334,0.003266493445591004,0.0740070765940064
C19,weak_late_weak_theme,false_positive_suppression,25,0.16,0.84,0.36,-0.005746813352273648,-0.14035050942891392
C20,weak_late_isolated,false_positive_suppression,78,0.14102564102564102,0.8589743589743589,0.44871794871794873,-0.004788990838600347,-0.3287040124454367

## No-Background Decision-Maker Report
- We tested a predeclared library of professional continuation combinations.
- This is diagnostic only, not deployment-ready.
- Missing raw quote/status data still limits real trading claims.

## Mandatory Final Verdict
```text
Measured facts:
- See task_406c_decision.csv and professional_combo_quality.csv.

What we can conclude:
- Predeclared combinations can be evaluated with exact labels and no inferred lifecycle matching.

What we cannot conclude:
- We cannot claim deployment-ready alpha.

Recommended next action:
- Review source-complete positive combinations and raw-source gaps before policy simulation.

Deployment status:
- NOT_DEPLOYMENT_READY
```