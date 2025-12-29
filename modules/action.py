"""
Analytics Business Framework - Step 5: Action
Action Recommendations and Automated Rules

Trả lời câu hỏi: "Chúng ta nên làm gì ngay bây giờ?"
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG


class ActionPriority(Enum):
    """Action priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ActionCategory(Enum):
    """Categories of recommended actions"""
    UA_OPTIMIZATION = "User Acquisition"
    MONETIZATION = "Monetization"
    RETENTION = "Retention"
    PRODUCT = "Product"
    INVESTIGATION = "Investigation"


@dataclass
class Action:
    """Recommended action data structure"""
    id: str
    title: str
    description: str
    category: ActionCategory
    priority: ActionPriority
    impact_estimate: str
    effort_estimate: str
    owner: str = "Not Assigned"
    due_date: datetime = None
    status: str = "Open"
    related_metrics: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.name,
            'impact_estimate': self.impact_estimate,
            'effort_estimate': self.effort_estimate,
            'owner': self.owner,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'related_metrics': self.related_metrics
        }


class AutomatedRules:
    """
    Automated Rules Engine
    
    Tự động thực hiện hành động khi điều kiện được đáp ứng:
    - Nếu ROAS của Campaign < ngưỡng → Giảm bid hoặc tắt quảng cáo
    - Nếu User có risk churn cao + pLTV cao → Gửi khuyến mãi
    """
    
    def __init__(self):
        self.rules: List[Dict] = []
        self.triggered_actions: List[Dict] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default business rules"""
        self.rules = [
            {
                'id': 'rule_roas_critical',
                'name': 'ROAS Critical - Pause Campaign',
                'condition': lambda m: m.get('roas', 1) < CONFIG.alerts.roas_danger,
                'action': 'pause_campaign',
                'priority': ActionPriority.CRITICAL,
                'description': 'Pause campaign when ROAS falls below danger threshold'
            },
            {
                'id': 'rule_roas_warning',
                'name': 'ROAS Warning - Reduce Bid',
                'condition': lambda m: CONFIG.alerts.roas_danger <= m.get('roas', 1) < CONFIG.alerts.roas_warning,
                'action': 'reduce_bid',
                'priority': ActionPriority.HIGH,
                'description': 'Reduce bid by 20% when ROAS is below warning threshold'
            },
            {
                'id': 'rule_high_churn_high_ltv',
                'name': 'High Risk + High Value - Send Offer',
                'condition': lambda u: u.get('churn_probability', 0) > 0.7 and u.get('pltv', 0) > 2.0,
                'action': 'send_personalized_offer',
                'priority': ActionPriority.HIGH,
                'description': 'Send personalized retention offer to high-value users at risk'
            },
            {
                'id': 'rule_inactive_user',
                'name': 'Inactive User - Re-engagement',
                'condition': lambda u: u.get('days_inactive', 0) >= 7,
                'action': 'send_push_notification',
                'priority': ActionPriority.MEDIUM,
                'description': 'Send re-engagement push to users inactive for 7+ days'
            },
            {
                'id': 'rule_high_performing_campaign',
                'name': 'High Performing Campaign - Scale Up',
                'condition': lambda m: m.get('roas', 0) > CONFIG.alerts.roas_safe * 1.5,
                'action': 'increase_budget',
                'priority': ActionPriority.MEDIUM,
                'description': 'Increase budget for campaigns with ROAS > 150% of safe threshold'
            }
        ]
    
    def add_rule(self, 
                 rule_id: str, 
                 name: str,
                 condition: Callable,
                 action: str,
                 priority: ActionPriority,
                 description: str = ""):
        """Add a custom rule"""
        self.rules.append({
            'id': rule_id,
            'name': name,
            'condition': condition,
            'action': action,
            'priority': priority,
            'description': description
        })
    
    def evaluate_rules(self, data: Dict) -> List[Dict]:
        """
        Evaluate all rules against provided data
        
        Args:
            data: Dictionary with metric/user data
            
        Returns:
            List of triggered actions
        """
        triggered = []
        
        for rule in self.rules:
            try:
                if rule['condition'](data):
                    triggered.append({
                        'rule_id': rule['id'],
                        'rule_name': rule['name'],
                        'action': rule['action'],
                        'priority': rule['priority'].name,
                        'description': rule['description'],
                        'triggered_at': datetime.now().isoformat(),
                        'data_snapshot': data
                    })
            except Exception as e:
                continue  # Skip rules that error
        
        self.triggered_actions.extend(triggered)
        return triggered
    
    def evaluate_campaigns(self, campaigns_df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluate rules for multiple campaigns
        
        Args:
            campaigns_df: DataFrame with campaign metrics
            
        Returns:
            DataFrame with recommended actions
        """
        results = []
        
        for _, row in campaigns_df.iterrows():
            campaign_data = row.to_dict()
            triggers = self.evaluate_rules(campaign_data)
            
            if triggers:
                for t in triggers:
                    results.append({
                        'campaign_id': campaign_data.get('campaign_id', 'unknown'),
                        'campaign_name': campaign_data.get('campaign_name', 'unknown'),
                        'current_roas': campaign_data.get('roas', campaign_data.get('roas_d7', 0)),
                        'action': t['action'],
                        'priority': t['priority'],
                        'rule': t['rule_name']
                    })
        
        return pd.DataFrame(results)
    
    def evaluate_users(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluate rules for multiple users
        
        Args:
            users_df: DataFrame with user data
            
        Returns:
            DataFrame with recommended actions per user
        """
        results = []
        
        for _, row in users_df.iterrows():
            user_data = row.to_dict()
            triggers = self.evaluate_rules(user_data)
            
            if triggers:
                for t in triggers:
                    results.append({
                        'user_id': user_data.get('user_id', 'unknown'),
                        'segment': user_data.get('segment', 'unknown'),
                        'action': t['action'],
                        'priority': t['priority'],
                        'rule': t['rule_name']
                    })
        
        return pd.DataFrame(results)
    
    def get_action_summary(self) -> Dict:
        """Get summary of triggered actions"""
        if not self.triggered_actions:
            return {'total': 0}
        
        by_action = {}
        by_priority = {}
        
        for action in self.triggered_actions:
            action_type = action['action']
            priority = action['priority']
            
            by_action[action_type] = by_action.get(action_type, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        return {
            'total': len(self.triggered_actions),
            'by_action': by_action,
            'by_priority': by_priority
        }


class ActionRecommender:
    """
    Action Recommendation Engine
    
    Generate strategic recommendations based on analysis results.
    """
    
    def __init__(self):
        self.recommendations: List[Action] = []
        self._action_counter = 0
    
    def _generate_action_id(self) -> str:
        self._action_counter += 1
        return f"action_{datetime.now().strftime('%Y%m%d')}_{self._action_counter:03d}"
    
    def recommend_from_alerts(self, alerts: List[Dict]) -> List[Action]:
        """
        Generate recommendations from monitoring alerts
        
        Args:
            alerts: List of alert dictionaries
            
        Returns:
            List of recommended actions
        """
        actions = []
        
        for alert in alerts:
            level = alert.get('level', 'warning')
            metric = alert.get('metric', 'Unknown')
            
            if metric == 'ROAS':
                if level == 'critical':
                    action = Action(
                        id=self._generate_action_id(),
                        title="Emergency: Review UA Spend",
                        description="ROAS is critically low. Immediately review and pause underperforming campaigns.",
                        category=ActionCategory.UA_OPTIMIZATION,
                        priority=ActionPriority.CRITICAL,
                        impact_estimate="High - Prevent further loss",
                        effort_estimate="Low - 1 hour",
                        related_metrics=['ROAS', 'CPI', 'LTV']
                    )
                    actions.append(action)
            
            elif metric == 'Retention':
                action = Action(
                    id=self._generate_action_id(),
                    title="Investigate Retention Drop",
                    description="Retention has dropped significantly. Analyze by cohort and version to identify root cause.",
                    category=ActionCategory.INVESTIGATION,
                    priority=ActionPriority.HIGH if level == 'critical' else ActionPriority.MEDIUM,
                    impact_estimate="Medium - Identify issue before it worsens",
                    effort_estimate="Medium - 2-4 hours",
                    related_metrics=['D1 Retention', 'D7 Retention', 'Churn Rate']
                )
                actions.append(action)
            
            elif metric == 'Revenue':
                action = Action(
                    id=self._generate_action_id(),
                    title="Revenue Recovery Plan",
                    description="Revenue is below target. Review pricing, promotions, and ad monetization settings.",
                    category=ActionCategory.MONETIZATION,
                    priority=ActionPriority.HIGH,
                    impact_estimate="High - Direct revenue impact",
                    effort_estimate="Medium - 4-8 hours",
                    related_metrics=['ARPU', 'ARPDAU', 'eCPM', 'Sub Conversion']
                )
                actions.append(action)
        
        self.recommendations.extend(actions)
        return actions
    
    def recommend_from_funnel(self, funnel_analysis: Dict) -> List[Action]:
        """
        Generate recommendations from funnel analysis
        
        Args:
            funnel_analysis: Dictionary with biggest drop-off info
            
        Returns:
            List of recommended actions
        """
        actions = []
        
        if not funnel_analysis:
            return actions
        
        step_name = funnel_analysis.get('step_name', 'Unknown')
        drop_rate = funnel_analysis.get('drop_off_rate', 0)
        
        if drop_rate > 50:
            priority = ActionPriority.CRITICAL
            impact = "Very High - Major conversion blocker"
        elif drop_rate > 30:
            priority = ActionPriority.HIGH
            impact = "High - Significant conversion loss"
        else:
            priority = ActionPriority.MEDIUM
            impact = "Medium - Room for improvement"
        
        action = Action(
            id=self._generate_action_id(),
            title=f"Optimize: {step_name}",
            description=f"This step has a {drop_rate:.1f}% drop-off rate. Prioritize UX improvement here.",
            category=ActionCategory.PRODUCT,
            priority=priority,
            impact_estimate=impact,
            effort_estimate="Medium-High - May require dev work",
            related_metrics=['Funnel Conversion', 'Drop-off Rate']
        )
        actions.append(action)
        
        self.recommendations.extend(actions)
        return actions
    
    def recommend_for_cohort(self, cohort_comparison: pd.DataFrame) -> List[Action]:
        """
        Generate recommendations from cohort comparison
        
        Args:
            cohort_comparison: DataFrame comparing cohorts
            
        Returns:
            List of recommended actions
        """
        actions = []
        
        for _, row in cohort_comparison.iterrows():
            metric = row.get('Metric', 'unknown')
            winner = row.get('Winner', 'Tie')
            diff_pct = row.get('Difference %', '0%')
            
            if winner == 'B' and metric in ['retention_rate', 'ltv', 'arpu']:
                # Newer cohort is performing worse
                action = Action(
                    id=self._generate_action_id(),
                    title=f"Investigate {metric} Decline",
                    description=f"Recent cohort shows {diff_pct} decline in {metric}. Check for app changes or UA quality issues.",
                    category=ActionCategory.INVESTIGATION,
                    priority=ActionPriority.HIGH,
                    impact_estimate="High - Declining metrics need attention",
                    effort_estimate="Medium - 2-4 hours analysis",
                    related_metrics=[metric]
                )
                actions.append(action)
        
        self.recommendations.extend(actions)
        return actions
    
    def prioritize_roadmap(self, 
                           product_issues: List[Dict],
                           max_items: int = 5) -> pd.DataFrame:
        """
        Prioritize product roadmap based on impact analysis
        
        Args:
            product_issues: List of issues with impact scores
            max_items: Maximum items to return
            
        Returns:
            DataFrame with prioritized roadmap
        """
        # Sort by impact and effort
        sorted_issues = sorted(
            product_issues,
            key=lambda x: (-x.get('impact_score', 0), x.get('effort_score', 10))
        )
        
        roadmap = []
        for i, issue in enumerate(sorted_issues[:max_items]):
            roadmap.append({
                'Priority': i + 1,
                'Issue': issue.get('title', 'Unknown'),
                'Impact': issue.get('impact_score', 0),
                'Effort': issue.get('effort_score', 0),
                'ROI Score': round(issue.get('impact_score', 0) / max(issue.get('effort_score', 1), 1), 2),
                'Recommendation': issue.get('recommendation', 'Review and prioritize')
            })
        
        return pd.DataFrame(roadmap)
    
    def get_all_recommendations(self) -> pd.DataFrame:
        """Get all recommendations as DataFrame"""
        if not self.recommendations:
            return pd.DataFrame()
        
        return pd.DataFrame([r.to_dict() for r in self.recommendations])
    
    def get_recommendations_by_priority(self) -> Dict[str, List[Action]]:
        """Group recommendations by priority"""
        grouped = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        for action in self.recommendations:
            grouped[action.priority.name].append(action)
        
        return grouped


class PersonalizedOffer:
    """
    Personalized Offer Generator
    
    Gửi Push Notification kèm khuyến mãi cho user phù hợp
    """
    
    def __init__(self):
        self.offer_templates = {
            'high_value_churn': {
                'title': "We miss you! 🎁",
                'body': "Come back and enjoy 30% off your next subscription",
                'discount_pct': 30,
                'valid_days': 3
            },
            'trial_abandoner': {
                'title': "Your trial is waiting ⏰",
                'body': "Complete your trial and unlock all features",
                'discount_pct': 20,
                'valid_days': 7
            },
            'engaged_free_user': {
                'title': "Upgrade your experience 🚀",
                'body': "Get Premium with exclusive first-time discount",
                'discount_pct': 25,
                'valid_days': 5
            },
            'occasional_user': {
                'title': "Something new for you! ✨",
                'body': "Check out our latest features",
                'discount_pct': 0,
                'valid_days': 14
            }
        }
    
    def select_offer(self, user_profile: Dict) -> Dict:
        """
        Select best offer for user based on their profile
        
        Args:
            user_profile: Dictionary with user characteristics
            
        Returns:
            Dictionary with offer details
        """
        churn_prob = user_profile.get('churn_probability', 0)
        pltv = user_profile.get('pltv', 0)
        segment = user_profile.get('segment', '')
        
        # High value at risk -> best offer
        if churn_prob > 0.7 and pltv > 2.0:
            offer_key = 'high_value_churn'
        elif 'Trial' in segment or user_profile.get('in_trial', False):
            offer_key = 'trial_abandoner'
        elif pltv > 1.0 and churn_prob < 0.3:
            offer_key = 'engaged_free_user'
        else:
            offer_key = 'occasional_user'
        
        offer = self.offer_templates[offer_key].copy()
        offer['offer_key'] = offer_key
        offer['user_id'] = user_profile.get('user_id', 'unknown')
        offer['generated_at'] = datetime.now().isoformat()
        
        return offer
    
    def generate_offers_batch(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate personalized offers for multiple users
        
        Args:
            users_df: DataFrame with user profiles
            
        Returns:
            DataFrame with offers for each user
        """
        offers = []
        
        for _, row in users_df.iterrows():
            user_profile = row.to_dict()
            offer = self.select_offer(user_profile)
            offers.append(offer)
        
        return pd.DataFrame(offers)


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 5: ACTION RECOMMENDATIONS")
    print("=" * 60)
    
    # Automated Rules Demo
    print("\n🤖 Automated Rules:")
    rules_engine = AutomatedRules()
    
    # Test campaign data
    campaign_data = {
        'campaign_id': 'camp_001',
        'roas': 0.65,
        'spend': 5000
    }
    
    triggers = rules_engine.evaluate_rules(campaign_data)
    for t in triggers:
        print(f"  ⚡ {t['rule_name']} -> {t['action']}")
    
    # Action Recommender Demo
    print("\n📋 Recommendations:")
    recommender = ActionRecommender()
    
    # From alerts
    alerts = [{'level': 'critical', 'metric': 'ROAS'}]
    actions = recommender.recommend_from_alerts(alerts)
    
    for action in actions:
        print(f"  [{action.priority.name}] {action.title}")
        print(f"     Impact: {action.impact_estimate}")
    
    # Personalized Offers Demo  
    print("\n🎁 Personalized Offers:")
    offer_gen = PersonalizedOffer()
    
    sample_user = {
        'user_id': 'user_001',
        'churn_probability': 0.8,
        'pltv': 3.5,
        'segment': 'High Value - At Risk'
    }
    
    offer = offer_gen.select_offer(sample_user)
    print(f"  Offer: {offer['title']}")
    print(f"  Discount: {offer['discount_pct']}%")
