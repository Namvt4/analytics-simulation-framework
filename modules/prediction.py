"""
Analytics Business Framework - Step 2: Prediction
pLTV, Churn Prediction, and Fraud Detection

Trả lời câu hỏi: "User này có khả năng nạp tiền không? 
LTV của họ sau 365 ngày là bao nhiêu?"
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


class PLTVPredictor:
    """
    Predicted Lifetime Value (pLTV) Calculator
    
    Dự báo tổng doanh thu trọn đời (Hybrid LTV) ngay từ Day 0 hoặc Day 3
    bằng cách kết hợp dự báo:
    - Mua hàng (IAP)
    - Gia hạn thuê bao (Subscription)
    - Tương tác quảng cáo (IAA)
    """
    
    def __init__(self):
        self.retention_curve = CONFIG.retention.get_curve()
        self._build_daily_retention()
    
    def _build_daily_retention(self):
        """Build daily retention by interpolation"""
        known_days = sorted(self.retention_curve.keys())
        max_day = CONFIG.simulation_days
        
        self.daily_retention = {}
        
        for day in range(max_day + 1):
            if day in self.retention_curve:
                self.daily_retention[day] = self.retention_curve[day]
            else:
                prev_day = max([d for d in known_days if d < day], default=0)
                next_day = min([d for d in known_days if d > day], default=max_day)
                
                if prev_day == next_day:
                    self.daily_retention[day] = self.retention_curve.get(prev_day, 0.01)
                else:
                    prev_rate = self.retention_curve.get(prev_day, 1.0)
                    next_rate = self.retention_curve.get(next_day, 0.01)
                    progress = (day - prev_day) / (next_day - prev_day)
                    
                    log_prev = np.log(max(prev_rate, 0.001))
                    log_next = np.log(max(next_rate, 0.001))
                    self.daily_retention[day] = np.exp(log_prev + progress * (log_next - log_prev))
    
    def predict_ltv(self, 
                    days: int = 365,
                    observed_days: int = 0,
                    observed_revenue: float = 0,
                    retention_multiplier: float = 1.0) -> Dict:
        """
        Predict LTV for a user/cohort
        
        Args:
            days: Days to predict LTV
            observed_days: Days of observed data
            observed_revenue: Revenue already observed
            retention_multiplier: Adjustment based on early behavior
            
        Returns:
            Dictionary with LTV breakdown
        """
        arpdau = CONFIG.ads.arpdau
        sub_arpu_daily = CONFIG.subscription.get_subscription_arpu() / 30
        
        ltv_iaa = 0
        ltv_iap = 0
        daily_breakdown = []
        
        for day in range(days + 1):
            if day <= observed_days:
                # Use actual data for observed period
                daily_iaa = observed_revenue / (observed_days + 1) * 0.7  # 70% from ads
                daily_iap = observed_revenue / (observed_days + 1) * 0.3  # 30% from IAP
            else:
                # Predict future
                retention = self.daily_retention.get(day, 0.01) * retention_multiplier
                retention = min(1.0, max(0.001, retention))
                
                daily_iaa = retention * arpdau
                daily_iap = retention * sub_arpu_daily
            
            ltv_iaa += daily_iaa
            ltv_iap += daily_iap
            
            daily_breakdown.append({
                'day': day,
                'ltv_iaa_cumulative': ltv_iaa,
                'ltv_iap_cumulative': ltv_iap,
                'ltv_total_cumulative': ltv_iaa + ltv_iap
            })
        
        return {
            'ltv_iaa': round(ltv_iaa, 4),
            'ltv_iap': round(ltv_iap, 4),
            'ltv_total': round(ltv_iaa + ltv_iap, 4),
            'days': days,
            'observed_days': observed_days,
            'daily_breakdown': daily_breakdown
        }
    
    def predict_cohort_ltv(self, cohort_data: pd.DataFrame) -> pd.DataFrame:
        """
        Predict LTV for a cohort of users
        
        Args:
            cohort_data: DataFrame with columns [user_id, days_since_install, revenue_to_date]
            
        Returns:
            DataFrame with pLTV predictions for each user
        """
        results = []
        
        for _, row in cohort_data.iterrows():
            user_id = row.get('user_id', 'unknown')
            days_since_install = row.get('days_since_install', 0)
            revenue_to_date = row.get('revenue_to_date', 0)
            
            # Adjust retention multiplier based on observed behavior
            expected_retention = self.daily_retention.get(days_since_install, 0.1)
            if days_since_install > 0 and revenue_to_date > 0:
                # User is active and monetizing - boost multiplier
                retention_multiplier = 1.2
            elif days_since_install > 7 and revenue_to_date == 0:
                # User inactive - reduce multiplier
                retention_multiplier = 0.8
            else:
                retention_multiplier = 1.0
            
            ltv = self.predict_ltv(
                days=365,
                observed_days=days_since_install,
                observed_revenue=revenue_to_date,
                retention_multiplier=retention_multiplier
            )
            
            results.append({
                'user_id': user_id,
                'days_since_install': days_since_install,
                'revenue_to_date': revenue_to_date,
                'pltv_365': ltv['ltv_total'],
                'pltv_iaa': ltv['ltv_iaa'],
                'pltv_iap': ltv['ltv_iap']
            })
        
        return pd.DataFrame(results)


class ChurnPredictor:
    """
    Churn Prediction Model
    
    Nhận diện người dùng có dấu hiệu rời bỏ trong 48h tới
    dựa trên các tín hiệu hành vi.
    """
    
    def __init__(self):
        # Churn risk weights for different signals
        self.weights = {
            'days_inactive': 0.3,          # Days since last activity
            'session_decline': 0.2,         # Session frequency decline
            'engagement_decline': 0.2,      # Engagement score decline
            'low_ltv_potential': 0.15,      # Low predicted LTV
            'no_purchases': 0.15            # No purchase history
        }
    
    def calculate_churn_probability(self, user_features: Dict) -> float:
        """
        Calculate churn probability for a single user
        
        Args:
            user_features: Dictionary with user behavior features
            
        Returns:
            Churn probability [0, 1]
        """
        risk_score = 0
        
        # Days inactive (higher = more risk)
        days_inactive = user_features.get('days_inactive', 0)
        if days_inactive >= 7:
            risk_score += self.weights['days_inactive'] * 1.0
        elif days_inactive >= 3:
            risk_score += self.weights['days_inactive'] * 0.7
        elif days_inactive >= 1:
            risk_score += self.weights['days_inactive'] * 0.3
        
        # Session frequency decline
        session_decline = user_features.get('session_decline_pct', 0)
        if session_decline > 50:
            risk_score += self.weights['session_decline'] * 1.0
        elif session_decline > 25:
            risk_score += self.weights['session_decline'] * 0.5
        
        # Engagement decline
        engagement_decline = user_features.get('engagement_decline_pct', 0)
        if engagement_decline > 40:
            risk_score += self.weights['engagement_decline'] * 1.0
        elif engagement_decline > 20:
            risk_score += self.weights['engagement_decline'] * 0.5
        
        # Low LTV potential
        pltv = user_features.get('pltv', 0)
        if pltv < 0.5:
            risk_score += self.weights['low_ltv_potential'] * 1.0
        elif pltv < 1.0:
            risk_score += self.weights['low_ltv_potential'] * 0.5
        
        # No purchase history
        if not user_features.get('has_purchased', False):
            risk_score += self.weights['no_purchases'] * 0.5
        
        return min(1.0, risk_score)
    
    def predict_churn_batch(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict churn probability for multiple users
        
        Args:
            users_df: DataFrame with user features
            
        Returns:
            DataFrame with churn predictions and risk levels
        """
        results = []
        
        for _, row in users_df.iterrows():
            features = row.to_dict()
            churn_prob = self.calculate_churn_probability(features)
            
            # Determine risk level
            if churn_prob >= 0.7:
                risk_level = 'High'
            elif churn_prob >= 0.4:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            results.append({
                'user_id': features.get('user_id', 'unknown'),
                'churn_probability': round(churn_prob, 4),
                'risk_level': risk_level,
                'recommended_action': self._get_recommended_action(churn_prob, features)
            })
        
        return pd.DataFrame(results)
    
    def _get_recommended_action(self, churn_prob: float, features: Dict) -> str:
        """Get recommended action based on churn probability and user value"""
        pltv = features.get('pltv', 0)
        
        if churn_prob >= 0.7:
            if pltv >= 2.0:
                return "HIGH PRIORITY: Send personalized offer immediately"
            else:
                return "Send re-engagement push notification"
        elif churn_prob >= 0.4:
            if pltv >= 2.0:
                return "Add to retargeting campaign"
            else:
                return "Send generic promotion"
        else:
            return "No action needed"
    
    def get_at_risk_users(self, 
                          users_df: pd.DataFrame, 
                          threshold: float = 0.5) -> pd.DataFrame:
        """
        Get users with churn probability above threshold
        
        Args:
            users_df: DataFrame with user features
            threshold: Churn probability threshold
            
        Returns:
            DataFrame with at-risk users, sorted by churn probability
        """
        predictions = self.predict_churn_batch(users_df)
        at_risk = predictions[predictions['churn_probability'] >= threshold]
        return at_risk.sort_values('churn_probability', ascending=False)


class FraudDetector:
    """
    Fraud Detection for Invalid Traffic
    
    Dự báo giao dịch ảo hoặc click tặc dựa trên các pattern bất thường.
    """
    
    def __init__(self):
        self.thresholds = {
            'click_to_install_time_min': 2,        # Minimum seconds
            'session_duration_min': 3,              # Minimum seconds
            'events_per_session_max': 500,          # Maximum events
            'installs_per_ip_max': 5,               # Maximum installs from same IP
            'revenue_per_user_max': 1000            # Maximum daily revenue
        }
    
    def calculate_fraud_score(self, event_data: Dict) -> Tuple[float, List[str]]:
        """
        Calculate fraud score for an event/user
        
        Args:
            event_data: Dictionary with event details
            
        Returns:
            Tuple of (fraud_score, list of red flags)
        """
        fraud_score = 0
        red_flags = []
        
        # Check click-to-install time
        cti_time = event_data.get('click_to_install_seconds', 10)
        if cti_time < self.thresholds['click_to_install_time_min']:
            fraud_score += 0.4
            red_flags.append(f"Click-to-install time too short: {cti_time}s")
        
        # Check session duration
        session_duration = event_data.get('session_duration_seconds', 60)
        if session_duration < self.thresholds['session_duration_min']:
            fraud_score += 0.3
            red_flags.append(f"Session duration too short: {session_duration}s")
        
        # Check events per session
        events_count = event_data.get('events_per_session', 10)
        if events_count > self.thresholds['events_per_session_max']:
            fraud_score += 0.3
            red_flags.append(f"Too many events: {events_count}")
        
        # Check installs from same IP
        ip_installs = event_data.get('installs_from_same_ip', 1)
        if ip_installs > self.thresholds['installs_per_ip_max']:
            fraud_score += 0.5
            red_flags.append(f"Multiple installs from same IP: {ip_installs}")
        
        # Check revenue anomaly
        daily_revenue = event_data.get('daily_revenue', 0)
        if daily_revenue > self.thresholds['revenue_per_user_max']:
            fraud_score += 0.5
            red_flags.append(f"Abnormal revenue: ${daily_revenue}")
        
        return min(1.0, fraud_score), red_flags
    
    def detect_fraud_batch(self, events_df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect fraud for multiple events/users
        
        Args:
            events_df: DataFrame with event data
            
        Returns:
            DataFrame with fraud scores and flags
        """
        results = []
        
        for _, row in events_df.iterrows():
            event_data = row.to_dict()
            fraud_score, red_flags = self.calculate_fraud_score(event_data)
            
            # Determine fraud classification
            if fraud_score >= 0.7:
                classification = 'Fraud'
            elif fraud_score >= 0.4:
                classification = 'Suspicious'
            else:
                classification = 'Valid'
            
            results.append({
                'event_id': event_data.get('event_id', 'unknown'),
                'user_id': event_data.get('user_id', 'unknown'),
                'fraud_score': round(fraud_score, 4),
                'classification': classification,
                'red_flags': '; '.join(red_flags) if red_flags else 'None'
            })
        
        return pd.DataFrame(results)


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 2: PREDICTION")
    print("=" * 60)
    
    # pLTV Demo
    print("\n📊 pLTV Prediction:")
    predictor = PLTVPredictor()
    ltv = predictor.predict_ltv(days=365)
    print(f"  LTV (365 days): ${ltv['ltv_total']:.4f}")
    print(f"    - IAA: ${ltv['ltv_iaa']:.4f}")
    print(f"    - IAP: ${ltv['ltv_iap']:.4f}")
    
    # Churn Demo
    print("\n⚠️ Churn Prediction:")
    churn_predictor = ChurnPredictor()
    sample_user = {
        'user_id': 'user_001',
        'days_inactive': 5,
        'session_decline_pct': 40,
        'engagement_decline_pct': 30,
        'pltv': 1.5,
        'has_purchased': False
    }
    churn_prob = churn_predictor.calculate_churn_probability(sample_user)
    print(f"  Sample User Churn Probability: {churn_prob * 100:.1f}%")
