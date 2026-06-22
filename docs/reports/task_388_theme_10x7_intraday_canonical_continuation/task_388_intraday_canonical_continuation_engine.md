# Task 388 - Intraday Canonical Continuation Engine

## Decision
task_388_verdict,intraday_engine_status,available_symbol_count,canonical_event_count,canonical_lifecycle_count,entry_count,add_count,scale_count,reduce_count,exit_count,closed_lifecycle_count,event_ordering_ready_flag,symbol_session_inference_used_flag,threshold_relaxation_flag,next_priority
COMPLETE_PASS,INTRADAY_CANONICAL_STREAM_READY,70,3970,1165,1165,610,375,695,1125,1125,1,0,0,task386_387_on_intraday_stream

## Data Availability
symbol,available_flag,path,missing_reason
AFRM,1,data\raw\us_intraday\AFRM.csv,
AMD,1,data\raw\us_intraday\AMD.csv,
AMGN,1,data\raw\us_intraday\AMGN.csv,
AMZN,1,data\raw\us_intraday\AMZN.csv,
ARM,1,data\raw\us_intraday\ARM.csv,
ASML,1,data\raw\us_intraday\ASML.csv,
ASTS,1,data\raw\us_intraday\ASTS.csv,
AVGO,1,data\raw\us_intraday\AVGO.csv,
BA,1,data\raw\us_intraday\BA.csv,
CEG,1,data\raw\us_intraday\CEG.csv,
COIN,1,data\raw\us_intraday\COIN.csv,
CRM,1,data\raw\us_intraday\CRM.csv,
CRWD,1,data\raw\us_intraday\CRWD.csv,
DDOG,1,data\raw\us_intraday\DDOG.csv,
EMR,1,data\raw\us_intraday\EMR.csv,
ESTC,1,data\raw\us_intraday\ESTC.csv,
ETN,1,data\raw\us_intraday\ETN.csv,
F,1,data\raw\us_intraday\F.csv,
FTNT,1,data\raw\us_intraday\FTNT.csv,
GD,1,data\raw\us_intraday\GD.csv,
GE,1,data\raw\us_intraday\GE.csv,
GEV,1,data\raw\us_intraday\GEV.csv,
GM,1,data\raw\us_intraday\GM.csv,
GOOGL,1,data\raw\us_intraday\GOOGL.csv,
GTLB,1,data\raw\us_intraday\GTLB.csv,
HON,1,data\raw\us_intraday\HON.csv,
HOOD,1,data\raw\us_intraday\HOOD.csv,
IBIT,1,data\raw\us_intraday\IBIT.csv,
IR,1,data\raw\us_intraday\IR.csv,
ISRG,1,data\raw\us_intraday\ISRG.csv,
LCID,1,data\raw\us_intraday\LCID.csv,
LLY,1,data\raw\us_intraday\LLY.csv,
LMT,1,data\raw\us_intraday\LMT.csv,
MBLY,1,data\raw\us_intraday\MBLY.csv,
MDB,1,data\raw\us_intraday\MDB.csv,
META,1,data\raw\us_intraday\META.csv,
MRNA,1,data\raw\us_intraday\MRNA.csv,
MRVL,1,data\raw\us_intraday\MRVL.csv,
MSFT,1,data\raw\us_intraday\MSFT.csv,
MSTR,1,data\raw\us_intraday\MSTR.csv,
NEE,1,data\raw\us_intraday\NEE.csv,
NET,1,data\raw\us_intraday\NET.csv,
NOC,1,data\raw\us_intraday\NOC.csv,
NOW,1,data\raw\us_intraday\NOW.csv,
NVDA,1,data\raw\us_intraday\NVDA.csv,
NVO,1,data\raw\us_intraday\NVO.csv,
OKTA,1,data\raw\us_intraday\OKTA.csv,
ORCL,1,data\raw\us_intraday\ORCL.csv,
PANW,1,data\raw\us_intraday\PANW.csv,
PH,1,data\raw\us_intraday\PH.csv,
PLTR,1,data\raw\us_intraday\PLTR.csv,
PWR,1,data\raw\us_intraday\PWR.csv,
PYPL,1,data\raw\us_intraday\PYPL.csv,
REGN,1,data\raw\us_intraday\REGN.csv,
RIVN,1,data\raw\us_intraday\RIVN.csv,
RKLB,1,data\raw\us_intraday\RKLB.csv,
ROK,1,data\raw\us_intraday\ROK.csv,
RTX,1,data\raw\us_intraday\RTX.csv,
S,1,data\raw\us_intraday\S.csv,
SNOW,1,data\raw\us_intraday\SNOW.csv,
SOFI,1,data\raw\us_intraday\SOFI.csv,
TEAM,1,data\raw\us_intraday\TEAM.csv,
TER,1,data\raw\us_intraday\TER.csv,
TSLA,1,data\raw\us_intraday\TSLA.csv,
TSM,1,data\raw\us_intraday\TSM.csv,
UBER,1,data\raw\us_intraday\UBER.csv,
VRT,1,data\raw\us_intraday\VRT.csv,
VRTX,1,data\raw\us_intraday\VRTX.csv,
VST,1,data\raw\us_intraday\VST.csv,
ZS,1,data\raw\us_intraday\ZS.csv,

## Event Ordering
same_timestamp_multiple_events,transition_after_exit,event_ordering_ready_flag
0,0,1