import asyncio, random, time
from config import PROFILE_IDS, EMAIL_POOL
from mlx_api import sign_in, start_profile, stop_profile
from websites import load_websites
from form_utils import fill_and_submit
from browser_utils import connect_to_browser
from results import save_results

def main():
    token = sign_in()
    websites = load_websites()
    results = []

    for idx,url in enumerate(websites):
        profile_id = PROFILE_IDS[idx % len(PROFILE_IDS)]
        email = random.choice(EMAIL_POOL)

        stop_profile(token, profile_id)
        resp, cdp = start_profile(token, "folder_id_placeholder", profile_id)
        if not cdp: continue

        asyncio.run(process_website(cdp, url, email, token, profile_id, results))

    save_results(results)

async def process_website(cdp_endpoint, url, email, token, profile_id, results):
    pw, browser = await connect_to_browser(cdp_endpoint)
    if not browser: return
    page = await browser.new_page()
    await page.goto(url)
    success = await fill_and_submit(page, email)
    results.append((url, success))
    await browser.close()
    await pw.stop()
    stop_profile(token, profile_id)

if __name__=="__main__":
    main()
