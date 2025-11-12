import asyncio
import random
import re
from typing import Optional, Tuple, List
from playwright.async_api import Page
from model.models import insert_submission
from constants import EMAIL_NEWSLETTER
from email_reader import read_emails
from urllib.parse import urlparse

NEWSLETTER_KEYWORDS = {
    'en': ['newsletter', 'subscribe', 'signup', 'sign up', 'email', 'updates', 'join', 'stay updated', 
           'get notified', 'mailing list', 'be first', 'hear about', 'promotion', 'promo', 'exclusive',
           'special offer', 'deals', 'discount', 'stay in touch', 'keep me updated', 'get updates',
           'join our list', 'email list', 'sign me up'],
    'de': ['newsletter', 'abonnieren', 'anmelden', 'registrieren', 'e-mail', 'jetzt anmelden', 'erhalte', 
           'bleib', 'vorname', 'nachname', 'erste', 'hören', 'angebot'],
    'fr': ['newsletter', 'abonner', "s'inscrire", 'inscription', 'email', 'première', 'offre'],
    'es': ['newsletter', 'boletín', 'suscribirse', 'registrarse', 'primera', 'oferta'],
    'it': ['newsletter', 'iscriviti', 'registrati', 'abbonati', 'prima', 'offerta'],
    'nl': ['nieuwsbrief', 'abonneren', 'aanmelden', 'eerste', 'aanbieding'],
    'pt': ['newsletter', 'boletim', 'inscrever', 'primeira', 'oferta'],
    'pl': ['newsletter', 'biuletyn', 'zapisz się', 'pierwsza', 'oferta'],
    'sv': ['nyhetsbrev', 'prenumerera', 'första', 'erbjudande'],
    'da': ['nyhedsbrev', 'tilmeld', 'første', 'tilbud'],
    'no': ['nyhetsbrev', 'abonner', 'første', 'tilbud']
}
ALL_KEYWORDS = list({kw.lower() for kws in NEWSLETTER_KEYWORDS.values() for kw in kws})

# Success message keywords
SUCCESS_KEYWORDS = [
    'thank', 'thanks', 'success', 'confirmed', 'subscribed', 'signed up', 'welcome',
    'check your email', 'check your inbox', 'verify', 'confirmation', 'almost there',
    'one more step', 'you\'re in', 'you are in', 'congratulations', 'done', 'great',
    'awesome', 'perfect', 'received', 'got it', 'submitted', 'registered'
]

FIRST_NAMES = ["James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Jennifer", "Daniel", "Laura"]
LAST_NAMES = ["Mitchell", "Parker", "Roberts", "Anderson", "Johnson", "Williams", "Brown", "Davis", "Miller", "Wilson"]

def extract_domain_keywords(url: str) -> List[str]:
    """Extract keywords from domain name for email matching"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = re.sub(r'^www\.', '', domain)
        domain = re.sub(r'\.(com|org|net|io|co|uk|de|fr|es|it)$', '', domain)
        parts = re.split(r'[-_.]', domain)
        keywords = [p for p in parts if len(p) > 2]
        return keywords
    except:
        return []

async def check_for_confirmation_email(website_url: str, wait_minutes: float = 1.0) -> Tuple[bool, Optional[str]]:
    """Wait for and check confirmation email"""
    print(f"\n📧 Waiting {wait_minutes} minutes for confirmation email...")
    domain_keywords = extract_domain_keywords(website_url)
    await asyncio.sleep(wait_minutes * 60)
    
    try:
        emails = read_emails(limit=20)
        if not emails:
            return False, None
        
        for email_data in reversed(emails):
            from_field = email_data.get('from', '').lower()
            subject = email_data.get('subject', '').lower()
            
            match_found = False
            for keyword in domain_keywords:
                if keyword.lower() in from_field or keyword.lower() in subject:
                    match_found = True
                    break
            
            if match_found:
                print(f"\n✅ CONFIRMATION EMAIL FOUND!")
                return True, email_data.get('body', '')
        
        return False, emails[-1].get('body', '') if emails else None
    except:
        return False, None

async def human_type(element, text: str):
    """Type text with human-like delays"""
    await element.fill('')
    for char in text:
        delay = random.uniform(80, 180)
        await element.type(char, delay=delay)
        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(0.2, 0.5))

async def close_popups_and_overlays(page: Page):
    """Close any popups, modals, sidebars, or overlays that might be blocking the page"""
    try:
        closed_something = await page.evaluate('''() => {
            let closed = false;
            
            // Common close button selectors
            const closeSelectors = [
                'button[aria-label*="close" i]',
                'button[aria-label*="dismiss" i]',
                '[class*="close" i]',
                '[class*="dismiss" i]',
                '[id*="close" i]',
                'button.modal-close',
                '.modal-backdrop',
                '[data-dismiss]',
                'button[title*="close" i]',
                '.popup-close',
                'svg[class*="close" i]',
                '[aria-label*="cerrar" i]', // Spanish
                '[aria-label*="fermer" i]', // French
                '[aria-label*="schließen" i]' // German
            ];
            
            // Try to click close buttons
            for (const selector of closeSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {
                    if (el.offsetParent !== null) {
                        try {
                            el.click();
                            closed = true;
                        } catch (e) {}
                    }
                }
            }
            
            // Remove modal backdrops and overlays
            const overlays = document.querySelectorAll('[class*="overlay" i], [class*="backdrop" i], [class*="modal" i]');
            for (const overlay of overlays) {
                if (overlay.offsetParent !== null) {
                    const style = window.getComputedStyle(overlay);
                    if (style.position === 'fixed' || style.position === 'absolute') {
                        try {
                            overlay.remove();
                            closed = true;
                        } catch (e) {}
                    }
                }
            }
            
            // Close navigation drawers/sidebars
            const navDrawers = document.querySelectorAll('[class*="drawer" i], [class*="sidebar" i], [class*="nav-menu" i]');
            for (const drawer of navDrawers) {
                if (drawer.offsetParent !== null) {
                    const style = window.getComputedStyle(drawer);
                    if (style.position === 'fixed' && style.zIndex > 100) {
                        try {
                            drawer.style.display = 'none';
                            closed = true;
                        } catch (e) {}
                    }
                }
            }
            
            return closed;
        }''')
        
        if closed_something:
            print("      ✓ Closed popup/overlay")
            await asyncio.sleep(0.5)
    except:
        pass

async def human_click(element) -> bool:
    """Click element with human-like behavior - NO TIMEOUT"""
    try:
        await element.scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        await element.hover()
        await asyncio.sleep(0.3)
        await element.click(no_wait_after=True)
        await asyncio.sleep(1)
        return True
    except Exception as e:
        print(f"      Click failed: {e}")
        return False

async def wait_for_content_loaded(page: Page):
    """Wait for page content to load - NO TIMEOUT LIMIT"""
    print("   ⏳ Waiting for page to fully load (no timeout)...")
    try:
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_function("() => document.body && document.body.innerText.length > 100")
        print("   ✅ Page loaded successfully")
    except Exception as e:
        print(f"   ⚠️ Load state check: {e}")
        # Continue anyway - page might be loaded enough

async def find_visible_newsletter_triggers(page: Page) -> List[Tuple[object, str]]:
    """Find all visible newsletter trigger buttons"""
    EXCLUDE_KEYWORDS = ['spotify', 'apple music', 'youtube', 'soundcloud', 'facebook', 'instagram', 
                        'twitter', 'play', 'listen', 'watch', 'shop', 'buy', 'login', 'contact']
    
    selectors = ['button', 'a', '[role="button"]']
    found_triggers = []
    
    for selector in selectors:
        try:
            elements = await page.locator(selector).all()
            for elem in elements:
                try:
                    if not await elem.is_visible():
                        continue
                    text = await elem.inner_text()
                    text_lower = text.lower().strip()
                    if any(excl in text_lower for excl in EXCLUDE_KEYWORDS):
                        continue
                    if any(kw in text_lower for kw in ALL_KEYWORDS):
                        found_triggers.append((elem, text))
                except:
                    continue
        except:
            continue
    
    return found_triggers

async def find_all_form_inputs(page: Page, form_container) -> List[Tuple[str, object]]:
    """Find all input fields in a form container"""
    all_inputs = []
    input_selectors = ['input[type="text"]', 'input[type="email"]', 'input[type="tel"]',
                       'input[name*="name" i]', 'input[name*="email" i]', 'input[placeholder*="email" i]']
    
    seen_elements = set()
    
    for selector in input_selectors:
        try:
            elements = await form_container.locator(selector).all()
            for elem in elements:
                try:
                    elem_id = await elem.evaluate('el => el.outerHTML')
                    if elem_id in seen_elements:
                        continue
                    seen_elements.add(elem_id)
                    
                    if not await elem.is_visible():
                        continue
                    
                    box = await elem.bounding_box()
                    if not box:
                        continue
                    
                    field_info = await elem.evaluate('''el => {
                        const name = (el.name || '').toLowerCase();
                        const placeholder = (el.placeholder || '').toLowerCase();
                        const type = (el.type || '').toLowerCase();
                        return {name, placeholder, type};
                    }''')
                    
                    field_type = 'text'
                    combined = f"{field_info['name']} {field_info['placeholder']}"
                    
                    if field_info['type'] == 'email' or 'email' in combined:
                        field_type = 'email'
                    elif 'first' in combined or 'fname' in combined:
                        field_type = 'fname'
                    elif 'last' in combined or 'lname' in combined:
                        field_type = 'lname'
                    elif 'phone' in combined or 'tel' in combined:
                        field_type = 'phone'
                    elif 'name' in combined:
                        field_type = 'fname'
                    
                    all_inputs.append((field_type, elem, box['y']))
                except:
                    continue
        except:
            continue
    
    all_inputs.sort(key=lambda x: x[2])
    return [(f[0], f[1]) for f in all_inputs]

async def find_all_checkboxes_on_page(page: Page) -> List[object]:
    """Find all visible checkboxes on page"""
    checkboxes = []
    try:
        all_checkboxes = await page.locator('input[type="checkbox"]').all()
        for cb in all_checkboxes:
            try:
                is_visible = await cb.evaluate('''el => {
                    if (el.offsetParent !== null) return true;
                    const label = el.closest('label');
                    if (label && label.offsetParent !== null) return true;
                    return false;
                }''')
                if is_visible:
                    checkboxes.append(cb)
            except:
                continue
    except:
        pass
    return checkboxes

async def check_checkbox(checkbox_elem) -> bool:
    """Check a checkbox with multiple methods"""
    try:
        if await checkbox_elem.is_checked():
            return True
        await checkbox_elem.scroll_into_view_if_needed()
        try:
            await checkbox_elem.click(force=True)
            await asyncio.sleep(0.2)
            if await checkbox_elem.is_checked():
                return True
        except:
            pass
        try:
            await checkbox_elem.evaluate('el => { el.checked = true; el.dispatchEvent(new Event("change")); }')
            return True
        except:
            pass
        return False
    except:
        return False

async def find_form_with_all_fields(page: Page) -> Tuple[Optional[object], List, List]:
    """Find newsletter form with fields"""
    form_selectors = ['form', 'div[class*="newsletter" i]', 'div[class*="subscribe" i]', 'div', 'section']
    
    for selector in form_selectors:
        try:
            containers = await page.locator(selector).all()
            for container in containers:
                try:
                    if not await container.is_visible():
                        continue
                    
                    has_email = await container.locator('input[type="email"], input[name*="email" i]').count() > 0
                    if not has_email:
                        continue
                    
                    context_text = await container.evaluate('el => el.innerText.toLowerCase()')
                    is_newsletter = any(kw in context_text for kw in ALL_KEYWORDS)
                    
                    if is_newsletter:
                        all_fields = await find_all_form_inputs(page, container)
                        if all_fields:
                            submit_btn = None
                            try:
                                buttons = await container.locator('button, input[type="submit"]').all()
                                for btn in buttons:
                                    if await btn.is_visible():
                                        submit_btn = btn
                                        break
                            except:
                                pass
                            
                            all_checkboxes = await find_all_checkboxes_on_page(page)
                            return submit_btn, all_checkboxes, all_fields
                except:
                    continue
        except:
            continue
    
    return None, [], []

async def handle_hcaptcha(page: Page) -> bool:
    """Handle hCaptcha if present"""
    try:
        has_hcaptcha = await page.evaluate('''() => {
            return typeof window.hcaptcha !== 'undefined' || 
                   document.querySelector('.h-captcha') !== null;
        }''')
        
        if not has_hcaptcha:
            return True
        
        print("   ⚠️ hCaptcha detected, attempting execute...")
        
        executed = await page.evaluate('''() => {
            try {
                if (typeof window.hcaptcha !== 'undefined') {
                    window.hcaptcha.execute();
                    return true;
                }
                return false;
            } catch(e) {
                return false;
            }
        }''')
        
        if not executed:
            return False
        
        for i in range(30):
            token = await page.evaluate('''() => {
                const textarea = document.querySelector('textarea[name="h-captcha-response"]');
                return textarea ? textarea.value : null;
            }''')
            if token and len(token) > 10:
                return True
            await asyncio.sleep(1)
        
        return False
    except:
        return False

async def check_for_success_indicators(page: Page, initial_url: str, initial_state: dict) -> Tuple[bool, str]:
    """Check for success indicators: green text, URL change, form disappearance, success messages"""
    try:
        # Check 1: URL changed?
        current_url = page.url
        if current_url != initial_url:
            print(f"      ✓ URL changed: {initial_url} → {current_url}")
            return True, "url_change"
        
        # Check 2: Form disappeared?
        new_state = await page.evaluate('''() => {
            const emails = document.querySelectorAll('input[type="email"]');
            return {
                count: emails.length,
                visible: Array.from(emails).filter(e => e.offsetParent !== null).length
            };
        }''')
        
        if new_state['visible'] == 0 and initial_state['visible'] > 0:
            print(f"      ✓ Form disappeared")
            return True, "form_disappeared"
        
        if new_state['count'] < initial_state['count']:
            print(f"      ✓ Form count decreased")
            return True, "form_count_decreased"
        
        # Check 3: Green/success colored text appeared?
        green_text = await page.evaluate('''() => {
            const elements = document.querySelectorAll('*');
            for (const el of elements) {
                const style = window.getComputedStyle(el);
                const color = style.color;
                const bgColor = style.backgroundColor;
                
                // Check for green colors (rgb values where green > red && green > blue)
                const colorMatch = color.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)/);
                const bgMatch = bgColor.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)/);
                
                if (colorMatch) {
                    const [_, r, g, b] = colorMatch.map(Number);
                    if (g > r && g > b && g > 100) {
                        const text = el.innerText.trim();
                        if (text.length > 5 && text.length < 200) {
                            return text;
                        }
                    }
                }
                
                if (bgMatch) {
                    const [_, r, g, b] = bgMatch.map(Number);
                    if (g > r && g > b && g > 100) {
                        const text = el.innerText.trim();
                        if (text.length > 5 && text.length < 200) {
                            return text;
                        }
                    }
                }
            }
            return null;
        }''')
        
        if green_text:
            print(f"      ✓ Green text found: '{green_text[:50]}...'")
            return True, "green_text"
        
        # Check 4: Success message keywords?
        page_text = await page.evaluate('() => document.body.innerText.toLowerCase()')
        for keyword in SUCCESS_KEYWORDS:
            if keyword in page_text:
                print(f"      ✓ Success keyword found: '{keyword}'")
                return True, "success_keyword"
        
        return False, "no_indicators"
        
    except Exception as e:
        print(f"      ⚠️ Error checking indicators: {e}")
        return False, "check_error"

async def nuclear_submit_with_retry(page: Page, submit_elem: Optional[object], all_fields: List) -> bool:
    """Try all 4 submission methods with 40s wait after each"""
    
    print("\n🚀 TRYING SUBMISSION METHODS (40s wait after each)...")
    
    initial_url = page.url
    initial_state = await page.evaluate('''() => {
        const emails = document.querySelectorAll('input[type="email"]');
        return {
            count: emails.length,
            visible: Array.from(emails).filter(e => e.offsetParent !== null).length
        };
    }''')
    
    methods = [
        ("METHOD 1: Playwright click", "playwright"),
        ("METHOD 2: JS element click", "js_elem"),
        ("METHOD 3: JS button search", "js_search"),
        ("METHOD 4: Enter + form.submit", "enter_submit")
    ]
    
    for method_name, method_type in methods:
        print(f"\n   → {method_name}")
        clicked = False
        
        # Close popups before attempting click
        await close_popups_and_overlays(page)
        
        try:
            if method_type == "playwright" and submit_elem:
                try:
                    await submit_elem.scroll_into_view_if_needed()
                    await asyncio.sleep(0.2)
                    await submit_elem.click(force=True)
                    clicked = True
                    print(f"      ✓ Clicked")
                except Exception as e:
                    print(f"      ✗ Failed: {e}")
            
            elif method_type == "js_elem" and submit_elem:
                try:
                    await submit_elem.evaluate('el => el.click()')
                    clicked = True
                    print(f"      ✓ Clicked")
                except Exception as e:
                    print(f"      ✗ Failed: {e}")
            
            elif method_type == "js_search":
                try:
                    clicked = await page.evaluate('''() => {
                        const emails = document.querySelectorAll('input[type="email"]');
                        for (const email of emails) {
                            const container = email.closest('form, div, section');
                            if (container) {
                                const btns = container.querySelectorAll('button, input[type="submit"]');
                                for (const btn of btns) {
                                    if (btn.offsetParent !== null) {
                                        btn.click();
                                        return true;
                                    }
                                }
                            }
                        }
                        return false;
                    }''')
                    print(f"      {'✓' if clicked else '✗'} {'Found button' if clicked else 'No button'}")
                except Exception as e:
                    print(f"      ✗ Failed: {e}")
            
            elif method_type == "enter_submit":
                if all_fields:
                    try:
                        for field_type, field_elem in all_fields:
                            if field_type == 'email':
                                await field_elem.press('Enter')
                                clicked = True
                                print(f"      ✓ Pressed Enter")
                                break
                    except:
                        pass
                
                if not clicked:
                    try:
                        clicked = await page.evaluate('''() => {
                            const forms = document.querySelectorAll('form');
                            for (const form of forms) {
                                if (form.querySelector('input[type="email"]')) {
                                    form.submit();
                                    return true;
                                }
                            }
                            return false;
                        }''')
                        print(f"      {'✓' if clicked else '✗'} {'Called form.submit' if clicked else 'No form'}")
                    except Exception as e:
                        print(f"      ✗ Failed: {e}")
            
            if not clicked:
                print(f"      ⏭️ Skip to next method")
                continue
            
            # Wait 40 seconds with checks every 2s
            print(f"      ⏳ Waiting 40s with success checks...")
            
            for i in range(20):  # 20 checks × 2s = 40s
                await asyncio.sleep(2)
                
                # Close any popups that appear during wait
                await close_popups_and_overlays(page)
                
                success, reason = await check_for_success_indicators(page, initial_url, initial_state)
                
                if success:
                    print(f"      ✅ SUCCESS DETECTED! Reason: {reason} (after {(i+1)*2}s)")
                    return True
            
            print(f"      ❌ No success indicators after 40s")
            print(f"      → Trying next method...")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            continue
    
    print("\n   ❌ ALL 4 METHODS FAILED")
    return False

async def fill_and_submit(page: Page, submit_elem: Optional[object], all_checkboxes: List, 
                          all_fields: List, website_url: str) -> bool:
    """Fill form and submit with retry methods"""
    
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    phone = f"+1{random.randint(2000000000, 9999999999)}"
    
    print(f"\n✍️ Filling: {first_name} {last_name}, {EMAIL_NEWSLETTER}")
    
    initial_url = page.url
    
    try:
        # Close any popups before starting
        await close_popups_and_overlays(page)
        
        # Fill fields
        for field_type, field_elem in all_fields:
            try:
                # Close popups before each field
                await close_popups_and_overlays(page)
                
                value = first_name if field_type == 'fname' else last_name if field_type == 'lname' else EMAIL_NEWSLETTER if field_type == 'email' else phone if field_type == 'phone' else first_name
                await field_elem.scroll_into_view_if_needed()
                await field_elem.click()
                await human_type(field_elem, value)
            except Exception as e:
                print(f"   Field fill error: {e}")
                pass
        
        # Check boxes
        if all_checkboxes:
            for cb in all_checkboxes:
                try:
                    await check_checkbox(cb)
                except:
                    pass
        
        # Close popups before hCaptcha
        await close_popups_and_overlays(page)
        
        # Handle hCaptcha
        await handle_hcaptcha(page)
        
        # Close popups before submit
        await close_popups_and_overlays(page)
        
        # Try all methods
        submission_worked = await nuclear_submit_with_retry(page, submit_elem, all_fields)
        
        success = submission_worked
        
        if success:
            print("\n✅ VERIFIED SUCCESS!")
            submission_status = "success"
            email_found, _ = await check_for_confirmation_email(website_url, wait_minutes=1.0)
            if email_found:
                submission_status = "success_with_email"
            else:
                submission_status = "success_no_email"
        else:
            print("\n❌ SUBMISSION FAILED")
            submission_status = "failed"
        
        # Save to DB
        try:
            website_name = await page.title()
            insert_submission(
                website_name=website_name or "Unknown",
                website_url=website_url,
                email_used=EMAIL_NEWSLETTER,
                submission_status=submission_status,
                captcha_status="hcaptcha_handled" if submission_worked else "not_checked",
                blocked_status=False
            )
        except Exception as e:
            print(f"   DB insert error: {e}")
            pass
        
        return success
    except Exception as e:
        print(f"   Form submission error: {e}")
        return False

async def natural_scroll_down(page: Page):
    """Scroll down naturally"""
    viewport_height = await page.evaluate('() => window.innerHeight')
    await page.evaluate(f'window.scrollBy({{top: {int(viewport_height * 0.7)}, behavior: "smooth"}})')

async def handle_newsletter_page(page: Page) -> bool:
    """Main handler - NO TIMEOUTS on page load"""
    print("\n" + "=" * 70)
    print("🤖 NEWSLETTER AUTOMATION (ENHANCED SUCCESS DETECTION)")
    print(f"📧 Email: {EMAIL_NEWSLETTER}")
    print("⚡ Checks: URL change | Form disappear | Green text | Success keywords")
    print("🛡️ Auto-close: Popups | Modals | Sidebars | Overlays")
    print("=" * 70)

    website_url = page.url
    await wait_for_content_loaded(page)
    await close_popups_and_overlays(page)
    try:
        page_text = await page.evaluate('() => document.body.innerText.toLowerCase()')
        if any(phrase in page_text for phrase in ['sorry, this store is currently unavailable', 'temporarily unavailable']):
            print(f"⚠️ Website unavailable")
            return False
    except:
        pass

    # STEP 1: Look for visible form
    print("\n" + "=" * 70)
    print("STEP 1: Looking for visible form...")
    print("=" * 70)

    submit_elem, all_checkboxes, all_fields = await find_form_with_all_fields(page)

    if all_fields:
        print("\n✅ Visible form found!")
        return await fill_and_submit(page, submit_elem, all_checkboxes, all_fields, website_url)

    # STEP 2: Look for buttons
    print("\n" + "=" * 70)
    print("STEP 2: Looking for newsletter buttons...")
    print("=" * 70)

    triggers = await find_visible_newsletter_triggers(page)

    if not triggers:
        await natural_scroll_down(page)
        await asyncio.sleep(1)
        await close_popups_and_overlays(page)  # Close popups after scroll
        triggers = await find_visible_newsletter_triggers(page)
        if not triggers:
            print("\n❌ No triggers found")
            return False

    # STEP 3: Click trigger
    print("\n" + "=" * 70)
    print("STEP 3: Clicking trigger...")
    print("=" * 70)

    trigger_elem, trigger_text = triggers[0]
    print(f"   Clicking: '{trigger_text}'")
    
    # Close popups before clicking trigger
    await close_popups_and_overlays(page)
    clicked = await human_click(trigger_elem)

    if not clicked:
        return False

    await asyncio.sleep(3)
    
    # Close popups after trigger click
    await close_popups_and_overlays(page)

    submit_elem, all_checkboxes, all_fields = await find_form_with_all_fields(page)

    if all_fields:
        print("\n✅ Form appeared!")
        return await fill_and_submit(page, submit_elem, all_checkboxes, all_fields, website_url)
    else:
        print("\n❌ No form appeared")
        return False