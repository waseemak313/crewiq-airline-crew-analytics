-- ============================================================
-- CrewIQ — 03_disruption_analysis.sql
-- Root cause intelligence, severity breakdown, cascade rates
-- Monday pattern analysis and base-level disruption ranking
-- ============================================================

-- ── 1. Disruption root cause Pareto ──────────────────────────
-- The 80/20 view: which causes drive the most disruptions
SELECT '── DISRUPTION ROOT CAUSE PARETO ──' AS section;

SELECT
    root_cause,
    COUNT(*)                                            AS disruption_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_total,
    ROUND(AVG(delay_minutes), 0)                        AS avg_delay_min,
    MAX(delay_minutes)                                  AS max_delay_min,
    SUM(CASE WHEN cascaded = 1 THEN 1 ELSE 0 END)       AS cascaded_count,
    ROUND(SUM(CASE WHEN cascaded = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS cascade_rate_pct,
    ROUND(SUM(CASE WHEN severity = 'High' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS high_severity_pct
FROM disruptions
GROUP BY root_cause
ORDER BY disruption_count DESC;


-- ── 2. Disruption severity breakdown ─────────────────────────
SELECT '' AS spacer;
SELECT '── SEVERITY BREAKDOWN ──' AS section;

SELECT
    severity,
    COUNT(*)                                            AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_total,
    ROUND(AVG(delay_minutes), 0)                        AS avg_delay_min,
    ROUND(AVG(CASE WHEN cascaded = 1 THEN 1.0 ELSE 0.0 END) * 100, 1) AS cascade_rate_pct,
    GROUP_CONCAT(DISTINCT recovery_action)              AS recovery_actions_used
FROM disruptions
GROUP BY severity
ORDER BY CASE severity WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;


-- ── 3. Day-of-week disruption pattern ────────────────────────
-- Key finding: Monday spike driven by red-eye + rest patterns
SELECT '' AS spacer;
SELECT '── DISRUPTIONS BY DAY OF WEEK ──' AS section;

SELECT
    day_of_week,
    COUNT(*)                                            AS disruption_count,
    ROUND(AVG(delay_minutes), 0)                        AS avg_delay_min,
    SUM(CASE WHEN root_cause = 'Crew callout' THEN 1 ELSE 0 END) AS crew_callout_count,
    SUM(CASE WHEN cascaded = 1 THEN 1 ELSE 0 END)       AS cascaded_count,
    CASE
        WHEN COUNT(*) = (SELECT MAX(cnt) FROM (
            SELECT COUNT(*) AS cnt FROM disruptions GROUP BY day_of_week
        )) THEN '🔴 PEAK DAY'
        WHEN COUNT(*) >= (SELECT AVG(cnt) * 1.2 FROM (
            SELECT COUNT(*) AS cnt FROM disruptions GROUP BY day_of_week
        )) THEN '🟡 ELEVATED'
        ELSE ''
    END                                                 AS flag
FROM disruptions
GROUP BY day_of_week
ORDER BY CASE day_of_week
    WHEN 'Monday'    THEN 1 WHEN 'Tuesday'   THEN 2
    WHEN 'Wednesday' THEN 3 WHEN 'Thursday'  THEN 4
    WHEN 'Friday'    THEN 5 WHEN 'Saturday'  THEN 6
    WHEN 'Sunday'    THEN 7 END;


-- ── 4. Base-level disruption ranking ─────────────────────────
SELECT '' AS spacer;
SELECT '── DISRUPTIONS BY BASE ──' AS section;

SELECT
    d.base,
    COUNT(*)                                            AS total_disruptions,
    ROUND(COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM flight_schedule fs WHERE fs.base = d.base), 1)
                                                        AS disruption_rate_pct,
    ROUND(AVG(d.delay_minutes), 0)                      AS avg_delay_min,
    SUM(CASE WHEN d.severity = 'High' THEN 1 ELSE 0 END) AS high_severity,
    SUM(CASE WHEN d.root_cause = 'Crew callout' THEN 1 ELSE 0 END) AS crew_callouts,
    SUM(CASE WHEN d.cascaded = 1 THEN 1 ELSE 0 END)     AS cascaded,
    CASE
        WHEN ROUND(COUNT(*) * 100.0 /
            (SELECT COUNT(*) FROM flight_schedule fs WHERE fs.base = d.base), 1) > 7
        THEN '🔴 HIGH RISK BASE'
        WHEN ROUND(COUNT(*) * 100.0 /
            (SELECT COUNT(*) FROM flight_schedule fs WHERE fs.base = d.base), 1) > 5
        THEN '🟡 MONITOR'
        ELSE '🟢 STABLE'
    END                                                 AS risk_flag
FROM disruptions d
GROUP BY d.base
ORDER BY disruption_rate_pct DESC;


-- ── 5. Red-eye pairing disruption analysis ───────────────────
-- Quantifies the red-eye fatigue effect on disruption probability
SELECT '' AS spacer;
SELECT '── RED-EYE vs STANDARD PAIRING DISRUPTION RATE ──' AS section;

SELECT
    pairing_type,
    COUNT(*)                                            AS total_disruptions,
    ROUND(COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM flight_schedule fs WHERE fs.pairing_type = d.pairing_type), 1)
                                                        AS disruption_rate_pct,
    ROUND(AVG(delay_minutes), 0)                        AS avg_delay_min,
    SUM(CASE WHEN root_cause = 'Crew callout' THEN 1 ELSE 0 END) AS crew_callouts,
    SUM(CASE WHEN root_cause = 'Crew rest violation' THEN 1 ELSE 0 END) AS rest_violations
FROM disruptions d
GROUP BY pairing_type
ORDER BY disruption_rate_pct DESC;


-- ── 6. Monthly disruption trend ──────────────────────────────
SELECT '' AS spacer;
SELECT '── MONTHLY DISRUPTION TREND ──' AS section;

SELECT
    month,
    COUNT(*)                                            AS disruptions,
    ROUND(AVG(delay_minutes), 0)                        AS avg_delay_min,
    SUM(CASE WHEN severity = 'High' THEN 1 ELSE 0 END)  AS high_severity,
    SUM(CASE WHEN cascaded = 1 THEN 1 ELSE 0 END)        AS cascaded,
    SUM(CASE WHEN root_cause = 'Weather' THEN 1 ELSE 0 END) AS weather_related
FROM disruptions
GROUP BY month
ORDER BY CASE month
    WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3
    WHEN 'April'   THEN 4 WHEN 'May'      THEN 5 WHEN 'June'  THEN 6 END;
