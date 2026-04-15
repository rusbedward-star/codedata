import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase


class DashboardApiTests(TestCase):
    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        source_file = Path(__file__).resolve().parents[2] / "冰柠销量数据.csv"
        self.temp_monthly_file = Path(self.temp_dir.name) / "冰柠销量数据.csv"
        shutil.copyfile(source_file, self.temp_monthly_file)
        self.monthly_file_patcher = patch("dashboard.views.MONTHLY_DATA_FILE", self.temp_monthly_file)
        self.monthly_file_patcher.start()

    def tearDown(self):
        self.monthly_file_patcher.stop()
        self.temp_dir.cleanup()
        super().tearDown()

    def test_overview_endpoint(self):
        response = self.client.get("/api/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("project_name", response.json())

    def test_sample_data_endpoint(self):
        response = self.client.get("/api/sample-data/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

    def test_metrics_endpoint(self):
        response = self.client.get("/api/metrics/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

    def test_forecast_endpoint(self):
        response = self.client.get("/api/forecast/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

    def test_model_detail_endpoint(self):
        response = self.client.get("/api/model-detail/", {"model": "随机森林"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["model"], "随机森林")

    def test_modules_endpoint(self):
        response = self.client.get("/api/modules/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("frontend_modules", response.json())

    def test_insights_endpoint(self):
        response = self.client.get("/api/insights/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("recommendations", response.json())

    def test_metric_chart_endpoint(self):
        response = self.client.get("/api/charts/rmse/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "echarts", status_code=200)

    def test_model_chart_endpoint(self):
        response = self.client.get("/api/charts/model-forecast/", {"model": "LSTM"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "echarts", status_code=200)

    def test_image_endpoint(self):
        response = self.client.get("/api/media/results/MAE指标对比图.png/")
        self.assertEqual(response.status_code, 200)

    def test_create_sample_data_endpoint(self):
        payload = {
            "date": "2026-03",
            "sales": 61.23,
            "last_month_sales": 53.45,
            "last_year_same_month": 63.25,
            "is_holiday": 0,
            "is_promo": 1,
            "region": "白云区",
            "product_series": "冰柠系列",
        }
        response = self.client.post(
            "/api/sample-data/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["item"]["month"], 3)

        list_response = self.client.get("/api/sample-data/")
        dates = [row["date"] for row in list_response.json()["items"]]
        self.assertIn("2026-03", dates)

    def test_update_sample_data_endpoint(self):
        payload = {
            "date": "2024-05",
            "sales": 77.77,
            "last_month_sales": 58.34,
            "last_year_same_month": "",
            "is_holiday": 1,
            "is_promo": 1,
            "region": "天河区",
            "product_series": "冰柠清爽系列",
        }
        response = self.client.put(
            "/api/sample-data/2024-05/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item"]["sales"], 77.77)
        self.assertEqual(response.json()["item"]["product_series"], "冰柠清爽系列")

    def test_delete_sample_data_endpoint(self):
        response = self.client.delete("/api/sample-data/2024-05/")
        self.assertEqual(response.status_code, 200)

        list_response = self.client.get("/api/sample-data/")
        dates = [row["date"] for row in list_response.json()["items"]]
        self.assertNotIn("2024-05", dates)

# Create your tests here.
