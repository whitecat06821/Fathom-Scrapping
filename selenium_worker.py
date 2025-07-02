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
import sys
import concurrent.futures

JOBS_DIR = 'jobs'
RESULTS_DIR = 'results'
CHROME_PROFILE_PATH = r"C:\Users\Success\AppData\Local\Google\Chrome\User Data\Profile 209"
CHROMEDRIVER_PATH = os.path.join(os.getcwd(), 'chromedriver-win64', 'chromedriver.exe')

print_lock = threading.Lock()
def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)
        sys.stdout.flush()

def process_job_in_tab(driver, job_path, tab_lock):
    job_id = None
    try:
        with open(job_path, 'r', encoding='utf-8') as f:
            job = json.load(f)
        job_id = job['job_id']
        call_name = job['call_name']
        call_date = job['call_date']
        call_link = job['call_link']
        safe_print(f'[{job_id}] ▶️ Processing job: {job_id} | {call_name} | {call_link}')
        transcript = None
        error = None
        with tab_lock:
            driver.execute_script("window.open('');")
            tab_handle = driver.window_handles[-1]
            driver.switch_to.window(tab_handle)
            try:
                safe_print(f'[{job_id}] 🌍 Navigating to: {call_link}')
                driver.get(call_link)
                time.sleep(5)
                safe_print(f'[{job_id}] ⏳ Waiting for loader to disappear...')
                WebDriverWait(driver, 30).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "ui-loader"))
                )
                safe_print(f'[{job_id}] ✅ Loader gone.')
                try:
                    transcript_tab = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Transcript'] or text()='Transcript']"))
                    )
                    transcript_tab.click()
                    safe_print(f"[{job_id}] 🗂️ Clicked 'Transcript' tab.")
                    time.sleep(1)
                    try:
                        safe_print(f"[{job_id}] 🔎 Waiting for 'Copy Transcript' button to be clickable...")
                        copy_btn = WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Copy Transcript']]"))
                        )
                        copy_btn.click()
                        safe_print(f"[{job_id}] ✅ Clicked 'Copy Transcript' button.")
                        time.sleep(10)
                        try:
                            import pyperclip
                            transcript = pyperclip.paste()
                            safe_print(f'[{job_id}] 📋 Transcript from clipboard (first 100 chars): {transcript[:100]} ...')
                            if transcript and transcript.strip():
                                txt_path = os.path.join(RESULTS_DIR, f'{job_id}.txt')
                                with open(txt_path, 'w', encoding='utf-8') as txt_file:
                                    txt_file.write(transcript)
                                safe_print(f'[{job_id}] 📝 Transcript saved to: {txt_path}')
                        except Exception as e:
                            safe_print(f'[{job_id}] ❌ Could not get transcript from clipboard: {e}')
                    except Exception as e:
                        safe_print(f"[{job_id}] ❌ Could not click 'Copy Transcript' button: {e}")
                        try:
                            buttons = driver.find_elements(By.TAG_NAME, "button")
                            safe_print(f"[{job_id}] 🔘 Available buttons on page after clicking 'Transcript' tab:")
                            for idx, btn in enumerate(buttons):
                                try:
                                    safe_print(f'[{job_id}]   [{idx}] {btn.text}')
                                except Exception:
                                    safe_print(f'[{job_id}]   [{idx}] <unreadable button>')
                        except Exception as e2:
                            safe_print(f'[{job_id}] ⚠️ Could not list buttons: {e2}')
                except Exception as e:
                    safe_print(f"[{job_id}] ❌ Could not click 'Transcript' tab: {e}")
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
                safe_print(f'[{job_id}] 💾 Result written: {result_path}')
                try:
                    if os.path.exists(job_path):
                        os.remove(job_path)
                        safe_print(f'[{job_id}] 🗑️ Job file removed: {job_path}')
                    else:
                        safe_print(f'[{job_id}] ⚠️ Job file already removed: {job_path}')
                except Exception as e:
                    safe_print(f'[{job_id}] ❌ Error removing job file: {e}')
            finally:
                driver.close()
                if driver.window_handles:
                    driver.switch_to.window(driver.window_handles[0])
    except Exception as e:
        safe_print(f'[{job_id}] ❌ Exception in job: {e}')

def main():
    os.makedirs(JOBS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    safe_print('👀 Watching for jobs...')
    tab_lock = threading.Lock()
    threads = []
    driver = None
    max_workers = 3  # Limit concurrent jobs
    try:
        while True:
            jobs = [f for f in os.listdir(JOBS_DIR) if f.endswith('.json')]
            if jobs and driver is None:
                options = Options()
                options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
                options.add_experimental_option("detach", True)
                # options.add_argument("--headless=new")  # Uncomment to run headless if your workflow supports it
                service = Service(CHROMEDRIVER_PATH)
                driver = webdriver.Chrome(service=service, options=options)
                safe_print('🚗 Browser started.')
            # Use ThreadPoolExecutor to limit concurrency
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for job_file in jobs:
                    job_path = os.path.join(JOBS_DIR, job_file)
                    futures.append(executor.submit(process_job_in_tab, driver, job_path, tab_lock))
                # Wait for all jobs to finish
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        safe_print(f'[MAIN] ❌ Exception in thread: {e}')
            # If no jobs and driver is not None, close browser
            if not jobs and driver is not None:
                driver.quit()
                driver = None
                safe_print('🛑 Browser closed (no jobs left).')
            time.sleep(2)
    finally:
        if driver is not None:
            driver.quit()
            safe_print("🛑 Browser closed (on exit).")

if __name__ == '__main__':
    main()