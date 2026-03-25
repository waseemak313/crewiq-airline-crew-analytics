# ✈️ CrewIQ — Airline Crew Strategy & Intelligence Analytics

> A full-stack business analytics project simulating the crew strategy and intelligence function at a major U.S. airline — covering data engineering, SQL analysis, predictive modeling, and executive dashboards.

---

##  Project Overview

Airlines operate one of the most complex workforce systems in any industry. Crew members must be scheduled months in advance, comply with FAA/ICAO duty time regulations, maintain aircraft-type qualifications, and be recoverable within hours when disruptions hit. Even small inefficiencies — an understaffed base, a chronic Monday callout pattern, a fatigue-heavy pairing — cost airlines millions annually.

**CrewIQ** replicates the analytical work done by a Crew Strategy & Intelligence team:
- Forecasting crew availability gaps before they become operational crises
- Identifying root causes of disruptions using structured classification
- Measuring pairing efficiency across routes and hub bases
- Surfacing workforce health signals for leadership

---

##  Repository Structure

```
crewiq-airline-crew-analytics/
│
├── README.md
├── data/
│   ├── crew_roster.csv          # 500 crew members | 5 hub bases | 6 crew types
│   ├── flight_schedule.csv      # 3,000 pairings | Jan–Jun 2024
│   ├── disruptions.csv          # 190 disruption events | 8 root cause categories
│   └── fatigue_logs.csv         # 2,586 monthly duty records | FAA Part 117 tracking
│
├── sql/
│   ├── 01_schema.sql            # Table definitions and relationships
│   ├── 02_crew_availability.sql # Weekly availability by base and crew type
│   ├── 03_disruption_analysis.sql # Root cause ranking, severity, cascade rates
│   └── 04_pairing_efficiency.sql  # Deadhead %, utilization KPIs by route
│
├── notebooks/
│   ├── 01_data_generation.py    # Synthetic dataset generator (numpy + pandas)
│   ├── 02_eda.ipynb             # Exploratory analysis + visualizations
│   ├── 03_availability_model.ipynb # Rolling forecast + coverage gap detection
│   └── 04_disruption_analysis.ipynb # Root cause Pareto, heatmaps, severity model
│
├── outputs/
│   └── insights_brief.pdf       # 2-page executive summary of findings
│
└── tableau/
    └── crewiq_dashboard.twbx    # Tableau packaged workbook (3 dashboards)
```

---

## Dataset Overview

All data is synthetically generated using realistic airline industry distributions. No proprietary or PII data is used.

| Dataset | Rows | Key Fields |
|---|---|---|
| `crew_roster.csv` | 500 | employee_id, crew_type, base, hire_date, aircraft_qual, employment_status |
| `flight_schedule.csv` | 3,000 | pairing_id, origin, destination, pairing_type, aircraft_type, assigned crew |
| `disruptions.csv` | 190 | root_cause, delay_minutes, severity, cascaded, recovery_action |
| `fatigue_logs.csv` | 2,586 | total_duty_hrs, utilization_pct, rest_violations, fatigue_risk_score |

**Design principles:**
- Hub callout rates calibrated to realistic patterns (ORD: 8.2%, LAX: 3.9%)
- Monday disruption multiplier of 1.6× reflects real-world post-weekend patterns
- Red-eye pairings carry a 1.45× disruption probability — matching NTSB fatigue data
- Fatigue scores composite: duty hours + rest violations + red-eye exposure

---

## Key Findings

1. **ORD Monday callout rate is 2.1× the network average**, concentrated in red-eye pairing types. Adjusting Sunday pairing cutoff times is projected to reduce Monday callouts by ~18%.

2. **Crew callout is the #1 disruption root cause (28%)**, followed by weather (22%) and ATC delays (15%). High-severity disruptions cascade 55% of the time — making early intervention critical.

3. **Deadhead rate of 8.5% represents significant cost exposure.** Three routes account for 31% of all deadhead legs — a targeted reassignment of those pairings could recover 200+ duty hours per month.

4. **Average crew utilization is 80%**, but ORD and JFK show utilization spikes above 90% in Q1, correlated with elevated fatigue scores and rest violations.

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data Generation | Python (numpy, pandas) |
| Data Storage | SQLite |
| SQL Analysis | SQLite / standard ANSI SQL |
| Modeling | Python (pandas, rolling forecasts) |
| Visualization | Tableau Public |
| Documentation | Markdown, PDF |

---

## How to Run

```bash
# Clone the repo
git clone https://github.com/yourusername/crewiq-airline-crew-analytics.git
cd crewiq-airline-crew-analytics

# Install dependencies
pip install pandas numpy

# Generate all datasets
python notebooks/01_data_generation.py

# Run SQL analysis (requires SQLite)
sqlite3 crewiq.db < sql/01_schema.sql
sqlite3 crewiq.db < sql/02_crew_availability.sql
```

---

## Business Context

This project is designed to mirror the analytical scope of a **Crew Strategy & Intelligence** role at a major airline. The core questions it answers are:

- *Which bases are projected to fall below minimum crew coverage in the next 2 weeks?*
- *What structural patterns are driving chronic disruptions — and when/where do they peak?*
- *Which pairings are operationally inefficient, and what is the cost exposure?*
- *Which crew members are at elevated fatigue risk, and how does that correlate with callout behavior?*

These are the exact questions that fuel scheduling adjustments, reserve policy changes, and workforce planning decisions at airline operations centers.

---

## License

MIT License — free to use, adapt, and build on.

---

*Built as a portfolio project for Crew Strategy & Intelligence roles in the airline industry.*
