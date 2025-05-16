import argparse
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument('--no-proxy-server')

    print("Initialize webdriver")
    driver = webdriver.Chrome(options)
    driver.switch_to.window(driver.window_handles[0])
    wait = WebDriverWait(driver, 100)
    print(f"Go to {url}")
    driver.get(url)
    wait.until(EC.element_to_be_clickable((By.ID, "otc"))).send_keys(code)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type=\"submit\"]"))).click()
    print("Pass 1")
    wait.until(EC.element_to_be_clickable((By.ID, "usernameEntry"))).send_keys(email)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type=\"submit\"]"))).click()
    print("Pass 2")
    wait.until(EC.element_to_be_clickable((By.ID, "passwordEntry"))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type=\"submit\"]"))).click()
    try:
        print("Pass 3")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[aria-live="polite"]')))
    except Exception as e:
        print(e)
    try:
        print("Pass 4")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="primaryButton"]'))).click()
    except Exception as e:
        print(e)
    try:
        print("Pass 5")
        wait.until(EC.presence_of_all_elements_located((By.ID, 'idDiv_Finish_ErrTxt')))
    except Exception as e:
        print(e)
    print("Close driver")

    driver.close()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: graph_auth.py <url> <code> <email> <password>", file=sys.stderr)
        sys.exit(1)
    main()
