import os
import json
import asyncio
from playwright.async_api import async_playwright
import random

JOBS_DIR = 'jobs'
RESULTS_DIR = 'results'

USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]
VIEWPORT = {"width": 1280, "height": 800}

# Set this to your Chrome user data directory (update the path as needed)
CHROME_USER_DATA_DIR = r"C:\Users\Success\AppData\Local\Google\Chrome\User Data\Profile 209"

async def process_job(job_path):
    with open(job_path, 'r', encoding='utf-8') as f:
        job = json.load(f)
    job_id = job['job_id']
    call_name = job['call_name']
    call_date = job['call_date']
    call_link = job['call_link']
    print(f'▶️ Processing job: {job_id} | {call_name} | {call_link}')
    transcript = None
    error = None
    try:
        print('🌐 Launching browser in headed mode (debug) with your Chrome profile and extensions...')
        async with async_playwright() as p:
            user_agent = random.choice(USER_AGENTS)
            # Use launch_persistent_context for full profile and extension support
            context = await p.chromium.launch_persistent_context(
                CHROME_USER_DATA_DIR,
                headless=False,
                viewport=VIEWPORT,
                user_agent=user_agent,
                permissions=["clipboard-read", "clipboard-write"],
                locale="en-US",
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1"
            })
            print('🔔 Please ensure your VPN extension (e.g., OneVPN) is active in the opened browser window.')
            print('⏳ Waiting 7 seconds for VPN to auto-connect before starting automation...')
            await asyncio.sleep(7)
            print('🕒 Starting automation!')
            print(f'🌍 Navigating to: {call_link}')
            await page.goto(call_link, timeout=60000)
            print('✅ Page loaded!')
            await page.wait_for_selector("button:has-text('Copy Transcript')", timeout=15000)
            await page.click("button:has-text('Copy Transcript')")
            await page.wait_for_selector("text=Done", timeout=15000)
            await asyncio.sleep(1.5)
            try:
                transcript = await page.evaluate('''() => navigator.clipboard.readText()''')
            except Exception:
                transcript = None
            if not transcript:
                try:
                    transcript = await page.inner_text('div.transcript')
                except Exception:
                    transcript = None
            await context.close()
    except Exception as e:
        error = str(e)
        print(f'❌ Error processing job {job_id}: {error}')
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
    os.remove(job_path)
    print(f'🗑️ Job file removed: {job_path}')

# INSTRUCTIONS:
# When the browser window opens, manually activate your VPN extension (e.g., OneVPN) before pressing Enter in the terminal.
# This ensures all browser traffic (including Playwright automation) is routed through your VPN.

async def main():
    os.makedirs(JOBS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print('👀 Watching for jobs...')
    while True:
        jobs = [f for f in os.listdir(JOBS_DIR) if f.endswith('.json')]
        if jobs:
            for job_file in jobs:
                job_path = os.path.join(JOBS_DIR, job_file)
                await process_job(job_path)
        await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(main())