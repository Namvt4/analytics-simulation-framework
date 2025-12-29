"""
Generate sample CSV files for BigQuery import
Run: python generate_sample_csv.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

# Create folder
os.makedirs('sample_csv', exist_ok=True)

print("=" * 50)
print("Generating Sample CSV Files for BigQuery")
print("=" * 50)

# 1. daily_metrics (simplified - aggregated)
print("\n1️⃣ Creating daily_metrics.csv...")
dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
daily_records = []
for date in dates:
    dau = int(45000 + np.random.randint(-5000, 10000))
    for _ in range(min(dau, 1000)):  # Sample 1000 users per day
        user_id = f'user_{np.random.randint(1, 50001):05d}'
        daily_records.append({
            'date': date.strftime('%Y-%m-%d'),
            'user_id': user_id,
            'ad_revenue': round(0.001 + np.random.random() * 0.009, 6),
            'iap_revenue': round(0.5 + np.random.random() * 9.5, 2) if np.random.random() < 0.05 else 0,
            'spend': round(0.05 + np.random.random() * 0.05, 4)
        })

df = pd.DataFrame(daily_records)
df.to_csv('sample_csv/daily_metrics.csv', index=False)
print(f"   ✅ Created: {len(df):,} records")

# 2. campaigns
print("\n2️⃣ Creating campaigns.csv...")
sources = ['facebook', 'google', 'unity', 'applovin', 'tiktok']
source_names = {'facebook': 'Facebook Ads', 'google': 'Google UAC', 'unity': 'Unity Ads', 
                'applovin': 'AppLovin', 'tiktok': 'TikTok Ads'}
countries = ['US', 'VN', 'BR', 'IN', 'TH', 'ID', 'JP', 'KR']
cpi_map = {'US': 2.5, 'VN': 0.4, 'BR': 0.5, 'IN': 0.3, 'TH': 0.6, 'ID': 0.5, 'JP': 2.0, 'KR': 1.5}

campaign_records = []
for day in range(30):
    date = (datetime.now() - timedelta(days=day)).strftime('%Y-%m-%d')
    for source in sources:
        for country in countries:
            cpi = cpi_map.get(country, 0.8) * (0.8 + np.random.random() * 0.4)
            installs = int(100 + np.random.random() * 400)
            spend = round(installs * cpi, 2)
            roas = 0.4 + np.random.random() * 1.2
            campaign_records.append({
                'date': date,
                'campaign_id': f'{source}_{country}_{date[:7].replace("-", "")}',
                'campaign_name': f'{source_names[source]} - {country}',
                'media_source': source,
                'country': country,
                'installs': installs,
                'spend': spend,
                'revenue_d7': round(spend * roas, 2)
            })

df = pd.DataFrame(campaign_records)
df.to_csv('sample_csv/campaigns.csv', index=False)
print(f"   ✅ Created: {len(df):,} records")

# 3. cohort_retention
print("\n3️⃣ Creating cohort_retention.csv...")
retention_rates = {0: 1.0, 1: 0.40, 3: 0.30, 7: 0.20, 14: 0.15, 30: 0.10, 60: 0.07, 90: 0.05}
cohort_records = []
for cohort_num in range(1, 6):  # 5 cohorts
    cohort_date = (datetime.now() - timedelta(days=cohort_num * 15)).strftime('%Y-%m-%d')
    cohort_size = 5000
    for user_num in range(1, 501):  # 500 sample users per cohort
        user_id = f'cohort_{cohort_num}_user_{user_num:05d}'
        for day, rate in retention_rates.items():
            if np.random.random() < rate:
                cohort_records.append({
                    'cohort_date': cohort_date,
                    'days_since_install': day,
                    'user_id': user_id,
                    'cohort_size': cohort_size
                })

df = pd.DataFrame(cohort_records)
df.to_csv('sample_csv/cohort_retention.csv', index=False)
print(f"   ✅ Created: {len(df):,} records")

# 4. user_segments
print("\n4️⃣ Creating user_segments.csv...")
segments = ['Whale', 'Dolphin', 'Minnow', 'Free User']
segment_probs = [0.05, 0.10, 0.25, 0.60]

user_records = []
for i in range(1, 5001):
    segment = np.random.choice(segments, p=segment_probs)
    ltv_mult = {'Whale': 5, 'Dolphin': 2, 'Minnow': 1, 'Free User': 0.2}[segment]
    user_records.append({
        'user_id': f'user_{i:05d}',
        'segment': segment,
        'ltv_predicted': round(ltv_mult * (0.5 + np.random.random()), 2),
        'churn_probability': round(np.random.random(), 4),
        'last_active_date': (datetime.now() - timedelta(days=int(np.random.random() * 30))).strftime('%Y-%m-%d'),
        'days_since_install': int(1 + np.random.random() * 364)
    })

df = pd.DataFrame(user_records)
df.to_csv('sample_csv/user_segments.csv', index=False)
print(f"   ✅ Created: {len(df):,} records")

# 5. funnel_events
print("\n5️⃣ Creating funnel_events.csv...")
funnel_steps = [
    ('App Open', 1, 1.0),
    ('Onboarding Start', 2, 0.85),
    ('Onboarding Complete', 3, 0.68),
    ('First Action', 4, 0.51),
    ('Trial Start', 5, 0.20),
    ('Subscription', 6, 0.03)
]

funnel_records = []
for i in range(1, 10001):
    user_id = f'user_{i:05d}'
    for step_name, step_order, rate in funnel_steps:
        if np.random.random() < rate:
            funnel_records.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'user_id': user_id,
                'step_name': step_name,
                'step_order': step_order
            })

df = pd.DataFrame(funnel_records)
df.to_csv('sample_csv/funnel_events.csv', index=False)
print(f"   ✅ Created: {len(df):,} records")

print("\n" + "=" * 50)
print("✅ All CSV files created in: sample_csv/")
print("=" * 50)
print("\nTo import to BigQuery:")
print("1. Open: https://console.cloud.google.com/bigquery")
print("2. Select project: team-begamob")
print("3. Create dataset: analytics")
print("4. CREATE TABLE → Upload CSV → Auto-detect schema")
