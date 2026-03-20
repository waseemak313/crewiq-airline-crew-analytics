"""
CrewIQ — Module 4: Crew Availability Forecasting Model
=======================================================
Builds a rolling forecast that predicts crew coverage gaps
2 weeks ahead by base and crew type.

What this model does:
  - Calculates weekly available crew per base using fatigue + callout data
  - Applies a rolling 4-week average to smooth noise
  - Projects forward 2 weeks using trend + seasonality signals
  - Flags bases predicted to fall below minimum coverage thresholds
  - Outputs a risk table and forecast chart

Business value:
  "Gives the scheduling team a 2-week advance signal to pull reserves,
   approve voluntary pickups, or adjust pairing assignments before
   a shortage becomes an operational crisis."

Run from project root:
    python notebooks/04_availability_model.py

Output:
    outputs/forecast_chart.png
    outputs/coverage_risk_report.csv
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import warnings
import os
warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH    = os.path.join(BASE_DIR, 'crewiq.db')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':      'DejaVu Sans',
    'font.size':        10,
    'axes.titlesize':   12,
    'axes.titleweight': 'bold',
    'axes.titlepad':    12,
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'axes.grid':        True,
    'grid.alpha':       0.3,
    'grid.linestyle':   '--',
    'figure.facecolor': 'white',
    'axes.facecolor':   '#FAFAFA',
})

COLORS = {
    'ORD': '#1A3A5C', 'ATL': '#2E86AB', 'DFW': '#A23B72',
    'LAX': '#F18F01', 'JFK': '#C73E1D',
}
BASE_ORDER = ['ORD', 'ATL', 'DFW', 'LAX', 'JFK']

# Minimum safe coverage thresholds (active crew floor per base)
# Below these levels scheduling cannot absorb a normal callout wave
MIN_COVERAGE = {'ORD': 85, 'ATL': 80, 'DFW': 65, 'LAX': 60, 'JFK': 38}

print("\n" + "="*60)
print("  CrewIQ — Module 4: Availability Forecasting Model")
print("="*60)

# ── Load data ──────────────────────────────────────────────────────────────
conn    = sqlite3.connect(DB_PATH)
crew    = pd.read_sql("SELECT * FROM crew_roster",  conn)
fatigue = pd.read_sql("SELECT * FROM fatigue_logs", conn)
conn.close()

# ── Step 1: Build monthly available crew count per base ───────────────────
# "Available" = active + not called out this month
print("\n  Step 1: Building availability baseline...")

active = crew[crew['employment_status'] == 'Active'][['employee_id', 'base', 'crew_type']]

# Monthly availability = active crew who did NOT call out
monthly_avail = fatigue.merge(active, on='employee_id', suffixes=('', '_roster'))
monthly_avail['available'] = (monthly_avail['called_out'] == 0).astype(int)

avail_by_base = monthly_avail.groupby(['base', 'month']).agg(
    total_crew   =('employee_id', 'count'),
    available    =('available',   'sum'),
    callouts     =('called_out',  'sum'),
    avg_fatigue  =('fatigue_risk_score', 'mean'),
    avg_util     =('utilization_pct',    'mean'),
).reset_index()

avail_by_base['avail_rate'] = (
    avail_by_base['available'] / avail_by_base['total_crew'] * 100
)
avail_by_base['month_dt'] = pd.to_datetime(avail_by_base['month'])
avail_by_base = avail_by_base.sort_values(['base', 'month_dt'])

print(f"  ✓ Built availability matrix: "
      f"{len(avail_by_base)} base-month records")

# ── Step 2: Rolling 4-week average + trend calculation ────────────────────
print("\n  Step 2: Computing rolling averages and trends...")

forecast_records = []

for base in BASE_ORDER:
    df = avail_by_base[avail_by_base['base'] == base].copy()
    df = df.sort_values('month_dt').reset_index(drop=True)

    # Rolling 4-month average (equivalent to 4-week rolling in weekly data)
    df['rolling_avail']   = df['available'].rolling(window=3, min_periods=1).mean()
    df['rolling_fatigue'] = df['avg_fatigue'].rolling(window=3, min_periods=1).mean()

    # Trend: slope of available crew over last 3 months (linear)
    if len(df) >= 3:
        x    = np.arange(len(df))
        slope, intercept = np.polyfit(x, df['available'], 1)
    else:
        slope = 0

    # ── Step 3: Project 2 months forward ──────────────────────────────────
    last_month   = df['month_dt'].max()
    last_avail   = df['rolling_avail'].iloc[-1]
    last_fatigue = df['rolling_fatigue'].iloc[-1]

    for weeks_ahead in [4, 8]:   # ~1 month and ~2 months ahead
        # Projection = rolling avg + trend adjustment
        # Fatigue drag: high fatigue score increases callout probability
        fatigue_drag    = max(0, (last_fatigue - 50) / 100 * 0.08)
        trend_adj       = slope * (weeks_ahead / 4)
        projected_avail = last_avail + trend_adj - (last_avail * fatigue_drag)
        projected_avail = max(0, round(projected_avail, 1))

        min_thresh      = MIN_COVERAGE[base]
        gap             = round(projected_avail - min_thresh, 1)
        shortage        = projected_avail < min_thresh

        # Risk level
        if projected_avail < min_thresh * 0.85:
            risk = 'CRITICAL'
        elif projected_avail < min_thresh:
            risk = 'AT RISK'
        elif projected_avail < min_thresh * 1.10:
            risk = 'WATCH'
        else:
            risk = 'OK'

        proj_month = last_month + pd.DateOffset(weeks=weeks_ahead)

        forecast_records.append({
            'base':              base,
            'forecast_month':    proj_month.strftime('%Y-%m'),
            'weeks_ahead':       weeks_ahead,
            'current_available': int(last_avail),
            'projected_available': projected_avail,
            'min_threshold':     min_thresh,
            'gap_vs_threshold':  gap,
            'trend_per_month':   round(slope, 2),
            'fatigue_drag_pct':  round(fatigue_drag * 100, 1),
            'shortage_flag':     shortage,
            'risk_level':        risk,
        })

forecast_df = pd.DataFrame(forecast_records)
print(f"  ✓ Generated {len(forecast_df)} forecast records (2 horizons × 5 bases)")

# ── Step 4: Print the risk report ─────────────────────────────────────────
print("\n" + "="*60)
print("  COVERAGE RISK REPORT — 2-MONTH FORECAST")
print("="*60)
print(f"  {'Base':<6} {'Horizon':<12} {'Current':>9} {'Projected':>11} "
      f"{'Threshold':>11} {'Gap':>7} {'Risk':<10}")
print("  " + "-"*68)

for _, row in forecast_df.sort_values(['weeks_ahead', 'risk_level']).iterrows():
    gap_str = f"{row['gap_vs_threshold']:+.0f}"
    flag    = "⚠" if row['shortage_flag'] else " "
    horizon = f"+{row['weeks_ahead']}wks"
    print(f"  {row['base']:<6} {horizon:<12} "
          f"{row['current_available']:>9.0f} "
          f"{row['projected_available']:>11.1f} "
          f"{row['min_threshold']:>11} "
          f"{gap_str:>7}  "
          f"{flag} {row['risk_level']}")

at_risk = forecast_df[forecast_df['shortage_flag'] == True]
print(f"\n  ⚠  {len(at_risk)} base-horizon combinations flagged as AT RISK or CRITICAL")

# ── Step 5: Save risk report CSV ──────────────────────────────────────────
csv_path = os.path.join(OUTPUT_DIR, 'coverage_risk_report.csv')
forecast_df.to_csv(csv_path, index=False)
print(f"  ✓ Saved: outputs/coverage_risk_report.csv")

# ── Step 6: Build forecast charts ─────────────────────────────────────────
print("\n  Building forecast charts...")

fig = plt.figure(figsize=(20, 22))
fig.suptitle(
    'CrewIQ — Crew Availability Forecast & Coverage Risk Model',
    fontsize=16, fontweight='bold', y=0.98, color='#1A3A5C'
)
fig.text(
    0.5, 0.965,
    'Rolling average + trend model  |  2-month forward projection  |  Shaded = below minimum threshold',
    ha='center', fontsize=9, color='#666666'
)

gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.5, wspace=0.35,
                       left=0.07, right=0.96, top=0.94, bottom=0.04)

# ── Chart A: Availability trend per base (5 small multiples) ──────────────
for idx, base in enumerate(BASE_ORDER):
    row_i = idx // 2
    col_i = idx % 2
    if idx == 4:
        ax = fig.add_subplot(gs[2, 0])
    else:
        ax = fig.add_subplot(gs[row_i, col_i])

    df_base = avail_by_base[avail_by_base['base'] == base].copy()
    df_base = df_base.sort_values('month_dt')

    months     = df_base['month_dt'].dt.strftime('%b')
    avail_vals = df_base['available'].values
    rolling    = df_base['available'].rolling(3, min_periods=1).mean().values

    x = np.arange(len(months))

    # Historical bars
    ax.bar(x, avail_vals, color=COLORS[base], alpha=0.55,
           edgecolor='white', linewidth=0.5, width=0.6, label='Actual available')

    # Rolling average line
    ax.plot(x, rolling, color=COLORS[base], linewidth=2.2,
            marker='o', markersize=5, label='3-month rolling avg', zorder=5)

    # Project 2 forward points
    fwd = forecast_df[forecast_df['base'] == base].sort_values('weeks_ahead')
    if len(fwd) >= 2:
        proj_x    = [len(x) - 1, len(x), len(x) + 1]
        proj_y    = [rolling[-1],
                     fwd.iloc[0]['projected_available'],
                     fwd.iloc[1]['projected_available']]
        ax.plot(proj_x, proj_y, color=COLORS[base], linewidth=2,
                linestyle='--', marker='D', markersize=6,
                markerfacecolor='white', markeredgecolor=COLORS[base],
                markeredgewidth=2, label='Forecast', zorder=6)

        # Risk labels on projected points
        for px, py, risk in zip(proj_x[1:], proj_y[1:],
                                fwd['risk_level'].values):
            color_map = {'CRITICAL': '#C73E1D', 'AT RISK': '#F18F01',
                         'WATCH': '#A23B72', 'OK': '#2E86AB'}
            ax.annotate(risk, (px, py),
                        textcoords='offset points', xytext=(0, 10),
                        ha='center', fontsize=7, fontweight='bold',
                        color=color_map.get(risk, '#333'))

    # Minimum threshold line
    min_t = MIN_COVERAGE[base]
    all_x = np.arange(len(x) + 2)
    ax.axhline(min_t, color='#C73E1D', linestyle=':', linewidth=1.5,
               label=f'Min threshold ({min_t})', zorder=4)

    # Shade below threshold
    ax.fill_between(all_x, 0, min_t,
                    color='#C73E1D', alpha=0.06, zorder=0)

    # X-axis labels (historical + forecast)
    all_labels = list(months) + ['Proj+1M', 'Proj+2M']
    ax.set_xticks(np.arange(len(all_labels)))
    ax.set_xticklabels(all_labels, fontsize=7.5)
    ax.set_xlim(-0.5, len(all_labels) - 0.5)
    ax.set_ylabel('Available Crew', fontsize=8)
    ax.set_title(f'{base} — Availability Trend & Forecast')
    ax.legend(loc='lower left', fontsize=6.5, framealpha=0.8)

    # Current vs threshold annotation
    current = int(rolling[-1])
    thresh  = MIN_COVERAGE[base]
    buffer  = current - thresh
    ax.text(0.98, 0.97,
            f"Current: {current}  |  Threshold: {thresh}  |  Buffer: {buffer:+d}",
            transform=ax.transAxes, ha='right', va='top',
            fontsize=7, color='#444',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='#ccc', alpha=0.9))

print("  ✓ Charts A-E: Base availability trends + forecasts")

# ── Chart F: Risk summary heatmap ─────────────────────────────────────────
ax_heat = fig.add_subplot(gs[2, 1])

risk_order  = ['CRITICAL', 'AT RISK', 'WATCH', 'OK']
risk_scores = {'CRITICAL': 3, 'AT RISK': 2, 'WATCH': 1, 'OK': 0}
heat_data   = forecast_df.pivot(
    index='base', columns='weeks_ahead', values='risk_level'
).reindex(BASE_ORDER)
heat_data.columns = ['+4 weeks', '+8 weeks']

heat_num = heat_data.map(lambda x: risk_scores.get(x, 0))

cmap = plt.cm.RdYlGn_r
im   = ax_heat.imshow(heat_num.values, cmap=cmap, aspect='auto',
                      vmin=0, vmax=3)

ax_heat.set_xticks([0, 1])
ax_heat.set_xticklabels(['+4 weeks', '+8 weeks'], fontsize=9)
ax_heat.set_yticks(range(5))
ax_heat.set_yticklabels(BASE_ORDER, fontsize=9)

# Annotate cells
for i in range(5):
    for j in range(2):
        val   = heat_data.iloc[i, j]
        score = heat_scores = heat_num.iloc[i, j]
        color = 'white' if score >= 2 else '#222'
        ax_heat.text(j, i, val, ha='center', va='center',
                     fontsize=9, fontweight='bold', color=color)

ax_heat.set_title('Coverage Risk Summary\n(2-month forecast horizon)')

# Colorbar legend
cbar = fig.colorbar(im, ax=ax_heat, fraction=0.046, pad=0.08)
cbar.set_ticks([0, 1, 2, 3])
cbar.set_ticklabels(['OK', 'WATCH', 'AT RISK', 'CRITICAL'], fontsize=8)

print("  ✓ Chart F: Risk summary heatmap")

# ── Save ──────────────────────────────────────────────────────────────────
out_path = os.path.join(OUTPUT_DIR, 'forecast_chart.png')
fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close('all')
print(f"  ✓ Saved: outputs/forecast_chart.png")

# ── Step 7: Key findings summary ──────────────────────────────────────────
print("\n" + "="*60)
print("  KEY FORECAST FINDINGS")
print("="*60)

critical = forecast_df[forecast_df['risk_level'] == 'CRITICAL']
at_risk  = forecast_df[forecast_df['risk_level'] == 'AT RISK']
watch    = forecast_df[forecast_df['risk_level'] == 'WATCH']

if len(critical):
    print(f"\n  🔴 CRITICAL ({len(critical)} flags):")
    for _, r in critical.iterrows():
        print(f"     {r['base']} at +{r['weeks_ahead']}wks — "
              f"projected {r['projected_available']:.0f} vs "
              f"threshold {r['min_threshold']} "
              f"(gap: {r['gap_vs_threshold']:+.0f})")

if len(at_risk):
    print(f"\n  🟠 AT RISK ({len(at_risk)} flags):")
    for _, r in at_risk.iterrows():
        print(f"     {r['base']} at +{r['weeks_ahead']}wks — "
              f"projected {r['projected_available']:.0f} vs "
              f"threshold {r['min_threshold']} "
              f"(gap: {r['gap_vs_threshold']:+.0f})")

if len(watch):
    print(f"\n  🟡 WATCH ({len(watch)} flags):")
    for _, r in watch.iterrows():
        print(f"     {r['base']} at +{r['weeks_ahead']}wks — "
              f"buffer only {r['gap_vs_threshold']:+.0f} crew above threshold")

print(f"\n  Recommended actions:")
for _, r in forecast_df[forecast_df['shortage_flag']].iterrows():
    shortage = abs(r['gap_vs_threshold'])
    print(f"  → {r['base']} (+{r['weeks_ahead']}wks): "
          f"Activate {int(shortage)+2} reserves or open voluntary pickups")

print("\n" + "="*60 + "\n")
