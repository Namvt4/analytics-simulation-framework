"""
Analytics Business Framework - BigQuery Connector
Handles all BigQuery data operations

Có 3 cách để kết nối BigQuery:
1. Service Account (file JSON) - cho production/server
2. gcloud CLI (User Account) - cho development local
3. Application Default Credentials (ADC) - tự động tìm credentials

Để dùng gcloud CLI:
1. Cài gcloud: https://cloud.google.com/sdk/docs/install
2. Chạy: gcloud auth application-default login
3. Set BQ_PROJECT_ID trong .env hoặc environment
"""

import pandas as pd
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import os

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    import google.auth
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    print("Warning: google-cloud-bigquery not installed. Using sample data.")


class BigQueryConnector:
    """
    BigQuery connector for fetching analytics data
    
    Hỗ trợ nhiều phương thức xác thực:
    - Service Account (file JSON)
    - gcloud CLI (User Account) - KHÔNG cần service account
    - Application Default Credentials (ADC)
    
    Falls back to sample data if BigQuery is not configured.
    """
    
    def __init__(self, project_id: str = None, credentials_path: str = None):
        self.project_id = project_id or os.getenv("BQ_PROJECT_ID")
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.client = None
        self._connected = False
        self.auth_method = None
        
    def connect(self) -> bool:
        """
        Establish connection to BigQuery
        
        Thử các phương thức xác thực theo thứ tự:
        1. Service Account (nếu có GOOGLE_APPLICATION_CREDENTIALS)
        2. gcloud CLI / Application Default Credentials
        
        Returns:
            True if connected successfully
        """
        if not BIGQUERY_AVAILABLE:
            print("❌ BigQuery library not available. Install: pip install google-cloud-bigquery")
            return False
            
        if not self.project_id:
            print("❌ BigQuery project ID not configured. Set BQ_PROJECT_ID environment variable.")
            return False
        
        # Method 1: Service Account (if credentials file provided)
        if self.credentials_path and os.path.exists(self.credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = bigquery.Client(
                    project=self.project_id,
                    credentials=credentials
                )
                self._connected = True
                self.auth_method = "Service Account"
                print(f"✅ Connected to BigQuery using Service Account")
                print(f"   Project: {self.project_id}")
                return True
            except Exception as e:
                print(f"⚠️ Service Account auth failed: {e}")
        
        # Method 2: gcloud CLI / Application Default Credentials (ADC)
        # This works if user has run: gcloud auth application-default login
        try:
            credentials, project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            # Use provided project_id or fall back to default project
            project_to_use = self.project_id or project
            
            self.client = bigquery.Client(
                project=project_to_use,
                credentials=credentials
            )
            self._connected = True
            self.auth_method = "gcloud CLI / ADC"
            print(f"✅ Connected to BigQuery using gcloud CLI (Application Default Credentials)")
            print(f"   Project: {project_to_use}")
            print(f"   💡 Không cần service account! Đang dùng tài khoản Google của bạn.")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to BigQuery: {e}")
            print(f"\n💡 Hướng dẫn kết nối không cần Service Account:")
            print(f"   1. Cài gcloud CLI: https://cloud.google.com/sdk/docs/install")
            print(f"   2. Chạy: gcloud auth application-default login")
            print(f"   3. Set environment variable: BQ_PROJECT_ID=your-project-id")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to BigQuery"""
        return self._connected and self.client is not None
    
    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame"""
        if not self.is_connected:
            if not self.connect():
                raise ConnectionError("Cannot connect to BigQuery")
        
        try:
            query_job = self.client.query(sql)
            return query_job.to_dataframe()
        except Exception as e:
            raise Exception(f"Query failed: {e}")
    
    def get_daily_metrics(self, 
                          start_date: datetime, 
                          end_date: datetime,
                          dataset: str = "analytics") -> pd.DataFrame:
        """
        Fetch daily metrics (DAU, Revenue, ROAS, etc.)
        
        Args:
            start_date: Start date for the query
            end_date: End date for the query
            dataset: BigQuery dataset name
            
        Returns:
            DataFrame with daily metrics
        """
        sql = f"""
        SELECT
            date,
            COUNT(DISTINCT user_id) as dau,
            SUM(ad_revenue) as iaa_revenue,
            SUM(iap_revenue) as iap_revenue,
            SUM(ad_revenue + iap_revenue) as total_revenue,
            SUM(spend) as total_spend,
            SAFE_DIVIDE(SUM(ad_revenue + iap_revenue), SUM(spend)) as roas
        FROM `{self.project_id}.{dataset}.daily_metrics`
        WHERE date BETWEEN '{start_date.strftime('%Y-%m-%d')}' 
              AND '{end_date.strftime('%Y-%m-%d')}'
        GROUP BY date
        ORDER BY date
        """
        return self.query(sql)
    
    def get_cohort_retention(self,
                             cohort_date: datetime,
                             dataset: str = "analytics") -> pd.DataFrame:
        """
        Fetch cohort retention data
        
        Args:
            cohort_date: The cohort install date
            dataset: BigQuery dataset name
            
        Returns:
            DataFrame with retention by day
        """
        sql = f"""
        SELECT
            days_since_install,
            COUNT(DISTINCT user_id) as active_users,
            SAFE_DIVIDE(
                COUNT(DISTINCT user_id),
                MAX(cohort_size)
            ) as retention_rate
        FROM `{self.project_id}.{dataset}.cohort_retention`
        WHERE cohort_date = '{cohort_date.strftime('%Y-%m-%d')}'
        GROUP BY days_since_install
        ORDER BY days_since_install
        """
        return self.query(sql)
    
    def get_campaign_performance(self,
                                 start_date: datetime,
                                 end_date: datetime,
                                 dataset: str = "analytics") -> pd.DataFrame:
        """
        Fetch campaign performance data for analysis
        
        Args:
            start_date: Start date
            end_date: End date
            dataset: BigQuery dataset name
            
        Returns:
            DataFrame with campaign metrics
        """
        sql = f"""
        SELECT
            campaign_id,
            campaign_name,
            media_source,
            country,
            SUM(installs) as installs,
            SUM(spend) as spend,
            SAFE_DIVIDE(SUM(spend), SUM(installs)) as cpi,
            SUM(revenue_d7) as revenue_d7,
            SAFE_DIVIDE(SUM(revenue_d7), SUM(spend)) as roas_d7
        FROM `{self.project_id}.{dataset}.campaigns`
        WHERE date BETWEEN '{start_date.strftime('%Y-%m-%d')}' 
              AND '{end_date.strftime('%Y-%m-%d')}'
        GROUP BY campaign_id, campaign_name, media_source, country
        ORDER BY spend DESC
        """
        return self.query(sql)
    
    def get_user_segments(self, dataset: str = "analytics") -> pd.DataFrame:
        """
        Fetch user segments for personalization
        
        Returns:
            DataFrame with user segment data
        """
        sql = f"""
        SELECT
            user_id,
            segment,
            ltv_predicted,
            churn_probability,
            last_active_date,
            days_since_install
        FROM `{self.project_id}.{dataset}.user_segments`
        WHERE segment IS NOT NULL
        """
        return self.query(sql)
    
    def get_funnel_data(self,
                        start_date: datetime,
                        end_date: datetime,
                        dataset: str = "analytics") -> pd.DataFrame:
        """
        Fetch funnel conversion data for analysis
        
        Returns:
            DataFrame with funnel steps and conversion rates
        """
        sql = f"""
        SELECT
            step_name,
            step_order,
            COUNT(DISTINCT user_id) as users,
            LAG(COUNT(DISTINCT user_id)) OVER (ORDER BY step_order) as prev_users.
        FROM `{self.project_id}.{dataset}.funnel_events`
        WHERE date BETWEEN '{start_date.strftime('%Y-%m-%d')}' 
              AND '{end_date.strftime('%Y-%m-%d')}'
        GROUP BY step_name, step_order
        ORDER BY step_order
        """
        return self.query(sql)


# Singleton instance
_connector = None

def get_connector() -> BigQueryConnector:
    """Get or create BigQuery connector instance"""
    global _connector
    if _connector is None:
        _connector = BigQueryConnector()
    return _connector
