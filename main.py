# main.py
import os
import random
import time
import asyncio
import requests
from config import (
    USERNAME, PASSWORD, MLX_BASE, MLX_LAUNCHER_V2, HEADERS,
    FOLDER_ID, PROFILE_IDS, EMAIL_POOL, WEBSITES_FILE
)
from mlx_api import sign_in, start_profile, stop_profile
from websites import load_websites
from browser_utils import connect_to_browser
from form_utils import handle_newsletter_page
from results import save_results
from model.models import create_table
from db import test_connection


def start_profile_safe(token, folder_id, profile_id, launcher_v2, headers=None):
    """Start profile and wait for CDP endpoint to be ready"""
    resp, endpoint = start_profile(token, folder_id, profile_id, launcher_v2, headers)
    if not endpoint:
        print(f"⚠️ Profile {profile_id} failed to start. Skipping...")
        return None

    # Wait for CDP endpoint to respond
    for i in range(10):
        try:
            r = requests.get(f"{endpoint}/json/version", timeout=3)
            if r.status_code == 200:
                return endpoint
        except:
            pass
        time.sleep(1)
    print(f"⚠️ Profile {profile_id} CDP endpoint not ready. Skipping...")
    return None


async def run_with_profile(cdp_endpoint, url):
    """Connect to browser CDP and perform newsletter workflow"""
    pw, browser = await connect_to_browser(cdp_endpoint)
    if not browser:
        print("Failed to connect to browser.")
        if pw:
            try:
                await pw.stop()
            except:
                pass
        return False

    success = False
    try:
        contexts = browser.contexts
        context = contexts[0] if contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(url, wait_until='domcontentloaded', timeout=0)
        await asyncio.sleep(random.uniform(2, 5))

        # handle newsletter page/form
        success = await handle_newsletter_page(page)

    except Exception as e:
        print(f"Unexpected error while processing {url}: {e}")
    finally:
        try:
            await browser.close()
        except:
            pass
        try:
            await pw.stop()
        except:
            pass

    return success


async def process_websites(token, websites):
    """Main async workflow to process all websites with profile fallback"""
    results = []

    for idx, url in enumerate(websites):
        print("\n" + "#" * 60)
        print(f"PROCESSING {idx+1}/{len(websites)} -> {url}")

        profile_started = False
        email = random.choice(EMAIL_POOL)

        # Try each profile until one starts successfully
        for profile_id in PROFILE_IDS:
            print(f"\nTrying profile {profile_id} for {url}")

            # stop profile (best-effort)
            stop_profile(token, profile_id, MLX_LAUNCHER_V2, HEADERS)
            await asyncio.sleep(2)

            # start profile safely
            cdp_endpoint = start_profile_safe(token, FOLDER_ID, profile_id, MLX_LAUNCHER_V2, HEADERS)
            if not cdp_endpoint:
                print(f"⚠️ Profile {profile_id} failed. Trying next profile...")
                continue  # try next profile

            profile_started = True
            await asyncio.sleep(6)  # allow profile initialization

            # run newsletter workflow
            try:
                success = await run_with_profile(cdp_endpoint, url)
                results.append((url, success))
                print(f"✅ Website {url} processed using profile {profile_id}")
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results.append((url, False))
            finally:
                print(f"Cleaning up: stopping profile {profile_id}")
                stop_profile(token, profile_id, MLX_LAUNCHER_V2, HEADERS)
                await asyncio.sleep(2)

            break  # profile worked, move to next website

        if not profile_started:
            print(f"⚠️ All profiles failed for {url}. Skipping website.")
            results.append((url, False))

        # polite delay before next website
        if idx < len(websites) - 1:
            wait_time = random.randint(12, 25)
            print(f"Waiting {wait_time}s before next website...")
            await asyncio.sleep(wait_time)

    return results


def main():
    print("="*60)
    print("📧 MultiLogin Newsletter Automation")
    print("="*60)

    test_connection()
    create_table()

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

    start_time = time.time()
    results = asyncio.run(process_websites(token, websites))

    # save results
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print("Run finished. Saving results...")
    save_results(results)
    print(f"Elapsed time: {int(elapsed // 60)}m {int(elapsed % 60)}s")
    print("="*60)


if __name__ == "__main__":
    main()
