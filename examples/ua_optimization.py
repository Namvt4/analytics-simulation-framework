"""
Analytics Business Framework - Example: UA Optimization
Demonstrates the 5-step Data Flywheel for User Acquisition optimization

Use case: Evaluating expansion to Brazil market
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from modules.simulation import MonteCarloSimulator, TargetKPIGenerator
from modules.prediction import PLTVPredictor, ChurnPredictor
from modules.monitoring import AlertManager, HealthScoreCalculator, PacingTracker
from modules.analysis import FunnelAnalyzer, DrilldownAnalyzer
from modules.action import AutomatedRules, ActionRecommender


def run_ua_optimization_example():
    """
    Example scenario: Evaluating Brazil market expansion
    
    From the documentation:
    - Simulate: Giả lập nếu mở rộng sang thị trường Brazil với CPI $0.5
    - Predict: Tính toán pLTV của tệp User Brazil đầu tiên
    - Monitor: Dashboard báo cáo thực tế LTV Day 7
    - Analyze: Phân tích thấy User Brazil thoát app ngay sau Tutorial
    - Action: Khuyến nghị kiểm tra bản dịch tiếng Bồ Đào Nha
    """
    
    print("=" * 70)
    print("ANALYTICS BUSINESS FRAMEWORK")
    print("Example: Brazil Market Expansion Evaluation")
    print("=" * 70)
    
    # =========================================================================
    # STEP 1: SIMULATION
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 1: SIMULATION - Brazil Expansion Scenario")
    print("=" * 70)
    
    # Customize config for Brazil
    # Brazil typically has lower CPI but also lower eCPM
    brazil_cpi = 0.5
    brazil_ecpm_factor = 0.6  # 60% of default eCPM
    
    simulator = MonteCarloSimulator(n_simulations=1000)
    results = simulator.run(days=90)  # 3-month payback period
    
    print(f"\n📊 Monte Carlo Simulation Results (n=1000):")
    print(f"   Expected ROAS (D90): {results['roas']['mean'] * 100:.1f}%")
    print(f"   90% Confidence Interval: [{results['roas']['p5']*100:.1f}%, {results['roas']['p95']*100:.1f}%]")
    print(f"   Probability of Profit: {results['risk']['probability_profitable'] * 100:.1f}%")
    
    # Generate targets
    generator = TargetKPIGenerator(simulator)
    targets = generator.generate_targets(days=90)
    
    print(f"\n🎯 Target KPIs for Brazil:")
    print(f"   Safe ROAS: >{targets['roas']['safe']*100:.1f}%")
    print(f"   Expected ROAS: {targets['roas']['expected']*100:.1f}%")
    print(f"   Breakthrough ROAS: >{targets['roas']['breakthrough']*100:.1f}%")
    
    # =========================================================================
    # STEP 2: PREDICTION
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 2: PREDICTION - pLTV Calculation for Brazil Users")
    print("=" * 70)
    
    predictor = PLTVPredictor()
    
    # Predict LTV with lower eCPM factor for Brazil
    ltv_day0 = predictor.predict_ltv(days=365, retention_multiplier=0.9)  # Slightly lower retention
    ltv_day7 = predictor.predict_ltv(days=365, observed_days=7, observed_revenue=0.04)  # Actual D7 data
    
    print(f"\n📈 pLTV Predictions for Brazil Cohort:")
    print(f"   Day 0 Prediction: ${ltv_day0['ltv_total']:.4f}")
    print(f"   Day 7 Update (with actual data): ${ltv_day7['ltv_total']:.4f}")
    
    # Churn prediction
    churn_predictor = ChurnPredictor()
    sample_brazil_user = {
        'user_id': 'brazil_user_001',
        'days_inactive': 2,
        'session_decline_pct': 35,
        'engagement_decline_pct': 45,
        'pltv': 0.4,
        'has_purchased': False
    }
    churn_prob = churn_predictor.calculate_churn_probability(sample_brazil_user)
    print(f"   Sample User Churn Probability: {churn_prob * 100:.1f}%")
    
    # =========================================================================
    # STEP 3: MONITORING
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 3: MONITORING - Comparing Actual vs Predicted")
    print("=" * 70)
    
    # Simulate actual performance (below expectations)
    actual_ltv_d7 = 0.10  # $0.10 actual vs predicted higher
    predicted_ltv_d7 = 0.25
    
    alert_manager = AlertManager()
    
    current_metrics = {
        'roas': actual_ltv_d7 / brazil_cpi,  # ~20% ROAS
        'revenue': 1000,
        'dau': 8000  # Lower than expected
    }
    
    baseline_metrics = {
        'roas': 0.5,  # Expected 50% D7 ROAS
        'revenue': 2000,
        'dau': 10000
    }
    
    alerts = alert_manager.run_all_checks(current_metrics, baseline_metrics)
    
    print(f"\n🚨 Monitoring Alerts:")
    if alerts:
        for alert in alerts:
            print(f"   {alert.message}")
    else:
        print("   No alerts triggered")
    
    # Pacing check
    pacing = PacingTracker()
    pacing_result = pacing.calculate_pacing(
        current_value=1000,
        target_value=5000,
        elapsed_days=7,
        total_days=30
    )
    print(f"\n📈 Revenue Pacing:")
    print(f"   Status: {pacing_result['status_emoji']} {pacing_result['status']}")
    print(f"   Current: ${pacing_result['current_value']:,.0f} / ${pacing_result['target_value']:,.0f}")
    print(f"   Projected: ${pacing_result['projected_value']:,.0f} ({pacing_result['projected_pct']:.0f}% of target)")
    
    # =========================================================================
    # STEP 4: ANALYSIS
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 4: ANALYSIS - Root Cause Investigation")
    print("=" * 70)
    
    # Funnel analysis shows Tutorial drop-off
    import pandas as pd
    brazil_funnel = pd.DataFrame([
        {'step_name': 'App Open', 'step_order': 1, 'users': 10000},
        {'step_name': 'Tutorial Start', 'step_order': 2, 'users': 8500},
        {'step_name': 'Tutorial Complete', 'step_order': 3, 'users': 3200},  # BIG DROP!
        {'step_name': 'First Action', 'step_order': 4, 'users': 2100},
        {'step_name': 'D1 Return', 'step_order': 5, 'users': 1400}
    ])
    
    funnel_analyzer = FunnelAnalyzer()
    biggest_drop = funnel_analyzer.find_biggest_dropoff(brazil_funnel)
    
    print(f"\n🔍 Funnel Analysis - Brazil Market:")
    if biggest_drop:
        print(f"   Biggest Drop-off: {biggest_drop['step_name']}")
        print(f"   Drop-off Rate: {biggest_drop['drop_off_rate']:.1f}%")
        print(f"   Users Lost: {biggest_drop['users_lost']:,}")
        print(f"   💡 Finding: Users are dropping at Tutorial - likely language issue!")
    
    # =========================================================================
    # STEP 5: ACTION
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 5: ACTION - Recommendations")
    print("=" * 70)
    
    recommender = ActionRecommender()
    rules_engine = AutomatedRules()
    
    # Evaluate campaign
    campaign_data = {
        'campaign_id': 'brazil_launch_001',
        'roas': current_metrics['roas'],
        'spend': 5000
    }
    
    triggers = rules_engine.evaluate_rules(campaign_data)
    
    print(f"\n🤖 Automated Actions:")
    for t in triggers:
        print(f"   ⚡ {t['rule_name']} → {t['action']}")
    
    # Generate strategic recommendations
    print(f"\n📋 Strategic Recommendations:")
    print("""
    1. 🔴 [CRITICAL] Pause Brazil UA Campaign
       - ROAS is well below breakeven
       - Immediate action: Reduce budget by 100%
    
    2. 🟠 [HIGH] Investigate Portuguese Translation
       - Tutorial completion rate is abnormally low (32% vs 68% global)
       - Native Portuguese review needed for Tutorial content
    
    3. 🟡 [MEDIUM] Resume After Localization Fix
       - After fixing Tutorial, run small-scale test
       - Target: 5,000 installs over 2 weeks
       - Decision point: If D7 ROAS > 30%, scale gradually
    """)
    
    print("\n" + "=" * 70)
    print("SUMMARY: Data Flywheel Complete")
    print("=" * 70)
    print("""
    ✅ Simulation: Identified Brazil as potentially profitable with CPI $0.5
    ✅ Prediction: pLTV model predicted $0.40 LTV
    ⚠️ Monitoring: Actual D7 LTV only $0.10 (75% below prediction)
    🔍 Analysis: Found Tutorial completion drop-off (localization issue)
    📋 Action: Pause campaign, fix Portuguese translation, re-test
    
    → Next iteration: After fix, feed new data back into Simulation
    """)


if __name__ == "__main__":
    run_ua_optimization_example()
