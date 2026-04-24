# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "plotly>=5.20",
#     "kaleido>=1.0.0",   # static image export — 1.x is much faster on Windows
#     "pandas>=2.2",
# ]
# ///
"""
Generate charts from the issue and stargazer datasets.

Uses plotly for rendering (proper text layout, annotations, legends) and exports
PNGs that embed cleanly in GitHub markdown.

Run with uv (handles dependencies via the PEP 723 metadata block above):

    uv run scripts/plot_charts.py
    uv run scripts/plot_charts.py --issues-only
    uv run scripts/plot_charts.py --stars-only

Charts produced:

  ISSUES:
    daily-external-authors.png     — the interaction-limit story (Apr 16–21)
    daily-author-mix.png           — daily issues coloured by author association
    daily-closure-mix.png          — high-volume not-planned closure days highlighted
    daily-issue-volume.png         — opened vs closed over time

  STARGAZERS:
    weekly-star-volume.png         — when stars arrived
    weekly-account-quality-signals.png — account-quality signals per week
"""

from __future__ import annotations
import argparse
import gzip
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


WIDTH = 1100
HEIGHT = 560

PAL = {
    "external":   "#2E5BBA",
    "owner":      "#C85A3C",
    "contributor": "#3B8F5B",
    "opened":     "#2E5BBA",
    "closed":     "#C85A3C",
    "completed":  "#3B8F5B",
    "not_planned": "#C85A3C",
    "duplicate":  "#8A8A8A",
    "throwaway":  "#C85A3C",
    "age_30d":    "#D79830",
    "age_1d":     "#B07BCB",
    "stars":      "#2E5BBA",
    "shade_red":  "rgba(200, 90, 60, 0.14)",
    "shade_amb":  "rgba(215, 152, 48, 0.14)",
    "text":       "#1A1A1A",
    "subtext":    "#4A4A4A",
}


def load_jsonl(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def base_layout(title: str, subtitle: str, y_label: str) -> dict:
    return dict(
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:13px;color:{PAL['subtext']}'>{subtitle}</span>",
            x=0.5, xanchor="center", y=0.96, yanchor="top",
            font=dict(size=17, color=PAL["text"]),
        ),
        width=WIDTH, height=HEIGHT,
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=70, r=40, t=120, b=90),
        legend=dict(
            orientation="h", x=0.5, xanchor="center",
            y=-0.22, yanchor="bottom",
            font=dict(size=12), bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False, showline=True, linecolor="#555555",
            tickfont=dict(size=11, color=PAL["subtext"]),
        ),
        yaxis=dict(
            title=dict(text=y_label, font=dict(size=12, color=PAL["subtext"])),
            showgrid=True, gridcolor="#EDEDED",
            tickfont=dict(size=11, color=PAL["subtext"]),
            zeroline=False,
        ),
        font=dict(family="system-ui,-apple-system,Segoe UI,sans-serif"),
    )


def add_interaction_limit_shade(fig: go.Figure):
    """Shade the Apr 16–21 2026 interaction-limit window."""
    fig.add_shape(
        type="rect", xref="x", yref="paper",
        x0="2026-04-16", x1="2026-04-22",
        y0=0, y1=1,
        fillcolor="rgba(200, 90, 60, 0.14)",
        line_width=0, layer="below",
    )
    # Place annotation at the midpoint date (Apr 19) above plot area
    fig.add_annotation(
        xref="x", yref="paper",
        x="2026-04-19", y=1.03, yanchor="bottom",
        text="<b>Apr 16–21  interaction-limit active</b>",
        showarrow=True, arrowhead=0, arrowcolor="#C85A3C",
        arrowwidth=1, ax=0, ay=-10,
        font=dict(size=12, color="#C85A3C"),
        bgcolor="rgba(255,255,255,0.85)",
    )


def add_mass_close_markers(fig: go.Figure):
    """Mark the two high-volume not-planned closure days with clear labelled callouts offset laterally."""
    for date, label, ax_offset in [
        ("2026-02-08", "Feb 8:  55 not-planned", -90),
        ("2026-04-10", "Apr 10:  40 not-planned", 90),
    ]:
        fig.add_vline(
            x=date, line_width=1, line_dash="dash", line_color="#1A1A1A",
            opacity=0.5,
        )
        fig.add_annotation(
            xref="x", yref="paper", x=date, y=1.02, yanchor="bottom",
            text=f"<b>{label}</b>",
            showarrow=True, arrowhead=2, arrowcolor="#1A1A1A",
            arrowwidth=1, ax=ax_offset, ay=-12,
            font=dict(size=11, color="#1A1A1A"),
            bgcolor="rgba(255,255,255,0.9)", bordercolor="#1A1A1A", borderwidth=1,
        )


def save(fig: go.Figure, out_path: Path) -> None:
    fig.write_image(str(out_path), width=WIDTH, height=HEIGHT, scale=2)
    print(f"wrote {out_path}")


# ---------------------------------------------------------------------------
# Issue charts
# ---------------------------------------------------------------------------

def plot_issues(path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = load_jsonl(path)
    if not records:
        print(f"no records in {path}", file=sys.stderr)
        return
    print(f"loaded {len(records)} issues")

    df = pd.DataFrame(records)
    df["created_day"] = pd.to_datetime(df["createdAt"]).dt.tz_localize(None).dt.normalize()
    df["closed_day"] = pd.to_datetime(df["closedAt"], errors="coerce").dt.tz_localize(None).dt.normalize()

    span = pd.date_range(df["created_day"].min(), df["created_day"].max(), freq="D")

    def unique_per_day(assoc: str) -> pd.Series:
        sub = df[df["authorAssociation"] == assoc]
        return sub.groupby("created_day")["author"].nunique().reindex(span, fill_value=0)

    ext = unique_per_day("NONE")
    own = unique_per_day("OWNER")

    ext_roll = ext.rolling(7, min_periods=1).mean()
    own_roll = own.rolling(7, min_periods=1).mean()

    # ---- Chart 1: interaction-limit story ----
    fig = go.Figure()
    # Raw daily values as light markers behind the rolling line, so the reader
    # sees both the noise floor and the signal.
    fig.add_trace(go.Scatter(
        x=ext.index, y=ext.values, mode="markers",
        marker=dict(size=3, color=PAL["external"], opacity=0.25),
        name="External daily (raw)", showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=ext_roll.index, y=ext_roll.values, mode="lines",
        line=dict(color=PAL["external"], width=2.6),
        name="External community (7-day avg)",
    ))
    fig.add_trace(go.Scatter(
        x=own.index, y=own.values, mode="markers",
        marker=dict(size=3, color=PAL["owner"], opacity=0.25),
        name="Owner daily (raw)", showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=own_roll.index, y=own_roll.values, mode="lines",
        line=dict(color=PAL["owner"], width=2.6),
        name="Repository owner (7-day avg)",
    ))
    fig.update_layout(**base_layout(
        title="For 7 months the tracker was open to everyone. Then for 6 days in April 2026, it wasn't.",
        subtitle="Unique issue authors per day, split by GitHub author-association. Dots = raw, lines = 7-day rolling average.",
        y_label="Unique authors per day",
    ))
    add_interaction_limit_shade(fig)
    save(fig, out_dir / "daily-external-authors.png")

    # ---- Chart 2: stacked bars, author mix ----
    def count_per_day(assoc: str) -> pd.Series:
        sub = df[df["authorAssociation"] == assoc]
        return sub.groupby("created_day").size().reindex(span, fill_value=0)

    mix_none = count_per_day("NONE")
    mix_con = count_per_day("CONTRIBUTOR")
    mix_own = count_per_day("OWNER")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=mix_none.index, y=mix_none.values,
                         marker_color=PAL["external"], name="External community (NONE)"))
    fig.add_trace(go.Bar(x=mix_con.index, y=mix_con.values,
                         marker_color=PAL["contributor"], name="Contributor (prior PR)"))
    fig.add_trace(go.Bar(x=mix_own.index, y=mix_own.values,
                         marker_color=PAL["owner"], name="Repository owner"))
    fig.update_layout(
        barmode="stack",
        **base_layout(
            title="Daily issues, coloured by who filed them — April 16–19 bars have no community blue",
            subtitle="Every issue ever filed, placed on the day it was opened. During the interaction-limit window only contributors and the owner could file.",
            y_label="Issues opened",
        ),
    )
    add_interaction_limit_shade(fig)
    save(fig, out_dir / "daily-author-mix.png")

    # ---- Chart 3: closure mix ----
    closed = df.dropna(subset=["closed_day"]).copy()
    closed_span = pd.date_range(closed["closed_day"].min(), closed["closed_day"].max(), freq="D")

    def close_per_day(reason: str) -> pd.Series:
        sub = closed[closed["stateReason"] == reason]
        return sub.groupby("closed_day").size().reindex(closed_span, fill_value=0)

    completed = close_per_day("COMPLETED")
    not_planned = close_per_day("NOT_PLANNED")
    duplicate = close_per_day("DUPLICATE")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=completed.index, y=completed.values,
                         marker_color=PAL["completed"], name="Closed — completed"))
    fig.add_trace(go.Bar(x=not_planned.index, y=not_planned.values,
                         marker_color=PAL["not_planned"], name="Closed — not planned"))
    fig.add_trace(go.Bar(x=duplicate.index, y=duplicate.values,
                         marker_color=PAL["duplicate"], name="Closed — duplicate"))
    fig.update_layout(
        barmode="stack",
        **base_layout(
            title="121 issues closed as 'not planned' — two days account for 78 of them",
            subtitle="Daily issue closures coloured by close reason. Orange columns are high-volume not-planned closure days.",
            y_label="Issues closed",
        ),
    )
    add_mass_close_markers(fig)
    save(fig, out_dir / "daily-closure-mix.png")

    # ---- Chart 4: opened vs closed, 7d rolling ----
    opened_total = df.groupby("created_day").size().reindex(span, fill_value=0)
    closed_total = closed.groupby("closed_day").size().reindex(span, fill_value=0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=opened_total.index,
                             y=opened_total.rolling(7, min_periods=1).mean().values,
                             mode="lines",
                             line=dict(color=PAL["opened"], width=2.6),
                             name="Issues opened (7-day avg)"))
    fig.add_trace(go.Scatter(x=closed_total.index,
                             y=closed_total.rolling(7, min_periods=1).mean().values,
                             mode="lines",
                             line=dict(color=PAL["closed"], width=2.6),
                             name="Issues closed (7-day avg)"))
    fig.update_layout(**base_layout(
        title="The mid-April surge has not been absorbed — opened outruns closed",
        subtitle="7-day rolling averages of issues opened vs closed each day.",
        y_label="Issues per day",
    ))
    add_interaction_limit_shade(fig)
    save(fig, out_dir / "daily-issue-volume.png")


# ---------------------------------------------------------------------------
# Stargazer charts
# ---------------------------------------------------------------------------

def plot_stars(path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = load_jsonl(path)
    if not records:
        print(f"no records in {path}", file=sys.stderr)
        return
    print(f"loaded {len(records)} stars")

    # Flatten nested GraphQL shape
    df = pd.DataFrame([{
        "starred_at": r["starredAt"],
        "created_at": r["node"]["createdAt"],
        "followers": r["node"]["followers"]["totalCount"],
        "repos": r["node"]["repositories"]["totalCount"],
    } for r in records])
    df["starred_day"] = pd.to_datetime(df["starred_at"]).dt.tz_localize(None).dt.normalize()
    df["created"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)
    df["starred"] = pd.to_datetime(df["starred_at"]).dt.tz_localize(None)
    df["week"] = df["starred_day"] - pd.to_timedelta(df["starred_day"].dt.weekday, unit="D")
    df["age_days"] = (df["starred"] - df["created"]).dt.total_seconds() / 86400
    df["throwaway"] = (df["repos"] == 0) & (df["followers"] == 0)

    weekly = df.groupby("week").agg(
        stars=("starred_at", "size"),
        throwaway_pct=("throwaway", lambda s: 100 * s.mean()),
        f30_pct=("age_days", lambda s: 100 * (s < 30).mean()),
        f1_pct=("age_days", lambda s: 100 * (s < 1).mean()),
    ).reset_index()

    peak_week = weekly.loc[weekly["stars"].idxmax()]

    # Chart 5: weekly stars
    fig = go.Figure()
    fig.add_trace(go.Bar(x=weekly["week"], y=weekly["stars"],
                         marker_color=PAL["stars"], name="Stars per week"))
    fig.update_layout(**base_layout(
        title=f"22% of all-time stars arrived in a single week — April 13–19, 2026",
        subtitle=f"Stars added per calendar week. {len(df):,} stars total as of {df['starred_day'].max().date()}.",
        y_label="Stars per week",
    ))
    fig.add_annotation(
        x=peak_week["week"], y=peak_week["stars"],
        text=f"<b>Week of {peak_week['week'].date()}:  {int(peak_week['stars']):,} stars</b>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1,
        ax=-140, ay=-30, arrowcolor="#1A1A1A",
        font=dict(size=12, color="#1A1A1A"),
        bgcolor="rgba(255,255,255,0.92)", bordercolor="#1A1A1A", borderwidth=1,
    )
    save(fig, out_dir / "weekly-star-volume.png")

    # Chart 6: account-quality signals
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weekly["week"], y=weekly["throwaway_pct"],
                             mode="lines+markers",
                             line=dict(color=PAL["throwaway"], width=2.6),
                             marker=dict(size=5),
                             name="0 repos + 0 followers"))
    fig.add_trace(go.Scatter(x=weekly["week"], y=weekly["f30_pct"],
                             mode="lines+markers",
                             line=dict(color=PAL["age_30d"], width=2.2),
                             marker=dict(size=4),
                             name="Account &lt;30 days old"))
    fig.add_trace(go.Scatter(x=weekly["week"], y=weekly["f1_pct"],
                             mode="lines+markers",
                             line=dict(color=PAL["age_1d"], width=2.2),
                             marker=dict(size=4),
                             name="Account &lt;1 day old"))
    fig.add_hline(y=3.3, line_dash="dot", line_color="#8A8A8A",
                  annotation_text="Pre-adoption baseline: 3.3%",
                  annotation_position="top left",
                  annotation_font=dict(size=11, color="#4A4A4A"))
    fig.update_layout(**base_layout(
        title="Account-quality signals rose materially into the April peak",
        subtitle="% of each week's stargazers matching low-account-activity shape signatures.",
        y_label="% of weekly stars",
    ))
    fig.update_yaxes(ticksuffix="%")
    save(fig, out_dir / "weekly-account-quality-signals.png")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", default=str(repo_root / "evidence" / "software-quality" / "issues-graphql.jsonl.gz"))
    ap.add_argument("--stars", default=str(repo_root / "evidence" / "stargazers" / "stars-graphql.jsonl.gz"))
    ap.add_argument("--issues-out", default=str(repo_root / "evidence" / "software-quality"))
    ap.add_argument("--stars-out", default=str(repo_root / "evidence" / "stargazers"))
    ap.add_argument("--issues-only", action="store_true")
    ap.add_argument("--stars-only", action="store_true")
    args = ap.parse_args()

    if not args.stars_only:
        p = Path(args.issues)
        if p.exists():
            plot_issues(p, Path(args.issues_out))
        else:
            print(f"skipping issues: {p} not found")
    if not args.issues_only:
        p = Path(args.stars)
        if p.exists():
            plot_stars(p, Path(args.stars_out))
        else:
            print(f"skipping stars: {p} not found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
