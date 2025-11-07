#!/usr/bin/env python3
"""
Multilogin X + Playwright Stealth + Newsletter Form Filler
-----------------------------------------------------------
Purpose:
- Start a Multilogin profile via the launcher API
- Connect via Playwright with stealth techniques
- Simulate human-like actions to evade CAPTCHA detection
- Automatically find and fill newsletter forms in any language
- Track CAPTCHA appearance after EVERY action
- Wait 1-2 minutes after submission
"""

import json
import time
import random
import asyncio
import requests
from hashlib import md5
import urllib3
import re

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[!] Missing dependencies. Install with:")
    print("    pip install playwright")
    print("    playwright install chromium")
    exit(1)

# === CONFIG ===
USERNAME = "nils@keaz.app"
PASSWORD = "6WucMdiVL#PbL#q"
MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER_V2 = "https://launcher.mlx.yt:45001/api/v2"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

FOLDER_ID = "b749e3ad-c25d-41ad-8285-1843505be99f"
PROFILE_ID = "e689f0ac-9a4c-4cfd-8aab-be937e1af00c"
TEST_URL = "https://sivankarim.com"

# Newsletter form data
NEWSLETTER_EMAIL = "test.user@example.com"
NEWSLETTER_NAME = "John Doe"

WAIT_FOR_PROFILE_SECONDS = 15
CONNECT_RETRY_INTERVAL = 2
WAIT_AFTER_SUBMISSION = random.randint(60, 120)  # 1-2 minutes
# ==============

# Multi-language newsletter keywords
NEWSLETTER_KEYWORDS = {
    'english': ['newsletter', 'subscribe', 'signup', 'sign up', 'email', 'updates', 'join'],
    'german': ['newsletter', 'abonnieren', 'anmelden', 'registrieren', 'e-mail', 'updates'],
    'french': ['newsletter', 'abonner', "s'inscrire", 'inscription', 'email', 'actualités'],
    'spanish': ['newsletter', 'suscribir', 'registrarse', 'inscribirse', 'correo', 'actualizaciones'],
    'italian': ['newsletter', 'iscriviti', 'registrati', 'email', 'aggiornamenti'],
    'dutch': ['nieuwsbrief', 'abonneren', 'aanmelden', 'registreren', 'email'],
    'portuguese': ['newsletter', 'inscrever', 'cadastrar', 'email', 'atualizações'],
    'polish': ['newsletter', 'zapisz', 'subskrybuj', 'email', 'aktualizacje'],
}

# CAPTCHA action counter
action_counter = 0


def sign_in(username, password):
    """Authenticate with Multilogin and return a token."""
    sign_url = f"{MLX_BASE}/user/signin"
    payload = {"email": username, "password": md5(password.encode()).hexdigest()}
    try:
        r = requests.post(sign_url, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        token = data["data"]["token"]
        print(f"[+] Signed in. Token (truncated): {token[:20]}...")
        return token
    except Exception as e:
        print("[!] Sign-in failed:", e)
        if hasattr(e, "response") and e.response is not None:
            print("Response:", e.response.text)
        return None


def stop_profile(token, profile_id):
    """Stop a profile if it's already running."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    stop_url = f"{MLX_LAUNCHER_V2}/profile/stop"
    payload = {"profileId": profile_id}
    try:
        r = requests.post(stop_url, json=payload, headers=headers, timeout=10, verify=False)
        print(f"[*] stop_profile status {r.status_code}")
        return True
    except Exception as e:
        print("[!] stop_profile error (may be already stopped):", str(e)[:80])
        return False


def start_profile(token, folder_id, profile_id):
    """Start a Multilogin profile and get CDP endpoint."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    start_url = f"{MLX_LAUNCHER_V2}/profile/f/{folder_id}/p/{profile_id}/start"
    
    params = {"automation_type": "playwright", "headless_mode": "false"}
    
    try:
        r = requests.get(start_url, headers=headers, params=params, timeout=20, verify=False)
        print("[*] start_profile HTTP status:", r.status_code)
        resp_json = r.json()
        print("[*] start_profile JSON response:")
        print(json.dumps(resp_json, indent=2))

        data = resp_json.get("data", {})
        port = data.get("port")
        
        if not port:
            print("[!] No port found in response")
            return None, None
        
        cdp_endpoint = f"http://127.0.0.1:{port}"
        print("[*] Resolved CDP endpoint:", cdp_endpoint)
        return resp_json, cdp_endpoint
    except Exception as e:
        print("[!] Error starting profile:", e)
        return None, None


async def detect_captcha_detailed(page, action_name="Unknown Action"):
    """
    Detailed CAPTCHA detection with comprehensive reporting.
    Checks for all types of CAPTCHAs and reports after each action.
    """
    global action_counter
    action_counter += 1
    
    print("\n" + "🔍" * 40)
    print(f"CAPTCHA CHECK #{action_counter} - AFTER: {action_name}")
    print("🔍" * 40)
    
    captcha_results = {
        'found': False,
        'types': [],
        'details': []
    }
    
    # Comprehensive CAPTCHA selectors
    captcha_checks = {
        'reCAPTCHA v2': [
            'iframe[src*="recaptcha"]',
            '.g-recaptcha',
            '#g-recaptcha',
            '[class*="recaptcha"]'
        ],
        'reCAPTCHA v3': [
            'script[src*="recaptcha"]'
        ],
        'hCaptcha': [
            'iframe[src*="hcaptcha"]',
            '.h-captcha',
            '#h-captcha',
            '[class*="hcaptcha"]'
        ],
        'Cloudflare Turnstile': [
            'iframe[src*="cloudflare"]',
            'iframe[src*="turnstile"]',
            '.cf-turnstile',
            '[class*="turnstile"]'
        ],
        'FunCaptcha/Arkose': [
            'iframe[src*="funcaptcha"]',
            'iframe[src*="arkoselabs"]',
            'iframe[src*="arkose"]',
            '#arkose',
            '[class*="arkose"]'
        ],
        'Image CAPTCHA': [
            'img[src*="captcha"]',
            'img[alt*="captcha"]',
            '[id*="captcha"] img',
            'canvas[id*="captcha"]'
        ],
        'Generic CAPTCHA': [
            '[id*="captcha"]',
            '[class*="captcha"]',
            'input[name*="captcha"]'
        ]
    }
    
    # Check each CAPTCHA type
    for captcha_type, selectors in captcha_checks.items():
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    # Check if element is visible
                    for elem in elements:
                        try:
                            is_visible = await elem.is_visible()
                            if is_visible:
                                captcha_results['found'] = True
                                captcha_results['types'].append(captcha_type)
                                detail = f"  ✗ {captcha_type} DETECTED - Selector: {selector}"
                                captcha_results['details'].append(detail)
                                print(detail)
                                break
                        except:
                            continue
            except Exception:
                continue
    
    # Check page content for CAPTCHA text indicators
    try:
        page_text = await page.evaluate("document.body.innerText.toLowerCase()")
        captcha_text_indicators = [
            'verify you are human',
            'prove you are human',
            'captcha',
            'security check',
            'are you a robot',
            'bot detection',
            'checking your browser',
            'just a moment',
            'please verify',
            'complete the captcha'
        ]
        
        for indicator in captcha_text_indicators:
            if indicator in page_text:
                captcha_results['found'] = True
                if 'Text-based Challenge' not in captcha_results['types']:
                    captcha_results['types'].append('Text-based Challenge')
                detail = f"  ✗ Text indicator found: '{indicator}'"
                captcha_results['details'].append(detail)
                print(detail)
                break
    except Exception:
        pass
    
    # Final result
    if captcha_results['found']:
        print(f"\n❌ CAPTCHA STATUS: DETECTED")
        print(f"   Types found: {', '.join(set(captcha_results['types']))}")
        print(f"   Total detections: {len(captcha_results['details'])}")
    else:
        print(f"\n✅ CAPTCHA STATUS: CLEAN - No CAPTCHA detected")
    
    print("=" * 80 + "\n")
    
    return captcha_results['found'], list(set(captcha_results['types']))


async def human_like_mouse_movement(page, num_moves=None):
    """Simulate natural mouse movements across the page."""
    if num_moves is None:
        num_moves = random.randint(3, 6)
    
    print(f"[+] Simulating {num_moves} natural mouse movements...")
    
    try:
        viewport = page.viewport_size
        if not viewport:
            viewport = {'width': 1920, 'height': 1080}
        
        for i in range(num_moves):
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # Check CAPTCHA after mouse movement
            await detect_captcha_detailed(page, f"Mouse Movement #{i+1} to ({x}, {y})")
            
            if random.random() < 0.3:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.mouse.move(x + random.randint(-10, 10), y + random.randint(-10, 10))
    except Exception as e:
        print(f"[!] Mouse movement error: {e}")


async def human_like_scroll(page, scroll_count=None, scroll_to_bottom=False):
    """Simulate natural scrolling behavior with reading pauses."""
    if scroll_count is None:
        scroll_count = random.randint(3, 6)
    
    print(f"[+] Simulating {scroll_count} natural scrolls{'to bottom' if scroll_to_bottom else ''}...")
    
    if scroll_to_bottom:
        # Scroll to bottom in chunks
        total_height = await page.evaluate("document.body.scrollHeight")
        current_position = 0
        chunk_num = 0
        
        while current_position < total_height:
            chunk_num += 1
            distance = random.randint(200, 500)
            current_position += distance
            await page.evaluate(f"window.scrollTo({{ top: {current_position}, behavior: 'smooth' }})")
            await asyncio.sleep(random.uniform(0.8, 1.5))
            
            # Check CAPTCHA after each scroll chunk
            await detect_captcha_detailed(page, f"Scroll to Bottom - Chunk #{chunk_num} (position: {current_position}px)")
            
            # Update total height (in case page dynamically loads content)
            total_height = await page.evaluate("document.body.scrollHeight")
    else:
        for i in range(scroll_count):
            distance = random.randint(150, 400)
            direction = 1 if random.random() < 0.8 else -1
            
            await page.evaluate(f"window.scrollBy({{ top: {distance * direction}, behavior: 'smooth' }})")
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            # Check CAPTCHA after each scroll
            await detect_captcha_detailed(page, f"Scroll #{i+1} ({distance}px {'down' if direction > 0 else 'up'})")


async def inject_advanced_stealth(page):
    """Inject comprehensive stealth scripts to evade all detection."""
    print("[+] Injecting advanced anti-detection scripts...")
    
    stealth_js = """
    // Core WebDriver Concealment
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    
    // Chrome Runtime
    window.chrome = {
        runtime: {
            connect: () => {},
            sendMessage: () => {},
            onMessage: { addListener: () => {}, removeListener: () => {} }
        },
        loadTimes: function() {},
        csi: function() {},
        app: {}
    };
    
    // Permissions API
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // Plugin Array
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer'},
            {name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            {name: 'Native Client', description: '', filename: 'internal-nacl-plugin'}
        ]
    });
    
    // Languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    
    // Remove Automation Properties
    delete navigator.__proto__.webdriver;
    
    // Console Protection
    console.clear();
    
    // Iframe Detection
    Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
    Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
    
    // Realistic properties
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    """
    
    await page.add_init_script(stealth_js)


async def find_newsletter_form(page):
    """
    Intelligently find newsletter forms in multiple languages.
    Returns (form_element, email_input, submit_button, name_input_optional)
    """
    print("[+] Searching for newsletter form in multiple languages...")
    print("[*] Searching in languages: English, German, French, Spanish, Italian, Dutch, Portuguese, Polish")
    
    # Check CAPTCHA before form search
    await detect_captcha_detailed(page, "Before Newsletter Form Search")
    
    # First, let's look for newsletter sections/containers in the entire page
    page_content = await page.content()
    page_text = await page.evaluate("document.body.innerText.toLowerCase()")
    
    # Build comprehensive keyword list
    all_keywords = []
    for lang_keywords in NEWSLETTER_KEYWORDS.values():
        all_keywords.extend(lang_keywords)
    all_keywords = list(set([k.lower() for k in all_keywords]))
    
    print(f"[*] Searching for keywords: {', '.join(all_keywords[:10])}...")
    
    # Check if any newsletter keyword exists on the page
    found_keywords = [kw for kw in all_keywords if kw in page_text]
    if found_keywords:
        print(f"[+] Found newsletter keywords on page: {', '.join(found_keywords[:5])}")
    else:
        print("[!] No newsletter keywords found on page")
    
    # Try to find forms with email inputs
    all_forms = await page.query_selector_all('form')
    print(f"[*] Found {len(all_forms)} forms on page")
    
    # If no forms found, try alternative selectors
    if len(all_forms) == 0:
        print("[*] No <form> elements found, searching for alternative newsletter structures...")
        # Look for newsletter containers that might use AJAX submission
        newsletter_containers = await page.query_selector_all('[class*="newsletter"], [id*="newsletter"], [class*="subscribe"], [id*="subscribe"]')
        print(f"[*] Found {len(newsletter_containers)} potential newsletter containers")
    
    for idx, form in enumerate(all_forms):
        try:
            # Get form HTML and text content
            form_html = await form.inner_html()
            form_text = await form.inner_text()
            form_content = (form_html + " " + form_text).lower()
            
            # Check if form contains newsletter-related keywords
            contains_newsletter_keyword = any(keyword in form_content for keyword in all_keywords)
            
            if not contains_newsletter_keyword:
                continue
            
            print(f"[+] Found potential newsletter form #{idx + 1}")
            
            # Look for email input - expanded selectors
            email_input = None
            email_selectors = [
                'input[type="email"]',
                'input[name*="email" i]',
                'input[id*="email" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="e-mail" i]',
                'input[placeholder*="correo" i]',  # Spanish
                'input[placeholder*="mail" i]',
                'input[placeholder*="courrier" i]',  # French
                'input[placeholder*="posta" i]',  # Italian
                'input[name*="mail" i]',
                'input[id*="mail" i]',
                'input[class*="email" i]',
                'input[class*="mail" i]'
            ]
            
            for selector in email_selectors:
                email_input = await form.query_selector(selector)
                if email_input:
                    print(f"[+] Found email input with selector: {selector}")
                    break
            
            if not email_input:
                continue
            
            # Look for name input (optional)
            name_input = None
            name_selectors = [
                'input[name*="name" i]',
                'input[id*="name" i]',
                'input[placeholder*="name" i]',
                'input[placeholder*="nom" i]',
                'input[placeholder*="nombre" i]',
                'input[type="text"]'
            ]
            
            for selector in name_selectors:
                name_input = await form.query_selector(selector)
                if name_input and name_input != email_input:
                    print(f"[+] Found name input with selector: {selector}")
                    break
            
            # Look for submit button - expanded with multi-language support
            submit_button = None
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                # English
                'button:has-text("subscribe")', 'button:has-text("Subscribe")', 'button:has-text("SUBSCRIBE")',
                'button:has-text("sign up")', 'button:has-text("Sign up")', 'button:has-text("SIGN UP")',
                'button:has-text("submit")', 'button:has-text("Submit")',
                'button:has-text("join")', 'button:has-text("Join")',
                # German
                'button:has-text("abonnieren")', 'button:has-text("Abonnieren")', 'button:has-text("ABONNIEREN")',
                'button:has-text("anmelden")', 'button:has-text("Anmelden")', 'button:has-text("ANMELDEN")',
                'button:has-text("registrieren")', 'button:has-text("Registrieren")',
                # French
                'button:has-text("abonner")', 'button:has-text("Abonner")', 'button:has-text("S\'abonner")',
                'button:has-text("inscrire")', 'button:has-text("Inscrire")', 'button:has-text("S\'inscrire")',
                # Spanish
                'button:has-text("suscribir")', 'button:has-text("Suscribir")', 'button:has-text("SUSCRIBIR")',
                'button:has-text("suscríbete")', 'button:has-text("Suscríbete")',
                'button:has-text("registrarse")', 'button:has-text("Registrarse")',
                # Italian
                'button:has-text("iscriviti")', 'button:has-text("Iscriviti")', 'button:has-text("ISCRIVITI")',
                'button:has-text("registrati")', 'button:has-text("Registrati")',
                # Dutch
                'button:has-text("abonneren")', 'button:has-text("Abonneren")',
                'button:has-text("aanmelden")', 'button:has-text("Aanmelden")',
                # Portuguese
                'button:has-text("inscrever")', 'button:has-text("Inscrever")',
                'button:has-text("cadastrar")', 'button:has-text("Cadastrar")',
                # Polish
                'button:has-text("zapisz")', 'button:has-text("Zapisz")',
                'button:has-text("subskrybuj")', 'button:has-text("Subskrybuj")',
                # Generic fallback
                'button',  # Fallback to any button in form
                'input[type="button"]',
                '[role="button"]'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = await form.query_selector(selector)
                    if submit_button:
                        button_text = await submit_button.inner_text()
                        print(f"[+] Found submit button: '{button_text.strip()}'")
                        break
                except:
                    continue
            
            if email_input and submit_button:
                # Check CAPTCHA after finding form
                await detect_captcha_detailed(page, f"After Finding Newsletter Form #{idx+1}")
                return form, email_input, submit_button, name_input
        
        except Exception as e:
            print(f"[!] Error analyzing form #{idx + 1}: {e}")
            continue
    
    # If no form found yet, try searching outside of form elements
    print("[!] No newsletter form found in standard form elements")
    print("[*] Searching for newsletter inputs outside of forms...")
    
    # Look for email inputs anywhere on the page
    all_email_inputs = await page.query_selector_all(
        'input[type="email"], input[name*="email" i], input[id*="email" i], input[placeholder*="email" i]'
    )
    
    print(f"[*] Found {len(all_email_inputs)} email inputs on page (including outside forms)")
    
    for idx, email_input in enumerate(all_email_inputs):
        try:
            # Check if this input is related to newsletter
            parent = await email_input.evaluate_handle('el => el.closest("div, section, footer, aside")')
            if parent:
                parent_html = await parent.evaluate('el => el.innerHTML')
                parent_text = await parent.evaluate('el => el.innerText')
                parent_content = (parent_html + " " + parent_text).lower()
                
                # Check if parent contains newsletter keywords
                contains_newsletter = any(keyword in parent_content for keyword in all_keywords)
                
                if contains_newsletter:
                    print(f"[+] Found potential newsletter email input #{idx + 1} (outside form)")
                    
                    # Look for submit button near this input
                    submit_button = None
                    # Try to find button within same parent
                    buttons = await parent.query_selector_all('button, input[type="submit"], input[type="button"]')
                    
                    for btn in buttons:
                        try:
                            btn_text = await btn.inner_text()
                            btn_text_lower = btn_text.lower()
                            # Check if button text contains submit-like keywords
                            submit_keywords = ['subscribe', 'abonnieren', 'suscribir', 'iscriviti', 
                                             'sign up', 'anmelden', 'submit', 'send', 'enviar', 
                                             'invia', 'envoyer', 'versturen']
                            if any(kw in btn_text_lower for kw in submit_keywords):
                                submit_button = btn
                                print(f"[+] Found submit button: '{btn_text.strip()}'")
                                break
                        except:
                            continue
                    
                    if not submit_button and buttons:
                        # Use first button as fallback
                        submit_button = buttons[0]
                        try:
                            btn_text = await submit_button.inner_text()
                            print(f"[+] Using first available button: '{btn_text.strip()}'")
                        except:
                            print(f"[+] Using first available button (no text)")
                    
                    if submit_button:
                        # Look for name input nearby
                        name_input = None
                        name_inputs = await parent.query_selector_all('input[type="text"], input[name*="name" i]')
                        for ni in name_inputs:
                            if ni != email_input:
                                name_input = ni
                                print(f"[+] Found name input")
                                break
                        
                        await detect_captcha_detailed(page, f"After Finding Newsletter Input #{idx+1} (outside form)")
                        return None, email_input, submit_button, name_input
        except Exception as e:
            print(f"[!] Error analyzing email input #{idx + 1}: {e}")
            continue
    
    print("[!] No newsletter form or input found anywhere on page")
    return None, None, None, None


async def fill_newsletter_form(page):
    """Find and fill the newsletter form with human-like behavior."""
    print("\n" + "=" * 60)
    print("[+] STARTING NEWSLETTER FORM SEARCH AND FILL")
    print("=" * 60)
    
    # Check CAPTCHA at start
    await detect_captcha_detailed(page, "Start of Newsletter Form Fill Process")
    
    # First scroll down to reveal potential forms
    print("[+] Scrolling to bottom to reveal all forms...")
    await human_like_scroll(page, scroll_to_bottom=True)
    await asyncio.sleep(2)
    
    # Find the newsletter form
    form, email_input, submit_button, name_input = await find_newsletter_form(page)
    
    if not email_input or not submit_button:
        print("[!] Could not find newsletter form. Continuing anyway...")
        await detect_captcha_detailed(page, "After Failed Form Search")
        return False
    
    print("[+] Newsletter form found! Preparing to fill...")
    
    # Scroll to the form
    try:
        await email_input.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(1, 2))
        await detect_captcha_detailed(page, "After Scrolling to Email Input")
    except:
        pass
    
    # Move mouse to email input naturally
    print("[+] Moving to email field...")
    try:
        box = await email_input.bounding_box()
        if box:
            await page.mouse.move(
                box['x'] + box['width'] / 2,
                box['y'] + box['height'] / 2
            )
            await asyncio.sleep(random.uniform(0.5, 1))
            await detect_captcha_detailed(page, "After Moving Mouse to Email Field")
    except:
        pass
    
    # Click email input
    print("[+] Clicking email field...")
    await email_input.click()
    await asyncio.sleep(random.uniform(0.5, 1))
    await detect_captcha_detailed(page, "After Clicking Email Field")
    
    # Type email with human-like delays
    print(f"[+] Typing email: {NEWSLETTER_EMAIL}")
    for i, char in enumerate(NEWSLETTER_EMAIL):
        await email_input.type(char, delay=random.randint(50, 150))
        # Check CAPTCHA every 5 characters
        if (i + 1) % 5 == 0:
            await detect_captcha_detailed(page, f"While Typing Email - Character {i+1}")
    
    await asyncio.sleep(random.uniform(0.5, 1.5))
    await detect_captcha_detailed(page, "After Completing Email Input")
    
    # Fill name if input exists
    if name_input:
        print("[+] Name field found, filling it...")
        try:
            await name_input.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await detect_captcha_detailed(page, "After Scrolling to Name Field")
            
            box = await name_input.bounding_box()
            if box:
                await page.mouse.move(
                    box['x'] + box['width'] / 2,
                    box['y'] + box['height'] / 2
                )
                await asyncio.sleep(random.uniform(0.3, 0.7))
                await detect_captcha_detailed(page, "After Moving Mouse to Name Field")
            
            await name_input.click()
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await detect_captcha_detailed(page, "After Clicking Name Field")
            
            print(f"[+] Typing name: {NEWSLETTER_NAME}")
            for i, char in enumerate(NEWSLETTER_NAME):
                await name_input.type(char, delay=random.randint(50, 150))
                # Check CAPTCHA every 3 characters
                if (i + 1) % 3 == 0:
                    await detect_captcha_detailed(page, f"While Typing Name - Character {i+1}")
            
            await asyncio.sleep(random.uniform(0.5, 1))
            await detect_captcha_detailed(page, "After Completing Name Input")
        except Exception as e:
            print(f"[!] Error filling name field: {e}")
    
    # ============================================================
    # 🔥 CRITICAL FIX: Add randomized behavior BEFORE submission
    # ============================================================
    
    # Human-like hesitation: Review what was typed (simulate reading)
    print("[+] Simulating human review of form (reading what was typed)...")
    review_time = random.uniform(2.5, 5.5)  # 2.5-5.5 seconds
    await asyncio.sleep(review_time)
    await detect_captcha_detailed(page, f"After Form Review ({review_time:.1f}s)")
    
    # Random chance to "correct" something (move cursor back to email field briefly)
    if random.random() < 0.3:  # 30% chance
        print("[+] Simulating 'double-checking' email field...")
        try:
            box = await email_input.bounding_box()
            if box:
                await page.mouse.move(
                    box['x'] + box['width'] / 2,
                    box['y'] + box['height'] / 2
                )
                await asyncio.sleep(random.uniform(0.8, 1.5))
                await detect_captcha_detailed(page, "After Double-Checking Email")
        except:
            pass
    
    # Random small mouse movements (nervousness/hesitation)
    if random.random() < 0.4:  # 40% chance
        print("[+] Simulating nervous mouse movement...")
        try:
            current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
            for _ in range(random.randint(1, 3)):
                jitter_x = random.randint(-20, 20)
                jitter_y = random.randint(-20, 20)
                await page.mouse.move(
                    max(0, current_pos.get('x', 500) + jitter_x),
                    max(0, current_pos.get('y', 500) + jitter_y)
                )
                await asyncio.sleep(random.uniform(0.2, 0.4))
        except:
            pass
        await detect_captcha_detailed(page, "After Nervous Mouse Movement")
    
    # Move to submit button
    print("[+] Moving to submit button...")
    try:
        await submit_button.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.5, 1))
        await detect_captcha_detailed(page, "After Scrolling to Submit Button")
        
        box = await submit_button.bounding_box()
        if box:
            # Don't go exactly to center - add slight randomness
            offset_x = random.uniform(-5, 5)
            offset_y = random.uniform(-5, 5)
            await page.mouse.move(
                box['x'] + box['width'] / 2 + offset_x,
                box['y'] + box['height'] / 2 + offset_y
            )
            
            # Randomized wait before clicking (crucial!)
            pre_click_wait = random.uniform(1.2, 3.5)
            print(f"[+] Waiting {pre_click_wait:.1f}s before clicking (human hesitation)...")
            await asyncio.sleep(pre_click_wait)
            await detect_captcha_detailed(page, f"After Pre-Click Wait ({pre_click_wait:.1f}s)")
    except:
        pass
    
    # Random chance to hover away and come back (changed mind simulation)
    if random.random() < 0.25:  # 25% chance
        print("[+] Simulating 'almost clicked but hesitated' behavior...")
        try:
            box = await submit_button.bounding_box()
            if box:
                # Move away
                away_x = box['x'] + random.randint(-100, -50)
                away_y = box['y'] + random.randint(-30, 30)
                await page.mouse.move(away_x, away_y)
                await asyncio.sleep(random.uniform(0.5, 1.2))
                
                # Move back
                await page.mouse.move(
                    box['x'] + box['width'] / 2 + random.uniform(-3, 3),
                    box['y'] + box['height'] / 2 + random.uniform(-3, 3)
                )
                await asyncio.sleep(random.uniform(0.3, 0.7))
                await detect_captcha_detailed(page, "After Hesitation Behavior")
        except:
            pass
    
    # Final pre-click pause (random micro-hesitation)
    final_pause = random.uniform(0.3, 0.8)
    await asyncio.sleep(final_pause)
    await detect_captcha_detailed(page, "IMMEDIATELY Before Click")
    
    # Click submit button
    print("[+] Clicking submit button...")
    await submit_button.click()
    
    # Add variable delay after click (button press duration simulation)
    post_click_delay = random.uniform(0.15, 0.35)
    await asyncio.sleep(post_click_delay)
    
    await detect_captcha_detailed(page, "IMMEDIATELY After Clicking Submit Button")
    
    print("[✓] Newsletter form submitted!")
    
    # Wait for potential page response/redirect
    await asyncio.sleep(random.uniform(2, 4))
    await detect_captcha_detailed(page, "After Post-Submit Wait")
    
    # Wait for 1-2 minutes after submission
    wait_time = WAIT_AFTER_SUBMISSION
    print(f"[+] Waiting {wait_time} seconds after submission (human behavior)...")
    
    # During wait, perform some light interactions
    for i in range(wait_time // 15):
        await asyncio.sleep(random.uniform(10, 15))
        
        # Randomize activity during wait
        activity = random.choice(['mouse', 'scroll', 'idle'])
        if activity == 'mouse':
            await human_like_mouse_movement(page, num_moves=1)
        elif activity == 'scroll':
            scroll_distance = random.randint(-200, 200)
            await page.evaluate(f"window.scrollBy({{ top: {scroll_distance}, behavior: 'smooth' }})")
            await asyncio.sleep(random.uniform(0.5, 1))
        # else: idle (just wait)
        
        print(f"[*] Waited {(i+1)*15} seconds so far...")
        await detect_captcha_detailed(page, f"During Wait Period - {(i+1)*15}s elapsed")
    
    # Final wait for remaining time
    remaining = wait_time % 15
    if remaining > 0:
        await asyncio.sleep(remaining)
    
    await detect_captcha_detailed(page, "After Complete Wait Period")
    print("[✓] Wait period completed!")
    return True


async def check_cloudflare_challenge(page):
    """Check for Cloudflare challenge."""
    try:
        content = await page.content()
        text = content.lower()
        if "checking your browser" in text or "just a moment" in text:
            print("[!] Cloudflare challenge detected - waiting...")
            await asyncio.sleep(5)
            return True
        return False
    except Exception:
        return False


async def connect_playwright(cdp_endpoint, max_retries=10):
    """Connect to Multilogin browser via Playwright CDP with retries."""
    playwright = None
    for attempt in range(max_retries):
        try:
            print(f"[+] Attempting Playwright connection (attempt {attempt + 1}/{max_retries})...")
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(cdp_endpoint)
            
            print("[+] Connected to Multilogin browser via Playwright.")
            return playwright, browser
        except Exception as e:
            print(f"[-] Connection attempt {attempt + 1} failed: {str(e)[:100]}")
            if playwright:
                await playwright.stop()
            if attempt < max_retries - 1:
                await asyncio.sleep(CONNECT_RETRY_INTERVAL)
    
    print("[!] Could not connect to browser after maximum retries.")
    return None, None


async def run_diagnostics(browser):
    """Run the main diagnostic routine with newsletter form filling."""
    contexts = browser.contexts
    if not contexts:
        print("[!] No browser contexts found")
        return False
    
    context = contexts[0]
    pages = context.pages
    
    if not pages:
        page = await context.new_page()
    else:
        page = pages[0]
    
    # Inject advanced stealth
    await inject_advanced_stealth(page)
    
    # Navigate to target with more flexible wait strategy
    print(f"[*] Navigating to: {TEST_URL}")
    try:
        await page.goto(TEST_URL, wait_until='domcontentloaded', timeout=60000)
        print("[+] Page loaded (domcontentloaded)")
    except Exception as e:
        print(f"[!] Navigation with domcontentloaded failed: {e}")
        try:
            # Fallback: try with 'load' event
            await page.goto(TEST_URL, wait_until='load', timeout=60000)
            print("[+] Page loaded (load)")
        except Exception as e2:
            print(f"[!] Navigation failed: {e2}")
            # Last resort: just wait a bit
            await asyncio.sleep(10)
    
    # Wait for page to render
    print("[*] Waiting for page to fully render...")
    await asyncio.sleep(5)
    
    # Check CAPTCHA after page load
    await detect_captcha_detailed(page, "After Initial Page Load")
    
    # Wait for page to settle
    await asyncio.sleep(random.uniform(2, 3))
    
    # Check for Cloudflare challenge
    cf_initial = await check_cloudflare_challenge(page)
    if cf_initial:
        print("[*] Waiting for Cloudflare challenge to resolve...")
        await asyncio.sleep(10)
        await detect_captcha_detailed(page, "After Cloudflare Challenge Wait")
    
    # Perform initial natural browsing
    print("[+] Performing initial page exploration...")
    await human_like_mouse_movement(page, num_moves=3)
    await asyncio.sleep(random.uniform(1, 2))
    
    # Take initial screenshot
    await page.screenshot(path='page_initial.png', full_page=False)
    print("[+] Initial screenshot saved: page_initial.png")
    await detect_captcha_detailed(page, "After Taking Initial Screenshot")
    
    # MAIN TASK: Find and fill newsletter form
    form_filled = await fill_newsletter_form(page)
    
    # Take final screenshot
    await page.screenshot(path='page_final.png', full_page=False)
    print("[+] Final screenshot saved: page_final.png")
    await detect_captcha_detailed(page, "After Taking Final Screenshot")
    
    # Final results
    print("\n" + "=" * 60)
    print("===== FINAL RESULTS =====")
    print("=" * 60)
    print(f"URL: {page.url}")
    print(f"Title: {await page.title()}")
    print(f"Newsletter form filled: {form_filled}")
    print(f"Total CAPTCHA checks performed: {action_counter}")
    print("=" * 60)
    
    return form_filled


async def main_async(token):
    """Async main function."""
    print("[*] Stopping any existing profile instances...")
    stop_profile(token, PROFILE_ID)
    
    print("[*] Starting Multilogin profile...")
    resp_json, cdp_endpoint = start_profile(token, FOLDER_ID, PROFILE_ID)
    
    if not cdp_endpoint:
        print("[!] No valid CDP endpoint found. Check launcher response.")
        return False
    
    print(f"[*] Waiting {WAIT_FOR_PROFILE_SECONDS} seconds for profile to initialize...")
    await asyncio.sleep(WAIT_FOR_PROFILE_SECONDS)
    
    playwright, browser = await connect_playwright(cdp_endpoint)
    if not browser:
        print("[!] Connection to browser failed.")
        stop_profile(token, PROFILE_ID)
        return False
    
    success = False
    try:
        success = await run_diagnostics(browser)
    except Exception as e:
        print("[!] Error during execution:", e)
        import traceback
        traceback.print_exc()
    finally:
        print("[*] Cleaning up...")
        try:
            await browser.close()
        except Exception:
            pass
        
        try:
            await playwright.stop()
        except Exception:
            pass
        
        await asyncio.sleep(2)
        stop_profile(token, PROFILE_ID)
        
        if success:
            print("\n✅ [SUCCESS] Newsletter form filled and submitted!")
        else:
            print("\n⚠️  [WARNING] Newsletter form not found or submission failed")
        
        print("[+] Done.")
    
    return success


def main():
    print("=" * 70)
    print("Multilogin X + Playwright Ultra-Stealth + Newsletter Auto-Fill")
    print("WITH COMPREHENSIVE CAPTCHA TRACKING AFTER EVERY ACTION")
    print("=" * 70)
    
    token = sign_in(USERNAME, PASSWORD)
    if not token:
        return
    
    asyncio.run(main_async(token))


if __name__ == "__main__":
    main()