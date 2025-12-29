"""
Analytics Business Framework - Chart Components
Reusable chart components for the Streamlit dashboard
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def create_roas_distribution_chart(simulation_results: List[Dict]) -> go.Figure:
    """
    Create ROAS distribution histogram from Monte Carlo results
    
    Args:
        simulation_results: List of simulation result dictionaries
        
    Returns:
        Plotly figure
    """
    roas_values = [r['roas'] * 100 for r in simulation_results]
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=roas_values,
        nbinsx=50,
        name='ROAS Distribution',
        marker_color='#667eea',
        opacity=0.75
    ))
    
    # Add vertical line for breakeven (100%)
    fig.add_vline(x=100, line_dash="dash", line_color="red",
                  annotation_text="Breakeven", annotation_position="top")
    
    # Add mean line
    mean_roas = np.mean(roas_values)
    fig.add_vline(x=mean_roas, line_dash="dot", line_color="green",
                  annotation_text=f"Mean: {mean_roas:.1f}%", annotation_position="top left")
    
    fig.update_layout(
        title="ROAS Distribution (Monte Carlo Simulation)",
        xaxis_title="ROAS (%)",
        yaxis_title="Frequency",
        template="plotly_white",
        showlegend=False
    )
    
    return fig


def create_retention_curve_chart(retention_data: pd.DataFrame) -> go.Figure:
    """
    Create retention curve chart
    
    Args:
        retention_data: DataFrame with days_since_install and retention_rate
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=retention_data['days_since_install'],
        y=retention_data['retention_rate'] * 100,
        mode='lines+markers',
        name='Retention Rate',
        line=dict(color='#667eea', width=2),
        marker=dict(size=4)
    ))
    
    # Add key milestone markers
    key_days = [1, 7, 30, 90]
    for day in key_days:
        if day in retention_data['days_since_install'].values:
            rate = retention_data.loc[retention_data['days_since_install'] == day, 'retention_rate'].values[0] * 100
            fig.add_annotation(
                x=day,
                y=rate,
                text=f"D{day}: {rate:.1f}%",
                showarrow=True,
                arrowhead=2
            )
    
    fig.update_layout(
        title="User Retention Curve",
        xaxis_title="Days Since Install",
        yaxis_title="Retention Rate (%)",
        template="plotly_white",
        yaxis=dict(range=[0, 100])
    )
    
    return fig


def create_revenue_breakdown_chart(daily_data: pd.DataFrame) -> go.Figure:
    """
    Create stacked area chart for revenue breakdown
    
    Args:
        daily_data: DataFrame with date, iaa_revenue, iap_revenue
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_data['date'],
        y=daily_data['iaa_revenue'],
        mode='lines',
        name='Ad Revenue (IAA)',
        stackgroup='revenue',
        fillcolor='rgba(102, 126, 234, 0.6)',
        line=dict(color='#667eea')
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_data['date'],
        y=daily_data['iap_revenue'],
        mode='lines',
        name='In-App Purchases (IAP)',
        stackgroup='revenue',
        fillcolor='rgba(118, 75, 162, 0.6)',
        line=dict(color='#764ba2')
    ))
    
    fig.update_layout(
        title="Revenue Breakdown Over Time",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        template="plotly_white",
        hovermode='x unified'
    )
    
    return fig


def create_funnel_chart(funnel_data: pd.DataFrame) -> go.Figure:
    """
    Create funnel chart for conversion analysis
    
    Args:
        funnel_data: DataFrame with step_name and users
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(go.Funnel(
        y=funnel_data['step_name'],
        x=funnel_data['users'],
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(
            color=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
        ),
        connector=dict(line=dict(color="royalblue", dash="dot", width=3))
    ))
    
    fig.update_layout(
        title="User Conversion Funnel",
        template="plotly_white"
    )
    
    return fig


def create_campaign_performance_chart(campaign_data: pd.DataFrame) -> go.Figure:
    """
    Create scatter plot of campaign performance (ROAS vs Spend)
    
    Args:
        campaign_data: DataFrame with spend, roas_d7, media_source
        
    Returns:
        Plotly figure
    """
    roas_col = 'roas_d7' if 'roas_d7' in campaign_data.columns else 'roas'
    
    fig = px.scatter(
        campaign_data,
        x='spend',
        y=campaign_data[roas_col] * 100,
        color='media_source',
        size='installs',
        hover_name='campaign_name' if 'campaign_name' in campaign_data.columns else None,
        title="Campaign Performance: ROAS vs Spend"
    )
    
    # Add breakeven line
    fig.add_hline(y=100, line_dash="dash", line_color="red",
                  annotation_text="Breakeven")
    
    fig.update_layout(
        xaxis_title="Spend ($)",
        yaxis_title="ROAS (%)",
        template="plotly_white"
    )
    
    return fig


def create_health_score_gauge(score: float, status: str) -> go.Figure:
    """
    Create gauge chart for health score
    
    Args:
        score: Health score (0-100)
        status: Status text (Excellent, Good, Fair, Poor)
        
    Returns:
        Plotly figure
    """
    # Color based on score
    if score >= 80:
        bar_color = "#00cc66"
    elif score >= 60:
        bar_color = "#ffcc00"
    elif score >= 40:
        bar_color = "#ff9933"
    else:
        bar_color = "#ff3333"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Health Score: {status}"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': bar_color},
            'steps': [
                {'range': [0, 40], 'color': "#ffebee"},
                {'range': [40, 60], 'color': "#fff3e0"},
                {'range': [60, 80], 'color': "#fffde7"},
                {'range': [80, 100], 'color': "#e8f5e9"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig


def create_pacing_chart(pacing_data: Dict) -> go.Figure:
    """
    Create pacing progress chart
    
    Args:
        pacing_data: Dictionary with pacing metrics
        
    Returns:
        Plotly figure
    """
    current = pacing_data.get('current_value', 0)
    target = pacing_data.get('target_value', 100)
    projected = pacing_data.get('projected_value', 0)
    
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        name='Current',
        x=['Progress'],
        y=[current],
        marker_color='#667eea',
        text=[f"${current:,.0f}"],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Target',
        x=['Progress'],
        y=[target],
        marker_color='#e0e0e0',
        text=[f"${target:,.0f}"],
        textposition='outside'
    ))
    
    # Add projected line
    fig.add_hline(y=projected, line_dash="dash", line_color="green",
                  annotation_text=f"Projected: ${projected:,.0f}")
    
    fig.update_layout(
        title=f"Pacing: {pacing_data.get('status_emoji', '')} {pacing_data.get('status', '')}",
        barmode='overlay',
        template="plotly_white",
        showlegend=True
    )
    
    return fig


def create_cohort_heatmap(cohort_matrix: pd.DataFrame) -> go.Figure:
    """
    Create cohort retention heatmap
    
    Args:
        cohort_matrix: Pivot table with cohorts and retention rates
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=go.Heatmap(
        z=cohort_matrix.values * 100,
        x=cohort_matrix.columns,
        y=cohort_matrix.index,
        colorscale='Blues',
        text=[[f"{v*100:.1f}%" for v in row] for row in cohort_matrix.values],
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Cohort Retention Heatmap",
        xaxis_title="Days Since Install",
        yaxis_title="Cohort",
        template="plotly_white"
    )
    
    return fig


def create_kpi_cards(metrics: Dict) -> List[Dict]:
    """
    Create KPI card data for dashboard
    
    Args:
        metrics: Dictionary with metric values
        
    Returns:
        List of KPI card dictionaries
    """
    cards = []
    
    if 'dau' in metrics:
        cards.append({
            'title': 'DAU',
            'value': f"{metrics['dau']:,}",
            'delta': metrics.get('dau_change_pct', 0),
            'icon': '👥'
        })
    
    if 'revenue' in metrics or 'total_revenue' in metrics:
        rev = metrics.get('revenue', metrics.get('total_revenue', 0))
        cards.append({
            'title': 'Revenue',
            'value': f"${rev:,.2f}",
            'delta': metrics.get('revenue_change_pct', 0),
            'icon': '💰'
        })
    
    if 'roas' in metrics:
        cards.append({
            'title': 'ROAS',
            'value': f"{metrics['roas'] * 100:.1f}%",
            'delta': metrics.get('roas_change_pct', 0),
            'icon': '📈'
        })
    
    if 'ltv' in metrics:
        cards.append({
            'title': 'LTV (365d)',
            'value': f"${metrics['ltv']:.2f}",
            'delta': metrics.get('ltv_change_pct', 0),
            'icon': '💎'
        })
    
    return cards


def create_alert_timeline(alerts: List[Dict]) -> go.Figure:
    """
    Create timeline of alerts
    
    Args:
        alerts: List of alert dictionaries
        
    Returns:
        Plotly figure
    """
    if not alerts:
        return go.Figure()
    
    df = pd.DataFrame(alerts)
    
    # Color mapping for alert levels
    color_map = {
        'info': '#17a2b8',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'critical': '#6f42c1'
    }
    
    fig = go.Figure()
    
    for level in df['level'].unique():
        level_df = df[df['level'] == level]
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(level_df['timestamp']),
            y=[level] * len(level_df),
            mode='markers+text',
            name=level.capitalize(),
            marker=dict(size=12, color=color_map.get(level, '#6c757d')),
            text=level_df['metric'],
            textposition='top center'
        ))
    
    fig.update_layout(
        title="Alert Timeline",
        xaxis_title="Time",
        yaxis_title="Alert Level",
        template="plotly_white",
        showlegend=True
    )
    
    return fig
