import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading

JOBS_DIR = 'jobs'
RESULTS_DIR = 'results'
CHROME_PROFILE_PATH = r"C:\Users\Success\AppData\Local\Google\Chrome\User Data\Profile 209"
CHROMEDRIVER_PATH = os.path.join(os.getcwd(), 'chromedriver-win64', 'chromedriver.exe')

def process_job_in_tab(driver, job_path, tab_lock):
    with tab_lock:
        # Open a new tab
        driver.execute_script("window.open('');")
        tab_handle = driver.window_handles[-1]
        driver.switch_to.window(tab_handle)
        try:
            with open(job_path, 'r', encoding='utf-8') as f:
                job = json.load(f)
            job_id = job['job_id']
            call_name = job['call_name']
            call_date = job['call_date']
            call_link = job['call_link']
            print(f'▶️ Processing job: {job_id} | {call_name} | {call_link}')
            transcript = None
            error = None

            print(f'🌍 Navigating to: {call_link}')
            driver.get(call_link)
            time.sleep(5)

            # Wait for the loading overlay to disappear
            print("⏳ Waiting for loader to disappear...")
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "ui-loader"))
            )
            print("✅ Loader gone.")

            # Click the 'Transcript' tab first to reveal the Copy Transcript button
            try:
                transcript_tab = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Transcript'] or text()='Transcript']"))
                )
                transcript_tab.click()
                print("🗂️ Clicked 'Transcript' tab.")
                time.sleep(1)
                # After clicking the 'Transcript' tab, wait for and click the 'Copy Transcript' button
                try:
                    print("🔎 Waiting for 'Copy Transcript' button to be clickable...")
                    copy_btn = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Copy Transcript']]"))
                    )
                    copy_btn.click()
                    print("✅ Clicked 'Copy Transcript' button.")
                    time.sleep(10)  # Wait for clipboard to update
                    # Get transcript from clipboard
                    try:
                        import pyperclip
                        transcript = pyperclip.paste()
                        print("📋 Transcript from clipboard (first 100 chars):", transcript[:100], "...")
                        # Save transcript to a .txt file if not empty
                        if transcript and transcript.strip():
                            txt_path = os.path.join(RESULTS_DIR, f'{job_id}.txt')
                            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                                txt_file.write(transcript)
                            print(f'📝 Transcript saved to: {txt_path}')
                    except Exception as e:
                        print(f"❌ Could not get transcript from clipboard: {e}")
                except Exception as e:
                    print(f"❌ Could not click 'Copy Transcript' button: {e}")
                    # Print all button texts for debugging
                    try:
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        print("🔘 Available buttons on page after clicking 'Transcript' tab:")
                        for idx, btn in enumerate(buttons):
                            try:
                                print(f"  [{idx}] {btn.text}")
                            except Exception:
                                print(f"  [{idx}] <unreadable button>")
                    except Exception as e2:
                        print(f"⚠️ Could not list buttons: {e2}")
            except Exception as e:
                print(f"❌ Could not click 'Transcript' tab: {e}")

            result = {
                'job_id': job_id,
                'call_name': call_name,
                'call_date': call_date,
                'call_link': call_link,
                'transcript': transcript,
                'error': error
            }
            os.makedirs(RESULTS_DIR, exist_ok=True)
            result_path = os.path.join(RESULTS_DIR, f'{job_id}.json')
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f'💾 Result written: {result_path}')
            try:
                if os.path.exists(job_path):
                    os.remove(job_path)
                    print(f'🗑️ Job file removed: {job_path}')
                else:
                    print(f'⚠️ Job file already removed: {job_path}')
            except Exception as e:
                print(f'❌ Error removing job file: {e}')
        finally:
            # Close the tab
            driver.close()
            # Switch back to the first tab (or any remaining tab)
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])

def main():
    os.makedirs(JOBS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print('👀 Watching for jobs...')
    options = Options()
    options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
    options.add_experimental_option("detach", True)
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    tab_lock = threading.Lock()
    try:
        while True:
            jobs = [f for f in os.listdir(JOBS_DIR) if f.endswith('.json')]
            for job_file in jobs:
                job_path = os.path.join(JOBS_DIR, job_file)
                t = threading.Thread(target=process_job_in_tab, args=(driver, job_path, tab_lock))
                t.start()
            time.sleep(2)
    finally:
        driver.quit()
        print("🛑 Browser closed.")

if __name__ == '__main__':
    main()