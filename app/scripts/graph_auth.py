import argparse
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def main():
    parser = argparse.ArgumentParser(
        description="Microsoft Graph Authentication By Automation"
    )
    parser.add_argument(
        "url",
        help="URL of microsoft graph authentication"
    )
    parser.add_argument(
        "code",
        help="Device code for microsoft graph authentication"
    )
    parser.add_argument(
        "email",
        help="Email address"
    )
    parser.add_argument(
        "password",
        help="Password"
    )
    args = parser.parse_args()

    url = args.url
    code = args.code
    email = args.email
    password = args.password

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument('--no-proxy-server')
    options.add_argument("--disable-dev-shm-usage")

    print('installing service')
    driver_manager = ChromeDriverManager()
    service = Service(driver_manager.install())
    print(driver_manager._get_driver_binary_path(driver_manager.driver))
    print('initialize driver')
    driver = webdriver.Chrome(options=options, service=service)
    driver.switch_to.window(driver.window_handles[0])
    wait = WebDriverWait(driver, 60)
    driver.get(url)
    wait.until(EC.element_to_be_clickable((By.ID, "otc"))).send_keys(code)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type=\"submit\"]"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "usernameEntry"))).send_keys(email)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type=\"submit\"]"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "passwordEntry"))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type=\"submit\"]"))).click()
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[aria-live="polite"]')))
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="primaryButton"]'))).click()
    wait.until(EC.presence_of_all_elements_located((By.ID, 'idDiv_Finish_ErrTxt')))

    driver.close()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: graph_auth.py <url> <code> <email> <password>", file=sys.stderr)
        sys.exit(1)
    main()
