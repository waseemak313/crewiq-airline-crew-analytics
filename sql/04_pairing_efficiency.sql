-- ============================================================
-- CrewIQ — 04_pairing_efficiency.sql
-- Deadhead analysis, pairing cost efficiency, utilization KPIs
-- Identifies highest-cost routes and optimization opportunities
-- ============================================================

-- ── 1. Network-wide pairing efficiency summary ───────────────
SELECT '── NETWORK PAIRING EFFICIENCY SUMMARY ──' AS section;

SELECT
    COUNT(*)                                            AS total_pairings,
    SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END)    AS deadhead_pairings,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                        AS deadhead_rate_pct,
    ROUND(AVG(flight_duration_hrs), 2)                  AS avg_flight_duration_hrs,
    ROUND(SUM(flight_duration_hrs), 0)                  AS total_duty_hrs_flown,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN flight_duration_hrs ELSE 0 END), 0)
                                                        AS deadhead_duty_hrs_wasted,
    COUNT(DISTINCT origin || '-' || destination)        AS unique_routes
FROM flight_schedule;


-- ── 2. Deadhead rate by base ─────────────────────────────────
-- High deadhead = crew being repositioned = scheduling inefficiency
SELECT '' AS spacer;
SELECT '── DEADHEAD RATE BY BASE ──' AS section;

SELECT
    base,
    COUNT(*)                                            AS total_pairings,
    SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END)    AS deadhead_count,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                        AS deadhead_rate_pct,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN flight_duration_hrs ELSE 0 END), 1)
                                                        AS deadhead_hrs_wasted,
    CASE
        WHEN ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) > 10
        THEN '🔴 HIGH DEADHEAD — review crew positioning'
        WHEN ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) > 7
        THEN '🟡 ELEVATED'
        ELSE '🟢 ACCEPTABLE'
    END                                                 AS efficiency_flag
FROM flight_schedule
GROUP BY base
ORDER BY deadhead_rate_pct DESC;


-- ── 3. Top 10 routes by deadhead frequency ───────────────────
-- These are the specific routes to target for reassignment
SELECT '' AS spacer;
SELECT '── TOP 10 ROUTES BY DEADHEAD COUNT ──' AS section;

SELECT
    origin || ' → ' || destination                     AS route,
    base,
    COUNT(*)                                            AS total_pairings,
    SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END)    AS deadhead_count,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                        AS deadhead_rate_pct,
    ROUND(AVG(flight_duration_hrs), 2)                  AS avg_duration_hrs,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN flight_duration_hrs ELSE 0 END), 1)
                                                        AS deadhead_hrs_wasted
FROM flight_schedule
GROUP BY origin, destination
HAVING deadhead_count >= 3
ORDER BY deadhead_count DESC
LIMIT 10;


-- ── 4. Pairing type efficiency comparison ────────────────────
SELECT '' AS spacer;
SELECT '── EFFICIENCY BY PAIRING TYPE ──' AS section;

SELECT
    pairing_type,
    COUNT(*)                                            AS total_pairings,
    ROUND(AVG(flight_duration_hrs), 2)                  AS avg_duration_hrs,
    ROUND(AVG(pilots_required + fas_required), 1)       AS avg_crew_per_pairing,
    SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END)    AS deadheads,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                        AS deadhead_rate_pct,
    -- Efficiency score: higher duration + lower deadhead = more efficient
    ROUND(AVG(flight_duration_hrs) *
        (1 - SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)), 2)
                                                        AS efficiency_score
FROM flight_schedule
GROUP BY pairing_type
ORDER BY efficiency_score DESC;


-- ── 5. Aircraft utilization by type ──────────────────────────
SELECT '' AS spacer;
SELECT '── AIRCRAFT UTILIZATION BY TYPE ──' AS section;

SELECT
    aircraft_type,
    COUNT(*)                                            AS pairings,
    ROUND(AVG(flight_duration_hrs), 2)                  AS avg_flight_hrs,
    ROUND(SUM(flight_duration_hrs), 0)                  AS total_hrs_flown,
    AVG(pilots_required)                                AS pilots_per_flight,
    AVG(fas_required)                                   AS fas_per_flight,
    SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END)    AS deadheads,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                        AS deadhead_pct
FROM flight_schedule
GROUP BY aircraft_type
ORDER BY total_hrs_flown DESC;


-- ── 6. Monthly pairing volume trend ──────────────────────────
SELECT '' AS spacer;
SELECT '── MONTHLY PAIRING VOLUME AND EFFICIENCY TREND ──' AS section;

SELECT
    SUBSTR(departure_date, 1, 7)                        AS month,
    COUNT(*)                                            AS total_pairings,
    SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END)    AS deadheads,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                        AS deadhead_rate_pct,
    ROUND(AVG(flight_duration_hrs), 2)                  AS avg_duration_hrs,
    ROUND(SUM(flight_duration_hrs), 0)                  AS total_hrs
FROM flight_schedule
GROUP BY month
ORDER BY month;


-- ── 7. Optimization opportunity summary ──────────────────────
-- Executive-facing: what can we recover?
SELECT '' AS spacer;
SELECT '── OPTIMIZATION OPPORTUNITY SUMMARY ──' AS section;

SELECT
    'Deadhead reduction (top 10 routes)' AS opportunity,
    ROUND(SUM(CASE WHEN is_deadhead = 1 THEN flight_duration_hrs ELSE 0 END) *
        0.31, 0) || ' duty hours recoverable'           AS potential_impact
FROM flight_schedule

UNION ALL

SELECT
    'Avg pairing duration uplift (Turn → Overnight)',
    'Est. +0.8 hrs/pairing on ' ||
    COUNT(*) || ' Turn pairings'
FROM flight_schedule WHERE pairing_type = 'Turn'

UNION ALL

SELECT
    'Red-eye pairing reduction (disruption risk)',
    COUNT(*) || ' red-eye pairings = ' ||
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM flight_schedule), 1) ||
    '% of schedule — target <8%'
FROM flight_schedule WHERE pairing_type = 'Red-eye';
