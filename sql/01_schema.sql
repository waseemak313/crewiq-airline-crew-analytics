-- ============================================================
-- CrewIQ — 01_schema.sql
-- Table definitions and indexes for the CrewIQ database
-- ============================================================

-- ── Drop and recreate tables cleanly ────────────────────────
DROP TABLE IF EXISTS crew_roster;
DROP TABLE IF EXISTS flight_schedule;
DROP TABLE IF EXISTS disruptions;
DROP TABLE IF EXISTS fatigue_logs;

-- ── crew_roster ──────────────────────────────────────────────
CREATE TABLE crew_roster (
    employee_id         INTEGER PRIMARY KEY,
    full_name           TEXT    NOT NULL,
    crew_type           TEXT    NOT NULL,   -- Captain, First Officer, Flight Attendant, Senior FA
    base                TEXT    NOT NULL,   -- ORD, ATL, DFW, LAX, JFK
    hire_date           TEXT,
    years_of_service    REAL,
    aircraft_qual       TEXT,               -- comma-separated: 'B737, A320'
    employment_status   TEXT,               -- Active, Leave, Training, Inactive
    contract_type       TEXT,               -- Full-time, Part-time
    monthly_hour_cap    INTEGER             -- FAA Part 117: 100 pilots / 90 FAs
);

-- ── flight_schedule ──────────────────────────────────────────
CREATE TABLE flight_schedule (
    pairing_id          INTEGER PRIMARY KEY,
    departure_date      TEXT    NOT NULL,
    departure_time      TEXT,
    arrival_time        TEXT,
    origin              TEXT,
    destination         TEXT,
    aircraft_type       TEXT,
    flight_duration_hrs REAL,
    pairing_type        TEXT,               -- Turn, Overnight, Multi-day, Red-eye
    pilots_required     INTEGER,
    fas_required        INTEGER,
    assigned_pilot_id   INTEGER REFERENCES crew_roster(employee_id),
    assigned_fa_id      INTEGER REFERENCES crew_roster(employee_id),
    is_deadhead         INTEGER,            -- 0/1 boolean
    base                TEXT
);

-- ── disruptions ──────────────────────────────────────────────
CREATE TABLE disruptions (
    disruption_id       INTEGER PRIMARY KEY,
    pairing_id          INTEGER REFERENCES flight_schedule(pairing_id),
    disruption_date     TEXT    NOT NULL,
    base                TEXT,
    origin              TEXT,
    destination         TEXT,
    pairing_type        TEXT,
    root_cause          TEXT,               -- 8 categories
    delay_minutes       INTEGER,
    severity            TEXT,               -- Low, Medium, High
    cascaded            INTEGER,            -- 0/1 boolean
    recovery_action     TEXT,
    day_of_week         TEXT,
    month               TEXT
);

-- ── fatigue_logs ─────────────────────────────────────────────
CREATE TABLE fatigue_logs (
    log_id                  INTEGER PRIMARY KEY,
    employee_id             INTEGER REFERENCES crew_roster(employee_id),
    base                    TEXT,
    crew_type               TEXT,
    month                   TEXT,           -- YYYY-MM
    total_duty_hrs          REAL,
    monthly_hour_cap        INTEGER,
    utilization_pct         REAL,           -- total_duty_hrs / cap * 100
    n_pairings_flown        INTEGER,
    rest_violations         INTEGER,        -- count of <10hr rest gaps
    max_consecutive_days    INTEGER,
    redye_pairing_pct       REAL,
    fatigue_risk_score      REAL,           -- composite 0-100
    called_out              INTEGER         -- 0/1 boolean
);

-- ── Indexes for query performance ────────────────────────────
CREATE INDEX idx_crew_base       ON crew_roster(base);
CREATE INDEX idx_crew_type       ON crew_roster(crew_type);
CREATE INDEX idx_sched_base      ON flight_schedule(base);
CREATE INDEX idx_sched_date      ON flight_schedule(departure_date);
CREATE INDEX idx_sched_type      ON flight_schedule(pairing_type);
CREATE INDEX idx_dis_base        ON disruptions(base);
CREATE INDEX idx_dis_date        ON disruptions(disruption_date);
CREATE INDEX idx_dis_cause       ON disruptions(root_cause);
CREATE INDEX idx_fatigue_emp     ON fatigue_logs(employee_id);
CREATE INDEX idx_fatigue_base    ON fatigue_logs(base);
CREATE INDEX idx_fatigue_month   ON fatigue_logs(month);

SELECT 'Schema created successfully.' AS status;
