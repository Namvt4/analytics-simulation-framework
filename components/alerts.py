"""
Analytics Business Framework - Alert Components
UI components for displaying alerts on the dashboard
"""

import streamlit as st
from typing import Dict, List
from datetime import datetime


def render_alert_badge(level: str, message: str):
    """
    Render an alert badge in Streamlit
    
    Args:
        level: Alert level (info, warning, danger, critical)
        message: Alert message
    """
    colors = {
        'info': '#17a2b8',
        'warning': '#ffc107',
        'danger': '#dc3545', 
        'critical': '#6f42c1'
    }
    
    icons = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'danger': '🔴',
        'critical': '🚨'
    }
    
    color = colors.get(level, '#6c757d')
    icon = icons.get(level, '📢')
    
    st.markdown(f"""
    <div style="
        background-color: {color}20;
        border-left: 4px solid {color};
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 0 5px 5px 0;
    ">
        <span style="font-size: 1.2em;">{icon}</span>
        <strong style="color: {color};">{level.upper()}</strong>: {message}
    </div>
    """, unsafe_allow_html=True)


def render_alert_panel(alerts: List[Dict], max_alerts: int = 5):
    """
    Render a panel of recent alerts
    
    Args:
        alerts: List of alert dictionaries
        max_alerts: Maximum number of alerts to show
    """
    if not alerts:
        st.info("✅ No active alerts")
        return
    
    st.subheader(f"🚨 Active Alerts ({len(alerts)})")
    
    # Sort by timestamp (most recent first)
    sorted_alerts = sorted(
        alerts[:max_alerts],
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    for alert in sorted_alerts:
        render_alert_badge(
            level=alert.get('level', 'info'),
            message=alert.get('message', 'Unknown alert')
        )


def render_kpi_card(title: str, value: str, delta: float = None, icon: str = "📊"):
    """
    Render a KPI metric card
    
    Args:
        title: Card title
        value: Main value to display
        delta: Percentage change (optional)
        icon: Emoji icon
    """
    delta_color = "green" if delta and delta > 0 else "red" if delta and delta < 0 else "gray"
    delta_arrow = "↑" if delta and delta > 0 else "↓" if delta and delta < 0 else ""
    delta_text = f"{delta_arrow} {abs(delta):.1f}%" if delta else ""
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    ">
        <div style="font-size: 2em;">{icon}</div>
        <div style="font-size: 0.9em; opacity: 0.9;">{title}</div>
        <div style="font-size: 1.8em; font-weight: bold;">{value}</div>
        <div style="color: {delta_color}; font-size: 0.9em;">{delta_text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_indicator(status: str, label: str):
    """
    Render a status indicator (green/yellow/red dot)
    
    Args:
        status: Status level (good, warning, danger)
        label: Label text
    """
    colors = {
        'good': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545'
    }
    
    color = colors.get(status, '#6c757d')
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin: 5px 0;">
        <div style="
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: {color};
            margin-right: 10px;
        "></div>
        <span>{label}</span>
    </div>
    """, unsafe_allow_html=True)


def render_action_card(action: Dict):
    """
    Render an action recommendation card
    
    Args:
        action: Action dictionary with title, description, priority, etc.
    """
    priority_colors = {
        'CRITICAL': '#dc3545',
        'HIGH': '#fd7e14',
        'MEDIUM': '#ffc107',
        'LOW': '#28a745'
    }
    
    priority = action.get('priority', 'MEDIUM')
    color = priority_colors.get(priority, '#6c757d')
    
    st.markdown(f"""
    <div style="
        border: 1px solid #e0e0e0;
        border-left: 4px solid {color};
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        background: white;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>{action.get('title', 'Action')}</strong>
            <span style="
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.8em;
            ">{priority}</span>
        </div>
        <p style="color: #666; margin: 10px 0; font-size: 0.9em;">
            {action.get('description', '')}
        </p>
        <div style="font-size: 0.8em; color: #888;">
            <span>📊 Impact: {action.get('impact_estimate', 'N/A')}</span> | 
            <span>⏱️ Effort: {action.get('effort_estimate', 'N/A')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_pacing_bar(current: float, target: float, label: str):
    """
    Render a pacing progress bar
    
    Args:
        current: Current value
        target: Target value
        label: Label text
    """
    pct = min(100, (current / target * 100)) if target > 0 else 0
    
    if pct >= 100:
        color = '#28a745'
        status = '✅ On Track'
    elif pct >= 80:
        color = '#ffc107'
        status = '⚠️ Slightly Behind'
    else:
        color = '#dc3545'
        status = '🔴 Behind'
    
    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between;">
            <span>{label}</span>
            <span>{status}</span>
        </div>
        <div style="
            background-color: #e0e0e0;
            border-radius: 5px;
            height: 20px;
            margin-top: 5px;
        ">
            <div style="
                background-color: {color};
                width: {pct}%;
                height: 100%;
                border-radius: 5px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 0.8em;
            ">
                {pct:.0f}%
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #666;">
            <span>Current: ${current:,.0f}</span>
            <span>Target: ${target:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_data_freshness(last_update: datetime):
    """
    Render data freshness indicator
    
    Args:
        last_update: Datetime of last data update
    """
    now = datetime.now()
    diff = now - last_update
    
    if diff.total_seconds() < 3600:  # Less than 1 hour
        status = 'good'
        text = f"Updated {diff.seconds // 60} minutes ago"
    elif diff.total_seconds() < 86400:  # Less than 1 day
        status = 'warning'
        text = f"Updated {diff.seconds // 3600} hours ago"
    else:
        status = 'danger'
        text = f"Updated {diff.days} days ago"
    
    render_status_indicator(status, text)
