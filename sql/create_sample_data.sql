-- =====================================================
-- Analytics Business Framework - Sample Data for BigQuery
-- Project: team-begamob
-- Dataset: analytics
-- =====================================================

-- Bước 1: Tạo Dataset (nếu chưa có)
-- CREATE SCHEMA IF NOT EXISTS `team-begamob.analytics`;

-- =====================================================
-- Bảng 1: daily_metrics
-- Chứa dữ liệu DAU, doanh thu, chi tiêu theo ngày
-- =====================================================

CREATE TABLE IF NOT EXISTS `team-begamob.analytics.daily_metrics` (
    date DATE,
    user_id STRING,
    ad_revenue FLOAT64,
    iap_revenue FLOAT64,
    spend FLOAT64
);

-- Xóa dữ liệu cũ (nếu cần)
-- DELETE FROM `team-begamob.analytics.daily_metrics` WHERE TRUE;

-- Insert sample data (90 ngày gần đây)
INSERT INTO `team-begamob.analytics.daily_metrics` (date, user_id, ad_revenue, iap_revenue, spend)
WITH date_range AS (
    SELECT DATE_SUB(CURRENT_DATE(), INTERVAL day_offset DAY) as date
    FROM UNNEST(GENERATE_ARRAY(0, 89)) as day_offset
),
users AS (
    SELECT CONCAT('user_', LPAD(CAST(user_num AS STRING), 5, '0')) as user_id
    FROM UNNEST(GENERATE_ARRAY(1, 50000)) as user_num
),
daily_users AS (
    SELECT 
        d.date,
        u.user_id,
        -- Mỗi ngày chọn random khoảng 50% users hoạt động
        RAND() as user_rand
    FROM date_range d
    CROSS JOIN users u
)
SELECT 
    date,
    user_id,
    -- Ad Revenue: $0.001 - $0.01 per user per day
    ROUND(0.001 + RAND() * 0.009, 6) as ad_revenue,
    -- IAP Revenue: 5% users mua, $0.5 - $10 per purchase
    CASE 
        WHEN RAND() < 0.05 THEN ROUND(0.5 + RAND() * 9.5, 2)
        ELSE 0 
    END as iap_revenue,
    -- Spend được tính tổng theo ngày (sẽ cùng giá trị cho tất cả users trong ngày)
    0 as spend  -- Sẽ update sau
FROM daily_users
WHERE user_rand < 0.5;  -- ~50% DAU

-- Update spend cho mỗi ngày (tổng chi tiêu UA)
UPDATE `team-begamob.analytics.daily_metrics` m
SET spend = daily_spend.spend_per_user
FROM (
    SELECT 
        date,
        -- Chi tiêu $1000-$3000 per day, chia đều cho users
        ROUND((1000 + RAND() * 2000) / COUNT(*), 4) as spend_per_user
    FROM `team-begamob.analytics.daily_metrics`
    GROUP BY date
) daily_spend
WHERE m.date = daily_spend.date;


-- =====================================================
-- Bảng 2: cohort_retention
-- Chứa dữ liệu retention theo cohort
-- =====================================================

CREATE TABLE IF NOT EXISTS `team-begamob.analytics.cohort_retention` (
    cohort_date DATE,
    days_since_install INT64,
    user_id STRING,
    cohort_size INT64
);

-- Insert sample cohort data
INSERT INTO `team-begamob.analytics.cohort_retention` (cohort_date, days_since_install, user_id, cohort_size)
WITH cohorts AS (
    -- Tạo 10 cohorts, mỗi cohort 10,000 users
    SELECT 
        DATE_SUB(CURRENT_DATE(), INTERVAL (cohort_num * 10) DAY) as cohort_date,
        10000 as cohort_size,
        cohort_num
    FROM UNNEST(GENERATE_ARRAY(1, 10)) as cohort_num
),
users_per_cohort AS (
    SELECT 
        c.cohort_date,
        c.cohort_size,
        CONCAT('cohort_', c.cohort_num, '_user_', LPAD(CAST(user_num AS STRING), 5, '0')) as user_id
    FROM cohorts c
    CROSS JOIN UNNEST(GENERATE_ARRAY(1, 10000)) as user_num
),
retention_days AS (
    SELECT day FROM UNNEST([0, 1, 3, 7, 14, 30, 60, 90]) as day
),
-- Retention curve: D0=100%, D1=40%, D3=30%, D7=20%, D14=15%, D30=10%, D60=7%, D90=5%
retention_rates AS (
    SELECT 0 as day, 1.0 as rate UNION ALL
    SELECT 1, 0.40 UNION ALL
    SELECT 3, 0.30 UNION ALL
    SELECT 7, 0.20 UNION ALL
    SELECT 14, 0.15 UNION ALL
    SELECT 30, 0.10 UNION ALL
    SELECT 60, 0.07 UNION ALL
    SELECT 90, 0.05
)
SELECT 
    u.cohort_date,
    r.day as days_since_install,
    u.user_id,
    u.cohort_size
FROM users_per_cohort u
CROSS JOIN retention_rates r
WHERE RAND() < r.rate;  -- Randomly select users based on retention rate


-- =====================================================
-- Bảng 3: campaigns
-- Chứa dữ liệu performance của các chiến dịch UA
-- =====================================================

CREATE TABLE IF NOT EXISTS `team-begamob.analytics.campaigns` (
    date DATE,
    campaign_id STRING,
    campaign_name STRING,
    media_source STRING,
    country STRING,
    installs INT64,
    spend FLOAT64,
    revenue_d7 FLOAT64
);

-- Insert sample campaign data
INSERT INTO `team-begamob.analytics.campaigns` (date, campaign_id, campaign_name, media_source, country, installs, spend, revenue_d7)
WITH date_range AS (
    SELECT DATE_SUB(CURRENT_DATE(), INTERVAL day_offset DAY) as date
    FROM UNNEST(GENERATE_ARRAY(0, 29)) as day_offset  -- 30 ngày
),
media_sources AS (
    SELECT * FROM UNNEST([
        STRUCT('facebook' as source, 'Facebook Ads' as name),
        STRUCT('google', 'Google UAC'),
        STRUCT('unity', 'Unity Ads'),
        STRUCT('applovin', 'AppLovin'),
        STRUCT('tiktok', 'TikTok Ads'),
        STRUCT('organic', 'Organic')
    ])
),
countries AS (
    SELECT * FROM UNNEST(['US', 'VN', 'BR', 'IN', 'TH', 'ID', 'JP', 'KR']) as country
),
campaigns AS (
    SELECT 
        d.date,
        CONCAT(m.source, '_', c.country, '_', FORMAT_DATE('%Y%m', d.date)) as campaign_id,
        CONCAT(m.name, ' - ', c.country) as campaign_name,
        m.source as media_source,
        c.country,
        -- CPI varies by country: US $2-5, VN $0.3-0.8, others $0.5-2
        CASE c.country
            WHEN 'US' THEN 2.0 + RAND() * 3.0
            WHEN 'VN' THEN 0.3 + RAND() * 0.5
            WHEN 'BR' THEN 0.4 + RAND() * 0.6
            WHEN 'IN' THEN 0.2 + RAND() * 0.4
            ELSE 0.5 + RAND() * 1.5
        END as cpi,
        -- Base installs per day per campaign: 50-500
        CAST(50 + RAND() * 450 AS INT64) as base_installs
    FROM date_range d
    CROSS JOIN media_sources m
    CROSS JOIN countries c
    WHERE m.source != 'organic' OR RAND() < 0.3  -- Fewer organic entries
)
SELECT 
    date,
    campaign_id,
    campaign_name,
    media_source,
    country,
    base_installs as installs,
    ROUND(base_installs * cpi, 2) as spend,
    -- D7 Revenue: ROAS varies 0.5-1.5
    ROUND(base_installs * cpi * (0.5 + RAND() * 1.0), 2) as revenue_d7
FROM campaigns;


-- =====================================================
-- Bảng 4: user_segments (cho Prediction & Action)
-- =====================================================

CREATE TABLE IF NOT EXISTS `team-begamob.analytics.user_segments` (
    user_id STRING,
    segment STRING,
    ltv_predicted FLOAT64,
    churn_probability FLOAT64,
    last_active_date DATE,
    days_since_install INT64
);

INSERT INTO `team-begamob.analytics.user_segments` (user_id, segment, ltv_predicted, churn_probability, last_active_date, days_since_install)
WITH users AS (
    SELECT 
        CONCAT('user_', LPAD(CAST(user_num AS STRING), 5, '0')) as user_id,
        user_num
    FROM UNNEST(GENERATE_ARRAY(1, 10000)) as user_num
)
SELECT 
    user_id,
    -- Segment based on random distribution
    CASE 
        WHEN RAND() < 0.05 THEN 'Whale'
        WHEN RAND() < 0.15 THEN 'Dolphin'
        WHEN RAND() < 0.40 THEN 'Minnow'
        ELSE 'Free User'
    END as segment,
    -- LTV varies by implied segment
    ROUND(0.5 + RAND() * 10, 2) as ltv_predicted,
    -- Churn probability
    ROUND(RAND(), 4) as churn_probability,
    -- Last active: within 30 days
    DATE_SUB(CURRENT_DATE(), INTERVAL CAST(RAND() * 30 AS INT64) DAY) as last_active_date,
    -- Days since install: 1-365
    CAST(1 + RAND() * 364 AS INT64) as days_since_install
FROM users;


-- =====================================================
-- Bảng 5: funnel_events (cho Funnel Analysis)
-- =====================================================

CREATE TABLE IF NOT EXISTS `team-begamob.analytics.funnel_events` (
    date DATE,
    user_id STRING,
    step_name STRING,
    step_order INT64
);

INSERT INTO `team-begamob.analytics.funnel_events` (date, user_id, step_name, step_order)
WITH users AS (
    SELECT 
        CONCAT('user_', LPAD(CAST(user_num AS STRING), 5, '0')) as user_id
    FROM UNNEST(GENERATE_ARRAY(1, 10000)) as user_num
),
funnel_steps AS (
    SELECT * FROM UNNEST([
        STRUCT('App Open' as step_name, 1 as step_order, 1.0 as conversion_rate),
        STRUCT('Onboarding Start', 2, 0.85),
        STRUCT('Onboarding Complete', 3, 0.68),
        STRUCT('First Action', 4, 0.51),
        STRUCT('Trial Start', 5, 0.20),
        STRUCT('Subscription', 6, 0.03)
    ])
)
SELECT 
    CURRENT_DATE() as date,
    u.user_id,
    f.step_name,
    f.step_order
FROM users u
CROSS JOIN funnel_steps f
WHERE RAND() < f.conversion_rate;


-- =====================================================
-- Kiểm tra dữ liệu đã tạo
-- =====================================================

-- Kiểm tra daily_metrics
SELECT 
    date,
    COUNT(DISTINCT user_id) as dau,
    ROUND(SUM(ad_revenue), 2) as total_ad_revenue,
    ROUND(SUM(iap_revenue), 2) as total_iap_revenue,
    ROUND(SUM(spend), 2) as total_spend
FROM `team-begamob.analytics.daily_metrics`
GROUP BY date
ORDER BY date DESC
LIMIT 10;

-- Kiểm tra campaigns
SELECT 
    media_source,
    COUNT(DISTINCT campaign_id) as campaigns,
    SUM(installs) as total_installs,
    ROUND(SUM(spend), 2) as total_spend,
    ROUND(SUM(revenue_d7) / SUM(spend), 4) as avg_roas
FROM `team-begamob.analytics.campaigns`
GROUP BY media_source
ORDER BY total_spend DESC;
