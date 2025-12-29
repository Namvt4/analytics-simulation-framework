"""
Analytics Business Framework - Streamlit Web Dashboard
Main entry point for the 5-step Data Flywheel visualization

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from data.sample_data import get_sample_data
from modules.simulation import EnhancedMonteCarloSimulator as MonteCarloSimulator, TargetKPIGenerator
from modules.prediction import PLTVPredictor, ChurnPredictor
from modules.monitoring import AlertManager, HealthScoreCalculator, PacingTracker
from modules.analysis import DrilldownAnalyzer, FunnelAnalyzer, CohortAnalyzer
from modules.action import AutomatedRules, ActionRecommender, PersonalizedOffer
from pages.simulation_page import render_enhanced_simulation
from components.charts import (
    create_roas_distribution_chart,
    create_retention_curve_chart,
    create_revenue_breakdown_chart,
    create_funnel_chart,
    create_campaign_performance_chart,
    create_health_score_gauge,
    create_pacing_chart
)

# Page config
st.set_page_config(
    page_title="Analytics Business Framework",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #667eea;
    }
    .vn-note {
        background-color: #f0f8ff;
        border-left: 4px solid #667eea;
        padding: 10px 15px;
        margin: 10px 0;
        border-radius: 0 5px 5px 0;
        font-size: 0.9em;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'sample_data' not in st.session_state:
    st.session_state.sample_data = get_sample_data()

if 'simulation_run' not in st.session_state:
    st.session_state.simulation_run = False


def main():
    """Main dashboard function"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📊 Analytics Business Framework")
        st.markdown("*Khung phân tích nghiệp vụ*")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Điều hướng",
            ["🏠 Tổng quan", 
             "1️⃣ Mô phỏng",
             "2️⃣ Dự báo", 
             "3️⃣ Giám sát",
             "4️⃣ Phân tích",
             "5️⃣ Hành động"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Data source info
        st.markdown("### 📡 Nguồn dữ liệu")
        st.info("Đang dùng dữ liệu mẫu.\nKết nối BigQuery để có dữ liệu thực.")
        
        # Last update
        st.markdown(f"**Cập nhật:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Main content based on selected page
    if page == "🏠 Tổng quan":
        render_overview()
    elif page == "1️⃣ Mô phỏng":
        render_enhanced_simulation()
    elif page == "2️⃣ Dự báo":
        render_prediction()
    elif page == "3️⃣ Giám sát":
        render_monitoring()
    elif page == "4️⃣ Phân tích":
        render_analysis()
    elif page == "5️⃣ Hành động":
        render_action()


def render_overview():
    """Render overview dashboard"""
    st.markdown('<h1 class="main-header">Analytics Business Framework</h1>', unsafe_allow_html=True)
    st.markdown("### Vòng lặp Dữ liệu: Từ Giả lập đến Khuyến nghị Hành động")
    
    st.markdown("""
    <div class="vn-note">
    💡 <strong>Giới thiệu:</strong> Dashboard này triển khai quy trình 5 bước để phân tích và tối ưu hóa 
    ứng dụng di động: Mô phỏng → Dự báo → Giám sát → Phân tích → Hành động.
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Cards
    sample_data = st.session_state.sample_data
    daily_metrics = sample_data.get_daily_metrics(90)
    latest = daily_metrics.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📈 DAU (Người dùng hàng ngày)",
            value=f"{int(latest['dau']):,}",
            delta=f"{np.random.uniform(-5, 10):.1f}%",
            help="Daily Active Users - Số người dùng hoạt động mỗi ngày"
        )
    
    with col2:
        st.metric(
            label="💰 Doanh thu",
            value=f"${latest['total_revenue']:,.0f}",
            delta=f"{np.random.uniform(-3, 8):.1f}%",
            help="Tổng doanh thu từ quảng cáo (IAA) và mua hàng trong ứng dụng (IAP)"
        )
    
    with col3:
        st.metric(
            label="📊 ROAS",
            value=f"{latest['roas'] * 100:.1f}%",
            delta=f"{np.random.uniform(-2, 5):.1f}%",
            help="Return On Ad Spend - Tỷ suất hoàn vốn quảng cáo. ROAS > 100% = có lãi"
        )
    
    with col4:
        # Quick health calculation
        health_calc = HealthScoreCalculator()
        health = health_calc.calculate_health_score({
            'roas': latest['roas'],
            'd7_retention': 0.18,
            'revenue_growth_pct': 5,
            'ltv': 0.8,
            'cpi': CONFIG.ua.cpi_paid,
            'organic_rate': 0.3
        })
        st.metric(
            label=f"{health['status_emoji']} Điểm sức khỏe",
            value=f"{health['total_score']:.0f}/100",
            delta=health['status'],
            help="Chỉ số tổng hợp đánh giá tình trạng kinh doanh tổng thể"
        )
    
    st.markdown("---")
    
    # Two column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Xu hướng Doanh thu (90 ngày qua)")
        st.caption("*Biểu đồ thể hiện doanh thu hàng ngày từ quảng cáo (IAA) và mua hàng (IAP)*")
        fig = create_revenue_breakdown_chart(daily_metrics)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Đường cong Retention")
        st.caption("*Tỷ lệ % người dùng còn hoạt động sau N ngày cài đặt*")
        retention_data = sample_data.get_cohort_retention()
        fig = create_retention_curve_chart(retention_data)
        st.plotly_chart(fig, use_container_width=True)
    
    # Framework explanation
    st.markdown("---")
    st.markdown("### 🔄 Quy trình 5 Bước (Data Flywheel)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
        #### 1️⃣ Mô phỏng
        Giả lập Monte Carlo các kịch bản "What-if"
        
        *Ví dụ: Nếu tăng ngân sách 20% thì sao?*
        """)
    
    with col2:
        st.markdown("""
        #### 2️⃣ Dự báo
        Dự đoán pLTV, Churn, Gian lận
        
        *Ví dụ: User này có LTV bao nhiêu?*
        """)
    
    with col3:
        st.markdown("""
        #### 3️⃣ Giám sát
        Cảnh báo & Điểm sức khỏe thời gian thực
        
        *Ví dụ: Chỉ số có đúng hướng không?*
        """)
    
    with col4:
        st.markdown("""
        #### 4️⃣ Phân tích
        Tìm nguyên nhân gốc rễ (RCA)
        
        *Ví dụ: Tại sao doanh thu giảm?*
        """)
    
    with col5:
        st.markdown("""
        #### 5️⃣ Hành động
        Tự động & Khuyến nghị
        
        *Ví dụ: Nên làm gì bây giờ?*
        """)


def render_simulation():
    """Render Step 1: Simulation page"""
    st.markdown('<h2 class="step-header">1️⃣ Mô phỏng - Monte Carlo & What-if</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="vn-note">
    🎯 <strong>Mục tiêu:</strong> Trả lời câu hỏi "Nếu chúng ta thay đổi X, kết quả sẽ ra sao?"<br>
    📊 <strong>Phương pháp:</strong> Chạy 1000+ kịch bản giả lập với các biến động của CPI, eCPM, Retention...<br>
    📈 <strong>Kết quả:</strong> Phân phối xác suất ROAS và các ngưỡng mục tiêu (An toàn, Kỳ vọng, Bứt phá)
    </div>
    """, unsafe_allow_html=True)
    
    # Simulation parameters
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ Tham số")
        n_simulations = st.slider(
            "Số lượng kịch bản giả lập", 
            100, 5000, 1000, 100,
            help="Càng nhiều kịch bản, kết quả càng chính xác nhưng chạy lâu hơn"
        )
        sim_days = st.selectbox(
            "Thời gian dự báo", 
            [30, 90, 180, 365], 
            index=3,
            format_func=lambda x: f"{x} ngày"
        )
        
        if st.button("🎲 Chạy Mô phỏng", type="primary"):
            with st.spinner("Đang chạy giả lập Monte Carlo..."):
                simulator = MonteCarloSimulator(n_simulations=n_simulations)
                results = simulator.run(days=sim_days)
                st.session_state.simulation_results = results
                st.session_state.simulation_raw = simulator.results
                st.session_state.simulation_run = True
    
    with col2:
        if st.session_state.simulation_run and 'simulation_results' in st.session_state:
            results = st.session_state.simulation_results
            
            st.markdown("### 📊 Kết quả Mô phỏng")
            
            # Key metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric(
                    "ROAS Trung bình", 
                    f"{results['roas']['mean'] * 100:.1f}%",
                    help="Giá trị trung bình của ROAS qua tất cả các kịch bản"
                )
            with col_b:
                st.metric(
                    "Xác suất Có lãi", 
                    f"{results['risk']['probability_profitable'] * 100:.1f}%",
                    help="% kịch bản có ROAS >= 100%"
                )
            with col_c:
                st.metric(
                    "Khoảng tin cậy 90%", 
                    f"[{results['roas']['p5']*100:.0f}%, {results['roas']['p95']*100:.0f}%]",
                    help="90% kịch bản sẽ rơi vào khoảng này"
                )
    
    # Distribution chart
    if st.session_state.simulation_run and 'simulation_raw' in st.session_state:
        st.markdown("### 📈 Phân phối ROAS")
        st.caption("*Biểu đồ phân phối xác suất ROAS. Đường đỏ = Điểm hòa vốn (100%)*")
        fig = create_roas_distribution_chart(st.session_state.simulation_raw)
        st.plotly_chart(fig, use_container_width=True)
        
        # Target KPIs
        st.markdown("### 🎯 Ngưỡng KPI Mục tiêu")
        st.caption("*Dựa trên phân phối xác suất để xác định các mức kỳ vọng*")
        
        generator = TargetKPIGenerator()
        simulator = MonteCarloSimulator(n_simulations=n_simulations)
        simulator.results = st.session_state.simulation_raw
        generator.simulator = simulator
        targets = generator.generate_targets()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**🛡️ Ngưỡng An toàn (25%):** {targets['roas']['safe']*100:.1f}% ROAS\n\n*Xác suất 75% đạt được*")
        with col2:
            st.success(f"**📊 Ngưỡng Kỳ vọng (50%):** {targets['roas']['expected']*100:.1f}% ROAS\n\n*Xác suất 50% đạt được*")
        with col3:
            st.warning(f"**🚀 Ngưỡng Bứt phá (75%):** {targets['roas']['breakthrough']*100:.1f}% ROAS\n\n*Xác suất 25% đạt được*")


def render_prediction():
    """Render Step 2: Prediction page"""
    st.markdown('<h2 class="step-header">2️⃣ Dự báo - pLTV & Churn</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="vn-note">
    🎯 <strong>Mục tiêu:</strong> Trả lời "User này có khả năng nạp tiền không? LTV sau 365 ngày là bao nhiêu?"<br>
    📊 <strong>Mô hình:</strong> pLTV (Predicted Lifetime Value), Churn Prediction, Fraud Detection<br>
    📈 <strong>Ứng dụng:</strong> Phân loại user để cá nhân hóa trải nghiệm và tối ưu marketing
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 Dự báo LTV", "⚠️ Dự báo Rời bỏ"])
    
    with tab1:
        st.markdown("### Giá trị Trọn đời Dự kiến (pLTV)")
        st.caption("*Dự báo tổng doanh thu mà một user sẽ tạo ra trong suốt vòng đời sử dụng app*")
        
        predictor = PLTVPredictor()
        ltv_result = predictor.predict_ltv(days=365)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Tổng pLTV (365 ngày)", 
                f"${ltv_result['ltv_total']:.4f}",
                help="Giá trị trọn đời dự kiến sau 1 năm"
            )
        with col2:
            st.metric(
                "Doanh thu Quảng cáo (IAA)", 
                f"${ltv_result['ltv_iaa']:.4f}",
                help="In-App Advertising - Doanh thu từ quảng cáo hiển thị"
            )
        with col3:
            st.metric(
                "Doanh thu Mua hàng (IAP)", 
                f"${ltv_result['ltv_iap']:.4f}",
                help="In-App Purchase - Doanh thu từ mua subscription/item"
            )
        
        # LTV curve
        st.markdown("#### 📈 Đường cong LTV tích lũy")
        st.caption("*LTV tăng dần theo thời gian khi user tiếp tục sử dụng app*")
        breakdown = pd.DataFrame(ltv_result['daily_breakdown'])
        st.line_chart(breakdown.set_index('day')['ltv_total_cumulative'])
    
    with tab2:
        st.markdown("### Phân tích Rủi ro Rời bỏ (Churn)")
        st.caption("*Nhận diện user có dấu hiệu sắp ngừng sử dụng app trong 48h tới*")
        
        sample_data = st.session_state.sample_data
        users = sample_data.get_user_segments(100)
        
        predictor = ChurnPredictor()
        
        # Add mock features for churn prediction
        users['days_inactive'] = np.random.randint(0, 14, len(users))
        users['session_decline_pct'] = np.random.uniform(0, 60, len(users))
        users['engagement_decline_pct'] = np.random.uniform(0, 50, len(users))
        users['pltv'] = users['ltv_predicted']
        users['has_purchased'] = np.random.choice([True, False], len(users), p=[0.15, 0.85])
        
        churn_results = predictor.predict_churn_batch(users)
        
        # Summary
        high_risk = len(churn_results[churn_results['risk_level'] == 'High'])
        st.warning(f"⚠️ **{high_risk} người dùng** có NGUY CƠ CAO rời bỏ app")
        
        st.markdown("#### Danh sách User Cần Can thiệp")
        st.caption("*Những user này nên được gửi khuyến mãi hoặc thông báo giữ chân*")
        
        # Show high risk users
        display_df = churn_results[churn_results['risk_level'] == 'High'][['user_id', 'churn_probability', 'recommended_action']].head(10)
        display_df.columns = ['ID Người dùng', 'Xác suất rời bỏ', 'Hành động khuyến nghị']
        st.dataframe(display_df, use_container_width=True)


def render_monitoring():
    """Render Step 3: Monitoring page"""
    st.markdown('<h2 class="step-header">3️⃣ Giám sát - Cảnh báo & Sức khỏe</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="vn-note">
    🎯 <strong>Mục tiêu:</strong> Trả lời "Chỉ số hiện tại có đang đi đúng hướng không?"<br>
    📊 <strong>Chức năng:</strong> Cảnh báo real-time, Điểm sức khỏe tổng hợp, Theo dõi tiến độ<br>
    📈 <strong>Lợi ích:</strong> Phát hiện vấn đề sớm trước khi ảnh hưởng lớn đến kinh doanh
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🚨 Cảnh báo", "💪 Điểm Sức khỏe", "📈 Tiến độ Mục tiêu"])
    
    with tab1:
        st.markdown("### Cảnh báo Đang hoạt động")
        st.caption("*Hệ thống tự động phát hiện khi các chỉ số quan trọng giảm dưới ngưỡng*")
        
        alert_manager = AlertManager()
        
        # Simulate current vs baseline
        current = {'roas': 0.85, 'revenue': 4200, 'dau': 48000}
        baseline = {'roas': 1.0, 'revenue': 5000, 'dau': 50000}
        
        alerts = alert_manager.run_all_checks(current, baseline)
        
        if alerts:
            for alert in alerts:
                if alert.level.value == 'critical':
                    st.error(alert.message)
                elif alert.level.value == 'danger':
                    st.warning(alert.message)
                else:
                    st.info(alert.message)
        else:
            st.success("✅ Tất cả chỉ số đều trong ngưỡng bình thường!")
    
    with tab2:
        st.markdown("### Điểm Sức khỏe Kinh doanh")
        st.caption("*Chỉ số tổng hợp đánh giá tình trạng kinh doanh từ 0-100*")
        
        health_calc = HealthScoreCalculator()
        
        # Input metrics
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Điều chỉnh thông số:**")
            roas = st.slider(
                "ROAS hiện tại", 0.0, 2.0, 1.1, 0.05,
                help="Tỷ suất hoàn vốn quảng cáo"
            )
            d7_ret = st.slider(
                "Retention D7", 0.0, 0.5, 0.18, 0.01,
                help="Tỷ lệ người dùng còn hoạt động sau 7 ngày"
            )
            revenue_growth = st.slider(
                "Tăng trưởng Doanh thu %", -30.0, 30.0, 5.0, 1.0,
                help="Tăng trưởng so với tuần trước"
            )
        
        with col2:
            health = health_calc.calculate_health_score({
                'roas': roas,
                'd7_retention': d7_ret,
                'revenue_growth_pct': revenue_growth,
                'ltv': 0.8,
                'cpi': CONFIG.ua.cpi_paid,
                'organic_rate': 0.3
            })
            
            fig = create_health_score_gauge(health['total_score'], health['status'])
            st.plotly_chart(fig, use_container_width=True)
            
            # Status interpretation
            if health['total_score'] >= 80:
                st.success("🟢 **Tuyệt vời!** Kinh doanh đang rất tốt.")
            elif health['total_score'] >= 60:
                st.info("🟡 **Khá ổn.** Có thể cải thiện thêm một số chỉ số.")
            elif health['total_score'] >= 40:
                st.warning("🟠 **Cần chú ý.** Một số chỉ số đang dưới mức mong đợi.")
            else:
                st.error("🔴 **Cần hành động ngay!** Nhiều chỉ số đang ở mức báo động.")
    
    with tab3:
        st.markdown("### Theo dõi Tiến độ Mục tiêu (Pacing)")
        st.caption("*So sánh thực tế với kế hoạch để biết có đạt mục tiêu tháng không*")
        
        pacing = PacingTracker()
        
        # Simulate monthly pacing
        result = pacing.calculate_pacing(
            current_value=75000,
            target_value=150000,
            elapsed_days=15,
            total_days=30
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Tiến độ Hiện tại", 
                f"{result['value_achieved_pct']:.1f}%",
                help="% mục tiêu đã đạt được"
            )
            st.metric(
                "Dự báo Cuối kỳ", 
                f"${result['projected_value']:,.0f}",
                help="Nếu tiếp tục đà này, cuối tháng sẽ đạt bao nhiêu"
            )
        with col2:
            st.metric(
                "Số ngày còn lại", 
                result['days_remaining'],
                help="Thời gian còn lại để đạt mục tiêu"
            )
            st.metric(
                "Cần mỗi ngày", 
                f"${result['required_daily']:,.0f}",
                help="Doanh thu cần đạt mỗi ngày từ giờ để hoàn thành mục tiêu"
            )
        
        st.progress(result['value_achieved_pct'] / 100)
        st.markdown(f"**Trạng thái:** {result['status_emoji']} {result['status']}")


def render_analysis():
    """Render Step 4: Analysis page"""
    st.markdown('<h2 class="step-header">4️⃣ Phân tích - Tìm Nguyên nhân</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="vn-note">
    🎯 <strong>Mục tiêu:</strong> Trả lời "Tại sao doanh thu giảm? Do ARPU giảm hay Retention đi xuống?"<br>
    📊 <strong>Phương pháp:</strong> Drill-down theo nhiều chiều (Quốc gia, Nguồn, Phiên bản...), Phân tích Funnel, So sánh Cohort<br>
    📈 <strong>Kết quả:</strong> Xác định chính xác vấn đề nằm ở đâu để đưa ra giải pháp đúng
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🎯 Phân tích Funnel", "📊 Drill-down Chiến dịch", "👥 Phân tích Cohort"])
    
    with tab1:
        st.markdown("### Phễu Chuyển đổi Người dùng")
        st.caption("*Xem user rơi rụng ở bước nào trong hành trình sử dụng app*")
        
        sample_data = st.session_state.sample_data
        funnel_data = sample_data.get_funnel_data()
        
        analyzer = FunnelAnalyzer()
        analysis = analyzer.analyze_funnel(funnel_data)
        
        # Funnel chart
        fig = create_funnel_chart(funnel_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Biggest drop-off
        biggest_drop = analyzer.find_biggest_dropoff(funnel_data)
        if biggest_drop:
            st.error(f"""
            **🔴 Điểm rơi lớn nhất:** {biggest_drop['step_name']}
            - Tỷ lệ rơi: **{biggest_drop['drop_off_rate']}%**
            - Số user mất: **{biggest_drop['users_lost']:,}** người
            - 💡 **Khuyến nghị:** Cần ưu tiên cải thiện trải nghiệm ở bước này
            """)
    
    with tab2:
        st.markdown("### Hiệu quả Chiến dịch Quảng cáo")
        st.caption("*So sánh ROAS và Chi tiêu của các chiến dịch từ nhiều nguồn*")
        
        campaigns = sample_data.get_campaign_performance(20)
        
        # Campaign chart
        fig = create_campaign_performance_chart(campaigns)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Bảng Chi tiết Chiến dịch")
        # Performance table
        display_df = campaigns[['campaign_name', 'media_source', 'country', 'spend', 'roas_d7']].head(10)
        display_df.columns = ['Tên Chiến dịch', 'Nguồn', 'Quốc gia', 'Chi tiêu ($)', 'ROAS D7']
        st.dataframe(display_df, use_container_width=True)
    
    with tab3:
        st.markdown("### Phân tích Retention theo Cohort")
        st.caption("*So sánh tỷ lệ giữ chân user giữa các nhóm cài đặt khác nhau*")
        
        retention_data = sample_data.get_cohort_retention()
        
        retention_wide = retention_data.pivot_table(
            index='cohort_size',
            columns='days_since_install',
            values='retention_rate',
            aggfunc='mean'
        )[[0, 1, 3, 7, 14, 30, 60, 90]]
        
        retention_wide.columns = ['D0', 'D1', 'D3', 'D7', 'D14', 'D30', 'D60', 'D90']
        
        st.dataframe(retention_wide.style.format("{:.2%}"), use_container_width=True)
        
        st.info("""
        💡 **Cách đọc bảng:**
        - D0 = Ngày cài đặt (luôn 100%)
        - D7 = % user còn hoạt động sau 7 ngày
        - Nếu D7 > 20% là tốt, < 15% cần cải thiện onboarding
        """)


def render_action():
    """Render Step 5: Action page"""
    st.markdown('<h2 class="step-header">5️⃣ Hành động - Khuyến nghị & Tự động</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="vn-note">
    🎯 <strong>Mục tiêu:</strong> Trả lời "Chúng ta nên làm gì ngay bây giờ?"<br>
    📊 <strong>Cơ chế:</strong> Luật tự động (nếu X thì làm Y), Khuyến nghị chiến lược, Offer cá nhân hóa<br>
    📈 <strong>Giá trị:</strong> Chuyển hóa insight thành hành động cụ thể để tăng doanh thu
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🤖 Luật Tự động", "📋 Khuyến nghị Chiến lược", "🎁 Offer Cá nhân hóa"])
    
    with tab1:
        st.markdown("### Hệ thống Luật Tự động")
        st.caption("*Tự động thực hiện hành động khi điều kiện được đáp ứng*")
        
        st.info("""
        **Ví dụ các luật:**
        - Nếu ROAS chiến dịch < 80% → Tự động tạm dừng chiến dịch
        - Nếu ROAS chiến dịch > 150% → Tự động tăng ngân sách
        - Nếu User có churn risk cao + LTV cao → Gửi khuyến mãi giữ chân
        """)
        
        rules_engine = AutomatedRules()
        
        sample_data = st.session_state.sample_data
        campaigns = sample_data.get_campaign_performance(20)
        
        # Add roas column if not exists
        if 'roas' not in campaigns.columns and 'roas_d7' in campaigns.columns:
            campaigns['roas'] = campaigns['roas_d7']
        
        actions = rules_engine.evaluate_campaigns(campaigns)
        
        if not actions.empty:
            st.warning(f"⚡ **{len(actions)} hành động tự động** được kích hoạt")
            
            display_df = actions.copy()
            display_df.columns = ['ID Chiến dịch', 'Tên Chiến dịch', 'ROAS Hiện tại', 'Hành động', 'Độ ưu tiên', 'Luật']
            st.dataframe(display_df, use_container_width=True)
        else:
            st.success("✅ Không có hành động tự động nào cần thực hiện")
    
    with tab2:
        st.markdown("### Khuyến nghị Chiến lược")
        st.caption("*Đề xuất hành động dựa trên phân tích tình hình hiện tại*")
        
        recommender = ActionRecommender()
        
        # Generate recommendations from alerts
        sample_alerts = [
            {'level': 'warning', 'metric': 'ROAS'},
            {'level': 'danger', 'metric': 'Retention'}
        ]
        
        actions = recommender.recommend_from_alerts(sample_alerts)
        
        for action in actions:
            priority_color = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(action.priority.name, '⚪')
            
            priority_vn = {
                'CRITICAL': 'KHẨN CẤP',
                'HIGH': 'CAO',
                'MEDIUM': 'TRUNG BÌNH',
                'LOW': 'THẤP'
            }.get(action.priority.name, '')
            
            st.markdown(f"""
            **{priority_color} [{priority_vn}] {action.title}**
            
            {action.description}
            
            - 📊 **Mức độ ảnh hưởng:** {action.impact_estimate}
            - ⏱️ **Công sức thực hiện:** {action.effort_estimate}
            - 🏷️ **Danh mục:** {action.category.value}
            
            ---
            """)
    
    with tab3:
        st.markdown("### Offer Cá nhân hóa cho Người dùng")
        st.caption("*Tự động tạo khuyến mãi phù hợp với từng nhóm user*")
        
        offer_gen = PersonalizedOffer()
        
        sample_data = st.session_state.sample_data
        users = sample_data.get_user_segments(50)
        
        # Add required columns
        users['churn_probability'] = np.random.uniform(0, 1, len(users))
        users['pltv'] = users['ltv_predicted']
        
        # Filter to high-value at-risk users
        high_value_risk = users[
            (users['churn_probability'] > 0.6) & 
            (users['pltv'] > 2.0)
        ]
        
        if len(high_value_risk) > 0:
            offers = offer_gen.generate_offers_batch(high_value_risk)
            st.info(f"🎁 Đã tạo **{len(offers)} offer cá nhân hóa** cho user có giá trị cao đang có rủi ro rời bỏ")
            
            display_df = offers[['user_id', 'title', 'discount_pct', 'valid_days']].copy()
            display_df.columns = ['ID User', 'Tiêu đề Offer', 'Giảm giá %', 'Thời hạn (ngày)']
            st.dataframe(display_df, use_container_width=True)
            
            st.success("""
            💡 **Lợi ích:**
            - Giữ chân user có giá trị cao
            - Tối ưu chi phí marketing (chỉ gửi offer cho đúng đối tượng)
            - Tăng doanh thu bằng cách giảm churn rate
            """)
        else:
            st.success("✅ Không có user nào cần offer ưu tiên cao lúc này")


if __name__ == "__main__":
    main()
