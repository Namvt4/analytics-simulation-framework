"""
Analytics Business Framework - Step 4: Analysis
Root Cause Analysis (RCA), Drill-down, Funnel, and Cohort Analysis

Trả lời câu hỏi: "Tại sao doanh thu giảm? Do ARPU giảm hay 
Retention của tệp Android ở thị trường Mỹ đi xuống?"
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG


class DrilldownAnalyzer:
    """
    Drill-down Analysis
    
    Phân rã chỉ số theo Dimension:
    - Country
    - Media Source
    - App Version
    - Device Type
    - User Segment
    """
    
    def __init__(self):
        self.dimensions = ['country', 'media_source', 'version', 'device', 'segment']
    
    def analyze_metric_by_dimension(self, 
                                     data: pd.DataFrame,
                                     metric: str,
                                     dimension: str,
                                     baseline_value: float = None) -> pd.DataFrame:
        """
        Analyze a metric broken down by dimension
        
        Args:
            data: DataFrame with metrics and dimensions
            metric: Metric column to analyze
            dimension: Dimension column to group by
            baseline_value: Expected value for comparison
            
        Returns:
            DataFrame with dimension breakdown and variances
        """
        if dimension not in data.columns or metric not in data.columns:
            return pd.DataFrame()
        
        # Group by dimension
        grouped = data.groupby(dimension).agg({
            metric: ['sum', 'mean', 'count']
        }).reset_index()
        
        grouped.columns = [dimension, 'total', 'average', 'count']
        
        # Calculate contribution and variance
        total_sum = grouped['total'].sum()
        grouped['contribution_pct'] = (grouped['total'] / total_sum * 100).round(2)
        
        if baseline_value:
            grouped['vs_baseline'] = ((grouped['average'] - baseline_value) / baseline_value * 100).round(2)
            grouped['status'] = grouped['vs_baseline'].apply(
                lambda x: '🟢 Above' if x > 5 else ('🔴 Below' if x < -5 else '🟡 On Track')
            )
        
        return grouped.sort_values('total', ascending=False)
    
    def find_problem_areas(self, 
                           current_data: pd.DataFrame,
                           baseline_data: pd.DataFrame,
                           metric: str,
                           threshold_pct: float = 10) -> List[Dict]:
        """
        Identify dimensions with significant performance drops
        
        Args:
            current_data: Current period data
            baseline_data: Baseline/previous period data
            metric: Metric to analyze
            threshold_pct: Threshold for flagging significant drops
            
        Returns:
            List of problem areas with details
        """
        problems = []
        
        for dimension in self.dimensions:
            if dimension not in current_data.columns:
                continue
            
            current = current_data.groupby(dimension)[metric].mean()
            baseline = baseline_data.groupby(dimension)[metric].mean()
            
            for dim_value in current.index:
                if dim_value in baseline.index:
                    current_val = current[dim_value]
                    baseline_val = baseline[dim_value]
                    
                    if baseline_val > 0:
                        change_pct = (current_val - baseline_val) / baseline_val * 100
                        
                        if change_pct < -threshold_pct:
                            problems.append({
                                'dimension': dimension,
                                'value': dim_value,
                                'metric': metric,
                                'current': round(current_val, 4),
                                'baseline': round(baseline_val, 4),
                                'change_pct': round(change_pct, 2),
                                'impact': '🔴 High' if change_pct < -20 else '🟠 Medium'
                            })
        
        # Sort by severity
        problems.sort(key=lambda x: x['change_pct'])
        return problems
    
    def waterfall_decomposition(self, 
                                 current_data: pd.DataFrame,
                                 baseline_data: pd.DataFrame,
                                 metric: str,
                                 dimension: str) -> pd.DataFrame:
        """
        Create waterfall decomposition showing contribution of each dimension value
        
        Args:
            current_data: Current data
            baseline_data: Baseline data
            metric: Metric to decompose
            dimension: Dimension to analyze
            
        Returns:
            DataFrame with waterfall components
        """
        if dimension not in current_data.columns:
            return pd.DataFrame()
        
        current = current_data.groupby(dimension)[metric].sum()
        baseline = baseline_data.groupby(dimension)[metric].sum()
        
        all_dims = set(current.index) | set(baseline.index)
        
        components = []
        for dim_value in all_dims:
            curr_val = current.get(dim_value, 0)
            base_val = baseline.get(dim_value, 0)
            delta = curr_val - base_val
            
            components.append({
                dimension: dim_value,
                'baseline': round(base_val, 2),
                'current': round(curr_val, 2),
                'delta': round(delta, 2),
                'delta_pct': round(delta / base_val * 100, 2) if base_val > 0 else 0
            })
        
        df = pd.DataFrame(components)
        return df.sort_values('delta')


class FunnelAnalyzer:
    """
    Funnel Analysis
    
    Tìm ra điểm rơi (drop-off) trong hành trình trải nghiệm người dùng.
    """
    
    def __init__(self):
        self.default_funnel = [
            'app_open',
            'onboarding_start',
            'onboarding_complete',
            'first_action',
            'trial_start',
            'subscription_purchase'
        ]
    
    def analyze_funnel(self, funnel_data: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze funnel conversion rates
        
        Args:
            funnel_data: DataFrame with columns [step_name, step_order, users]
            
        Returns:
            DataFrame with conversion analysis
        """
        df = funnel_data.sort_values('step_order').copy()
        
        # Calculate conversion rates
        df['prev_users'] = df['users'].shift(1)
        df['conversion_rate'] = (df['users'] / df['prev_users']).fillna(1.0)
        df['drop_off_rate'] = 1 - df['conversion_rate']
        df['cumulative_conversion'] = df['users'] / df['users'].iloc[0]
        
        # Identify biggest drops
        df['drop_off_absolute'] = (df['prev_users'] - df['users']).fillna(0).astype(int)
        
        return df
    
    def find_biggest_dropoff(self, funnel_data: pd.DataFrame) -> Dict:
        """
        Find the step with the biggest drop-off
        
        Args:
            funnel_data: Funnel data
            
        Returns:
            Dictionary with biggest drop-off details
        """
        analysis = self.analyze_funnel(funnel_data)
        
        # Skip first row (no previous step)
        analysis = analysis.iloc[1:]
        
        if analysis.empty:
            return {}
        
        # Find max drop-off
        max_drop_idx = analysis['drop_off_rate'].idxmax()
        max_drop_row = analysis.loc[max_drop_idx]
        
        return {
            'step_name': max_drop_row['step_name'],
            'step_order': int(max_drop_row['step_order']),
            'drop_off_rate': round(max_drop_row['drop_off_rate'] * 100, 2),
            'users_lost': int(max_drop_row['drop_off_absolute']),
            'conversion_rate': round(max_drop_row['conversion_rate'] * 100, 2),
            'recommendation': f"Investigate why users drop at '{max_drop_row['step_name']}' step"
        }
    
    def compare_funnels(self, 
                        funnel_a: pd.DataFrame, 
                        funnel_b: pd.DataFrame,
                        label_a: str = "Current",
                        label_b: str = "Previous") -> pd.DataFrame:
        """
        Compare two funnels (e.g., current vs previous period)
        
        Args:
            funnel_a: First funnel data
            funnel_b: Second funnel data
            label_a: Label for first funnel
            label_b: Label for second funnel
            
        Returns:
            DataFrame with comparison
        """
        analysis_a = self.analyze_funnel(funnel_a)
        analysis_b = self.analyze_funnel(funnel_b)
        
        merged = analysis_a.merge(
            analysis_b[['step_name', 'conversion_rate', 'users']],
            on='step_name',
            suffixes=(f'_{label_a}', f'_{label_b}')
        )
        
        merged['conversion_diff'] = (
            merged[f'conversion_rate_{label_a}'] - merged[f'conversion_rate_{label_b}']
        ) * 100
        
        return merged


class CohortAnalyzer:
    """
    Cohort Analysis
    
    So sánh hiệu quả giữa các đợt cập nhật hoặc chiến dịch UA.
    """
    
    def __init__(self):
        pass
    
    def build_retention_matrix(self, 
                                cohort_data: pd.DataFrame,
                                cohort_column: str = 'cohort_date',
                                day_column: str = 'days_since_install',
                                value_column: str = 'retention_rate') -> pd.DataFrame:
        """
        Build a cohort retention matrix
        
        Args:
            cohort_data: Data with cohort, day, and retention info
            cohort_column: Column identifying cohort
            day_column: Column with days since install
            value_column: Column with retention rate
            
        Returns:
            Pivot table with cohorts as rows, days as columns
        """
        matrix = cohort_data.pivot_table(
            values=value_column,
            index=cohort_column,
            columns=day_column,
            aggfunc='mean'
        )
        
        return matrix.round(4)
    
    def compare_cohorts(self, 
                        cohort_a_data: pd.DataFrame,
                        cohort_b_data: pd.DataFrame,
                        metrics: List[str] = None) -> pd.DataFrame:
        """
        Compare two cohorts on key metrics
        
        Args:
            cohort_a_data: First cohort data
            cohort_b_data: Second cohort data
            metrics: List of metrics to compare
            
        Returns:
            DataFrame with comparison
        """
        if metrics is None:
            metrics = ['retention_rate', 'ltv', 'arpu', 'sessions']
        
        results = []
        
        for metric in metrics:
            if metric in cohort_a_data.columns and metric in cohort_b_data.columns:
                mean_a = cohort_a_data[metric].mean()
                mean_b = cohort_b_data[metric].mean()
                diff = mean_a - mean_b
                diff_pct = (diff / mean_b * 100) if mean_b != 0 else 0
                
                results.append({
                    'Metric': metric,
                    'Cohort A': round(mean_a, 4),
                    'Cohort B': round(mean_b, 4),
                    'Difference': round(diff, 4),
                    'Difference %': f"{diff_pct:+.1f}%",
                    'Winner': 'A' if diff > 0 else ('B' if diff < 0 else 'Tie')
                })
        
        return pd.DataFrame(results)
    
    def calculate_cohort_ltv_curve(self, 
                                    cohort_data: pd.DataFrame,
                                    max_day: int = 90) -> pd.DataFrame:
        """
        Calculate cumulative LTV curve for a cohort
        
        Args:
            cohort_data: Cohort data with daily revenue
            max_day: Maximum days to analyze
            
        Returns:
            DataFrame with daily cumulative LTV
        """
        days = range(max_day + 1)
        cumulative_ltv = []
        
        for day in days:
            day_data = cohort_data[cohort_data['days_since_install'] <= day]
            total_ltv = day_data['revenue'].sum() / day_data['user_id'].nunique()
            cumulative_ltv.append({
                'day': day,
                'cumulative_ltv': round(total_ltv, 4)
            })
        
        return pd.DataFrame(cumulative_ltv)


class CannibalizationDetector:
    """
    Cannibalization Detector
    
    Phân tích sự xung đột giữa các dòng tiền 
    (Ví dụ: Ads có làm giảm tỷ lệ Sub không?)
    """
    
    def __init__(self):
        pass
    
    def analyze_revenue_streams(self, user_data: pd.DataFrame) -> Dict:
        """
        Analyze relationship between revenue streams
        
        Args:
            user_data: DataFrame with iaa_revenue and iap_revenue columns
            
        Returns:
            Dictionary with cannibalization analysis
        """
        # Calculate correlations
        if 'iaa_revenue' in user_data.columns and 'iap_revenue' in user_data.columns:
            correlation = user_data['iaa_revenue'].corr(user_data['iap_revenue'])
        else:
            correlation = 0
        
        # Segment users
        high_ads = user_data['iaa_revenue'] > user_data['iaa_revenue'].median()
        low_ads = ~high_ads
        
        high_ads_iap = user_data.loc[high_ads, 'iap_revenue'].mean()
        low_ads_iap = user_data.loc[low_ads, 'iap_revenue'].mean()
        
        cannibalization_detected = high_ads_iap < low_ads_iap * 0.9
        
        return {
            'correlation': round(correlation, 4),
            'high_ads_iap_mean': round(high_ads_iap, 4),
            'low_ads_iap_mean': round(low_ads_iap, 4),
            'iap_difference_pct': round((high_ads_iap - low_ads_iap) / low_ads_iap * 100, 2) if low_ads_iap > 0 else 0,
            'cannibalization_detected': cannibalization_detected,
            'recommendation': (
                "Consider reducing ad frequency for high-value subscription prospects"
                if cannibalization_detected else
                "No significant cannibalization detected"
            )
        }
    
    def ab_test_analysis(self, 
                          control_data: pd.DataFrame,
                          treatment_data: pd.DataFrame,
                          metric: str) -> Dict:
        """
        Analyze A/B test for cannibalization
        
        Args:
            control_data: Control group data
            treatment_data: Treatment group data
            metric: Metric to analyze
            
        Returns:
            Dictionary with test results
        """
        control_mean = control_data[metric].mean()
        treatment_mean = treatment_data[metric].mean()
        
        control_std = control_data[metric].std()
        treatment_std = treatment_data[metric].std()
        
        # Simple t-test approximation
        pooled_std = np.sqrt(
            (control_std**2 / len(control_data)) + 
            (treatment_std**2 / len(treatment_data))
        )
        
        z_score = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0
        
        # Approximate p-value
        significant = abs(z_score) > 1.96  # 95% confidence
        
        return {
            'control_mean': round(control_mean, 4),
            'treatment_mean': round(treatment_mean, 4),
            'difference': round(treatment_mean - control_mean, 4),
            'difference_pct': round((treatment_mean - control_mean) / control_mean * 100, 2) if control_mean > 0 else 0,
            'z_score': round(z_score, 4),
            'significant': significant,
            'conclusion': (
                f"Treatment {'increased' if treatment_mean > control_mean else 'decreased'} {metric} by "
                f"{abs(treatment_mean - control_mean) / control_mean * 100:.1f}% "
                f"({'statistically significant' if significant else 'not significant'})"
            )
        }


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 4: ANALYSIS (RCA)")
    print("=" * 60)
    
    # Funnel Analysis Demo
    print("\n📊 Funnel Analysis:")
    funnel_analyzer = FunnelAnalyzer()
    
    funnel_data = pd.DataFrame([
        {'step_name': 'App Open', 'step_order': 1, 'users': 10000},
        {'step_name': 'Onboarding Start', 'step_order': 2, 'users': 8500},
        {'step_name': 'Onboarding Complete', 'step_order': 3, 'users': 6800},
        {'step_name': 'First Action', 'step_order': 4, 'users': 5100},
        {'step_name': 'Trial Start', 'step_order': 5, 'users': 2040},
        {'step_name': 'Subscription', 'step_order': 6, 'users': 306}
    ])
    
    biggest_drop = funnel_analyzer.find_biggest_dropoff(funnel_data)
    if biggest_drop:
        print(f"  Biggest drop-off: {biggest_drop['step_name']}")
        print(f"  Drop-off rate: {biggest_drop['drop_off_rate']}%")
        print(f"  Users lost: {biggest_drop['users_lost']:,}")
        print(f"  💡 {biggest_drop['recommendation']}")
