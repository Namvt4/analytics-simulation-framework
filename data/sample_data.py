"""
Analytics Business Framework - Sample Data
Provides sample data for testing and demo purposes when BigQuery is not available
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG


def generate_daily_metrics(days: int = 90) -> pd.DataFrame:
    """
    Generate sample daily metrics data
    
    Args:
        days: Number of days of data to generate
        
    Returns:
        DataFrame with daily metrics (DAU, Revenue, ROAS, etc.)
    """
    np.random.seed(42)
    
    base_date = datetime.now() - timedelta(days=days)
    dates = [base_date + timedelta(days=i) for i in range(days)]
    
    # Base values with some trend and seasonality
    base_dau = 50000
    base_spend = 5000
    
    data = []
    for i, date in enumerate(dates):
        # Add weekly seasonality (weekends have higher DAU)
        weekday_factor = 1.2 if date.weekday() >= 5 else 1.0
        
        # Add some growth trend
        growth_factor = 1 + (i / days) * 0.15
        
        # Random variation
        random_factor = np.random.normal(1.0, 0.1)
        
        dau = int(base_dau * weekday_factor * growth_factor * random_factor)
        spend = base_spend * growth_factor * np.random.normal(1.0, 0.15)
        
        arpdau = CONFIG.ads.arpdau_d0 * np.random.normal(1.0, 0.1)
        iaa_revenue = dau * arpdau
        
        # Calculate subscription revenue from all plans
        total_pay_rate = CONFIG.subscription.get_total_pay_rate()
        avg_sub_price = 5.0  # Rough average
        iap_revenue = dau * total_pay_rate * avg_sub_price / 30 * np.random.normal(1.0, 0.2)
        total_revenue = iaa_revenue + iap_revenue
        
        roas = total_revenue / spend if spend > 0 else 0
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'dau': dau,
            'iaa_revenue': round(iaa_revenue, 2),
            'iap_revenue': round(iap_revenue, 2),
            'total_revenue': round(total_revenue, 2),
            'total_spend': round(spend, 2),
            'roas': round(roas, 4)
        })
    
    return pd.DataFrame(data)


def generate_cohort_retention(cohort_size: int = 10000) -> pd.DataFrame:
    """
    Generate sample cohort retention data based on config
    
    Args:
        cohort_size: Initial cohort size
        
    Returns:
        DataFrame with retention by day
    """
    retention_curve = CONFIG.retention.get_curve()
    known_days = sorted(retention_curve.keys())
    
    data = []
    
    # Interpolate for all days up to 90
    for day in range(91):
        if day in retention_curve:
            rate = retention_curve[day]
        else:
            # Find surrounding known points
            prev_day = max([d for d in known_days if d < day])
            next_day = min([d for d in known_days if d > day])
            
            prev_rate = retention_curve[prev_day]
            next_rate = retention_curve[next_day]
            
            # Linear interpolation in log space
            progress = (day - prev_day) / (next_day - prev_day)
            log_rate = np.log(prev_rate) + progress * (np.log(next_rate) - np.log(prev_rate))
            rate = np.exp(log_rate)
        
        # Add some random variation
        rate = max(0.001, min(1.0, rate * np.random.normal(1.0, 0.05)))
        active_users = int(cohort_size * rate)
        
        data.append({
            'days_since_install': day,
            'active_users': active_users,
            'retention_rate': round(rate, 4),
            'cohort_size': cohort_size
        })
    
    return pd.DataFrame(data)


def generate_campaign_performance(n_campaigns: int = 20) -> pd.DataFrame:
    """
    Generate sample campaign performance data
    
    Args:
        n_campaigns: Number of campaigns to generate
        
    Returns:
        DataFrame with campaign metrics
    """
    np.random.seed(42)
    
    media_sources = ['Facebook', 'Google', 'TikTok', 'Unity', 'ironSource', 'AppLovin']
    countries = ['US', 'DE', 'UK', 'JP', 'BR', 'IN', 'FR', 'CA']
    
    data = []
    for i in range(n_campaigns):
        source = np.random.choice(media_sources)
        country = np.random.choice(countries)
        
        # Different sources have different typical metrics
        source_multipliers = {
            'Facebook': {'cpi': 1.0, 'roas': 1.1},
            'Google': {'cpi': 1.2, 'roas': 1.0},
            'TikTok': {'cpi': 0.7, 'roas': 0.9},
            'Unity': {'cpi': 0.5, 'roas': 0.8},
            'ironSource': {'cpi': 0.4, 'roas': 0.75},
            'AppLovin': {'cpi': 0.6, 'roas': 0.85}
        }
        
        mult = source_multipliers[source]
        
        installs = np.random.randint(500, 10000)
        cpi = CONFIG.ua.cpi_paid * mult['cpi'] * np.random.normal(1.0, 0.2)
        spend = installs * cpi
        
        # D7 revenue based on LTV estimate
        ltv_d7 = CONFIG.ads.arpdau_d0 * 7 * 0.5  # Rough D7 LTV
        revenue_d7 = installs * ltv_d7 * mult['roas'] * np.random.normal(1.0, 0.3)
        roas_d7 = revenue_d7 / spend if spend > 0 else 0
        
        data.append({
            'campaign_id': f'camp_{i+1:03d}',
            'campaign_name': f'{source}_{country}_{i+1}',
            'media_source': source,
            'country': country,
            'installs': installs,
            'spend': round(spend, 2),
            'cpi': round(cpi, 2),
            'revenue_d7': round(revenue_d7, 2),
            'roas_d7': round(roas_d7, 4)
        })
    
    return pd.DataFrame(data)


def generate_user_segments(n_users: int = 1000) -> pd.DataFrame:
    """
    Generate sample user segment data
    
    Args:
        n_users: Number of users to generate
        
    Returns:
        DataFrame with user segments
    """
    np.random.seed(42)
    
    segments = [
        'High Value - Engaged',
        'High Value - At Risk',
        'Medium Value - Engaged',
        'Medium Value - At Risk',
        'Low Value - Engaged',
        'Low Value - At Risk',
        'New User'
    ]
    
    segment_weights = [0.05, 0.03, 0.15, 0.10, 0.30, 0.17, 0.20]
    
    data = []
    for i in range(n_users):
        segment = np.random.choice(segments, p=segment_weights)
        
        # LTV and churn based on segment
        if 'High Value' in segment:
            ltv = np.random.uniform(5.0, 20.0)
        elif 'Medium Value' in segment:
            ltv = np.random.uniform(1.0, 5.0)
        else:
            ltv = np.random.uniform(0.1, 1.0)
        
        if 'At Risk' in segment:
            churn_prob = np.random.uniform(0.5, 0.9)
        elif 'New User' in segment:
            churn_prob = np.random.uniform(0.3, 0.6)
        else:
            churn_prob = np.random.uniform(0.05, 0.3)
        
        days_since_install = np.random.randint(0, 180)
        last_active_days_ago = np.random.randint(0, min(30, days_since_install + 1))
        
        data.append({
            'user_id': f'user_{i+1:06d}',
            'segment': segment,
            'ltv_predicted': round(ltv, 2),
            'churn_probability': round(churn_prob, 4),
            'days_since_install': days_since_install,
            'last_active_date': (datetime.now() - timedelta(days=last_active_days_ago)).strftime('%Y-%m-%d')
        })
    
    return pd.DataFrame(data)


def generate_funnel_data() -> pd.DataFrame:
    """
    Generate sample funnel conversion data
    
    Returns:
        DataFrame with funnel steps
    """
    steps = [
        ('App Open', 1, 10000),
        ('Onboarding Start', 2, 8500),
        ('Onboarding Complete', 3, 6800),
        ('First Action', 4, 5100),
        ('Trial Start', 5, 2040),
        ('Subscription Purchase', 6, 306)
    ]
    
    data = []
    for step_name, step_order, users in steps:
        prev_users = steps[step_order - 2][2] if step_order > 1 else users
        conversion_rate = users / prev_users if prev_users > 0 else 1.0
        
        data.append({
            'step_name': step_name,
            'step_order': step_order,
            'users': users,
            'conversion_rate': round(conversion_rate, 4),
            'drop_off_rate': round(1 - conversion_rate, 4)
        })
    
    return pd.DataFrame(data)


class SampleDataProvider:
    """
    Provides sample data for testing when BigQuery is not available
    """
    
    def __init__(self):
        self._cache = {}
    
    def get_daily_metrics(self, days: int = 90) -> pd.DataFrame:
        """Get cached or generate daily metrics"""
        cache_key = f'daily_{days}'
        if cache_key not in self._cache:
            self._cache[cache_key] = generate_daily_metrics(days)
        return self._cache[cache_key]
    
    def get_cohort_retention(self, cohort_size: int = 10000) -> pd.DataFrame:
        """Get cached or generate cohort retention"""
        cache_key = f'retention_{cohort_size}'
        if cache_key not in self._cache:
            self._cache[cache_key] = generate_cohort_retention(cohort_size)
        return self._cache[cache_key]
    
    def get_campaign_performance(self, n_campaigns: int = 20) -> pd.DataFrame:
        """Get cached or generate campaign performance"""
        cache_key = f'campaigns_{n_campaigns}'
        if cache_key not in self._cache:
            self._cache[cache_key] = generate_campaign_performance(n_campaigns)
        return self._cache[cache_key]
    
    def get_user_segments(self, n_users: int = 1000) -> pd.DataFrame:
        """Get cached or generate user segments"""
        cache_key = f'users_{n_users}'
        if cache_key not in self._cache:
            self._cache[cache_key] = generate_user_segments(n_users)
        return self._cache[cache_key]
    
    def get_funnel_data(self) -> pd.DataFrame:
        """Get cached or generate funnel data"""
        if 'funnel' not in self._cache:
            self._cache['funnel'] = generate_funnel_data()
        return self._cache['funnel']


# Singleton instance
_provider = None

def get_sample_data() -> SampleDataProvider:
    """Get or create sample data provider instance"""
    global _provider
    if _provider is None:
        _provider = SampleDataProvider()
    return _provider
