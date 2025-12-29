"""
Analytics Business Framework - Step 3: Monitoring
Real-time Dashboard Alerts and Health Scores

Trả lời câu hỏi: "Chỉ số hiện tại có đang đi đúng hướng không?"
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    level: AlertLevel
    metric: str
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    dimension: str = None  # Optional: Country, Campaign, etc.
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'level': self.level.value,
            'metric': self.metric,
            'message': self.message,
            'current_value': self.current_value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'dimension': self.dimension
        }


class AlertManager:
    """
    Real-time Alerting System
    
    Cảnh báo khi DAU hoặc Revenue tụt quá ngưỡng mô phỏng.
    """
    
    def __init__(self):
        self.thresholds = CONFIG.alerts
        self.alerts: List[Alert] = []
        self._alert_counter = 0
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        self._alert_counter += 1
        return f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._alert_counter}"
    
    def check_roas(self, current_roas: float, baseline_roas: float = None) -> Optional[Alert]:
        """
        Check ROAS against thresholds
        
        Args:
            current_roas: Current ROAS value
            baseline_roas: Baseline for comparison (optional)
            
        Returns:
            Alert if threshold breached, else None
        """
        if current_roas < self.thresholds.roas_danger:
            level = AlertLevel.CRITICAL
            message = f"🚨 ROAS critically low at {current_roas * 100:.1f}% (target: >{self.thresholds.roas_danger * 100:.0f}%)"
        elif current_roas < self.thresholds.roas_warning:
            level = AlertLevel.DANGER
            message = f"⚠️ ROAS below breakeven at {current_roas * 100:.1f}%"
        elif current_roas < self.thresholds.roas_safe:
            level = AlertLevel.WARNING
            message = f"📉 ROAS below safe zone at {current_roas * 100:.1f}%"
        else:
            return None
        
        alert = Alert(
            id=self._generate_alert_id(),
            level=level,
            metric='ROAS',
            message=message,
            current_value=current_roas,
            threshold=self.thresholds.roas_warning,
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        return alert
    
    def check_retention_drop(self, 
                              current_retention: float, 
                              baseline_retention: float) -> Optional[Alert]:
        """
        Check retention against baseline
        
        Args:
            current_retention: Current retention rate
            baseline_retention: Expected retention rate
            
        Returns:
            Alert if significant drop detected
        """
        if baseline_retention == 0:
            return None
        
        drop_pct = (baseline_retention - current_retention) / baseline_retention
        
        if drop_pct >= self.thresholds.retention_drop_danger:
            level = AlertLevel.CRITICAL
            message = f"🚨 Retention dropped {drop_pct * 100:.1f}% from baseline"
        elif drop_pct >= self.thresholds.retention_drop_warning:
            level = AlertLevel.WARNING
            message = f"📉 Retention dropped {drop_pct * 100:.1f}% from baseline"
        else:
            return None
        
        alert = Alert(
            id=self._generate_alert_id(),
            level=level,
            metric='Retention',
            message=message,
            current_value=current_retention,
            threshold=baseline_retention * (1 - self.thresholds.retention_drop_warning),
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        return alert
    
    def check_revenue_drop(self, 
                           current_revenue: float, 
                           baseline_revenue: float) -> Optional[Alert]:
        """
        Check revenue against baseline
        
        Args:
            current_revenue: Current daily revenue
            baseline_revenue: Expected daily revenue
            
        Returns:
            Alert if significant drop detected
        """
        if baseline_revenue == 0:
            return None
        
        drop_pct = (baseline_revenue - current_revenue) / baseline_revenue
        
        if drop_pct >= self.thresholds.revenue_drop_danger:
            level = AlertLevel.CRITICAL
            message = f"🚨 Revenue dropped {drop_pct * 100:.1f}% (${current_revenue:,.0f} vs expected ${baseline_revenue:,.0f})"
        elif drop_pct >= self.thresholds.revenue_drop_warning:
            level = AlertLevel.WARNING
            message = f"📉 Revenue dropped {drop_pct * 100:.1f}% from expected"
        else:
            return None
        
        alert = Alert(
            id=self._generate_alert_id(),
            level=level,
            metric='Revenue',
            message=message,
            current_value=current_revenue,
            threshold=baseline_revenue * (1 - self.thresholds.revenue_drop_warning),
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        return alert
    
    def check_dau_drop(self, current_dau: int, baseline_dau: int) -> Optional[Alert]:
        """Check DAU against baseline"""
        if baseline_dau == 0:
            return None
        
        drop_pct = (baseline_dau - current_dau) / baseline_dau
        
        if drop_pct >= self.thresholds.dau_drop_danger:
            level = AlertLevel.CRITICAL
            message = f"🚨 DAU dropped {drop_pct * 100:.1f}% ({current_dau:,} vs expected {baseline_dau:,})"
        elif drop_pct >= self.thresholds.dau_drop_warning:
            level = AlertLevel.WARNING
            message = f"📉 DAU dropped {drop_pct * 100:.1f}% from expected"
        else:
            return None
        
        alert = Alert(
            id=self._generate_alert_id(),
            level=level,
            metric='DAU',
            message=message,
            current_value=current_dau,
            threshold=baseline_dau * (1 - self.thresholds.dau_drop_warning),
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        return alert
    
    def run_all_checks(self, metrics: Dict, baselines: Dict) -> List[Alert]:
        """
        Run all metric checks
        
        Args:
            metrics: Current metric values
            baselines: Expected/baseline values
            
        Returns:
            List of triggered alerts
        """
        new_alerts = []
        
        # ROAS check
        if 'roas' in metrics:
            alert = self.check_roas(metrics['roas'], baselines.get('roas'))
            if alert:
                new_alerts.append(alert)
        
        # Retention check
        if 'retention' in metrics and 'retention' in baselines:
            alert = self.check_retention_drop(metrics['retention'], baselines['retention'])
            if alert:
                new_alerts.append(alert)
        
        # Revenue check
        if 'revenue' in metrics and 'revenue' in baselines:
            alert = self.check_revenue_drop(metrics['revenue'], baselines['revenue'])
            if alert:
                new_alerts.append(alert)
        
        # DAU check
        if 'dau' in metrics and 'dau' in baselines:
            alert = self.check_dau_drop(int(metrics['dau']), int(baselines['dau']))
            if alert:
                new_alerts.append(alert)
        
        return new_alerts
    
    def get_active_alerts(self, max_age_hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        return [a for a in self.alerts if a.timestamp > cutoff]
    
    def get_alerts_df(self) -> pd.DataFrame:
        """Get all alerts as DataFrame"""
        if not self.alerts:
            return pd.DataFrame()
        return pd.DataFrame([a.to_dict() for a in self.alerts])


class HealthScoreCalculator:
    """
    Health Score & NRPU Calculator
    
    Giám sát chỉ số sức khỏe tổng quát và doanh thu ròng trên mỗi người dùng.
    """
    
    def __init__(self):
        self.weights = {
            'roas': 0.30,
            'retention': 0.25,
            'revenue_growth': 0.20,
            'ltv_vs_cpi': 0.15,
            'user_quality': 0.10
        }
    
    def calculate_health_score(self, metrics: Dict) -> Dict:
        """
        Calculate overall business health score (0-100)
        
        Args:
            metrics: Dictionary with current metrics
            
        Returns:
            Dictionary with health score and component breakdown
        """
        scores = {}
        
        # ROAS Score (0-100)
        roas = metrics.get('roas', 0)
        if roas >= 1.5:
            scores['roas'] = 100
        elif roas >= 1.0:
            scores['roas'] = 60 + (roas - 1.0) * 80  # 60-100 for ROAS 1.0-1.5
        elif roas >= 0.5:
            scores['roas'] = 20 + (roas - 0.5) * 80  # 20-60 for ROAS 0.5-1.0
        else:
            scores['roas'] = roas * 40  # 0-20 for ROAS 0-0.5
        
        # Retention Score (based on D7)
        d7_retention = metrics.get('d7_retention', 0)
        if d7_retention >= 0.25:
            scores['retention'] = 100
        elif d7_retention >= 0.15:
            scores['retention'] = 50 + (d7_retention - 0.15) * 500
        else:
            scores['retention'] = d7_retention / 0.15 * 50
        
        # Revenue Growth Score
        revenue_growth = metrics.get('revenue_growth_pct', 0)
        if revenue_growth >= 20:
            scores['revenue_growth'] = 100
        elif revenue_growth >= 0:
            scores['revenue_growth'] = 50 + revenue_growth * 2.5
        else:
            scores['revenue_growth'] = max(0, 50 + revenue_growth * 2)
        
        # LTV vs CPI Score
        ltv = metrics.get('ltv', 0)
        cpi = metrics.get('cpi', 1)
        ltv_ratio = ltv / cpi if cpi > 0 else 0
        if ltv_ratio >= 2.0:
            scores['ltv_vs_cpi'] = 100
        elif ltv_ratio >= 1.0:
            scores['ltv_vs_cpi'] = 50 + (ltv_ratio - 1.0) * 50
        else:
            scores['ltv_vs_cpi'] = ltv_ratio * 50
        
        # User Quality Score (based on organic rate and engagement)
        organic_rate = metrics.get('organic_rate', 0.3)
        scores['user_quality'] = min(100, organic_rate * 200 + 40)
        
        # Calculate weighted total
        total_score = sum(
            scores.get(key, 0) * weight 
            for key, weight in self.weights.items()
        )
        
        # Determine health status
        if total_score >= 80:
            status = 'Excellent'
            status_emoji = '🟢'
        elif total_score >= 60:
            status = 'Good'
            status_emoji = '🟡'
        elif total_score >= 40:
            status = 'Fair'
            status_emoji = '🟠'
        else:
            status = 'Poor'
            status_emoji = '🔴'
        
        return {
            'total_score': round(total_score, 1),
            'status': status,
            'status_emoji': status_emoji,
            'component_scores': {k: round(v, 1) for k, v in scores.items()},
            'weights': self.weights
        }
    
    def calculate_nrpu(self, metrics: Dict) -> Dict:
        """
        Calculate Net Revenue Per User (NRPU)
        
        NRPU = (Total Revenue - Total Spend) / Total Users
        
        Args:
            metrics: Dictionary with revenue and spend data
            
        Returns:
            Dictionary with NRPU breakdown
        """
        total_revenue = metrics.get('total_revenue', 0)
        total_spend = metrics.get('total_spend', 0)
        total_users = metrics.get('total_users', 1)
        
        net_revenue = total_revenue - total_spend
        nrpu = net_revenue / total_users if total_users > 0 else 0
        
        # Calculate components
        arpu = total_revenue / total_users if total_users > 0 else 0
        cpi = total_spend / total_users if total_users > 0 else 0
        
        return {
            'nrpu': round(nrpu, 4),
            'arpu': round(arpu, 4),
            'cpi': round(cpi, 4),
            'total_revenue': total_revenue,
            'total_spend': total_spend,
            'net_revenue': net_revenue,
            'total_users': total_users,
            'profitable': nrpu > 0
        }


class PacingTracker:
    """
    Pacing Tracker
    
    Theo dõi tiến độ hoàn thành mục tiêu tháng/quý.
    """
    
    def __init__(self):
        pass
    
    def calculate_pacing(self, 
                         current_value: float,
                         target_value: float,
                         elapsed_days: int,
                         total_days: int) -> Dict:
        """
        Calculate pacing status
        
        Args:
            current_value: Current cumulative value
            target_value: Target value for the period
            elapsed_days: Days elapsed in the period
            total_days: Total days in the period
            
        Returns:
            Dictionary with pacing metrics
        """
        if total_days == 0 or target_value == 0:
            return {'pacing_pct': 0, 'status': 'Unknown'}
        
        time_elapsed_pct = elapsed_days / total_days
        value_achieved_pct = current_value / target_value
        
        # Pacing: are we on track?
        # If value_achieved >= time_elapsed, we're on track
        pacing_ratio = value_achieved_pct / time_elapsed_pct if time_elapsed_pct > 0 else 0
        
        # Projected end value
        if time_elapsed_pct > 0:
            projected_value = current_value / time_elapsed_pct
            projected_pct = projected_value / target_value
        else:
            projected_value = 0
            projected_pct = 0
        
        # Determine status
        if pacing_ratio >= 1.1:
            status = 'Ahead'
            status_emoji = '🚀'
        elif pacing_ratio >= 0.95:
            status = 'On Track'
            status_emoji = '✅'
        elif pacing_ratio >= 0.8:
            status = 'Slightly Behind'
            status_emoji = '⚠️'
        else:
            status = 'Behind'
            status_emoji = '🔴'
        
        return {
            'current_value': current_value,
            'target_value': target_value,
            'elapsed_days': elapsed_days,
            'total_days': total_days,
            'time_elapsed_pct': round(time_elapsed_pct * 100, 1),
            'value_achieved_pct': round(value_achieved_pct * 100, 1),
            'pacing_ratio': round(pacing_ratio, 3),
            'projected_value': round(projected_value, 2),
            'projected_pct': round(projected_pct * 100, 1),
            'status': status,
            'status_emoji': status_emoji,
            'days_remaining': total_days - elapsed_days,
            'required_daily': round((target_value - current_value) / max(1, total_days - elapsed_days), 2)
        }
    
    def track_multiple_kpis(self, kpis: List[Dict]) -> pd.DataFrame:
        """
        Track pacing for multiple KPIs
        
        Args:
            kpis: List of dicts with {name, current, target, elapsed_days, total_days}
            
        Returns:
            DataFrame with pacing status for each KPI
        """
        results = []
        
        for kpi in kpis:
            pacing = self.calculate_pacing(
                current_value=kpi.get('current', 0),
                target_value=kpi.get('target', 0),
                elapsed_days=kpi.get('elapsed_days', 0),
                total_days=kpi.get('total_days', 30)
            )
            
            results.append({
                'KPI': kpi.get('name', 'Unknown'),
                'Current': f"{pacing['current_value']:,.0f}",
                'Target': f"{pacing['target_value']:,.0f}",
                'Progress': f"{pacing['value_achieved_pct']:.0%}",
                'Pacing': f"{pacing['status_emoji']} {pacing['status']}",
                'Projected': f"{pacing['projected_pct']:.0f}%"
            })
        
        return pd.DataFrame(results)


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 3: MONITORING")
    print("=" * 60)
    
    # Alert Manager Demo
    print("\n🚨 Alert Check:")
    alert_manager = AlertManager()
    
    # Simulate metrics
    current_metrics = {'roas': 0.75, 'revenue': 4000, 'dau': 45000}
    baseline = {'roas': 1.0, 'revenue': 5000, 'dau': 50000}
    
    alerts = alert_manager.run_all_checks(current_metrics, baseline)
    for alert in alerts:
        print(f"  {alert.message}")
    
    # Health Score Demo
    print("\n📊 Health Score:")
    health_calc = HealthScoreCalculator()
    health = health_calc.calculate_health_score({
        'roas': 1.1,
        'd7_retention': 0.18,
        'revenue_growth_pct': 5,
        'ltv': 0.8,
        'cpi': 0.5,
        'organic_rate': 0.3
    })
    print(f"  {health['status_emoji']} Overall Score: {health['total_score']}/100 ({health['status']})")
    
    # Pacing Demo
    print("\n📈 Pacing:")
    pacing = PacingTracker()
    result = pacing.calculate_pacing(
        current_value=75000,
        target_value=150000,
        elapsed_days=15,
        total_days=30
    )
    print(f"  {result['status_emoji']} Revenue Pacing: {result['pacing_ratio']:.0%} ({result['status']})")
