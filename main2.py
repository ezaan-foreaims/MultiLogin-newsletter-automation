#!/usr/bin/env python3
import json
import time
import random
import asyncio
import requests
from hashlib import md5
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ ERROR: Missing dependencies!")
    print("Run: pip install playwright")
    print("Then: playwright install chromium")
    exit(1)


USERNAME = "nils@keaz.app"
PASSWORD = "6WucMdiVL#PbL#q"
MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER_V2 = "https://launcher.mlx.yt:45001/api/v2"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

FOLDER_ID = "b749e3ad-c25d-41ad-8285-1843505be99f"
PROFILE_ID = "87b446f5-4fca-40e8-b1bc-ff928e2d46c4"
TEST_URL = "http://perapera.eu"

EMAIL_POOL = [
    "james.mitchell92@gmail.com",
    "sarah.parker.uk@outlook.com",
    "michael.roberts2024@yahoo.com",
    "victor.von_doom2026@gmail.com",
    "steve.oldrogars1945@gmail.com",
    "james.marson1961@gmail.com",
    "reed.richard@1691gmail.com",
    "tony.stark2008@starkindustries.com",
    "bruce.banner1975@gmail.com",
    "natasha.romanoff1991@outlook.com",
    "clint.barton1984@yahoo.com",
    "wanda.maximoff1995@gmail.com",
    "peter.parker2001@dailybugle.net",
    "stephen.strange2016@gmail.com",
    "carol.danvers1989@starforce.com"
]


SELECTED_EMAIL = random.choice(EMAIL_POOL)

NEWSLETTER_KEYWORDS = ['newsletter', 'subscribe', 'signup', 'sign up', 'email', 'updates', 'join']



def sign_in(username, password):
    """Authenticate with Multilogin."""
    try:
        url = f"{MLX_BASE}/user/signin"
        payload = {"email": username, "password": md5(password.encode()).hexdigest()}
        r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        token = r.json()["data"]["token"]
        print(f"✅ Authenticated")
        return token
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return None


def stop_profile(token, profile_id):
    """Stop Multilogin profile."""
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        url = f"{MLX_LAUNCHER_V2}/profile/stop"
        requests.post(url, json={"profileId": profile_id}, headers=headers, timeout=10, verify=False)
        print("🛑 Profile stopped")
        return True
    except:
        return False


def start_profile(token, folder_id, profile_id):
    """Start Multilogin profile and get CDP endpoint."""
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        url = f"{MLX_LAUNCHER_V2}/profile/f/{folder_id}/p/{profile_id}/start"
        params = {"automation_type": "playwright", "headless_mode": "false"}
        
        r = requests.get(url, headers=headers, params=params, timeout=20, verify=False)
        resp = r.json()
        port = resp.get("data", {}).get("port")
        
        if not port:
            print("❌ No CDP port in response")
            return None, None
        
        endpoint = f"http://127.0.0.1:{port}"
        print(f"✅ Profile started | CDP: {endpoint}")
        return resp, endpoint
    except Exception as e:
        print(f"❌ Start failed: {e}")
        return None, None



async def type_human(element, text):
    """Type with human speed and variance."""
    for char in text:
        delay = random.randint(80, 250)
        await element.type(char, delay=delay)
        
        # Random micro-pauses
        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(0.2, 0.5))



async def find_newsletter_form(page):
    """Locate newsletter signup form."""
    print("🔍 Searching for newsletter form...")
    
    page_text = await page.evaluate("document.body.innerText.toLowerCase()")
    
    forms = await page.query_selector_all('form')
    print(f"📋 Analyzing {len(forms)} forms...")
    
    for idx, form in enumerate(forms):
        try:
            html = await form.inner_html()
            text = await form.inner_text()
            content = (html + " " + text).lower()
            
            if not any(k in content for k in NEWSLETTER_KEYWORDS):
                continue
            
            # Find email input
            email_in = None
            for sel in ['input[type="email"]', 'input[name*="email" i]', 'input[id*="email" i]']:
                email_in = await form.query_selector(sel)
                if email_in:
                    break
            
            if not email_in:
                continue
            
            # Find submit button
            submit = None
            for sel in ['button[type="submit"]', 'input[type="submit"]', 'button']:
                submit = await form.query_selector(sel)
                if submit:
                    break
            
            if email_in and submit:
                print(f"✅ Newsletter form found!")
                return form, email_in, submit
                
        except:
            continue
    
    # Search outside forms
    print("🔍 Searching outside forms...")
    email_inputs = await page.query_selector_all('input[type="email"], input[name*="email" i]')
    
    for email_in in email_inputs:
        try:
            parent = await email_in.evaluate_handle('el => el.closest("div, section, footer")')
            if parent:
                parent_text = await parent.evaluate('el => el.innerText.toLowerCase()')
                
                if any(k in parent_text for k in NEWSLETTER_KEYWORDS):
                    btns = await parent.query_selector_all('button, input[type="submit"]')
                    if btns:
                        print("✅ Found newsletter input!")
                        return None, email_in, btns[0]
        except:
            continue
    
    print("❌ No newsletter form found")
    return None, None, None



async def fill_newsletter(page):
    """Find and fill newsletter form."""
    print(f"\n📧 Email: {SELECTED_EMAIL}")
    
    # Find form
    form, email_in, submit = await find_newsletter_form(page)
    
    if not email_in or not submit:
        print("❌ Form not found")
        return False
    
    # Scroll to form with human-like behavior
    print("📜 Scrolling to form...")
    await email_in.scroll_into_view_if_needed()
    await asyncio.sleep(random.uniform(1.2, 2.3))
    
    # Move mouse to email field area
    print("🖱️  Moving to email field...")
    box = await email_in.bounding_box()
    if box:
        x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
        y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.3, 0.6))
    
    # Click email field
    print("👆 Clicking email field...")
    await email_in.click()
    await asyncio.sleep(random.uniform(0.6, 1.1))
    
    # Clear field first (in case there's placeholder)
    await email_in.fill('')
    await asyncio.sleep(0.2)
    
    # Type email
    print("⌨️  Typing email...")
    await type_human(email_in, SELECTED_EMAIL)
    await asyncio.sleep(random.uniform(1, 1.8))
    
    # Validate that email was typed correctly
    typed_value = await email_in.input_value()
    print(f"✅ Email entered: {typed_value}")
    
    # Move mouse to submit button
    print("🖱️  Moving to submit button...")
    submit_box = await submit.bounding_box()
    if submit_box:
        x = submit_box['x'] + submit_box['width'] * random.uniform(0.4, 0.6)
        y = submit_box['y'] + submit_box['height'] * random.uniform(0.4, 0.6)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.5, 1))
    
    # Check if button is enabled and visible
    is_visible = await submit.is_visible()
    is_enabled = await submit.is_enabled()
    print(f"📊 Button state - Visible: {is_visible}, Enabled: {is_enabled}")
    
    if not is_visible or not is_enabled:
        print("⚠️  Button not ready, waiting...")
        await asyncio.sleep(2)
    
    # Try multiple click strategies
    print("👆 Attempting submit (Strategy 1: Standard Click)...")
    try:
        await submit.click(delay=random.randint(80, 150), timeout=5000)
        print("✅ Click executed")
    except Exception as e:
        print(f"⚠️  Standard click warning: {e}")
    
    await asyncio.sleep(1)
    
    # Check if form is still there (if yes, submission didn't work)
    try:
        still_there = await email_in.is_visible()
        if still_there:
            print("⚠️  Form still visible, trying force click...")
            
            # Strategy 2: Force click with noWaitAfter
            try:
                await submit.click(force=True, no_wait_after=True)
                print("✅ Force click executed")
            except:
                pass
            
            await asyncio.sleep(0.8)
            
            # Strategy 3: Dispatch click event directly
            print("🔧 Trying JavaScript click...")
            await submit.evaluate('el => el.click()')
            
            await asyncio.sleep(0.5)
            
            # Strategy 4: If it's in a form, submit the form directly
            if form:
                print("🔧 Trying form.submit()...")
                await form.evaluate('form => form.submit()')
    except:
        print("✅ Form disappeared (likely submitted)")
    
    # Wait for navigation or response
    print("⏳ Waiting for response...")
    await asyncio.sleep(4)
    
    # Check for success indicators
    try:
        page_text = await page.evaluate("document.body.innerText.toLowerCase()")
        success_keywords = ['thank', 'success', 'subscribed', 'confirmed', 'check your email', 'almost done']
        
        if any(keyword in page_text for keyword in success_keywords):
            print("✅ Success message detected!")
            return True
        else:
            # Check if form disappeared
            try:
                form_gone = not await email_in.is_visible()
                if form_gone:
                    print("✅ Form disappeared (likely submitted)")
                    return True
                else:
                    print("⚠️  Form still visible, submission may have failed")
                    return False
            except:
                print("✅ Form elements gone (likely submitted)")
                return True
    except Exception as e:
        print(f"⚠️  Could not verify submission: {e}")
        return False


async def connect_to_browser(cdp_endpoint, max_retries=10):
    """Connect Playwright to CDP endpoint."""
    pw = None
    
    for attempt in range(max_retries):
        try:
            print(f"🔌 Connecting... (attempt {attempt+1}/{max_retries})")
            
            pw = await async_playwright().start()
            browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
            
            print("✅ Connected!")
            return pw, browser
            
        except Exception as e:
            if pw:
                await pw.stop()
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
    
    print("❌ Connection failed")
    return None, None


async def run_main_flow(browser):
    """Main execution flow."""
    contexts = browser.contexts
    if not contexts:
        print("❌ No browser contexts")
        return False
    
    context = contexts[0]
    pages = context.pages
    
    if not pages:
        page = await context.new_page()
    else:
        page = pages[0]
    
    # Navigate
    print(f"\n🌐 Navigating to: {TEST_URL}")
    try:
        await page.goto(TEST_URL, wait_until='domcontentloaded', timeout=60000)
        print("✅ Page loaded")
    except Exception as e:
        print(f"⚠️  Navigation warning: {e}")
        await asyncio.sleep(5)
    
    # Random browsing delay
    await asyncio.sleep(random.uniform(2.5, 4))
    
    # Optional: Random mouse movements
    print("🖱️  Simulating natural browsing...")
    for _ in range(random.randint(1, 2)):
        x = random.randint(200, 700)
        y = random.randint(200, 500)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.4, 0.8))
    
    # Fill form
    success = await fill_newsletter(page)
    
    # Give extra time to see the result
    await asyncio.sleep(3)
    
    return success


async def async_main(token):
    """Async main entry point."""
    print("🛑 Stopping existing profile...")
    stop_profile(token, PROFILE_ID)
    
    print("🚀 Starting profile...")
    resp, cdp = start_profile(token, FOLDER_ID, PROFILE_ID)
    
    if not cdp:
        return False
    
    print("⏰ Waiting for profile initialization...")
    await asyncio.sleep(15)
    
    pw, browser = await connect_to_browser(cdp)
    if not browser:
        stop_profile(token, PROFILE_ID)
        return False
    
    success = False
    try:
        success = await run_main_flow(browser)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleanup...")
        
        try:
            await browser.close()
        except:
            pass
        
        try:
            await pw.stop()
        except:
            pass
        
        await asyncio.sleep(3)
        stop_profile(token, PROFILE_ID)
        
        if success:
            print("\n✅ SUCCESS!")
        else:
            print("\n⚠️  Check browser for result")
    
    return success


def main():
    """Main entry point."""
    print("="*50)
    print("📧 Simple Newsletter Signup")
    print("="*50)
    
    token = sign_in(USERNAME, PASSWORD)
    if not token:
        print("❌ Authentication failed")
        return
    
    asyncio.run(async_main(token))


if __name__ == "__main__":
    main()