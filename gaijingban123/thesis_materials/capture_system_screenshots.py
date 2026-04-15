import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "thesis_materials" / "system_screenshots"
BASE_URL = "http://127.0.0.1:4173"
BROWSER_PATH = (
    Path.home()
    / "Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/"
    / "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)

ROUTES = [
    ("/", "dashboard.png", "系统首页"),
    ("/data-center", "data-center.png", "数据中心"),
    ("/metrics", "metrics.png", "模型评估"),
    ("/forecast", "forecast.png", "预测结果"),
    ("/charts?category=metrics", "charts.png", "图表中心"),
    ("/system", "system.png", "系统设计"),
]


def build_driver():
    options = Options()
    options.binary_location = str(BROWSER_PATH)
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1440,1800")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--hide-scrollbars")
    service = Service(ChromeDriverManager(driver_version="143.0.7499.4").install())
    return webdriver.Chrome(service=service, options=options)


def capture_route(driver, route, filename):
    url = f"{BASE_URL}{route}"
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".app-shell")),
    )
    time.sleep(2 if "charts" not in route else 4)
    height = driver.execute_script(
        "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);",
    )
    driver.set_window_size(1440, max(1100, min(height + 120, 2400)))
    time.sleep(1)
    output_path = OUTPUT_DIR / filename
    driver.save_screenshot(str(output_path))
    return output_path


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    driver = build_driver()
    try:
        for route, filename, title in ROUTES:
            path = capture_route(driver, route, filename)
            print(f"{title}: {path}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
