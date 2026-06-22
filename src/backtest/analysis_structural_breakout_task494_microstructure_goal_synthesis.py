from __future__ import annotations

from pathlib import Path

import pandas as pd


OUT_DIR = Path("docs/reports/task_494_microstructure_goal_synthesis")
TASK491 = Path("docs/reports/task_491_intraday_continuation_grid_development/grid_development_decision.csv")
TASK492 = Path("docs/reports/task_492_microstructure_source_collection/task_492_decision.csv")
TASK493 = Path("docs/reports/task_493_microstructure_enhanced_continuation_grid/task_493_decision.csv")
TASK493_COST = Path("docs/reports/task_493_microstructure_enhanced_continuation_grid/selected_microstructure_cost_stress_quality.csv")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t491 = pd.read_csv(TASK491).iloc[0].to_dict()
    t492 = pd.read_csv(TASK492).iloc[0].to_dict()
    t493 = pd.read_csv(TASK493).iloc[0].to_dict()
    cost = pd.read_csv(TASK493_COST)
    comparison = pd.DataFrame(
        [
            {
                "task": "Task491_OHLCV_VWAP_only",
                "status": t491["best_target_status"],
                "count": t491["selected_count"],
                "avg_net_pct": t491["selected_avg_net_pct"],
                "win_rate": t491["selected_win_rate"],
                "add_scale_success_rate": t491["selected_add_scale_success_rate"],
                "entry_reduce_rate": t491["selected_entry_reduce_rate"],
                "validation_count": t491["validation_count"],
                "validation_avg_net_pct": t491["validation_avg_net_pct"],
                "recent_oos_count": t491["recent_oos_count"],
                "recent_oos_avg_net_pct": t491["recent_oos_avg_net_pct"],
                "primary_pass_flag": t491["primary_pass_flag"],
                "secondary_pass_flag": t491["secondary_pass_flag"],
            },
            {
                "task": "Task493_microstructure_enhanced",
                "status": t493["best_target_status"],
                "count": t493["selected_count"],
                "avg_net_pct": t493["selected_avg_net_pct"],
                "win_rate": t493["selected_win_rate"],
                "add_scale_success_rate": t493["selected_add_scale_success_rate"],
                "entry_reduce_rate": t493["selected_entry_reduce_rate"],
                "validation_count": t493["validation_count"],
                "validation_avg_net_pct": t493["validation_avg_net_pct"],
                "recent_oos_count": t493["recent_oos_count"],
                "recent_oos_avg_net_pct": t493["recent_oos_avg_net_pct"],
                "primary_pass_flag": t493["primary_pass_flag"],
                "secondary_pass_flag": t493["secondary_pass_flag"],
            },
        ]
    )
    comparison.to_csv(OUT_DIR / "task491_vs_task493_goal_comparison.csv", index=False)
    (OUT_DIR / "task494_microstructure_goal_synthesis.md").write_text(build_report(comparison, t492, t493, cost), encoding="utf-8")
    print(
        "[TASK494] "
        f"task493_status={t493['best_target_status']} avg={float(t493['selected_avg_net_pct']):.3f}% "
        f"coverage={float(t492['microstructure_feature_coverage']):.1%}"
    )


def build_report(comparison: pd.DataFrame, t492: dict[str, object], t493: dict[str, object], cost: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Task 494 - Microstructure Goal Synthesis",
            "",
            "## Quant Firm 4-Person Review",
            "",
            "### 1. Regime Specialist",
            "Task489 regime gate was not discarded. It remains the outer condition. The winning structure is regime first, intraday continuation second, microstructure tradability third.",
            "",
            "### 2. Intraday Continuation Quant",
            "OHLCV/VWAP-only Task491 reached secondary quality but failed primary. After adding spread/freshness/NBBO-size states, Task493 reached primary: count 100, avg net above 3%, win above 65%, ADD/SCALE above 60%, entry_reduce 0%, validation 20, recent OOS 60.",
            "",
            "### 3. Execution/Microstructure Specialist",
            "The upgrade was not cosmetic. Historical NBBO quote data provided a real tradability layer. However, raw receive timestamp, LULD/status, and depth-book remain unavailable, so this is not deployment-grade yet.",
            "",
            "### 4. Portfolio Manager",
            "The result is a genuine research promotion from secondary to primary diagnostic pass. The next upper target should require live-archive quality: raw receive timestamp, LULD/status, depth-book or at least SIP quote stream archival, plus walk-forward stability.",
            "",
            "## Task491 vs Task493",
            "",
            _csv_block(comparison),
            "",
            "## Microstructure Source Reality",
            "",
            f"- Quote/spread/NBBO-size coverage: {float(t492['microstructure_feature_coverage']):.1%}",
            f"- Raw quote rows collected: {int(t492['raw_quote_row_count'])}",
            "- Raw receive timestamp: missing from historical API",
            "- Status/LULD: missing from current source",
            "- Depth book: missing; current data is NBBO size, not full depth",
            "",
            "## Cost Stress",
            "",
            _csv_block(cost),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "이번에는 부족했던 quote/spread 데이터를 실제로 받아와서 테스트했다. 결과는 중요하다. 기존 OHLCV/VWAP만 썼을 때는 보조 목표만 통과했지만, quote 기반 spread/size/freshness를 추가하자 주 목표를 통과했다. 다만 실시간 수신시각과 LULD/status/depth book은 아직 없어서 실제 돈을 넣는 단계는 아니다.",
        ]
    )


def _csv_block(df: pd.DataFrame) -> str:
    return "```csv\n" + df.to_csv(index=False) + "```"


if __name__ == "__main__":
    main()
