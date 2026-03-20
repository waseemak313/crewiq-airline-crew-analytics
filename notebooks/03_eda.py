"""
CrewIQ — Module 3: Exploratory Data Analysis
=============================================
Generates 8 publication-quality charts covering:
  1. Crew composition by base and type
  2. Monthly utilization by base (heatmap)
  3. Callout rate by base — ORD vs network
  4. Disruption root cause Pareto
  5. Disruptions by day of week
  6. Disruption severity by base (stacked bar)
  7. Red-eye vs standard pairing disruption rate
  8. Fatigue risk score distribution by base

Run from project root:
    python notebooks/03_eda.py

Output: outputs/eda_charts.png  (all 8 charts in one figure)
        outputs/ individual PNGs for each chart
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH     = os.path.join(BASE_DIR, 'crewiq.db')
OUTPUT_DIR  = os.path.join(BASE_DIR, 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          10,
    'axes.titlesize':     12,
    'axes.titleweight':   'bold',
    'axes.titlepad':      12,
    'axes.labelsize':     9,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.grid':          True,
    'axes.grid.axis':     'y',
    'grid.alpha':         0.3,
    'grid.linestyle':     '--',
    'xtick.labelsize':    8,
    'ytick.labelsize':    8,
    'legend.fontsize':    8,
    'figure.facecolor':   'white',
    'axes.facecolor':     '#FAFAFA',
})

# Airline-themed color palette
COLORS = {
    'ORD': '#1A3A5C',   # deep navy
    'ATL': '#2E86AB',   # steel blue
    'DFW': '#A23B72',   # plum
    'LAX': '#F18F01',   # amber
    'JFK': '#C73E1D',   # red
}
BASE_ORDER  = ['ORD', 'ATL', 'DFW', 'LAX', 'JFK']
BASE_COLORS = [COLORS[b] for b in BASE_ORDER]

SEV_COLORS  = {'High': '#C73E1D', 'Medium': '#F18F01', 'Low': '#2E86AB'}
DOW_ORDER   = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

# ── Load data ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  CrewIQ — Module 3: Exploratory Data Analysis")
print("="*60)

conn     = sqlite3.connect(DB_PATH)
crew     = pd.read_sql("SELECT * FROM crew_roster",     conn)
schedule = pd.read_sql("SELECT * FROM flight_schedule", conn)
dis      = pd.read_sql("SELECT * FROM disruptions",     conn)
fatigue  = pd.read_sql("SELECT * FROM fatigue_logs",    conn)
conn.close()

print(f"  Loaded: {len(crew)} crew | {len(schedule)} pairings | "
      f"{len(dis)} disruptions | {len(fatigue)} fatigue records")

# ── Figure layout ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 24))
fig.suptitle(
    'CrewIQ — Crew Strategy & Intelligence Analytics Dashboard',
    fontsize=16, fontweight='bold', y=0.98, color='#1A3A5C'
)
fig.text(0.5, 0.965, 'Jan – Jun 2024  |  5 Hub Bases  |  500 Crew  |  3,000 Pairings',
         ha='center', fontsize=9, color='#666666')

gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.52, wspace=0.35,
                       left=0.07, right=0.96, top=0.94, bottom=0.04)

# ═══════════════════════════════════════════════════════════════════════════
# Chart 1 — Crew composition by base
# ═══════════════════════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0, 0])

active = crew[crew['employment_status'] == 'Active']
comp   = active.groupby(['base', 'crew_type']).size().unstack(fill_value=0)
comp   = comp.reindex(BASE_ORDER)

crew_type_colors = ['#1A3A5C', '#2E86AB', '#F18F01', '#C73E1D']
crew_types       = ['Captain', 'First Officer', 'Flight Attendant', 'Senior FA']
comp             = comp.reindex(columns=[c for c in crew_types if c in comp.columns])

comp.plot(kind='bar', ax=ax1, color=crew_type_colors[:len(comp.columns)],
          edgecolor='white', linewidth=0.5, width=0.72)

ax1.set_title('Active Crew Composition by Base')
ax1.set_xlabel('')
ax1.set_ylabel('Headcount')
ax1.set_xticklabels(BASE_ORDER, rotation=0)
ax1.legend(loc='upper right', framealpha=0.8)

# Add total labels on top of each bar group
for i, base in enumerate(comp.index):
    total = comp.loc[base].sum()
    ax1.text(i, total + 1.5, str(int(total)),
             ha='center', va='bottom', fontsize=8, fontweight='bold', color='#333')

print("  ✓ Chart 1: Crew composition")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 2 — Monthly utilization heatmap by base
# ═══════════════════════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[0, 1])

util_pivot = fatigue.groupby(['base', 'month'])['utilization_pct'].mean().unstack()
util_pivot = util_pivot.reindex(BASE_ORDER)

month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
util_pivot.columns = month_labels

sns.heatmap(util_pivot, ax=ax2, cmap='YlOrRd', annot=True, fmt='.0f',
            linewidths=0.5, linecolor='white',
            cbar_kws={'label': 'Avg Utilization %', 'shrink': 0.8},
            vmin=60, vmax=100)

ax2.set_title('Monthly Crew Utilization % by Base')
ax2.set_xlabel('')
ax2.set_ylabel('')
ax2.tick_params(axis='x', rotation=0)
ax2.tick_params(axis='y', rotation=0)

# Highlight cells above 90% with a border
for i in range(len(util_pivot.index)):
    for j in range(len(util_pivot.columns)):
        val = util_pivot.iloc[i, j]
        if val > 90:
            ax2.add_patch(plt.Rectangle((j, i), 1, 1,
                          fill=False, edgecolor='#C73E1D', lw=2))

print("  ✓ Chart 2: Utilization heatmap")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 3 — Callout rate by base (ORD vs network highlight)
# ═══════════════════════════════════════════════════════════════════════════
ax3 = fig.add_subplot(gs[1, 0])

callout = fatigue.groupby('base').agg(
    total=('called_out', 'count'),
    callouts=('called_out', 'sum')
).reset_index()
callout['callout_rate'] = callout['callouts'] / callout['total'] * 100
callout = callout.set_index('base').reindex(BASE_ORDER).reset_index()

bar_colors = ['#C73E1D' if b == 'ORD' else '#2E86AB' for b in callout['base']]
bars = ax3.bar(callout['base'], callout['callout_rate'],
               color=bar_colors, edgecolor='white', linewidth=0.5, width=0.6)

# Network average line
network_avg = callout['callout_rate'].mean()
ax3.axhline(network_avg, color='#F18F01', linewidth=1.8, linestyle='--', zorder=5)
ax3.text(4.6, network_avg + 0.3, f'Network avg\n{network_avg:.1f}%',
         fontsize=7.5, color='#F18F01', ha='right', va='bottom')

# Value labels
for bar, val in zip(bars, callout['callout_rate']):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{val:.1f}%', ha='center', va='bottom', fontsize=8.5, fontweight='bold')

ax3.set_title('Crew Callout Rate by Base\n(ORD highlighted as outlier)')
ax3.set_xlabel('')
ax3.set_ylabel('Callout Rate (%)')
ax3.set_ylim(0, callout['callout_rate'].max() * 1.25)

legend_patches = [
    mpatches.Patch(color='#C73E1D', label='ORD — above threshold'),
    mpatches.Patch(color='#2E86AB', label='Other bases'),
    plt.Line2D([0], [0], color='#F18F01', linestyle='--', label='Network average'),
]
ax3.legend(handles=legend_patches, loc='upper right', framealpha=0.8)
print("  ✓ Chart 3: Callout rates")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 4 — Disruption root cause Pareto
# ═══════════════════════════════════════════════════════════════════════════
ax4 = fig.add_subplot(gs[1, 1])

pareto = dis.groupby('root_cause').size().sort_values(ascending=False).reset_index()
pareto.columns = ['root_cause', 'count']
pareto['cumulative_pct'] = pareto['count'].cumsum() / pareto['count'].sum() * 100

short_labels = {
    'Crew callout':           'Crew\ncallout',
    'Weather':                'Weather',
    'Mechanical':             'Mechanical',
    'ATC delay':              'ATC\ndelay',
    'Late inbound aircraft':  'Late\ninbound',
    'Crew rest violation':    'Rest\nviolation',
    'Training conflict':      'Training\nconflict',
    'Other':                  'Other',
}
pareto['label'] = pareto['root_cause'].map(short_labels)

ax4_twin = ax4.twinx()
ax4_twin.spines['top'].set_visible(False)

bars4 = ax4.bar(range(len(pareto)), pareto['count'],
                color='#1A3A5C', alpha=0.85, edgecolor='white', linewidth=0.5)
ax4_twin.plot(range(len(pareto)), pareto['cumulative_pct'],
              color='#C73E1D', marker='o', markersize=5, linewidth=1.8, zorder=5)
ax4_twin.axhline(80, color='#F18F01', linestyle='--', linewidth=1.2, alpha=0.7)
ax4_twin.text(len(pareto) - 0.5, 81.5, '80%', fontsize=7.5,
              color='#F18F01', ha='right')

ax4.set_xticks(range(len(pareto)))
ax4.set_xticklabels(pareto['label'], fontsize=7.5)
ax4.set_ylabel('Number of Disruptions')
ax4_twin.set_ylabel('Cumulative %', color='#C73E1D')
ax4_twin.tick_params(axis='y', labelcolor='#C73E1D')
ax4_twin.set_ylim(0, 115)
ax4.set_title('Disruption Root Cause — Pareto Analysis')

for bar, val in zip(bars4, pareto['count']):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             str(val), ha='center', va='bottom', fontsize=7.5)

print("  ✓ Chart 4: Pareto chart")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 5 — Disruptions by day of week
# ═══════════════════════════════════════════════════════════════════════════
ax5 = fig.add_subplot(gs[2, 0])

dow = dis.groupby('day_of_week').agg(
    count=('disruption_id', 'count'),
    avg_delay=('delay_minutes', 'mean'),
    callouts=('root_cause', lambda x: (x == 'Crew callout').sum())
).reindex(DOW_ORDER).reset_index()

dow_colors = ['#C73E1D' if d == 'Monday' else
              '#F18F01' if d == 'Friday'  else '#2E86AB'
              for d in dow['day_of_week']]

bars5 = ax5.bar(range(7), dow['count'], color=dow_colors,
                edgecolor='white', linewidth=0.5, width=0.65)

# Overlay avg delay as line on twin axis
ax5_twin = ax5.twinx()
ax5_twin.spines['top'].set_visible(False)
ax5_twin.plot(range(7), dow['avg_delay'], color='#A23B72',
              marker='D', markersize=5, linewidth=1.8, linestyle='--', zorder=5)
ax5_twin.set_ylabel('Avg Delay (min)', color='#A23B72')
ax5_twin.tick_params(axis='y', labelcolor='#A23B72')

ax5.set_xticks(range(7))
ax5.set_xticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
ax5.set_ylabel('Disruption Count')
ax5.set_title('Disruptions by Day of Week\n(Monday = peak, avg delay overlay)')

for bar, val in zip(bars5, dow['count']):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
             str(val), ha='center', va='bottom', fontsize=8)

legend_patches5 = [
    mpatches.Patch(color='#C73E1D', label='Monday (peak)'),
    mpatches.Patch(color='#F18F01', label='Friday (elevated)'),
    mpatches.Patch(color='#2E86AB', label='Other days'),
    plt.Line2D([0],[0], color='#A23B72', linestyle='--', marker='D',
               markersize=4, label='Avg delay (min)'),
]
ax5.legend(handles=legend_patches5, loc='upper right', framealpha=0.8, fontsize=7.5)
print("  ✓ Chart 5: Day-of-week pattern")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 6 — Disruption severity by base (stacked bar)
# ═══════════════════════════════════════════════════════════════════════════
ax6 = fig.add_subplot(gs[2, 1])

sev = dis.groupby(['base', 'severity']).size().unstack(fill_value=0)
sev = sev.reindex(BASE_ORDER)
for s in ['High', 'Medium', 'Low']:
    if s not in sev.columns:
        sev[s] = 0
sev = sev[['Low', 'Medium', 'High']]

bottom_low  = np.zeros(len(sev))
bottom_med  = sev['Low'].values.astype(float)
bottom_high = bottom_med + sev['Medium'].values.astype(float)

ax6.bar(BASE_ORDER, sev['Low'],    bottom=bottom_low,  color=SEV_COLORS['Low'],
        label='Low',    edgecolor='white', linewidth=0.5)
ax6.bar(BASE_ORDER, sev['Medium'], bottom=bottom_med,  color=SEV_COLORS['Medium'],
        label='Medium', edgecolor='white', linewidth=0.5)
ax6.bar(BASE_ORDER, sev['High'],   bottom=bottom_high, color=SEV_COLORS['High'],
        label='High',   edgecolor='white', linewidth=0.5)

# Total labels
for i, base in enumerate(BASE_ORDER):
    total = sev.loc[base].sum()
    ax6.text(i, total + 0.4, str(int(total)),
             ha='center', va='bottom', fontsize=8.5, fontweight='bold')

ax6.set_title('Disruption Severity by Base')
ax6.set_xlabel('')
ax6.set_ylabel('Disruption Count')
ax6.legend(loc='upper right', title='Severity', framealpha=0.8)
print("  ✓ Chart 6: Severity by base")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 7 — Red-eye vs standard disruption rate
# ═══════════════════════════════════════════════════════════════════════════
ax7 = fig.add_subplot(gs[3, 0])

pairing_counts = schedule.groupby('pairing_type').size().reset_index(name='total')
pairing_dis    = dis.groupby('pairing_type').size().reset_index(name='disruptions')
pairing_merge  = pairing_counts.merge(pairing_dis, on='pairing_type', how='left').fillna(0)
pairing_merge['dis_rate'] = pairing_merge['disruptions'] / pairing_merge['total'] * 100
pairing_merge  = pairing_merge.sort_values('dis_rate', ascending=False)

pt_colors = ['#C73E1D' if p == 'Red-eye' else '#1A3A5C'
             for p in pairing_merge['pairing_type']]

bars7 = ax7.barh(pairing_merge['pairing_type'], pairing_merge['dis_rate'],
                 color=pt_colors, edgecolor='white', linewidth=0.5, height=0.55)

# 8% safe threshold line
ax7.axvline(8, color='#F18F01', linestyle='--', linewidth=1.8, zorder=5)
ax7.text(8.1, 3.5, 'Safe threshold\n(8%)', fontsize=7.5, color='#F18F01', va='center')

for bar, val in zip(bars7, pairing_merge['dis_rate']):
    ax7.text(val + 0.1, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}%', va='center', fontsize=8.5, fontweight='bold')

ax7.set_xlabel('Disruption Rate (%)')
ax7.set_title('Disruption Rate by Pairing Type\n(Red-eye exceeds safe threshold)')
ax7.set_xlim(0, pairing_merge['dis_rate'].max() * 1.35)
ax7.grid(axis='x', alpha=0.3, linestyle='--')
ax7.grid(axis='y', alpha=0)

legend7 = [
    mpatches.Patch(color='#C73E1D', label='Red-eye (at-risk)'),
    mpatches.Patch(color='#1A3A5C', label='Standard pairings'),
    plt.Line2D([0],[0], color='#F18F01', linestyle='--', label='8% safe threshold'),
]
ax7.legend(handles=legend7, loc='lower right', framealpha=0.8, fontsize=7.5)
print("  ✓ Chart 7: Red-eye analysis")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 8 — Fatigue risk score distribution by base
# ═══════════════════════════════════════════════════════════════════════════
ax8 = fig.add_subplot(gs[3, 1])

for i, base in enumerate(BASE_ORDER):
    data = fatigue[fatigue['base'] == base]['fatigue_risk_score']
    color = COLORS[base]
    # Violin
    parts = ax8.violinplot(data, positions=[i], widths=0.7,
                           showmedians=False, showextrema=False)
    for pc in parts['bodies']:
        pc.set_facecolor(color)
        pc.set_alpha(0.65)
        pc.set_edgecolor('white')
    # Median dot
    ax8.scatter(i, data.median(), color='white', s=30, zorder=5)
    ax8.scatter(i, data.median(), color=color,  s=15, zorder=6)

# High-risk threshold
ax8.axhline(70, color='#C73E1D', linestyle='--', linewidth=1.5)
ax8.text(4.55, 71.5, 'High-risk\nthreshold (70)', fontsize=7.5,
         color='#C73E1D', ha='right')

ax8.set_xticks(range(5))
ax8.set_xticklabels(BASE_ORDER)
ax8.set_ylabel('Fatigue Risk Score (0–100)')
ax8.set_title('Fatigue Risk Score Distribution by Base\n(white dot = median)')
ax8.set_ylim(0, 105)
ax8.grid(axis='y', alpha=0.3, linestyle='--')
ax8.grid(axis='x', alpha=0)

legend8 = [mpatches.Patch(color=COLORS[b], label=b) for b in BASE_ORDER]
ax8.legend(handles=legend8, loc='upper right', framealpha=0.8,
           ncol=5, fontsize=7.5)
print("  ✓ Chart 8: Fatigue distribution")

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = os.path.join(OUTPUT_DIR, 'eda_charts.png')
fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"\n  ✓ Saved: outputs/eda_charts.png")

# Also save individual charts
individual_titles = [
    'crew_composition', 'utilization_heatmap', 'callout_rates',
    'disruption_pareto', 'disruption_by_dow', 'severity_by_base',
    'redye_analysis', 'fatigue_distribution'
]
axes_list = [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8]

for ax, name in zip(axes_list, individual_titles):
    fig_ind, ax_ind = plt.subplots(figsize=(8, 5))
    # Save bounding box of each axis from main figure
    extent = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(os.path.join(OUTPUT_DIR, f'{name}.png'),
                bbox_inches=extent.expanded(1.12, 1.18),
                dpi=150, facecolor='white')
    plt.close(fig_ind)

print(f"  ✓ Saved 8 individual chart PNGs to outputs/")

print("\n" + "="*60)
print("  EDA COMPLETE — Key Findings Summary")
print("="*60)

# Print key stats
print(f"\n  Crew utilization:")
for base in BASE_ORDER:
    avg = fatigue[fatigue['base']==base]['utilization_pct'].mean()
    print(f"    {base}: {avg:.1f}%")

print(f"\n  Callout rates:")
for base in BASE_ORDER:
    b_data = fatigue[fatigue['base']==base]
    rate = b_data['called_out'].sum() / len(b_data) * 100
    print(f"    {base}: {rate:.1f}%")

print(f"\n  Disruption rates by pairing type:")
for _, row in pairing_merge.iterrows():
    print(f"    {row['pairing_type']:<12}: {row['dis_rate']:.1f}%")

print(f"\n  Monday disruptions: {dow[dow['day_of_week']=='Monday']['count'].values[0]}")
print(f"  Network avg/day:    {dow['count'].mean():.1f}")
print("="*60 + "\n")

plt.close('all')
