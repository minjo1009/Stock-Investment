# Task T092 - Signal Alignment Audit

## 1. Summary
- total comparisons: 88
- match / minor / major: 88 / 0 / 0
- final status: PASS

## 2. Test Snapshot
- evidence run: 20260424_173938_pilot_run.json
- runtime snapshot timestamp: 2026-04-24T17:39:03.451719Z
- comparison cutoff timestamp: 2026-04-24T17:39:38.632526Z
- symbols: MSFT, AMZN, AMD, NVDA, AVGO, GOOGL, AAPL, META, TSLA, QCOM, NFLX, COST

## 3. Runtime Signal
- selected symbols: ['MSFT', 'AMZN', 'AMD']
- selected sectors: ['XLK', 'XLY']
- signal decision: BUY (AMD)

## 4. Backtest Signal
- selected symbols: ['MSFT', 'AMZN', 'AMD']
- selected sectors: ['XLK', 'XLY']
- signal decision: BUY (AMD)

## 5. Detailed Comparison

| Layer | Field | Runtime | Backtest | Status |
|------|------|--------|----------|--------|
| Data Layer | AAPL.close | 269.67999267578125 | 269.67999267578125 | MATCH |
| Data Layer | AAPL.ma20 | 259.2749984741211 | 259.2749984741211 | MATCH |
| Data Layer | AAPL.ma50 | 260.1693994140625 | 260.1693994140625 | MATCH |
| Data Layer | AAPL.ma200 | 253.00654922485353 | 253.00654922485353 | MATCH |
| Data Layer | AAPL.breakout_high_20 | 274.2799987792969 | 274.2799987792969 | MATCH |
| Feature Layer | AAPL.breakout_condition | False | False | MATCH |
| Feature Layer | AAPL.ma_condition | False | False | MATCH |
| Data Layer | AMD.close | 289.0 | 289.0 | MATCH |
| Data Layer | AMD.ma20 | 238.67650146484374 | 238.67650146484374 | MATCH |
| Data Layer | AMD.ma50 | 216.76480041503908 | 216.76480041503908 | MATCH |
| Data Layer | AMD.ma200 | 204.6383999633789 | 204.6383999633789 | MATCH |
| Data Layer | AMD.breakout_high_20 | 287.6099853515625 | 287.6099853515625 | MATCH |
| Feature Layer | AMD.breakout_condition | True | True | MATCH |
| Feature Layer | AMD.ma_condition | True | True | MATCH |
| Data Layer | AMZN.close | 253.2400054931641 | 253.2400054931641 | MATCH |
| Data Layer | AMZN.ma20 | 227.854500579834 | 227.854500579834 | MATCH |
| Data Layer | AMZN.ma50 | 216.43800018310546 | 216.43800018310546 | MATCH |
| Data Layer | AMZN.ma200 | 226.00764999389648 | 226.00764999389648 | MATCH |
| Data Layer | AMZN.breakout_high_20 | 256.17999267578125 | 256.17999267578125 | MATCH |
| Feature Layer | AMZN.breakout_condition | False | False | MATCH |
| Feature Layer | AMZN.ma_condition | True | True | MATCH |
| Data Layer | AVGO.close | 408.6199951171875 | 408.6199951171875 | MATCH |
| Data Layer | AVGO.ma20 | 352.9020004272461 | 352.9020004272461 | MATCH |
| Data Layer | AVGO.ma50 | 337.88880126953126 | 337.88880126953126 | MATCH |
| Data Layer | AVGO.ma200 | 335.17730056762696 | 335.17730056762696 | MATCH |
| Data Layer | AVGO.breakout_high_20 | 406.7300109863281 | 406.7300109863281 | MATCH |
| Feature Layer | AVGO.breakout_condition | True | True | MATCH |
| Feature Layer | AVGO.ma_condition | True | True | MATCH |
| Data Layer | COST.close | 1005.5753173828124 | 1005.5753173828124 | MATCH |
| Data Layer | COST.ma20 | 998.6077697753906 | 998.6077697753906 | MATCH |
| Data Layer | COST.ma50 | 995.3179064941406 | 995.3179064941406 | MATCH |
| Data Layer | COST.ma200 | 949.3921765136719 | 949.3921765136719 | MATCH |
| Data Layer | COST.breakout_high_20 | 1035.8199462890625 | 1035.8199462890625 | MATCH |
| Feature Layer | COST.breakout_condition | False | False | MATCH |
| Feature Layer | COST.ma_condition | True | True | MATCH |
| Data Layer | GOOGL.close | 338.0950012207031 | 338.0950012207031 | MATCH |
| Data Layer | GOOGL.ma20 | 311.7877487182617 | 311.7877487182617 | MATCH |
| Data Layer | GOOGL.ma50 | 308.45969848632814 | 308.45969848632814 | MATCH |
| Data Layer | GOOGL.ma200 | 274.88412467956545 | 274.88412467956545 | MATCH |
| Data Layer | GOOGL.breakout_high_20 | 342.32000732421875 | 342.32000732421875 | MATCH |
| Feature Layer | GOOGL.breakout_condition | False | False | MATCH |
| Feature Layer | GOOGL.ma_condition | True | True | MATCH |
| Data Layer | META.close | 674.0850219726562 | 674.0850219726562 | MATCH |
| Data Layer | META.ma20 | 614.8472503662109 | 614.8472503662109 | MATCH |
| Data Layer | META.ma50 | 629.9490979003906 | 629.9490979003906 | MATCH |
| Data Layer | META.ma200 | 680.5702239990235 | 680.5702239990235 | MATCH |
| Data Layer | META.breakout_high_20 | 691.52001953125 | 691.52001953125 | MATCH |
| Feature Layer | META.breakout_condition | False | False | MATCH |
| Feature Layer | META.ma_condition | False | False | MATCH |
| Data Layer | MSFT.close | 430.3009033203125 | 430.3009033203125 | MATCH |
| Data Layer | MSFT.ma20 | 386.6730453491211 | 386.6730453491211 | MATCH |
| Data Layer | MSFT.ma50 | 393.5500170898438 | 393.5500170898438 | MATCH |
| Data Layer | MSFT.ma200 | 470.88085433959964 | 470.88085433959964 | MATCH |
| Data Layer | MSFT.breakout_high_20 | 431.5799865722656 | 431.5799865722656 | MATCH |
| Feature Layer | MSFT.breakout_condition | False | False | MATCH |
| Feature Layer | MSFT.ma_condition | False | False | MATCH |
| Data Layer | NFLX.close | 93.69499969482422 | 93.69499969482422 | MATCH |
| Data Layer | NFLX.ma20 | 98.3957508087158 | 98.3957508087158 | MATCH |
| Data Layer | NFLX.ma50 | 92.68509963989258 | 92.68509963989258 | MATCH |
| Data Layer | NFLX.ma200 | 105.3473401260376 | 105.3473401260376 | MATCH |
| Data Layer | NFLX.breakout_high_20 | 108.9499969482422 | 108.9499969482422 | MATCH |
| Feature Layer | NFLX.breakout_condition | False | False | MATCH |
| Feature Layer | NFLX.ma_condition | True | True | MATCH |
| Data Layer | NVDA.close | 199.7749938964844 | 199.7749938964844 | MATCH |
| Data Layer | NVDA.ma20 | 185.34724960327148 | 185.34724960327148 | MATCH |
| Data Layer | NVDA.ma50 | 184.38429931640624 | 184.38429931640624 | MATCH |
| Data Layer | NVDA.ma200 | 182.40807525634764 | 182.40807525634764 | MATCH |
| Data Layer | NVDA.breakout_high_20 | 202.75 | 202.75 | MATCH |
| Feature Layer | NVDA.breakout_condition | False | False | MATCH |
| Feature Layer | NVDA.ma_condition | True | True | MATCH |
| Data Layer | QCOM.close | 137.27999877929688 | 137.27999877929688 | MATCH |
| Data Layer | QCOM.ma20 | 130.46050033569335 | 130.46050033569335 | MATCH |
| Data Layer | QCOM.ma50 | 134.55800018310546 | 134.55800018310546 | MATCH |
| Data Layer | QCOM.ma200 | 156.74089965820312 | 156.74089965820312 | MATCH |
| Data Layer | QCOM.breakout_high_20 | 138.5 | 138.5 | MATCH |
| Feature Layer | QCOM.breakout_condition | False | False | MATCH |
| Feature Layer | QCOM.ma_condition | False | False | MATCH |
| Data Layer | TSLA.close | 391.9498901367188 | 391.9498901367188 | MATCH |
| Data Layer | TSLA.ma20 | 369.7509963989258 | 369.7509963989258 | MATCH |
| Data Layer | TSLA.ma50 | 389.23719787597656 | 389.23719787597656 | MATCH |
| Data Layer | TSLA.ma200 | 400.09704956054685 | 400.09704956054685 | MATCH |
| Data Layer | TSLA.breakout_high_20 | 409.2799987792969 | 409.2799987792969 | MATCH |
| Feature Layer | TSLA.breakout_condition | False | False | MATCH |
| Feature Layer | TSLA.ma_condition | False | False | MATCH |
| Selection Layer | selected_symbols | ['MSFT', 'AMZN', 'AMD'] | ['MSFT', 'AMZN', 'AMD'] | MATCH |
| Selection Layer | selected_sectors | ['XLK', 'XLY'] | ['XLK', 'XLY'] | MATCH |
| Signal Layer | signal_type | BUY | BUY | MATCH |
| Signal Layer | signal_symbol | AMD | AMD | MATCH |

## 6. Mismatch Analysis
- none

## 7. Root Cause Categories
- none

## 8. Decision
- PASS

## 9. Final Answer
- Is runtime executing the same strategy as backtest? YES
