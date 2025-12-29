# Hướng dẫn Kết nối BigQuery

## 3 Cách Kết nối (chọn 1)

### 🔐 Cách 1: Service Account (cho Production/Server)
Phù hợp khi deploy lên server hoặc Cloud Run.

1. Tạo Service Account trong Google Cloud Console
2. Tải file JSON credentials
3. Set environment variable:
```bash
set GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
set BQ_PROJECT_ID=your-project-id
```

---

### 👤 Cách 2: gcloud CLI (KHUYẾN NGHỊ cho Development)
**Không cần service account!** Dùng tài khoản Google cá nhân.

**Bước 1: Cài đặt gcloud CLI**
- Tải: https://cloud.google.com/sdk/docs/install
- Hoặc: `winget install Google.CloudSDK`

**Bước 2: Đăng nhập**
```bash
gcloud auth application-default login
```
Trình duyệt sẽ mở ra, đăng nhập bằng tài khoản Google có quyền truy cập BigQuery.

**Bước 3: Set Project ID**
```bash
# Trong PowerShell
$env:BQ_PROJECT_ID = "your-project-id"

# Hoặc tạo file .env:
# BQ_PROJECT_ID=your-project-id
```

**Bước 4: Chạy Dashboard**
```bash
streamlit run app.py
```

---

### 🌐 Cách 3: Application Default Credentials (ADC)
Tự động tìm credentials theo thứ tự:
1. Environment variable `GOOGLE_APPLICATION_CREDENTIALS`
2. gcloud CLI credentials
3. Google Cloud compute metadata (trên GCP)

---

## Kiểm tra Kết nối

```python
from data.bigquery_connector import get_connector

connector = get_connector()
if connector.connect():
    print("✅ Kết nối thành công!")
    print(f"Phương thức: {connector.auth_method}")
else:
    print("❌ Kết nối thất bại")
```

---

## Yêu cầu Quyền (IAM)
Tài khoản cần có quyền:
- `roles/bigquery.dataViewer` - Đọc dữ liệu
- `roles/bigquery.jobUser` - Chạy query

---

## Troubleshooting

### Lỗi: "Could not automatically determine credentials"
→ Chạy: `gcloud auth application-default login`

### Lỗi: "Access Denied"
→ Kiểm tra quyền IAM của tài khoản trên project

### Lỗi: "Project not found"
→ Kiểm tra `BQ_PROJECT_ID` có đúng không

---

## Cấu trúc Bảng BigQuery (Mẫu)

Dashboard mong đợi các bảng sau trong dataset:

### `daily_metrics`
| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Ngày |
| user_id | STRING | ID người dùng |
| ad_revenue | FLOAT64 | Doanh thu quảng cáo |
| iap_revenue | FLOAT64 | Doanh thu mua hàng |
| spend | FLOAT64 | Chi tiêu quảng cáo |

### `cohort_retention`
| Column | Type | Description |
|--------|------|-------------|
| cohort_date | DATE | Ngày cài đặt |
| days_since_install | INT64 | Số ngày từ cài đặt |
| user_id | STRING | ID người dùng |
| cohort_size | INT64 | Tổng user trong cohort |

### `campaigns`
| Column | Type | Description |
|--------|------|-------------|
| campaign_id | STRING | ID chiến dịch |
| campaign_name | STRING | Tên chiến dịch |
| media_source | STRING | Nguồn (Facebook, Google...) |
| country | STRING | Quốc gia |
| installs | INT64 | Số lượt cài đặt |
| spend | FLOAT64 | Chi tiêu |
| revenue_d7 | FLOAT64 | Doanh thu D7 |
