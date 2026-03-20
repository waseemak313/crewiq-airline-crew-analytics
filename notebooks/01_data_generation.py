"""
CrewIQ — Module 1: Synthetic Data Generation
=============================================
Generates realistic airline crew operations data:
  - crew_roster.csv       : 500 crew members across 5 hubs
  - flight_schedule.csv   : 3,000 flight pairings over 6 months
  - disruptions.csv       : disruption events with root causes
  - fatigue_logs.csv      : duty hours and rest periods per crew member

All distributions are calibrated to real-world airline norms:
  - FAA/ICAO duty time limits (Part 117)
  - Industry-average callout rates (~4-6% per month)
  - Realistic hub-and-spoke network structure
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os

# ── Reproducibility ─────────────────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Constants ────────────────────────────────────────────────────────────────
HUBS = ['ORD', 'ATL', 'DFW', 'LAX', 'JFK']

# Spoke airports per hub (realistic route network)
SPOKES = {
    'ORD': ['MSP', 'DTW', 'MKE', 'STL', 'IND', 'CMH', 'CLE', 'PIT'],
    'ATL': ['MCO', 'MIA', 'CLT', 'BNA', 'MSY', 'TPA', 'RDU', 'CHS'],
    'DFW': ['HOU', 'SAT', 'AUS', 'OKC', 'TUL', 'ABQ', 'ELP', 'LBB'],
    'LAX': ['SFO', 'SAN', 'LAS', 'PHX', 'SJC', 'SMF', 'BUR', 'ONT'],
    'JFK': ['BOS', 'PHL', 'DCA', 'BWI', 'BDL', 'ALB', 'SYR', 'ROC'],
}

AIRCRAFT_TYPES = ['B737', 'B757', 'B767', 'A320', 'A321', 'B787']

# Crew counts per hub (weighted toward larger hubs)
HUB_CREW_WEIGHTS = {'ORD': 0.25, 'ATL': 0.25, 'DFW': 0.20, 'LAX': 0.18, 'JFK': 0.12}

# Callout rate multipliers per hub (ORD structurally higher — weather + scheduling)
CALLOUT_RATE = {'ORD': 0.082, 'ATL': 0.048, 'DFW': 0.051, 'LAX': 0.039, 'JFK': 0.057}

# Simulation period
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 6, 30)
N_DAYS     = (END_DATE - START_DATE).days + 1

FIRST_NAMES = [
    'James', 'Maria', 'Robert', 'Linda', 'Michael', 'Barbara', 'William', 'Patricia',
    'David', 'Jennifer', 'Richard', 'Jessica', 'Joseph', 'Sarah', 'Thomas', 'Karen',
    'Charles', 'Lisa', 'Christopher', 'Nancy', 'Daniel', 'Margaret', 'Matthew', 'Betty',
    'Anthony', 'Sandra', 'Mark', 'Ashley', 'Donald', 'Dorothy', 'Steven', 'Kimberly',
    'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle', 'Kenneth', 'Carol',
    'Kevin', 'Amanda', 'Brian', 'Melissa', 'George', 'Deborah', 'Timothy', 'Stephanie',
    'Ronald', 'Rebecca', 'Edward', 'Sharon', 'Jason', 'Laura', 'Jeffrey', 'Cynthia',
    'Ryan', 'Kathleen', 'Jacob', 'Amy', 'Gary', 'Angela', 'Nicholas', 'Shirley',
    'Eric', 'Anna', 'Jonathan', 'Brenda', 'Stephen', 'Pamela', 'Larry', 'Emma',
    'Justin', 'Nicole', 'Scott', 'Helen', 'Brandon', 'Samantha', 'Benjamin', 'Katherine'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
    'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
    'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
    'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
    'Carter', 'Roberts', 'Turner', 'Phillips', 'Evans', 'Collins', 'Stewart', 'Morris',
    'Murphy', 'Cook', 'Rogers', 'Morgan', 'Peterson', 'Cooper', 'Reed', 'Bailey',
    'Bell', 'Gomez', 'Kelly', 'Howard', 'Ward', 'Cox', 'Diaz', 'Richardson', 'Wood',
    'Watson', 'Brooks', 'Bennett', 'Gray', 'James', 'Reyes', 'Cruz', 'Hughes', 'Price'
]


# ═══════════════════════════════════════════════════════════════════════════
# 1. CREW ROSTER
# ═══════════════════════════════════════════════════════════════════════════
def generate_crew_roster(n=500):
    print("  Generating crew roster...")

    # Distribute crew across hubs by weight
    hub_counts = {}
    remaining = n
    hubs_list = list(HUBS)
    for i, hub in enumerate(hubs_list[:-1]):
        count = int(n * HUB_CREW_WEIGHTS[hub])
        hub_counts[hub] = count
        remaining -= count
    hub_counts[hubs_list[-1]] = remaining

    rows = []
    emp_id = 10001
    for hub, count in hub_counts.items():
        for _ in range(count):
            crew_type = np.random.choice(
                ['Captain', 'First Officer', 'Flight Attendant', 'Senior FA'],
                p=[0.18, 0.22, 0.42, 0.18]
            )

            # Seniority: captains and senior FAs have longer tenure
            if crew_type in ['Captain', 'Senior FA']:
                years_service = np.random.gamma(shape=6, scale=2.5)
            else:
                years_service = np.random.gamma(shape=2, scale=3.0)
            years_service = np.clip(years_service, 0.5, 35)

            hire_date = START_DATE - timedelta(days=int(years_service * 365))

            # Aircraft qualification (pilots rated on 1-3 types)
            all_ac = list(AIRCRAFT_TYPES)
            n_qual = np.random.choice([1, 2, 3], p=[0.45, 0.40, 0.15]) if crew_type in ['Captain', 'First Officer'] else 1
            qualifications = ', '.join(np.random.choice(all_ac, size=n_qual, replace=False))

            # Employment status
            status = np.random.choice(
                ['Active', 'Leave', 'Training', 'Inactive'],
                p=[0.87, 0.06, 0.05, 0.02]
            )

            # Contract type
            contract = np.random.choice(['Full-time', 'Part-time'], p=[0.88, 0.12])

            first = np.random.choice(FIRST_NAMES)
            last  = np.random.choice(LAST_NAMES)

            rows.append({
                'employee_id':      emp_id,
                'full_name':        f'{first} {last}',
                'crew_type':        crew_type,
                'base':             hub,
                'hire_date':        hire_date.strftime('%Y-%m-%d'),
                'years_of_service': round(years_service, 1),
                'aircraft_qual':    qualifications,
                'employment_status': status,
                'contract_type':    contract,
                'monthly_hour_cap': 100 if crew_type in ['Captain', 'First Officer'] else 90,
            })
            emp_id += 1

    df = pd.DataFrame(rows)
    print(f"    ✓ {len(df)} crew members across {df['base'].nunique()} hubs")
    print(f"    ✓ Types: {df['crew_type'].value_counts().to_dict()}")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 2. FLIGHT SCHEDULE / PAIRINGS
# ═══════════════════════════════════════════════════════════════════════════
def generate_flight_schedule(crew_df, n=3000):
    print("  Generating flight schedule...")

    active_crew = crew_df[crew_df['employment_status'] == 'Active'].copy()

    rows = []
    pairing_id = 50001

    # Distribute pairings across 26 weeks (~115/week)
    dates = [START_DATE + timedelta(days=i) for i in range(N_DAYS)]

    for i in range(n):
        dep_date = np.random.choice(dates)
        hub      = np.random.choice(HUBS, p=[0.25, 0.25, 0.20, 0.18, 0.12])
        spokes   = SPOKES[hub]
        dest     = np.random.choice(spokes)

        # Flight duration (hub-to-spoke: 1-5 hrs depending on hub)
        duration_hrs = np.random.uniform(1.0, 5.5)

        # Departure hour — realistic airline schedule peaks
        raw_p = np.array([0.06, 0.08, 0.09, 0.08, 0.07, 0.07, 0.06, 0.06, 0.05,
                          0.05, 0.05, 0.05, 0.05, 0.04, 0.04, 0.04, 0.04, 0.03])
        raw_p = raw_p / raw_p.sum()
        dep_hour = np.random.choice(list(range(5, 23)), p=raw_p)
        dep_time = dep_date + timedelta(hours=int(dep_hour), minutes=int(np.random.choice([0, 15, 30, 45])))
        arr_time = dep_time + timedelta(hours=duration_hrs)

        # Aircraft type
        aircraft = np.random.choice(AIRCRAFT_TYPES, p=[0.30, 0.15, 0.10, 0.25, 0.15, 0.05])

        # Crew required (based on aircraft)
        if aircraft in ['B767', 'B787']:
            pilots_req, fa_req = 2, 4
        elif aircraft in ['B757', 'A321']:
            pilots_req, fa_req = 2, 3
        else:
            pilots_req, fa_req = 2, 2

        # Assign a pilot and FA from same base
        base_crew = active_crew[active_crew['base'] == hub]
        pilots    = base_crew[base_crew['crew_type'].isin(['Captain', 'First Officer'])]
        fas       = base_crew[base_crew['crew_type'].isin(['Flight Attendant', 'Senior FA'])]

        assigned_pilot = int(pilots['employee_id'].sample(1).values[0]) if len(pilots) > 0 else None
        assigned_fa    = int(fas['employee_id'].sample(1).values[0])    if len(fas)    > 0 else None

        # Is this a deadhead? (positioning flight, ~8% of pairings)
        is_deadhead = np.random.random() < 0.08

        # Pairing type
        pairing_type = np.random.choice(
            ['Turn', 'Overnight', 'Multi-day', 'Red-eye'],
            p=[0.40, 0.30, 0.20, 0.10]
        )

        rows.append({
            'pairing_id':       pairing_id,
            'departure_date':   dep_date.strftime('%Y-%m-%d'),
            'departure_time':   dep_time.strftime('%Y-%m-%d %H:%M'),
            'arrival_time':     arr_time.strftime('%Y-%m-%d %H:%M'),
            'origin':           hub,
            'destination':      dest,
            'aircraft_type':    aircraft,
            'flight_duration_hrs': round(duration_hrs, 2),
            'pairing_type':     pairing_type,
            'pilots_required':  pilots_req,
            'fas_required':     fa_req,
            'assigned_pilot_id': assigned_pilot,
            'assigned_fa_id':   assigned_fa,
            'is_deadhead':      is_deadhead,
            'base':             hub,
        })
        pairing_id += 1

    df = pd.DataFrame(rows)
    print(f"    ✓ {len(df)} pairings | Deadheads: {df['is_deadhead'].sum()} ({df['is_deadhead'].mean()*100:.1f}%)")
    print(f"    ✓ Pairing types: {df['pairing_type'].value_counts().to_dict()}")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 3. DISRUPTIONS
# ═══════════════════════════════════════════════════════════════════════════
def generate_disruptions(schedule_df, crew_df):
    print("  Generating disruption logs...")

    ROOT_CAUSES = {
        'Crew callout':       0.28,  # sick call, personal emergency
        'Weather':            0.22,  # most common operational cause
        'ATC delay':          0.15,
        'Mechanical':         0.12,
        'Late inbound aircraft': 0.10,
        'Crew rest violation': 0.07, # FAA Part 117 trigger
        'Training conflict':  0.04,
        'Other':              0.02,
    }

    rows = []
    disruption_id = 70001

    for _, pairing in schedule_df.iterrows():
        hub = pairing['base']
        base_callout_rate = CALLOUT_RATE[hub]

        # Day-of-week effect (Monday worst, Friday second worst)
        dep_date = datetime.strptime(pairing['departure_date'], '%Y-%m-%d')
        dow = dep_date.weekday()  # 0=Mon, 6=Sun
        dow_multiplier = {0: 1.60, 1: 1.00, 2: 0.90, 3: 0.95, 4: 1.25, 5: 0.80, 6: 1.10}[dow]

        # Red-eye multiplier (disruptions much more likely after red-eye)
        redye_mult = 1.45 if pairing['pairing_type'] == 'Red-eye' else 1.0

        disruption_prob = base_callout_rate * dow_multiplier * redye_mult

        if np.random.random() < disruption_prob:
            root_cause = np.random.choice(
                list(ROOT_CAUSES.keys()),
                p=list(ROOT_CAUSES.values())
            )

            # Delay minutes distribution varies by cause
            delay_dist = {
                'Weather':            ('lognormal', 3.8, 0.9),
                'Mechanical':         ('lognormal', 4.0, 0.7),
                'Crew callout':       ('lognormal', 3.2, 0.8),
                'ATC delay':          ('lognormal', 3.0, 0.6),
                'Late inbound aircraft': ('lognormal', 2.8, 0.7),
                'Crew rest violation': ('lognormal', 4.2, 0.5),
                'Training conflict':  ('lognormal', 2.5, 0.6),
                'Other':              ('lognormal', 2.6, 0.8),
            }
            dist_params = delay_dist[root_cause]
            delay_min = int(np.clip(np.random.lognormal(dist_params[1], dist_params[2]), 15, 480))

            # Severity classification
            if delay_min < 60:
                severity = 'Low'
            elif delay_min < 180:
                severity = 'Medium'
            else:
                severity = 'High'

            # Did it cascade? (High-severity disruptions more likely to cascade)
            cascade_prob = {'Low': 0.05, 'Medium': 0.22, 'High': 0.55}[severity]
            cascaded = np.random.random() < cascade_prob

            # Recovery action taken
            recovery_actions = {
                'Crew callout':       ['Reserve activated', 'Pairing reassigned', 'Flight cancelled'],
                'Weather':            ['Delayed', 'Diverted', 'Cancelled', 'Held at gate'],
                'Mechanical':         ['Aircraft swapped', 'Delayed for repair', 'Flight cancelled'],
                'ATC delay':          ['Ground stop', 'Rerouted', 'Held'],
                'Late inbound aircraft': ['Gate hold', 'Crew swap', 'Delayed'],
                'Crew rest violation': ['Reserve activated', 'Flight delayed', 'Pairing split'],
                'Training conflict':  ['Training rescheduled', 'Reserve activated'],
                'Other':              ['Delayed', 'Cancelled'],
            }
            recovery = np.random.choice(recovery_actions[root_cause])

            rows.append({
                'disruption_id':   disruption_id,
                'pairing_id':      pairing['pairing_id'],
                'disruption_date': pairing['departure_date'],
                'base':            hub,
                'origin':          pairing['origin'],
                'destination':     pairing['destination'],
                'pairing_type':    pairing['pairing_type'],
                'root_cause':      root_cause,
                'delay_minutes':   delay_min,
                'severity':        severity,
                'cascaded':        cascaded,
                'recovery_action': recovery,
                'day_of_week':     dep_date.strftime('%A'),
                'month':           dep_date.strftime('%B'),
            })
            disruption_id += 1

    df = pd.DataFrame(rows)
    print(f"    ✓ {len(df)} disruptions ({len(df)/len(schedule_df)*100:.1f}% of pairings affected)")
    print(f"    ✓ Severity: {df['severity'].value_counts().to_dict()}")
    print(f"    ✓ Top cause: {df['root_cause'].value_counts().idxmax()}")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 4. FATIGUE / DUTY LOGS
# ═══════════════════════════════════════════════════════════════════════════
def generate_fatigue_logs(crew_df, schedule_df):
    print("  Generating fatigue and duty logs...")

    active_crew = crew_df[crew_df['employment_status'] == 'Active']
    rows = []
    log_id = 90001

    # Generate monthly logs for each active crew member
    months = pd.date_range(START_DATE, END_DATE, freq='MS')  # month starts

    for _, crew in active_crew.iterrows():
        emp_id   = crew['employee_id']
        hub      = crew['base']
        cap      = crew['monthly_hour_cap']
        c_type   = crew['crew_type']

        for month_start in months:
            month_end = month_start + pd.offsets.MonthEnd(0)

            # How many pairings did this crew member fly this month?
            # (Approximate — in real data this would be joined from schedule)
            if c_type in ['Captain', 'First Officer']:
                n_pairings = np.random.randint(8, 20)
            else:
                n_pairings = np.random.randint(10, 24)

            # Total duty hours (correlated with pairings)
            # FAA Part 117: pilots max 100 hrs/28 days; FAs max 90 hrs/month
            avg_hrs_per_pairing = np.random.uniform(3.5, 7.0)
            total_duty_hrs = round(n_pairings * avg_hrs_per_pairing, 1)
            total_duty_hrs = min(total_duty_hrs, cap * 1.05)  # allow slight overage for realism

            # Rest violations (flags where rest < 10 hrs between duties)
            rest_violations = 0
            if total_duty_hrs > cap * 0.85:
                rest_violations = np.random.randint(0, 3)
            
            # Consecutive days worked
            max_consec_days = np.random.randint(3, 7) if c_type in ['Captain', 'First Officer'] else np.random.randint(4, 8)

            # Fatigue risk score (composite: hours + violations + red-eye proportion)
            redye_pct = np.random.uniform(0.0, 0.25)
            fatigue_score = (
                (total_duty_hrs / cap) * 50 +
                rest_violations * 12 +
                redye_pct * 25 +
                np.random.normal(0, 3)
            )
            fatigue_score = round(np.clip(fatigue_score, 0, 100), 1)

            # Utilization rate
            utilization_pct = round(total_duty_hrs / cap * 100, 1)

            # Called out this month?
            callout_this_month = np.random.random() < (CALLOUT_RATE[hub] * 4)  # monthly rate

            rows.append({
                'log_id':              log_id,
                'employee_id':         emp_id,
                'base':                hub,
                'crew_type':           c_type,
                'month':               month_start.strftime('%Y-%m'),
                'total_duty_hrs':      total_duty_hrs,
                'monthly_hour_cap':    cap,
                'utilization_pct':     utilization_pct,
                'n_pairings_flown':    n_pairings,
                'rest_violations':     rest_violations,
                'max_consecutive_days': max_consec_days,
                'redye_pairing_pct':   round(redye_pct * 100, 1),
                'fatigue_risk_score':  fatigue_score,
                'called_out':          callout_this_month,
            })
            log_id += 1

    df = pd.DataFrame(rows)
    print(f"    ✓ {len(df)} monthly duty records across {df['employee_id'].nunique()} crew members")
    print(f"    ✓ Avg utilization: {df['utilization_pct'].mean():.1f}%")
    print(f"    ✓ Avg fatigue score: {df['fatigue_risk_score'].mean():.1f}/100")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "="*60)
    print("  CrewIQ — Module 1: Data Generation")
    print("="*60)

    crew_df     = generate_crew_roster(n=500)
    schedule_df = generate_flight_schedule(crew_df, n=3000)
    disrupt_df  = generate_disruptions(schedule_df, crew_df)
    fatigue_df  = generate_fatigue_logs(crew_df, schedule_df)

    # ── Save to CSV ──────────────────────────────────────────────────────
    print("\n  Saving datasets...")
    crew_df.to_csv(    os.path.join(OUTPUT_DIR, 'crew_roster.csv'),      index=False)
    schedule_df.to_csv(os.path.join(OUTPUT_DIR, 'flight_schedule.csv'),  index=False)
    disrupt_df.to_csv( os.path.join(OUTPUT_DIR, 'disruptions.csv'),      index=False)
    fatigue_df.to_csv( os.path.join(OUTPUT_DIR, 'fatigue_logs.csv'),     index=False)

    print("\n" + "="*60)
    print("  DATASET SUMMARY")
    print("="*60)
    print(f"  crew_roster.csv    : {len(crew_df):>6,} rows  | {len(crew_df.columns)} columns")
    print(f"  flight_schedule.csv: {len(schedule_df):>6,} rows  | {len(schedule_df.columns)} columns")
    print(f"  disruptions.csv    : {len(disrupt_df):>6,} rows  | {len(disrupt_df.columns)} columns")
    print(f"  fatigue_logs.csv   : {len(fatigue_df):>6,} rows  | {len(fatigue_df.columns)} columns")
    print(f"\n  Disruption rate    : {len(disrupt_df)/len(schedule_df)*100:.1f}% of pairings")
    print(f"  Avg fatigue score  : {fatigue_df['fatigue_risk_score'].mean():.1f} / 100")
    print(f"  High severity dis. : {(disrupt_df['severity']=='High').sum()}")
    print("\n  ✓ All files saved to /data/")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
