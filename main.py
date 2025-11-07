# main4.py
import os
import random
import time
import asyncio
from config import (
    USERNAME, PASSWORD, MLX_BASE, MLX_LAUNCHER_V2, HEADERS, 
    FOLDER_ID, PROFILE_IDS, EMAIL_POOL, WEBSITES_FILE
)
from mlx_api import sign_in, start_profile, stop_profile
from websites import load_websites
from browser_utils import connect_to_browser
from form_utils import handle_newsletter_page  # updated function
from results import save_results

def main():
    print("="*60)
    print("📧 MultiLogin Newsletter Automation")
    print("="*60)

    # sanity checks
    if not USERNAME or not PASSWORD:
        print("ERROR: USERNAME or PASSWORD missing in .env")
        return
    if not PROFILE_IDS:
        print("ERROR: PROFILE_IDS empty in .env")
        return
    if not EMAIL_POOL:
        print("ERROR: EMAIL_POOL empty in .env")
        return

    # authenticate
    print("🔐 Authenticating with Multilogin...")
    token = sign_in(USERNAME, PASSWORD, MLX_BASE, HEADERS)
    if not token:
        print("❌ Authentication failed. Aborting.")
        return

    # load websites
    websites = load_websites()
    if not websites:
        print("❌ No websites found. Aborting.")
        return

    print(f"Configuration: {len(websites)} websites, {len(PROFILE_IDS)} profiles, {len(EMAIL_POOL)} emails")
    input("Press ENTER to start processing (Ctrl+C to cancel)... ")

    results = []
    start_time = time.time()

    for idx, url in enumerate(websites):
        print("\n" + "#" * 60)
        print(f"PROCESSING {idx+1}/{len(websites)} -> {url}")
        profile_id = PROFILE_IDS[idx % len(PROFILE_IDS)]  # cycle profiles
        email = random.choice(EMAIL_POOL)

        # stop profile (best-effort)
        print("Stopping profile if running...")
        stop_profile(token, profile_id, MLX_LAUNCHER_V2, HEADERS)
        time.sleep(2)

        # start profile
        print("Starting profile...")
        resp, cdp_endpoint = start_profile(token, FOLDER_ID, profile_id, MLX_LAUNCHER_V2, HEADERS)
        if not cdp_endpoint:
            print(f"Failed to start profile {profile_id}. Skipping website.")
            results.append((url, False))
            continue

        time.sleep(6)  # allow profile initialization

        # run newsletter workflow
        try:
            success = asyncio.run(run_with_profile(cdp_endpoint, url, email))
            results.append((url, success))
        except Exception as e:
            print(f"Error processing {url}: {e}")
            results.append((url, False))
        finally:
            print("Cleaning up: stopping profile")
            stop_profile(token, profile_id, MLX_LAUNCHER_V2, HEADERS)
            time.sleep(2)

        # polite delay
        if idx < len(websites) - 1:
            wait_time = random.randint(12, 25)
            print(f"Waiting {wait_time}s before next website...")
            time.sleep(wait_time)

    # save results
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print("Run finished. Saving results...")
    save_results(results)
    print(f"Elapsed time: {int(elapsed // 60)}m {int(elapsed % 60)}s")
    print("="*60)


async def run_with_profile(cdp_endpoint, url, email):
    """
    Connect to browser CDP and perform newsletter workflow:
    1. Check for newsletter form
    2. If form exists → fill & submit
    3. If not → look for any newsletter link/button/heading,
       navigate there, wait for form, fill & submit
    """
    pw, browser = await connect_to_browser(cdp_endpoint)
    if not browser:
        print("Failed to connect to browser.")
        if pw:
            try: await pw.stop()
            except: pass
        return False

    success = False
    try:
        contexts = browser.contexts
        context = contexts[0] if contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(random.uniform(2, 5))

        # handle newsletter page/form
        success = await handle_newsletter_page(page, email)

    except Exception as e:
        print(f"Unexpected error while processing {url}: {e}")
    finally:
        try:
            await browser.close()
        except Exception:
            pass
        try:
            await pw.stop()
        except Exception:
            pass

    return success


if __name__ == "__main__":
    main()
