"""
Analytics Business Framework - Simulation Page Component
Enhanced simulation with adjustable parameters
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG, AppConfig, SubscriptionPlan
from modules.simulation import EnhancedMonteCarloSimulator, TargetKPIGenerator


def render_enhanced_simulation():
    """Render Enhanced Simulation page with full parameter controls"""
    
    st.markdown('<h2 class="step-header">1️⃣ Mô phỏng - Monte Carlo & What-if</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="vn-note">
    🎯 <strong>Mục tiêu:</strong> Dự báo ROAS và LTV dựa trên các thông số đầu vào có thể điều chỉnh<br>
    📊 <strong>Phương pháp:</strong> Chạy 1000+ kịch bản giả lập Monte Carlo với biến động ngẫu nhiên<br>
    📈 <strong>Kết quả:</strong> Phân phối xác suất và ngưỡng mục tiêu (Pessimistic, Safe, Expected, Breakthrough, Optimistic)
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for parameter groups
    tab_general, tab_ua, tab_ads, tab_retention, tab_subscription, tab_variation, tab_spend = st.tabs([
        "⚙️ Chung", 
        "📢 User Acquisition", 
        "📺 Monetization (Ads)", 
        "📉 Retention",
        "💳 Subscription",
        "📊 Biến động (Variation)",
        "💰 Spend Plan"
    ])
    
    # =========================================================================
    # TAB: GENERAL SETTINGS
    # =========================================================================
    with tab_general:
        st.markdown("### ⚙️ Cài đặt Chung")
        
        col1, col2 = st.columns(2)
        with col1:
            n_simulations = st.slider(
                "Số kịch bản giả lập",
                min_value=100, max_value=5000, value=1000, step=100,
                help="Càng nhiều kịch bản, kết quả càng chính xác nhưng chạy lâu hơn"
            )
        with col2:
            sim_days = st.selectbox(
                "Thời gian dự báo",
                options=[30, 90, 180, 365],
                index=3,
                format_func=lambda x: f"{x} ngày"
            )
        
        # Monetization Model Selection
        st.markdown("### 💰 Mô hình Monetization")
        st.caption("*Chọn các nguồn doanh thu áp dụng cho sản phẩm của bạn*")
        
        col_mon1, col_mon2 = st.columns(2)
        with col_mon1:
            enable_iaa = st.checkbox("📺 In-App Ads (IAA)", value=True, 
                                     help="Kích hoạt doanh thu từ quảng cáo trong ứng dụng")
        with col_mon2:
            enable_iap = st.checkbox("💳 Subscription / IAP", value=True,
                                     help="Kích hoạt doanh thu từ gói đăng ký và mua hàng trong ứng dụng")
    
    # =========================================================================
    # TAB: USER ACQUISITION
    # =========================================================================
    with tab_ua:
        st.markdown("### 📢 Thông số User Acquisition")
        st.caption("*Các thông số liên quan đến chi phí thu hút người dùng*")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpm = st.number_input(
                "CPM ($)",
                min_value=0.1, max_value=50.0, value=CONFIG.ua.cpm, step=0.5,
                help="Cost per Mille - Chi phí cho 1000 lượt hiển thị quảng cáo"
            )
            
        with col2:
            ctr = st.number_input(
                "CTR (%)",
                min_value=0.1, max_value=10.0, value=CONFIG.ua.ctr * 100, step=0.1,
                help="Click-Through Rate - Tỷ lệ click trên quảng cáo"
            ) / 100
            
        with col3:
            cvr = st.number_input(
                "CVR (%)",
                min_value=1.0, max_value=80.0, value=CONFIG.ua.cvr * 100, step=1.0,
                help="Conversion Rate - Tỷ lệ click → install"
            ) / 100
        
        # Calculated CPI
        cpi_paid = cpm / (1000 * ctr * cvr) if ctr > 0 and cvr > 0 else 0
        
        col1, col2 = st.columns(2)
        with col1:
            organic_ratio = st.slider(
                "Tỷ lệ Organic (%)",
                min_value=0, max_value=80, value=int(CONFIG.ua.organic_ratio * 100), step=5,
                help="Phần trăm users đến từ organic (không mất chi phí UA)"
            ) / 100
            
        with col2:
            blended_cpi = cpi_paid * (1 - organic_ratio)
            st.metric("CPI Paid", f"${cpi_paid:.2f}", help="Chi phí thu hút 1 user paid")
            st.metric("Blended CPI", f"${blended_cpi:.2f}", help="CPI trung bình bao gồm organic")
    
    # =========================================================================
    # TAB: MONETIZATION (ADS)
    # =========================================================================
    with tab_ads:
        st.markdown("### 📺 Thông số Monetization (In-App Ads)")
        
        if not enable_iaa:
            st.info("💡 In-App Ads đã được tắt. Bật lại ở tab **Chung** để cấu hình.")
            # Set default values when disabled
            ecpm_d0 = 0
            impressions_d0 = 0
            arpdau_d0 = 0
            ecpm_saturation = 0
            impressions_saturation = 0
            decay_half_life = 14
            rpr_drop = 0
        else:
            st.caption("*eCPM và Impressions có xu hướng giảm dần theo lifetime của user*")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Giá trị tại D0")
                ecpm_d0 = st.number_input(
                    "eCPM tại D0 ($)",
                    min_value=1.0, max_value=50.0, value=CONFIG.ads.ecpm_d0, step=0.5,
                    help="Doanh thu trung bình cho 1000 impressions tại ngày đầu tiên"
                )
                
                impressions_d0 = st.number_input(
                    "Impressions/DAU tại D0",
                    min_value=1.0, max_value=20.0, value=CONFIG.ads.impressions_per_dau_d0, step=0.5,
                    help="Số lượt xem quảng cáo mỗi user mỗi ngày tại D0"
                )
                
                arpdau_d0 = ecpm_d0 * impressions_d0 / 1000
                st.metric("ARPDAU tại D0", f"${arpdau_d0:.4f}")
            
            with col2:
                st.markdown("#### 📉 Decay Parameters")
                ecpm_saturation = st.slider(
                    "eCPM Saturation (%)",
                    min_value=0, max_value=100, value=int(CONFIG.ads.ecpm_saturation_ratio * 100), step=1,
                    help="eCPM giảm còn bao nhiêu % so với D0 khi bão hòa"
                ) / 100
                
                impressions_saturation = st.slider(
                    "Impressions Saturation (%)",
                    min_value=0, max_value=100, value=int(CONFIG.ads.impressions_saturation_ratio * 100), step=1,
                    help="Impressions giảm còn bao nhiêu % so với D0 khi bão hòa"
                ) / 100
                
                # RPR Drop = eCPM Saturation × Impressions Saturation
                rpr_drop = ecpm_saturation * impressions_saturation
                st.metric("RPR Drop", f"{rpr_drop*100:.1f}%", help="ARPDAU còn lại khi bão hòa = eCPM × Impressions Saturation")
                
                decay_half_life = st.slider(
                    "Half-life (ngày)",
                    min_value=1, max_value=365, value=14, step=1,
                    help="Thời gian để giảm 50% khoảng cách tới saturation"
                )
            
            # Preview ARPDAU curve
            st.markdown("#### 📈 Preview ARPDAU Decay")
            import math
            days_preview = [0, 7, 14, 30, 60, 90, 120, 180, 270, 365]  # Include D365
            arpdau_values = []
            for d in days_preview:
                if d == 0:
                    arpdau_values.append(arpdau_d0)
                else:
                    ecpm_sat = ecpm_d0 * ecpm_saturation
                    imp_sat = impressions_d0 * impressions_saturation
                    decay = math.exp(-d / decay_half_life)
                    ecpm_d = ecpm_sat + (ecpm_d0 - ecpm_sat) * decay
                    imp_d = imp_sat + (impressions_d0 - imp_sat) * decay
                    arpdau_values.append(ecpm_d * imp_d / 1000)
            
            fig = go.Figure()
            # Full curve
            fig.add_trace(go.Scatter(
                x=days_preview, y=arpdau_values,
                mode='lines', name='ARPDAU',
                line=dict(color='rgba(102, 126, 234, 0.6)', width=2),
                fill='tozeroy', fillcolor='rgba(102, 126, 234, 0.15)'
            ))
            # Input points
            fig.add_trace(go.Scatter(
                x=days_preview, y=arpdau_values,
                mode='markers', name='Points',
                marker=dict(size=8, color='#667eea', line=dict(width=1.5, color='white'))
            ))
            fig.update_layout(
                title=f"ARPDAU Decay (D0→D365) - RPR Drop: {rpr_drop*100:.0f}%",
                xaxis_title="Ngày", yaxis_title="ARPDAU ($)",
                height=220, margin=dict(t=35, b=30, l=50, r=20),
                template="plotly_white", showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================================
    # TAB: RETENTION
    # =========================================================================
    with tab_retention:
        st.markdown("### 📉 Retention Curve (tới D365)")
        st.caption("*Tỷ lệ % người dùng còn hoạt động sau N ngày cài đặt*")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            d1 = st.number_input("D1 (%)", 0.0, 100.0, float(CONFIG.retention.d1 * 100), 0.01, format="%.2f") / 100
            d3 = st.number_input("D3 (%)", 0.0, 100.0, float(CONFIG.retention.d3 * 100), 0.01, format="%.2f") / 100
            d7 = st.number_input("D7 (%)", 0.0, 100.0, float(CONFIG.retention.d7 * 100), 0.01, format="%.2f") / 100
            
        with col2:
            d14 = st.number_input("D14 (%)", 0.0, 100.0, float(CONFIG.retention.d14 * 100), 0.01, format="%.2f") / 100
            d30 = st.number_input("D30 (%)", 0.0, 100.0, float(CONFIG.retention.d30 * 100), 0.01, format="%.2f") / 100
            d60 = st.number_input("D60 (%)", 0.0, 100.0, float(CONFIG.retention.d60 * 100), 0.01, format="%.2f") / 100
            
        with col3:
            d90 = st.number_input("D90 (%)", 0.0, 100.0, float(CONFIG.retention.d90 * 100), 0.01, format="%.2f") / 100
            d180 = st.number_input("D180 (%)", 0.0, 100.0, float(CONFIG.retention.d180 * 100), 0.01, format="%.2f") / 100
            d365 = st.number_input("D365 (%)", 0.0, 100.0, float(CONFIG.retention.d365 * 100), 0.01, format="%.2f") / 100
        
        with col4:
            # Show retention summary
            st.markdown("**Summary:**")
            retention_points = {
                'D1': d1, 'D7': d7, 'D30': d30, 'D90': d90, 'D365': d365
            }
            for day, rate in retention_points.items():
                color = "🟢" if rate > 0.1 else "🟡" if rate > 0.05 else "🔴"
                st.markdown(f"{color} **{day}:** {rate*100:.1f}%")
        
        # Retention curve preview
        days_ret = [0, 1, 3, 7, 14, 30, 60, 90, 180, 365]
        rates = [1.0, d1, d3, d7, d14, d30, d60, d90, d180, d365]
        
        fig = go.Figure()
        # Full curve
        fig.add_trace(go.Scatter(
            x=days_ret, y=[r * 100 for r in rates],
            mode='lines', name='Retention',
            line=dict(color='rgba(118, 75, 162, 0.6)', width=2),
            fill='tozeroy', fillcolor='rgba(118, 75, 162, 0.15)'
        ))
        # Input points
        fig.add_trace(go.Scatter(
            x=days_ret, y=[r * 100 for r in rates],
            mode='markers', name='Points',
            marker=dict(size=8, color='#764ba2', line=dict(width=1.5, color='white'))
        ))
        fig.update_layout(
            title=f"User Retention Curve (D0→D365) - D365: {d365*100:.1f}%",
            xaxis_title="Ngày từ Install", yaxis_title="Retention (%)",
            yaxis=dict(range=[0, 105]),
            height=220, margin=dict(t=35, b=30, l=50, r=20),
            template="plotly_white", showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================================
    # TAB: SUBSCRIPTION
    # =========================================================================
    with tab_subscription:
        st.markdown("### 💳 Subscription Plans")
        
        if not enable_iap:
            st.info("💡 Subscription / IAP đã được tắt. Bật lại ở tab **Chung** để cấu hình.")
            # Set default empty subscription params when disabled
            subscription_params = {}
            exploitation_day = 0
            platform_fee_pct = 0
        else:
            st.caption("*Cấu hình các gói subscription: Weekly, Monthly, Yearly, Lifetime*")
            
            exploitation_day = st.number_input(
                "Ngày bắt đầu khai thác (show offer)",
                min_value=0, max_value=30, value=0,
                help="Ngày nào sau install sẽ bắt đầu hiển thị offer subscription"
            )
            
            # Platform fee settings
            st.markdown("**Phí nền tảng (App Store / Google Play):**")
            fee_col1, fee_col2 = st.columns([1, 2])
            with fee_col1:
                apply_platform_fee = st.checkbox("Áp dụng phí nền tảng", value=True, key="apply_platform_fee",
                                                  help="Apple/Google thu ~30% doanh thu từ IAP/Subscription")
            with fee_col2:
                if apply_platform_fee:
                    platform_fee_pct = st.slider("Tỷ lệ phí (%)", 0, 50, 30, 1, key="platform_fee_pct",
                                                  help="Thường là 30% cho năm đầu, 15% cho năm thứ 2+")
                else:
                    platform_fee_pct = 0
            
            st.markdown("**Chọn các gói subscription:**")
            plan_col1, plan_col2, plan_col3, plan_col4 = st.columns(4)
            with plan_col1:
                enable_weekly = st.checkbox("📅 Weekly", value=True, key="enable_weekly")
            with plan_col2:
                enable_monthly = st.checkbox("📆 Monthly", value=True, key="enable_monthly")
            with plan_col3:
                enable_yearly = st.checkbox("📅 Yearly", value=False, key="enable_yearly")
            with plan_col4:
                enable_lifetime = st.checkbox("♾️ Lifetime", value=False, key="enable_lifetime")
            
            st.markdown("---")
            
            # Create tabs for each subscription plan
            sub_weekly, sub_monthly, sub_yearly, sub_lifetime = st.tabs([
                "📅 Weekly", "📆 Monthly", "📅 Yearly", "♾️ Lifetime"
            ])
            
            subscription_params = {}
        
            with sub_weekly:
                st.markdown("#### Weekly Subscription")
                col1, col2 = st.columns(2)
                with col1:
                    weekly_price = st.number_input("Giá ($)", 0.99, 9.99, 2.99, 0.50, key="weekly_price")
                    weekly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 2.0, 0.5, key="weekly_pay", help="% users mua gói này") / 100
                    weekly_has_trial = st.checkbox("Có Trial", True, key="weekly_trial")
                with col2:
                    if weekly_has_trial:
                        weekly_trial_days = st.number_input("Trial (ngày)", 1, 14, 3, key="weekly_trial_days")
                        weekly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, 15.0, 1.0, key="weekly_trial_rate") / 100
                    else:
                        weekly_trial_days = 0
                        weekly_trial_rate = 1.0
                
                st.markdown("**Sub Retention (% còn lại):**")
                ret_col1, ret_col2, ret_col3 = st.columns(3)
                with ret_col1:
                    weekly_ret_1 = st.slider("Cycle 1 (Tuần 2)", 0, 100, 50, 1, key="weekly_ret1") / 100
                    weekly_ret_4 = st.slider("Cycle 4 (1 tháng)", 0, 100, 31, 1, key="weekly_ret4") / 100
                with ret_col2:
                    weekly_ret_6 = st.slider("Cycle 6 (1.5 tháng)", 0, 100, 24, 1, key="weekly_ret6") / 100
                    weekly_ret_9 = st.slider("Cycle 9 (2 tháng)", 0, 100, 18, 1, key="weekly_ret9") / 100
                with ret_col3:
                    weekly_ret_12 = st.slider("Cycle 12 (3 tháng)", 0, 100, 15, 1, key="weekly_ret12") / 100
                    weekly_ret_18 = st.slider("Cycle 18 (4.5 tháng)", 0, 100, 10, 1, key="weekly_ret18") / 100
                
                # Create SubscriptionRetentionCurve and interpolate full curve up to 52 cycles
                from config import SubscriptionRetentionCurve
                weekly_sub_ret = SubscriptionRetentionCurve(
                    cycle_0=1.0, cycle_1=weekly_ret_1, cycle_4=weekly_ret_4, 
                    cycle_6=weekly_ret_6, cycle_8=weekly_ret_9, cycle_12=weekly_ret_12,
                    cycle_24=weekly_ret_18, cycle_52=max(0.01, weekly_ret_18 * 0.3)  # Estimate cycle 52
                )
                
                # Input points for highlighting
                input_cycles = [0, 1, 4, 6, 9, 12, 18]
                input_retention = [1.0, weekly_ret_1, weekly_ret_4, weekly_ret_6, weekly_ret_9, weekly_ret_12, weekly_ret_18]
                
                # Full interpolated curve (0 to 52)
                all_cycles = list(range(0, 53))
                all_retention = [weekly_sub_ret.get_retention_at_cycle(c) for c in all_cycles]
                
                fig_weekly = go.Figure()
                # Full curve (interpolated) with fill - using spline for smooth curve
                fig_weekly.add_trace(go.Scatter(
                    x=all_cycles, y=[r*100 for r in all_retention],
                    mode='lines', name='Interpolated',
                    line=dict(color='rgba(102, 126, 234, 0.8)', width=2, shape='spline', smoothing=1.3),
                    fill='tozeroy', fillcolor='rgba(102, 126, 234, 0.15)'
                ))
                # Input points
                fig_weekly.add_trace(go.Scatter(
                    x=input_cycles, y=[r*100 for r in input_retention],
                    mode='markers', name='Input Points',
                    marker=dict(size=8, color='#667eea', line=dict(width=1.5, color='white'))
                ))
                fig_weekly.update_layout(
                    title=f"Weekly Sub Retention (52 tuần) - Cycle 52: {all_retention[52]*100:.1f}%",
                    xaxis_title="Billing Cycle (Week)", yaxis_title="Retention (%)",
                    yaxis=dict(range=[0, 105]), xaxis=dict(dtick=4),
                    height=220, margin=dict(t=35, b=30, l=50, r=20),
                    template="plotly_white", showlegend=False
                )
                st.plotly_chart(fig_weekly, use_container_width=True)
                
                subscription_params['weekly'] = {
                    'price': weekly_price, 'pay_rate': weekly_pay_rate if enable_weekly else 0,
                    'has_trial': weekly_has_trial, 'trial_days': weekly_trial_days,
                    'trial_to_paid': weekly_trial_rate,
                    'sub_ret_1': weekly_ret_1, 'sub_ret_4': weekly_ret_4, 'sub_ret_6': weekly_ret_6,
                    'sub_ret_9': weekly_ret_9, 'sub_ret_12': weekly_ret_12, 'sub_ret_18': weekly_ret_18,
                    'enabled': enable_weekly
                }
            with sub_monthly:
                st.markdown("#### Monthly Subscription")
                col1, col2 = st.columns(2)
                with col1:
                    monthly_price = st.number_input("Giá ($)", 1.99, 29.99, 9.99, 1.0, key="monthly_price")
                    monthly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 3.0, 0.5, key="monthly_pay") / 100
                    monthly_has_trial = st.checkbox("Có Trial", True, key="monthly_trial")
                with col2:
                    if monthly_has_trial:
                        monthly_trial_days = st.number_input("Trial (ngày)", 1, 30, 7, key="monthly_trial_days")
                        monthly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, 20.0, 1.0, key="monthly_trial_rate") / 100
                    else:
                        monthly_trial_days = 0
                        monthly_trial_rate = 1.0
                
                st.markdown("**Sub Retention (% còn lại):**")
                ret_col1, ret_col2 = st.columns(2)
                with ret_col1:
                    monthly_ret_1 = st.slider("Cycle 1 (Tháng 2)", 0, 100, 55, 1, key="monthly_ret1") / 100
                    monthly_ret_3 = st.slider("Cycle 3 (3 tháng)", 0, 100, 42, 1, key="monthly_ret3") / 100
                with ret_col2:
                    monthly_ret_6 = st.slider("Cycle 6 (6 tháng)", 0, 100, 30, 1, key="monthly_ret6") / 100
                    monthly_ret_12 = st.slider("Cycle 12 (1 năm)", 0, 100, 20, 1, key="monthly_ret12") / 100
                
                # Create SubscriptionRetentionCurve and interpolate full curve up to 12 cycles
                monthly_sub_ret = SubscriptionRetentionCurve(
                    cycle_0=1.0, cycle_1=monthly_ret_1, cycle_3=monthly_ret_3, 
                    cycle_6=monthly_ret_6, cycle_12=monthly_ret_12
                )
                
                # Input points for highlighting
                input_cycles = [0, 1, 3, 6, 12]
                input_retention = [1.0, monthly_ret_1, monthly_ret_3, monthly_ret_6, monthly_ret_12]
                
                # Full interpolated curve (0 to 12)
                all_cycles = list(range(0, 13))
                all_retention = [monthly_sub_ret.get_retention_at_cycle(c) for c in all_cycles]
                
                fig_monthly = go.Figure()
                # Full curve (interpolated) with fill - using spline for smooth curve
                fig_monthly.add_trace(go.Scatter(
                    x=all_cycles, y=[r*100 for r in all_retention],
                    mode='lines', name='Interpolated',
                    line=dict(color='rgba(29, 209, 161, 0.8)', width=2, shape='spline', smoothing=1.3),
                    fill='tozeroy', fillcolor='rgba(29, 209, 161, 0.15)'
                ))
                # Input points
                fig_monthly.add_trace(go.Scatter(
                    x=input_cycles, y=[r*100 for r in input_retention],
                    mode='markers', name='Input Points',
                    marker=dict(size=8, color='#1dd1a1', line=dict(width=1.5, color='white'))
                ))
                fig_monthly.update_layout(
                    title=f"Monthly Sub Retention (12 tháng) - Cycle 12: {monthly_ret_12*100:.1f}%",
                    xaxis_title="Billing Cycle (Month)", yaxis_title="Retention (%)",
                    yaxis=dict(range=[0, 105]), xaxis=dict(dtick=1),
                    height=220, margin=dict(t=35, b=30, l=50, r=20),
                    template="plotly_white", showlegend=False
                )
                st.plotly_chart(fig_monthly, use_container_width=True)
                
                subscription_params['monthly'] = {
                    'price': monthly_price, 'pay_rate': monthly_pay_rate if enable_monthly else 0,
                    'has_trial': monthly_has_trial, 'trial_days': monthly_trial_days,
                    'trial_to_paid': monthly_trial_rate,
                    'sub_ret_1': monthly_ret_1, 'sub_ret_3': monthly_ret_3, 'sub_ret_6': monthly_ret_6, 'sub_ret_12': monthly_ret_12,
                    'enabled': enable_monthly
                }
            
            with sub_yearly:
                st.markdown("#### Yearly Subscription")
                col1, col2 = st.columns(2)
                with col1:
                    yearly_price = st.number_input("Giá ($)", 9.99, 149.99, 49.99, 5.0, key="yearly_price")
                    yearly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 1.0, 0.2, key="yearly_pay") / 100
                    yearly_has_trial = st.checkbox("Có Trial", True, key="yearly_trial")
                with col2:
                    if yearly_has_trial:
                        yearly_trial_days = st.number_input("Trial (ngày)", 1, 30, 7, key="yearly_trial_days")
                        yearly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, 25.0, 1.0, key="yearly_trial_rate") / 100
                    else:
                        yearly_trial_days = 0
                        yearly_trial_rate = 1.0
                        
                    st.info("💡 Với cohort 365 ngày, gói Yearly chỉ có 1 lần thanh toán (không renewal)")
                
                subscription_params['yearly'] = {
                    'price': yearly_price, 'pay_rate': yearly_pay_rate if enable_yearly else 0,
                    'has_trial': yearly_has_trial, 'trial_days': yearly_trial_days,
                    'trial_to_paid': yearly_trial_rate,
                    'enabled': enable_yearly
                }
            
            with sub_lifetime:
                st.markdown("#### Lifetime (One-time Purchase)")
                col1, col2 = st.columns(2)
                with col1:
                    lifetime_price = st.number_input("Giá ($)", 29.99, 299.99, 99.99, 10.0, key="lifetime_price")
                    lifetime_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 0.5, 0.1, key="lifetime_pay") / 100
                with col2:
                    st.info("💡 Lifetime không có trial và không cần renewal")
                
                subscription_params['lifetime'] = {
                    'price': lifetime_price, 'pay_rate': lifetime_pay_rate if enable_lifetime else 0,
                    'has_trial': False, 'trial_days': 0,
                    'trial_to_paid': 1.0,
                    'enabled': enable_lifetime
                }
            
            # Summary
            total_pay_rate = sum([p['pay_rate'] for p in subscription_params.values()])
            st.markdown(f"**Tổng Pay Rate:** {total_pay_rate * 100:.1f}% users sẽ subscribe bất kỳ gói nào")
    
    # =========================================================================
    # TAB: VARIATION (BIẾN ĐỘNG)
    # =========================================================================
    with tab_variation:
        st.markdown("### 📊 Thông số Biến động (Variation)")
        st.caption("*Độ biến động của các thông số trong Monte Carlo simulation. Giá trị càng cao = kết quả càng phân tán*")
        
        st.markdown("""
        <div class="vn-note">
        💡 <strong>Giải thích:</strong> Mỗi kịch bản Monte Carlo sẽ lấy mẫu ngẫu nhiên từ phân phối 
        với độ lệch chuẩn = Giá trị mặc định × Variation %. <br>
        Ví dụ: CPM = $5.0, Variation = 15% → σ = $0.75 → CPM sẽ dao động trong khoảng $3.50 - $6.50 (±2σ)
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # UA Variations
        st.markdown("#### 📢 Biến động User Acquisition")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpm_variation = st.slider(
                "CPM Variation (%)",
                min_value=0.0, max_value=50.0, value=1.0, step=0.5,
                help="Độ biến động của CPM giữa các kịch bản",
                key="var_cpm"
            ) / 100
            
        with col2:
            ctr_variation = st.slider(
                "CTR Variation (%)",
                min_value=0.0, max_value=50.0, value=1.0, step=0.5,
                help="Độ biến động của Click-Through Rate",
                key="var_ctr"
            ) / 100
            
        with col3:
            cvr_variation = st.slider(
                "CVR Variation (%)",
                min_value=0.0, max_value=60.0, value=1.0, step=0.5,
                help="Độ biến động của Conversion Rate",
                key="var_cvr"
            ) / 100
        
        st.markdown("---")
        
        # Ads Variations
        st.markdown("#### 📺 Biến động Monetization")
        col1, col2 = st.columns(2)
        
        with col1:
            ecpm_variation = st.slider(
                "eCPM Variation (%)",
                min_value=0.0, max_value=50.0, value=1.0, step=0.5,
                help="Độ biến động của eCPM",
                key="var_ecpm"
            ) / 100
            
        with col2:
            impressions_variation = st.slider(
                "Impressions Variation (%)",
                min_value=0.0, max_value=40.0, value=1.0, step=0.5,
                help="Độ biến động của số lượt xem quảng cáo",
                key="var_impressions"
            ) / 100
        
        st.markdown("---")
        
        # Retention & Subscription Variations
        st.markdown("#### 📉 Biến động Retention & Subscription")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            retention_variation = st.slider(
                "Retention Variation (%)",
                min_value=0.0, max_value=40.0, value=1.0, step=0.5,
                help="Độ biến động của tỷ lệ retention",
                key="var_retention"
            ) / 100
            
        with col2:
            pay_rate_variation = st.slider(
                "Pay Rate Variation (%)",
                min_value=0.0, max_value=60.0, value=1.0, step=0.5,
                help="Độ biến động của tỷ lệ subscribe",
                key="var_pay_rate"
            ) / 100
            
        with col3:
            sub_ret_variation = st.slider(
                "Sub Retention Variation (%)",
                min_value=0.0, max_value=40.0, value=1.0, step=0.5,
                help="Độ biến động của tỷ lệ giữ chân subscription",
                key="var_sub_ret"
            ) / 100
        
        # Summary table
        st.markdown("---")
        st.markdown("#### 📋 Tổng hợp Variation")
        
        variation_df = pd.DataFrame([
            {"Thông số": "CPM", "Variation": f"±{cpm_variation*100:.2f}%", "Mô tả": "Chi phí 1000 impressions"},
            {"Thông số": "CTR", "Variation": f"±{ctr_variation*100:.2f}%", "Mô tả": "Tỷ lệ click"},
            {"Thông số": "CVR", "Variation": f"±{cvr_variation*100:.2f}%", "Mô tả": "Tỷ lệ click → install"},
            {"Thông số": "eCPM", "Variation": f"±{ecpm_variation*100:.2f}%", "Mô tả": "Doanh thu ads/1000 views"},
            {"Thông số": "Impressions", "Variation": f"±{impressions_variation*100:.2f}%", "Mô tả": "Số ads/user/ngày"},
            {"Thông số": "Retention", "Variation": f"±{retention_variation*100:.2f}%", "Mô tả": "Tỷ lệ giữ chân user"},
            {"Thông số": "Pay Rate", "Variation": f"±{pay_rate_variation*100:.2f}%", "Mô tả": "Tỷ lệ mua subscription"},
            {"Thông số": "Sub Retention", "Variation": f"±{sub_ret_variation*100:.2f}%", "Mô tả": "Tỷ lệ giữ chân subscriber"},
        ])
        st.dataframe(variation_df, use_container_width=True, hide_index=True)
    
    # Store variation params for use in simulation
    variation_params = {
        'cpm_variation': cpm_variation,
        'ctr_variation': ctr_variation,
        'cvr_variation': cvr_variation,
        'ecpm_variation': ecpm_variation,
        'impressions_variation': impressions_variation,
        'retention_variation': retention_variation,
        'pay_rate_variation': pay_rate_variation,
        'sub_ret_variation': sub_ret_variation
    }
    
    # =========================================================================
    # TAB: SPEND PLANNING
    # =========================================================================
    with tab_spend:
        st.markdown("### 💰 Kế hoạch Chi tiêu UA")
        st.caption("*Lập kế hoạch chi tiêu UA theo ngày trong tương lai và xem dự báo doanh thu/lợi nhuận*")
        
        st.markdown("""
        <div class="vn-note">
        💡 <strong>Hướng dẫn:</strong> Chọn khoảng thời gian chi tiêu và nhập budget hàng ngày. 
        Sau khi chạy simulation, bạn sẽ thấy dự báo doanh thu và lợi nhuận theo từng ngày.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Enable spend planning
        enable_spend_plan = st.checkbox("✅ Kích hoạt Spend Planning", value=True, key="enable_spend_plan",
                                         help="Bật để cấu hình kế hoạch chi tiêu và xem biểu đồ revenue/profit")
        
        if enable_spend_plan:
            # Date range selection
            st.markdown("#### 📅 Khoảng thời gian")
            date_col1, date_col2 = st.columns(2)
            
            with date_col1:
                spend_start_date = st.date_input(
                    "Ngày bắt đầu",
                    value=datetime.today(),
                    key="spend_start_date",
                    help="Ngày bắt đầu chiến dịch UA"
                )
            
            with date_col2:
                spend_end_date = st.date_input(
                    "Ngày kết thúc",
                    value=datetime.today() + timedelta(days=30),
                    key="spend_end_date",
                    help="Ngày kết thúc chiến dịch UA"
                )
            
            # Validate dates
            spend_total_days = (spend_end_date - spend_start_date).days + 1
            if spend_total_days <= 0:
                st.error("⚠️ Ngày kết thúc phải sau ngày bắt đầu!")
                spend_total_days = 1
            
            st.markdown("---")
            
            # Daily spend configuration
            st.markdown("#### 💵 Chi tiêu hàng ngày")
            
            spend_mode = st.radio(
                "Chế độ chi tiêu",
                ["Fixed Daily", "Weekday/Weekend Pattern", "Monthly Pattern", "Weekly Pattern"],
                horizontal=True,
                key="spend_mode",
                help="Fixed: cố định mỗi ngày. Pattern: khác nhau theo tuần/tháng."
            )
            
            if spend_mode == "Fixed Daily":
                daily_spend = st.number_input(
                    "Spend mỗi ngày ($)",
                    min_value=0.0, max_value=100000.0, value=100.0, step=10.0,
                    key="daily_spend_fixed",
                    help="Chi tiêu UA cố định mỗi ngày"
                )
                spend_schedule = {d: daily_spend for d in range(spend_total_days)}
                
            elif spend_mode == "Weekday/Weekend Pattern":
                spend_col1, spend_col2 = st.columns(2)
                with spend_col1:
                    weekday_spend = st.number_input(
                        "Spend ngày thường ($)",
                        min_value=0.0, max_value=100000.0, value=100.0, step=10.0,
                        key="weekday_spend"
                    )
                with spend_col2:
                    weekend_spend = st.number_input(
                        "Spend cuối tuần ($)",
                        min_value=0.0, max_value=100000.0, value=150.0, step=10.0,
                        key="weekend_spend"
                    )
                
                # Create schedule based on weekday/weekend
                spend_schedule = {}
                for d in range(spend_total_days):
                    date = spend_start_date + timedelta(days=d)
                    if date.weekday() >= 5:  # Saturday=5, Sunday=6
                        spend_schedule[d] = weekend_spend
                    else:
                        spend_schedule[d] = weekday_spend
                daily_spend = weekday_spend  # For average calculation
                
            elif spend_mode == "Monthly Pattern":
                st.info("💡 Monthly Pattern: Nhập spend trung bình mỗi ngày cho từng tháng")
                custom_months = min(12, (spend_total_days + 29) // 30)  # Max 12 months
                monthly_spends = []
                
                month_cols = st.columns(min(4, custom_months))
                for m in range(custom_months):
                    with month_cols[m % 4]:
                        monthly_spend = st.number_input(
                            f"Tháng {m+1} ($)",
                            min_value=0.0, max_value=100000.0, value=100.0 * (1 + m * 0.1), step=10.0,
                            key=f"month_{m}_spend"
                        )
                        monthly_spends.append(monthly_spend)
                
                # Create schedule based on monthly pattern
                spend_schedule = {}
                for d in range(spend_total_days):
                    month_idx = min(d // 30, len(monthly_spends) - 1)
                    spend_schedule[d] = monthly_spends[month_idx]
                daily_spend = np.mean(list(spend_schedule.values()))
                
            else:  # Weekly Pattern
                st.info("💡 Weekly Pattern: Nhập spend cho từng tuần")
                custom_weeks = min(8, (spend_total_days + 6) // 7)  # Max 8 weeks
                weekly_spends = []
                
                week_cols = st.columns(min(4, custom_weeks))
                for w in range(custom_weeks):
                    with week_cols[w % 4]:
                        weekly_spend = st.number_input(
                            f"Tuần {w+1} ($)",
                            min_value=0.0, max_value=100000.0, value=100.0 * (1 + w * 0.1), step=10.0,
                            key=f"week_{w}_spend"
                        )
                        weekly_spends.append(weekly_spend)
                
                # Create schedule based on weekly pattern
                spend_schedule = {}
                for d in range(spend_total_days):
                    week_idx = min(d // 7, len(weekly_spends) - 1)
                    spend_schedule[d] = weekly_spends[week_idx]
                daily_spend = np.mean(list(spend_schedule.values()))
            
            # Calculate totals
            total_spend = sum(spend_schedule.values())
            avg_daily_spend = total_spend / spend_total_days if spend_total_days > 0 else 0
            
            st.markdown("---")
            
            # Summary metrics
            st.markdown("#### 📊 Tổng kết Kế hoạch")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("📆 Số ngày", f"{spend_total_days} ngày")
            with summary_col2:
                st.metric("💵 Spend TB/ngày", f"${avg_daily_spend:,.0f}")
            with summary_col3:
                st.metric("💰 Tổng Spend", f"${total_spend:,.0f}")
            
            # Spend curve preview
            st.markdown("#### 📈 Preview Spend Curve")
            spend_dates = [spend_start_date + timedelta(days=d) for d in range(spend_total_days)]
            spend_values = [spend_schedule[d] for d in range(spend_total_days)]
            
            fig_spend = go.Figure()
            fig_spend.add_trace(go.Bar(
                x=spend_dates, y=spend_values,
                name='Daily Spend',
                marker_color='rgba(239, 68, 68, 0.7)'
            ))
            fig_spend.update_layout(
                title=f"Kế hoạch Chi tiêu ({spend_total_days} ngày) - Tổng: ${total_spend:,.0f}",
                xaxis_title="Ngày", yaxis_title="Spend ($)",
                height=250, margin=dict(t=35, b=30, l=50, r=20),
                template="plotly_white", showlegend=False
            )
            st.plotly_chart(fig_spend, use_container_width=True)
            
            # Store spend plan in session state
            st.session_state.spend_plan = {
                'enabled': True,
                'start_date': spend_start_date,
                'end_date': spend_end_date,
                'total_days': spend_total_days,
                'schedule': spend_schedule,
                'total_spend': total_spend,
                'avg_daily_spend': avg_daily_spend
            }
        else:
            st.session_state.spend_plan = {'enabled': False}
    
    # =========================================================================
    # RUN SIMULATION
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🎲 Chạy Mô phỏng")
    
    run_col1, run_col2 = st.columns([1, 3])
    
    with run_col1:
        run_button = st.button("🚀 Chạy Simulation", type="primary", use_container_width=True)
    
    with run_col2:
        st.caption(f"Sẽ chạy {n_simulations} kịch bản trong {sim_days} ngày với các thông số đã cấu hình")
    
    if run_button:
        # Build custom config
        custom_config = AppConfig()
        
        # UA
        custom_config.ua.cpm = cpm
        custom_config.ua.ctr = ctr
        custom_config.ua.cvr = cvr
        custom_config.ua.organic_ratio = organic_ratio
        
        # Ads - only set if IAA is enabled
        if enable_iaa:
            custom_config.ads.ecpm_d0 = ecpm_d0
            custom_config.ads.impressions_per_dau_d0 = impressions_d0
            custom_config.ads.ecpm_saturation_ratio = ecpm_saturation
            custom_config.ads.impressions_saturation_ratio = impressions_saturation
            custom_config.ads.decay_half_life_days = decay_half_life
        else:
            # Disable ads revenue
            custom_config.ads.ecpm_d0 = 0
            custom_config.ads.impressions_per_dau_d0 = 0
        
        # Retention
        custom_config.retention.d1 = d1
        custom_config.retention.d3 = d3
        custom_config.retention.d7 = d7
        custom_config.retention.d14 = d14
        custom_config.retention.d30 = d30
        custom_config.retention.d60 = d60
        custom_config.retention.d90 = d90
        custom_config.retention.d180 = d180
        custom_config.retention.d365 = d365
        
        # Subscription - only set if IAP is enabled
        if enable_iap and subscription_params:
            custom_config.subscription.exploitation_start_day = exploitation_day
            custom_config.subscription.platform_fee_rate = platform_fee_pct / 100  # Convert % to rate
            
            # Weekly - Using Subscription Retention Curve
            if 'weekly' in subscription_params:
                custom_config.subscription.weekly.price = subscription_params['weekly']['price']
                custom_config.subscription.weekly.pay_rate = subscription_params['weekly']['pay_rate']
                custom_config.subscription.weekly.has_trial = subscription_params['weekly']['has_trial']
                custom_config.subscription.weekly.trial_days = subscription_params['weekly']['trial_days']
                custom_config.subscription.weekly.trial_to_paid_rate = subscription_params['weekly']['trial_to_paid']
                custom_config.subscription.weekly.sub_retention.cycle_1 = subscription_params['weekly']['sub_ret_1']
                custom_config.subscription.weekly.sub_retention.cycle_4 = subscription_params['weekly']['sub_ret_4']
                custom_config.subscription.weekly.sub_retention.cycle_6 = subscription_params['weekly']['sub_ret_6']
                custom_config.subscription.weekly.sub_retention.cycle_8 = subscription_params['weekly']['sub_ret_9']  # Use cycle_8 for 9
                custom_config.subscription.weekly.sub_retention.cycle_12 = subscription_params['weekly']['sub_ret_12']
                custom_config.subscription.weekly.sub_retention.cycle_24 = subscription_params['weekly']['sub_ret_18']  # Approximate
            
            # Monthly - Using Subscription Retention Curve
            if 'monthly' in subscription_params:
                custom_config.subscription.monthly.price = subscription_params['monthly']['price']
                custom_config.subscription.monthly.pay_rate = subscription_params['monthly']['pay_rate']
                custom_config.subscription.monthly.has_trial = subscription_params['monthly']['has_trial']
                custom_config.subscription.monthly.trial_days = subscription_params['monthly']['trial_days']
                custom_config.subscription.monthly.trial_to_paid_rate = subscription_params['monthly']['trial_to_paid']
                custom_config.subscription.monthly.sub_retention.cycle_1 = subscription_params['monthly']['sub_ret_1']
                custom_config.subscription.monthly.sub_retention.cycle_3 = subscription_params['monthly']['sub_ret_3']
                custom_config.subscription.monthly.sub_retention.cycle_6 = subscription_params['monthly']['sub_ret_6']
                custom_config.subscription.monthly.sub_retention.cycle_12 = subscription_params['monthly']['sub_ret_12']
            
            # Yearly - Using Subscription Retention Curve
            if 'yearly' in subscription_params:
                custom_config.subscription.yearly.price = subscription_params['yearly']['price']
                custom_config.subscription.yearly.pay_rate = subscription_params['yearly']['pay_rate']
                custom_config.subscription.yearly.has_trial = subscription_params['yearly']['has_trial']
                custom_config.subscription.yearly.trial_days = subscription_params['yearly']['trial_days']
                custom_config.subscription.yearly.trial_to_paid_rate = subscription_params['yearly']['trial_to_paid']
                # Yearly không có renewal trong 360 ngày
            
            # Lifetime
            if 'lifetime' in subscription_params:
                custom_config.subscription.lifetime.price = subscription_params['lifetime']['price']
                custom_config.subscription.lifetime.pay_rate = subscription_params['lifetime']['pay_rate']
        else:
            # Disable subscription revenue by setting all pay_rates to 0
            custom_config.subscription.weekly.pay_rate = 0
            custom_config.subscription.monthly.pay_rate = 0
            custom_config.subscription.yearly.pay_rate = 0
            custom_config.subscription.lifetime.pay_rate = 0
        
        custom_config.simulation_days = sim_days
        
        # Variation parameters
        custom_config.simulation.cpm_variation = variation_params['cpm_variation']
        custom_config.simulation.ctr_variation = variation_params['ctr_variation']
        custom_config.simulation.cvr_variation = variation_params['cvr_variation']
        custom_config.simulation.ecpm_variation = variation_params['ecpm_variation']
        custom_config.simulation.retention_variation = variation_params['retention_variation']
        custom_config.simulation.pay_rate_variation = variation_params['pay_rate_variation']
        custom_config.simulation.sub_ret_variation = variation_params['sub_ret_variation']
        
        # Run simulation
        with st.spinner(f"Đang chạy {n_simulations} kịch bản Monte Carlo..."):
            simulator = EnhancedMonteCarloSimulator(config=custom_config, n_simulations=n_simulations)
            results = simulator.run(days=sim_days)
            
            st.session_state.simulation_results = results
            st.session_state.simulation_raw = simulator.results
            st.session_state.simulation_run = True
            st.session_state.simulation_config = custom_config
        
        st.success("✅ Simulation hoàn tất!")
    
    # =========================================================================
    # DISPLAY RESULTS
    # =========================================================================
    if st.session_state.get('simulation_run') and 'simulation_raw' in st.session_state:
        raw_results = st.session_state.simulation_raw
        
        # Calculate all statistics from raw_results to ensure consistency
        roas_arr = np.array([r['roas'] for r in raw_results])
        ltv_arr = np.array([r['ltv_total'] for r in raw_results])
        ltv_iaa_arr = np.array([r['ltv_iaa'] for r in raw_results])
        ltv_iap_arr = np.array([r['ltv_iap'] for r in raw_results])
        cpi_arr = np.array([r['blended_cpi'] for r in raw_results if r['blended_cpi'] != float('inf')])
        
        # Use MEAN for confidence intervals
        roas_mean = float(np.mean(roas_arr))
        roas_p5 = float(np.percentile(roas_arr, 5))
        roas_p95 = float(np.percentile(roas_arr, 95))
        
        ltv_mean = float(np.mean(ltv_arr))
        ltv_iaa_mean = float(np.mean(ltv_iaa_arr))
        ltv_iap_mean = float(np.mean(ltv_iap_arr))
        cpi_mean = float(np.mean(cpi_arr)) if len(cpi_arr) > 0 else 0
        
        prob_profit = float(np.mean([1 if r >= 1.0 else 0 for r in roas_arr]))
        n_simulations = len(raw_results)
        
        st.markdown("---")
        st.markdown("### 📊 Kết quả Mô phỏng")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "ROAS (Mean)",
                f"{roas_mean * 100:.1f}%",
                help="Giá trị ROAS trung bình - phản ánh kỳ vọng tổng thể"
            )
        
        with col2:
            st.metric(
                "Xác suất Có lãi",
                f"{prob_profit * 100:.1f}%",
                help="% kịch bản có ROAS >= 100%"
            )
        
        with col3:
            st.metric(
                "LTV (Mean)",
                f"${ltv_mean:.4f}",
                help="Lifetime Value trung vị per user"
            )
        
        with col4:
            st.metric(
                "CPI Blended",
                f"${cpi_mean:.2f}" if cpi_mean > 0 else "N/A",
                help="Chi phí thu hút user trung bình (bao gồm organic)"
            )
        
        # LTV Breakdown
        st.markdown("#### 💰 LTV Breakdown")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("LTV from Ads (IAA)", f"${ltv_iaa_mean:.4f}", 
                     f"{ltv_iaa_mean/ltv_mean*100:.1f}% of total" if ltv_mean > 0 else "")
        with col2:
            st.metric("LTV from Subs (IAP)", f"${ltv_iap_mean:.4f}",
                     f"{ltv_iap_mean/ltv_mean*100:.1f}% of total" if ltv_mean > 0 else "")
        with col3:
            st.metric("Total LTV", f"${ltv_mean:.4f}")
        
        # ROAS Distribution Chart
        st.markdown("#### 📈 Phân phối ROAS")
        
        roas_values = [r['roas'] * 100 for r in raw_results]
        
        # Calculate all percentiles for display
        roas_p25 = float(np.percentile(roas_arr, 25))
        roas_p50 = float(np.percentile(roas_arr, 50))  # = median
        roas_p75 = float(np.percentile(roas_arr, 75))
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=roas_values,
            nbinsx=50,
            name='ROAS Distribution',
            marker_color='#667eea',
            opacity=0.75
        ))
        
        # Add all ROAS lines
        # Pessimistic (P5)
        fig.add_vline(x=roas_p5 * 100, line_dash="dash", line_color="#ff6b6b", 
                     annotation_text=f"P5 ({roas_p5*100:.1f}%)", 
                     annotation_position="bottom left",
                     annotation_font_size=10)
        
        # Safe (P25)
        fig.add_vline(x=roas_p25 * 100, line_dash="dash", line_color="#feca57", 
                     annotation_text=f"P25 ({roas_p25*100:.1f}%)", 
                     annotation_position="bottom left",
                     annotation_font_size=10)
        
        # Median (P50)
        fig.add_vline(x=roas_p50 * 100, line_dash="solid", line_color="#1dd1a1", line_width=2,
                     annotation_text=f"Median ({roas_p50*100:.1f}%)", 
                     annotation_position="top left",
                     annotation_font_size=11)
        
        # Breakthrough (P75)
        fig.add_vline(x=roas_p75 * 100, line_dash="dash", line_color="#48dbfb", 
                     annotation_text=f"P75 ({roas_p75*100:.1f}%)", 
                     annotation_position="bottom right",
                     annotation_font_size=10)
        
        # Optimistic (P95)
        fig.add_vline(x=roas_p95 * 100, line_dash="dash", line_color="#5f27cd", 
                     annotation_text=f"P95 ({roas_p95*100:.1f}%)", 
                     annotation_position="bottom right",
                     annotation_font_size=10)
        
        # Breakeven (100%)
        fig.add_vline(x=100, line_dash="dot", line_color="red", line_width=2,
                     annotation_text="Breakeven", 
                     annotation_position="top right",
                     annotation_font_size=11)
        
        fig.update_layout(
            title=f"Phân phối ROAS ({n_simulations} kịch bản)",
            xaxis_title="ROAS (%)",
            yaxis_title="Số kịch bản",
            template="plotly_white",
            height=300,  # Adjusted height
            margin=dict(t=35, b=30, l=50, r=20),  # Consistent margin
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # =====================================================================
        # ROAS CURVES CHART - Show all scenarios over time
        # =====================================================================
        st.markdown("#### 📉 Đường ROAS theo Thời gian (Tất cả kịch bản)")
        
        # Check if roas_curve data is available
        if raw_results and 'roas_curve' in raw_results[0]:
            milestones = ['d0', 'd1', 'd3', 'd7', 'd14', 'd21', 'd30', 'd45', 'd60', 'd90', 'd120', 'd150', 'd180', 'd210', 'd240', 'd270', 'd300', 'd330', 'd365']
            milestone_days = [0, 1, 3, 7, 14, 21, 30, 45, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 365]
            
            fig_curves = go.Figure()
            
            # Limit number of curves to display for performance
            max_curves = min(100, len(raw_results))
            sample_indices = np.linspace(0, len(raw_results)-1, max_curves, dtype=int)
            
            # Plot each scenario as a semi-transparent line
            for idx in sample_indices:
                result = raw_results[idx]
                curve = result.get('roas_curve', {})
                
                # Build y_values
                y_values = []
                for i, m in enumerate(milestones):
                    if m in curve:
                        y_values.append(curve[m] * 100)
                    else:
                        # If milestone not in curve (old data), interpolate from final ROAS
                        day_num = milestone_days[i]
                        final_roas = result.get('roas', 0)
                        estimated = final_roas * (day_num / 365) * 100
                        y_values.append(estimated)
                
                fig_curves.add_trace(go.Scatter(
                    x=milestone_days,
                    y=y_values,
                    mode='lines',
                    line=dict(color='rgba(102, 126, 234, 0.15)', width=1),
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            # Add percentile lines (P5, P25, P50, P75, P95)
            for p, name, color, dash in [
                (5, 'P5 (Pessimistic)', '#ff6b6b', 'dash'),
                (25, 'P25 (Safe)', '#feca57', 'dash'),
                (50, 'P50 (Median)', '#1dd1a1', 'solid'),
                (75, 'P75 (Breakthrough)', '#48dbfb', 'dash'),
                (95, 'P95 (Optimistic)', '#5f27cd', 'dash')
            ]:
                y_percentile = []
                for i, m in enumerate(milestones):
                    # Get values for this milestone
                    values = []
                    for r in raw_results:
                        curve = r.get('roas_curve', {})
                        if m in curve:
                            values.append(curve[m] * 100)
                        else:
                            # Interpolate from final ROAS
                            day_num = milestone_days[i]
                            values.append(r.get('roas', 0) * (day_num / 365) * 100)
                    y_percentile.append(np.percentile(values, p))
                
                fig_curves.add_trace(go.Scatter(
                    x=milestone_days,
                    y=y_percentile,
                    mode='lines+markers',
                    name=name,
                    line=dict(color=color, width=2 if p == 50 else 1.5, dash=dash),
                    marker=dict(size=6 if p == 50 else 4)
                ))
            
            # Add breakeven line
            fig_curves.add_hline(y=100, line_dash="dot", line_color="red",
                               annotation_text="Breakeven (100%)", annotation_position="right")
            
            # Add Target line
            fig_curves.add_hline(y=130, line_dash="dash", line_color="#00b894",
                               annotation_text="Target (130%)", annotation_position="right")
            
            # Calculate reasonable Y-axis max based on P95 at D365
            final_roas_values = [r.get('roas_curve', {}).get('d365', r['roas']) * 100 for r in raw_results]
            y_max = max(np.percentile(final_roas_values, 95) * 1.2, 150)  # At least 150% or P95 + 20%
            y_max = min(y_max, 500)  # Cap at 500% max
            
            fig_curves.update_layout(
                title=f"ROAS theo Lifetime ({max_curves} kịch bản hiển thị)",
                xaxis_title="Ngày từ Install",
                yaxis_title="ROAS (%)",
                template="plotly_white",
                height=450,
                margin=dict(t=35, b=30, l=50, r=20),  # Consistent margin
                yaxis=dict(range=[0, y_max]),  # Cap Y-axis
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    type='linear',  # Ensure linear scale for proper proportions
                    tickmode='array',
                    tickvals=[0, 30, 60, 90, 120, 180, 270, 365],
                    ticktext=['D0', 'D30', 'D60', 'D90', 'D120', 'D180', 'D270', 'D365']
                )
            )
            st.plotly_chart(fig_curves, use_container_width=True)
        else:
            st.info("💡 Dữ liệu ROAS curve không khả dụng. Vui lòng chạy lại simulation.")
        
        # Target ROAS thresholds - Use raw results to calculate percentiles
        st.markdown("#### 🎯 Ngưỡng ROAS Mục tiêu")
        
        roas_values_arr = np.array([r['roas'] for r in raw_results])
        targets = {
            'roas': {
                'pessimistic': float(np.percentile(roas_values_arr, 5)),
                'safe': float(np.percentile(roas_values_arr, 25)),
                'expected': float(np.median(roas_values_arr)),  # Use MEDIAN
                'breakthrough': float(np.percentile(roas_values_arr, 75)),
                'optimistic': float(np.percentile(roas_values_arr, 95))
            }
        }
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div style="background:#ff6b6b; color:white; padding:10px; border-radius:5px; text-align:center;">
            <b>Pessimistic</b><br/>
            {targets['roas']['pessimistic']*100:.1f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background:#feca57; color:white; padding:10px; border-radius:5px; text-align:center;">
            <b>Safe (25%)</b><br/>
            {targets['roas']['safe']*100:.1f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background:#48dbfb; color:white; padding:10px; border-radius:5px; text-align:center;">
            <b>Expected</b><br/>
            {targets['roas']['expected']*100:.1f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background:#1dd1a1; color:white; padding:10px; border-radius:5px; text-align:center;">
            <b>Breakthrough</b><br/>
            {targets['roas']['breakthrough']*100:.1f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div style="background:#5f27cd; color:white; padding:10px; border-radius:5px; text-align:center;">
            <b>Optimistic</b><br/>
            {targets['roas']['optimistic']*100:.1f}%
            </div>
            """, unsafe_allow_html=True)
        
        # Confidence Interval
        st.markdown(f"""
        **Khoảng tin cậy 90%:** [{roas_p5*100:.1f}%, {roas_p95*100:.1f}%]
        
        *Nghĩa là 90% các kịch bản sẽ có ROAS nằm trong khoảng này.*
        """)
        
        # =====================================================================
        # REVENUE & PROFIT PROJECTION (Based on Spend Planning)
        # =====================================================================
        spend_plan = st.session_state.get('spend_plan', {'enabled': False})
        
        if spend_plan.get('enabled', False) and cpi_mean > 0:
            st.markdown("---")
            st.markdown("### 💹 Dự báo Doanh thu & Lợi nhuận theo Kế hoạch Chi tiêu")
            st.caption("*Dựa trên LTV simulation và kế hoạch spend đã cấu hình*")
            
            # Get spend plan data
            spend_schedule = spend_plan['schedule']
            spend_total_days = spend_plan['total_days']
            spend_start_date = spend_plan['start_date']
            total_spend = spend_plan['total_spend']
            
            # Use average daily breakdown from simulations to get LTV curve
            # Build LTV curve using mean LTV and simulation days
            sim_days_cfg = st.session_state.get('simulation_config', None)
            max_day = sim_days_cfg.simulation_days if sim_days_cfg else 365
            
            # Check if we have daily_breakdown data, otherwise build synthetic curve
            has_breakdown = raw_results and 'daily_breakdown' in raw_results[0] and len(raw_results[0].get('daily_breakdown', [])) > 0
            
            if has_breakdown:
                # Get average LTV contribution by day from all simulations
                sample_breakdown = raw_results[0]['daily_breakdown']
                max_day = len(sample_breakdown)
                
                # Build average cumulative LTV curve
                ltv_curve = []
                for day in range(max_day):
                    day_ltvs = []
                    for result in raw_results[:min(100, len(raw_results))]:  # Sample 100 for speed
                        if day < len(result.get('daily_breakdown', [])):
                            day_ltvs.append(result['daily_breakdown'][day].get('cumulative_total', 0))
                    ltv_curve.append(np.mean(day_ltvs) if day_ltvs else 0)
            else:
                # Fallback: Build synthetic LTV curve based on retention and mean LTV
                # LTV accumulates following retention curve shape
                st.info("💡 Sử dụng LTV curve ước tính từ giá trị trung bình.")
                ltv_curve = []
                config = st.session_state.get('simulation_config', None)
                if config:
                    # Simple exponential decay based LTV accumulation
                    for day in range(max_day):
                        # LTV accumulates roughly following: final_ltv * (1 - exp(-day/half_life))
                        progress = 1 - np.exp(-day / 30)  # ~30 day half-life
                        ltv_curve.append(ltv_mean * progress)
                else:
                    for day in range(max_day):
                        progress = 1 - np.exp(-day / 30)
                        ltv_curve.append(ltv_mean * progress)
            
            if len(ltv_curve) > 0:
                
                # Calculate daily revenue from cohorts
                # For each spend day, calculate how much revenue that cohort generates on each future day
                projection_days = min(spend_total_days + 90, 365)  # Project spend period + 90 days
                
                daily_revenue_iaa = [0.0] * projection_days
                daily_revenue_iap = [0.0] * projection_days
                daily_spend_proj = [0.0] * projection_days
                cumulative_spend = [0.0] * projection_days
                cumulative_revenue = [0.0] * projection_days
                
                # For each day we spend
                for spend_day_idx, daily_spend_val in spend_schedule.items():
                    if spend_day_idx >= projection_days:
                        continue
                        
                    # Calculate installs from this spend
                    installs = daily_spend_val / cpi_mean if cpi_mean > 0 else 0
                    
                    # Record spend
                    daily_spend_proj[spend_day_idx] = daily_spend_val
                    
                    # For this cohort, add revenue contribution to each future day
                    for days_since_install in range(min(len(ltv_curve), projection_days - spend_day_idx)):
                        revenue_day_idx = spend_day_idx + days_since_install
                        if revenue_day_idx >= projection_days:
                            break
                        
                        # Incremental LTV for this day
                        if days_since_install == 0:
                            increment = ltv_curve[0] if len(ltv_curve) > 0 else 0
                        else:
                            increment = ltv_curve[days_since_install] - ltv_curve[days_since_install - 1] if days_since_install < len(ltv_curve) else 0
                        
                        daily_rev = installs * increment
                        
                        # Split between IAA and IAP based on LTV breakdown
                        iaa_ratio = ltv_iaa_mean / ltv_mean if ltv_mean > 0 else 0.5
                        daily_revenue_iaa[revenue_day_idx] += daily_rev * iaa_ratio
                        daily_revenue_iap[revenue_day_idx] += daily_rev * (1 - iaa_ratio)
                
                # Calculate cumulative values
                for i in range(projection_days):
                    cumulative_spend[i] = sum(daily_spend_proj[:i+1])
                    cumulative_revenue[i] = sum(daily_revenue_iaa[:i+1]) + sum(daily_revenue_iap[:i+1])
                
                # Calculate daily and cumulative profit
                daily_profit = [daily_revenue_iaa[i] + daily_revenue_iap[i] - daily_spend_proj[i] for i in range(projection_days)]
                cumulative_profit = [cumulative_revenue[i] - cumulative_spend[i] for i in range(projection_days)]
                
                # Find break-even day
                breakeven_day = None
                for i, profit in enumerate(cumulative_profit):
                    if profit >= 0 and cumulative_spend[i] > 0:
                        breakeven_day = i
                        break
                
                # Create projection dates
                projection_dates = [spend_start_date + timedelta(days=d) for d in range(projection_days)]
                
                # Summary Metrics
                total_revenue_projected = cumulative_revenue[-1] if cumulative_revenue else 0
                total_profit_projected = cumulative_profit[-1] if cumulative_profit else 0
                final_roas = (total_revenue_projected / total_spend * 100) if total_spend > 0 else 0
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("💰 Tổng Chi tiêu", f"${total_spend:,.0f}")
                with metric_col2:
                    st.metric("📈 Doanh thu Dự kiến", f"${total_revenue_projected:,.0f}")
                with metric_col3:
                    profit_color = "🟢" if total_profit_projected > 0 else "🔴"
                    st.metric(f"{profit_color} Lợi nhuận", f"${total_profit_projected:,.0f}")
                with metric_col4:
                    if breakeven_day is not None:
                        st.metric("📍 Break-even", f"Ngày {breakeven_day + 1}")
                    else:
                        st.metric("📍 Break-even", "Chưa đạt", help="Chưa đạt điểm hòa vốn trong kỳ")
                
                # Chart 1: Daily Revenue (Stacked Bar)
                st.markdown("#### 📊 Doanh thu theo Ngày")
                
                fig_daily_rev = go.Figure()
                fig_daily_rev.add_trace(go.Bar(
                    x=projection_dates, y=daily_revenue_iaa,
                    name='IAA (Ads)', marker_color='rgba(102, 126, 234, 0.8)'
                ))
                fig_daily_rev.add_trace(go.Bar(
                    x=projection_dates, y=daily_revenue_iap,
                    name='IAP (Subscription)', marker_color='rgba(118, 75, 162, 0.8)'
                ))
                fig_daily_rev.add_trace(go.Scatter(
                    x=projection_dates, y=daily_spend_proj,
                    name='Daily Spend', mode='lines',
                    line=dict(color='rgba(239, 68, 68, 0.8)', width=2, dash='dot')
                ))
                
                fig_daily_rev.update_layout(
                    barmode='stack',
                    title=f"Doanh thu & Chi tiêu theo Ngày ({projection_days} ngày)",
                    xaxis_title="Ngày", yaxis_title="$ USD",
                    height=300, margin=dict(t=35, b=30, l=50, r=20),
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_daily_rev, use_container_width=True)
                
                # Chart 2: Cumulative Profit/Loss
                st.markdown("#### 📈 Lợi nhuận Tích lũy")
                
                fig_profit = go.Figure()
                
                # Color based on profit/loss
                colors = ['rgba(34, 197, 94, 0.7)' if p >= 0 else 'rgba(239, 68, 68, 0.7)' for p in cumulative_profit]
                
                fig_profit.add_trace(go.Scatter(
                    x=projection_dates, y=cumulative_profit,
                    mode='lines', name='Cumulative Profit',
                    line=dict(color='#22c55e', width=3),
                    fill='tozeroy', 
                    fillcolor='rgba(34, 197, 94, 0.15)'
                ))
                
                # Add cumulative revenue and spend lines
                fig_profit.add_trace(go.Scatter(
                    x=projection_dates, y=cumulative_revenue,
                    mode='lines', name='Cumulative Revenue',
                    line=dict(color='#667eea', width=2, dash='dash')
                ))
                fig_profit.add_trace(go.Scatter(
                    x=projection_dates, y=cumulative_spend,
                    mode='lines', name='Cumulative Spend',
                    line=dict(color='#ef4444', width=2, dash='dot')
                ))
                
                # Break-even line
                fig_profit.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1)
                
                # Mark break-even point with a vertical line using shapes
                if breakeven_day is not None and breakeven_day < len(projection_dates):
                    breakeven_date = projection_dates[breakeven_day]
                    breakeven_profit = cumulative_profit[breakeven_day]
                    
                    # Add break-even marker as a point
                    fig_profit.add_trace(go.Scatter(
                        x=[breakeven_date], y=[breakeven_profit],
                        mode='markers+text',
                        name='Break-even',
                        marker=dict(size=12, color='green', symbol='star'),
                        text=[f'Break-even D{breakeven_day+1}'],
                        textposition='top center',
                        showlegend=False
                    ))
                
                fig_profit.update_layout(
                    title=f"Lợi nhuận Tích lũy - ROAS dự kiến: {final_roas:.1f}%",
                    xaxis_title="Ngày", yaxis_title="$ USD",
                    height=350, margin=dict(t=35, b=30, l=50, r=20),
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_profit, use_container_width=True)
                
                # ROI Summary Table
                st.markdown("#### 📋 Tổng kết ROI theo Mốc thời gian")
                
                milestones_roi = [7, 14, 30, 60, 90] if projection_days >= 90 else [7, 14, 30]
                roi_data = []
                
                for milestone in milestones_roi:
                    if milestone < projection_days:
                        spend_at = cumulative_spend[milestone]
                        rev_at = cumulative_revenue[milestone]
                        profit_at = cumulative_profit[milestone]
                        roas_at = (rev_at / spend_at * 100) if spend_at > 0 else 0
                        
                        roi_data.append({
                            "Mốc": f"D{milestone}",
                            "Spend ($)": f"${spend_at:,.0f}",
                            "Revenue ($)": f"${rev_at:,.0f}",
                            "Profit ($)": f"${profit_at:,.0f}",
                            "ROAS (%)": f"{roas_at:.1f}%"
                        })
                
                if roi_data:
                    st.dataframe(pd.DataFrame(roi_data), use_container_width=True, hide_index=True)
        elif not spend_plan.get('enabled', False):
            st.info("💡 Bật **Spend Planning** ở tab '💰 Spend Plan' để xem dự báo doanh thu và lợi nhuận theo ngày.")


if __name__ == "__main__":
    # For testing
    import streamlit as st
    st.set_page_config(page_title="Simulation Test", layout="wide")
    render_enhanced_simulation()
