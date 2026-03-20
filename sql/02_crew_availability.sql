-- ============================================================
-- CrewIQ — 02_crew_availability.sql
-- Weekly crew availability by base and crew type
-- Flags weeks where coverage falls below safe thresholds
-- ============================================================

-- ── 1. Active crew headcount by base and type ────────────────
SELECT
    '── ACTIVE CREW BY BASE ──' AS section,
    '' AS base, '' AS crew_type, '' AS headcount,
    '' AS pct_of_base, '' AS note

UNION ALL

SELECT
    '',
    base,
    crew_type,
    COUNT(*)                                            AS headcount,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY base), 1) AS pct_of_base,
    CASE
        WHEN COUNT(*) < 15 THEN '⚠ LOW HEADCOUNT'
        ELSE ''
    END                                                 AS note
FROM crew_roster
WHERE employment_status = 'Active'
GROUP BY base, crew_type
ORDER BY base, headcount DESC;


-- ── 2. Monthly utilization and coverage by base ──────────────
SELECT '' AS spacer;
SELECT '── MONTHLY UTILIZATION BY BASE ──' AS section;

SELECT
    base,
    month,
    COUNT(DISTINCT employee_id)                         AS active_crew,
    ROUND(AVG(utilization_pct), 1)                      AS avg_utilization_pct,
    ROUND(AVG(fatigue_risk_score), 1)                   AS avg_fatigue_score,
    SUM(rest_violations)                                AS total_rest_violations,
    SUM(called_out)                                     AS total_callouts,
    ROUND(SUM(called_out) * 100.0 / COUNT(*), 1)        AS callout_rate_pct,
    CASE
        WHEN AVG(utilization_pct) > 90 THEN '🔴 OVER-UTILIZED'
        WHEN AVG(utilization_pct) > 80 THEN '🟡 WATCH'
        ELSE '🟢 OK'
    END                                                 AS utilization_flag
FROM fatigue_logs
GROUP BY base, month
ORDER BY base, month;


-- ── 3. Coverage gap detection ────────────────────────────────
-- Flags base+months where callout rate exceeds 8% (critical threshold)
SELECT '' AS spacer;
SELECT '── COVERAGE GAP ALERTS (callout rate > 8%) ──' AS section;

SELECT
    base,
    month,
    COUNT(DISTINCT employee_id)                         AS crew_count,
    SUM(called_out)                                     AS callouts,
    ROUND(SUM(called_out) * 100.0 / COUNT(*), 1)        AS callout_rate_pct,
    ROUND(AVG(fatigue_risk_score), 1)                   AS avg_fatigue_score,
    '⚠ COVERAGE RISK'                                   AS alert
FROM fatigue_logs
GROUP BY base, month
HAVING ROUND(SUM(called_out) * 100.0 / COUNT(*), 1) > 8.0
ORDER BY callout_rate_pct DESC;


-- ── 4. ORD vs network callout rate comparison ────────────────
-- The key finding: ORD callout rate vs all other bases combined
SELECT '' AS spacer;
SELECT '── ORD vs NETWORK CALLOUT RATE ──' AS section;

SELECT
    CASE WHEN base = 'ORD' THEN 'ORD (hub focus)' ELSE 'All other bases' END AS hub_group,
    COUNT(DISTINCT employee_id)                         AS crew_members,
    SUM(called_out)                                     AS total_callouts,
    ROUND(SUM(called_out) * 100.0 / COUNT(*), 2)        AS callout_rate_pct,
    ROUND(AVG(fatigue_risk_score), 1)                   AS avg_fatigue_score,
    ROUND(AVG(redye_pairing_pct), 1)                    AS avg_redye_exposure_pct
FROM fatigue_logs
GROUP BY CASE WHEN base = 'ORD' THEN 'ORD (hub focus)' ELSE 'All other bases' END
ORDER BY callout_rate_pct DESC;


-- ── 5. Crew members at highest fatigue risk ───────────────────
-- Top 15 crew by avg fatigue score — potential retention/burnout flags
SELECT '' AS spacer;
SELECT '── TOP 15 HIGH FATIGUE RISK CREW ──' AS section;

SELECT
    fl.employee_id,
    cr.full_name,
    cr.crew_type,
    cr.base,
    cr.years_of_service,
    ROUND(AVG(fl.fatigue_risk_score), 1)                AS avg_fatigue_score,
    ROUND(AVG(fl.utilization_pct), 1)                   AS avg_utilization_pct,
    SUM(fl.rest_violations)                             AS total_rest_violations,
    SUM(fl.called_out)                                  AS total_callouts,
    ROUND(AVG(fl.redye_pairing_pct), 1)                 AS avg_redye_pct
FROM fatigue_logs fl
JOIN crew_roster cr ON fl.employee_id = cr.employee_id
GROUP BY fl.employee_id
ORDER BY avg_fatigue_score DESC
LIMIT 15;
