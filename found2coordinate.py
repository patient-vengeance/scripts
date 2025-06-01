import pandas as pd
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_address_from_web(hosp_name):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    address = None
    try:
        driver.get("https://escreening.hpa.gov.tw/Hospital")
        input_box = driver.find_element(By.ID, "txtHospName")
        input_box.clear()
        input_box.send_keys(hosp_name)
        driver.find_element(By.CLASS_NAME, "sbtn").click()
        time.sleep(2)

        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='https://www.google.com.tw/maps/place/']")
        if links:
            href = links[0].get_attribute("href")
            raw_address = href.split("/place/")[-1].split("/")[0]
            address = urllib.parse.unquote(raw_address)
    except Exception as e:
        print(f"[ERROR] {hosp_name}: {e}")
    finally:
        driver.quit()
    return hosp_name, address or "無法找到地址"

def process_csv(input_csv="input.csv", output_csv="output_with_address.csv", max_workers=20):
    df = pd.read_csv(input_csv, encoding="big5")
    if "機構名稱" not in df.columns:
        raise ValueError("CSV must contain a column named '機構名稱'")

    name_list = df["機構名稱"].tolist()
    address_map = {}

    print(f"🔄 開始查詢，共 {len(name_list)} 筆，使用 {max_workers} 執行緒")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_address_from_web, name) for name in name_list]
        for future in as_completed(futures):
            name, address = future.result()
            print(f"✔️ {name} → {address}")
            address_map[name] = address

    # 加入地址欄位
    df["地址"] = df["機構名稱"].map(address_map)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"✅ 已完成並輸出：{output_csv}")

if __name__ == "__main__":
    process_csv("臺北市復健科醫療機構.csv", "output_with_address.csv", max_workers=20)
