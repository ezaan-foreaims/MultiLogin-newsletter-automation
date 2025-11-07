import asyncio
import random
from typing import Optional, Tuple, List
from playwright.async_api import Page

# ---------------------------
# Keywords
# ---------------------------
NEWSLETTER_KEYWORDS = {
    'en': ['newsletter', 'subscribe', 'signup', 'sign up', 'email', 'updates', 'join', 'stay updated', 'get notified', 'mailing list'],
    'de': ['newsletter', 'abonnieren', 'anmelden', 'registrieren', 'e-mail', 'jetzt anmelden', 'erhalte', 'bleib'],
    'fr': ['newsletter', 'abonner', "s'inscrire", 'inscription', 'email'],
    'es': ['newsletter', 'boletín', 'suscribirse', 'registrarse'],
    'it': ['newsletter', 'iscriviti', 'registrati', 'abbonati'],
    'nl': ['nieuwsbrief', 'abonneren', 'aanmelden'],
    'pt': ['newsletter', 'boletim', 'inscrever'],
    'pl': ['newsletter', 'biuletyn', 'zapisz się'],
    'sv': ['nyhetsbrev', 'prenumerera'],
    'da': ['nyhedsbrev', 'tilmeld'],
    'no': ['nyhetsbrev', 'abonner']
}
ALL_KEYWORDS = list({kw.lower() for kws in NEWSLETTER_KEYWORDS.values() for kw in kws})

SUCCESS_INDICATORS = [
    'thank', 'success', 'subscribed', 'confirm', 'check your email',
    'danke', 'erfolg', 'abonniert', 'bestätigen',
    'merci', 'succès', 'abonné', 'confirmer',
    'gracias', 'éxito', 'suscrito', 'confirmar',
    'grazie', 'successo', 'iscritto', 'conferma'
]

FIRST_NAMES = ["James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Jennifer", "Daniel", "Laura"]
LAST_NAMES = ["Mitchell", "Parker", "Roberts", "Anderson", "Johnson", "Williams", "Brown", "Davis", "Miller", "Wilson"]

# ---------------------------
# Human-like typing with realistic delays
# ---------------------------
async def human_type(element, text: str, wpm: int = 45):
    """Type like a real human with natural pauses and mistakes."""
    await element.fill('')  # Clear first
    await asyncio.sleep(random.uniform(0.3, 0.7))
    
    chars_per_second = (wpm * 5) / 60
    base_delay = 1000 / chars_per_second
    
    for i, char in enumerate(text):
        delay = base_delay * random.uniform(0.7, 1.8)
        
        if random.random() < 0.1:
            delay *= random.uniform(1.5, 3.0)
        
        if char == ' ' or (i > 0 and text[i-1] == ' '):
            delay *= random.uniform(1.2, 1.8)
        
        await element.type(char, delay=delay)
        
        if random.random() < 0.05:
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    await asyncio.sleep(random.uniform(0.3, 0.6))

# ---------------------------
# HUMAN-LIKE CLICK - Natural only
# ---------------------------
async def human_click(element) -> bool:
    """Click like a human - naturally, NO FORCING."""
    try:
        await asyncio.sleep(random.uniform(0.4, 0.9))
        
        await element.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        try:
            await element.hover()
            await asyncio.sleep(random.uniform(0.2, 0.5))
        except:
            pass
        
        await element.click(timeout=5000)
        await asyncio.sleep(random.uniform(0.5, 1.2))
        
        return True
    except Exception as e:
        print(f"     ⚠️ Click failed naturally: {e}")
        return False

# ---------------------------
# FIND VISIBLE ELEMENTS ONLY (NO HONEYPOTS)
# ---------------------------
async def find_visible_newsletter_triggers(page: Page) -> List[Tuple[object, str]]:
    """Find ONLY visible, clickable newsletter triggers. No hidden elements!"""
    print("\n🔍 Looking for VISIBLE newsletter buttons/links...")
    
    # Only look at clickable, visible elements
    selectors = [
        'button',
        'a',
        '[role="button"]',
    ]
    
    found_triggers = []
    
    for selector in selectors:
        try:
            elements = await page.locator(selector).all()
            
            for elem in elements:
                try:
                    # CRITICAL: Check visibility FIRST (avoid honeypots)
                    is_visible = await elem.is_visible()
                    if not is_visible:
                        continue  # Skip hidden elements completely
                    
                    # Get text
                    text = await elem.inner_text()
                    text_lower = text.lower().strip()
                    
                    # Check for newsletter keywords
                    if any(kw in text_lower for kw in ALL_KEYWORDS):
                        print(f"  ✅ Found visible trigger: '{text[:50]}'")
                        found_triggers.append((elem, text))
                
                except:
                    continue
        
        except:
            continue
    
    return found_triggers

# ---------------------------
# FIND VISIBLE NEWSLETTER FORM
# ---------------------------
async def find_visible_newsletter_form(page: Page) -> Tuple[Optional[object], Optional[object], Optional[object], Optional[object], Optional[object]]:
    """Find ONLY visible newsletter forms. No honeypots!"""
    print("\n🔍 Looking for VISIBLE newsletter forms...")
    
    # Only look at email inputs
    email_selectors = [
        'input[type="email"]',
        'input[name*="email" i]',
        'input[placeholder*="email" i]',
    ]
    
    for selector in email_selectors:
        try:
            elements = await page.locator(selector).all()
            
            for email_input in elements:
                try:
                    # CRITICAL: Check visibility FIRST
                    is_visible = await email_input.is_visible()
                    if not is_visible:
                        continue  # Skip hidden forms (honeypots!)
                    
                    # Check context for newsletter keywords
                    context_text = await email_input.evaluate('''el => {
                        let text = '';
                        let current = el;
                        for (let i = 0; i < 4 && current; i++) {
                            text += ' ' + (current.innerText || '');
                            current = current.parentElement;
                        }
                        
                        const form = el.closest('form');
                        if (form) text += ' ' + form.innerText;
                        
                        const label = el.closest('label') || document.querySelector(`label[for="${el.id}"]`);
                        if (label) text += ' ' + label.innerText;
                        
                        text += ' ' + (el.placeholder || '');
                        text += ' ' + (el.getAttribute('aria-label') || '');
                        
                        return text.toLowerCase();
                    }''')
                    
                    # Check if newsletter-related
                    is_newsletter = any(kw in context_text for kw in ALL_KEYWORDS)
                    
                    if is_newsletter:
                        print(f"  ✅ Found VISIBLE newsletter form!")
                        
                        # Find related elements (all must be visible!)
                        submit_btn = None
                        checkbox = None
                        fname = None
                        lname = None
                        
                        # Look for submit button
                        try:
                            parent = email_input.locator('..')
                            buttons = await parent.locator('button').all()
                            for btn in buttons:
                                if await btn.is_visible():
                                    submit_btn = btn
                                    break
                        except:
                            pass
                        
                        # Look for checkbox
                        try:
                            checkboxes = await parent.locator('input[type="checkbox"]').all()
                            for cb in checkboxes:
                                if await cb.is_visible():
                                    checkbox = cb
                                    break
                        except:
                            pass
                        
                        # Look for name fields
                        try:
                            fname_inputs = await parent.locator('input[name*="first" i], input[placeholder*="first" i]').all()
                            for fn in fname_inputs:
                                if await fn.is_visible():
                                    fname = fn
                                    break
                            
                            lname_inputs = await parent.locator('input[name*="last" i], input[placeholder*="last" i]').all()
                            for ln in lname_inputs:
                                if await ln.is_visible():
                                    lname = ln
                                    break
                        except:
                            pass
                        
                        return email_input, submit_btn, checkbox, fname, lname
                
                except:
                    continue
        
        except:
            continue
    
    return None, None, None, None, None

# ---------------------------
# FILL AND SUBMIT
# ---------------------------
async def fill_and_submit(page: Page, email_elem, submit_elem: Optional[object],
                          checkbox_elem: Optional[object], fname_elem: Optional[object],
                          lname_elem: Optional[object], email: str) -> bool:
    """Fill the form naturally like a human."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    print(f"\n✍️ Filling form (human-like):")
    print(f"   Name: {first_name} {last_name}")
    print(f"   Email: {email}")
    
    try:
        # Pause to "read" the form
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Fill first name
        if fname_elem:
            try:
                print("   → Filling first name...")
                await fname_elem.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.3, 0.6))
                await fname_elem.click(timeout=3000)
                await human_type(fname_elem, first_name, wpm=random.randint(40, 55))
            except Exception as e:
                print(f"   ⚠️ Could not fill first name: {e}")
        
        if fname_elem and lname_elem:
            await asyncio.sleep(random.uniform(0.5, 1.0))
        
        # Fill last name
        if lname_elem:
            try:
                print("   → Filling last name...")
                await lname_elem.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.3, 0.6))
                await lname_elem.click(timeout=3000)
                await human_type(lname_elem, last_name, wpm=random.randint(40, 55))
            except Exception as e:
                print(f"   ⚠️ Could not fill last name: {e}")
        
        await asyncio.sleep(random.uniform(0.6, 1.2))
        
        # Fill email
        print("   → Filling email...")
        await email_elem.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.3, 0.6))
        await email_elem.click(timeout=3000)
        await human_type(email_elem, email, wpm=random.randint(45, 60))
        
        # Handle checkbox
        if checkbox_elem:
            try:
                is_checked = await checkbox_elem.is_checked()
                print(f"   → Checkbox: {'checked' if is_checked else 'unchecked'}")
                if not is_checked:
                    print("   → Checking checkbox...")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await checkbox_elem.scroll_into_view_if_needed()
                    await human_click(checkbox_elem)
            except Exception as e:
                print(f"   ⚠️ Could not handle checkbox: {e}")
        
        # Pause before submitting
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # SUBMIT
        print("\n🚀 Submitting...")
        
        if submit_elem:
            print("   → Clicking submit button...")
            clicked = await human_click(submit_elem)
            if not clicked:
                print("   ⚠️ Button click failed, trying Enter...")
                await email_elem.press('Enter')
                await asyncio.sleep(random.uniform(0.5, 1.0))
        else:
            print("   → No submit button, pressing Enter...")
            await asyncio.sleep(random.uniform(0.3, 0.6))
            await email_elem.press('Enter')
            await asyncio.sleep(random.uniform(0.5, 1.0))
        
        # Wait for response
        await asyncio.sleep(random.uniform(2.0, 3.5))
        
        # Check success
        page_text = await page.evaluate('() => document.body.innerText.toLowerCase()')
        url = page.url.lower()
        
        if any(word in page_text for word in SUCCESS_INDICATORS) or any(word in url for word in ['thank', 'success', 'confirm']):
            print("\n✅ SUBMISSION SUCCESSFUL!")
            return True
        
        print("\n⚠️ Submitted (no confirmation detected)")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during submission: {e}")
        return False

# ---------------------------
# NATURAL SCROLL (only if needed)
# ---------------------------
async def natural_scroll_down(page: Page):
    """Scroll down naturally, like reading."""
    print("\n📜 Scrolling down naturally...")
    
    viewport_height = await page.evaluate('() => window.innerHeight')
    scroll_amount = int(viewport_height * random.uniform(0.6, 0.9))
    
    await page.evaluate(f'window.scrollBy({{top: {scroll_amount}, behavior: "smooth"}})')
    await asyncio.sleep(random.uniform(1.0, 1.8))

# ---------------------------
# MAIN HANDLER - HUMAN FLOW
# ---------------------------
async def handle_newsletter_page(page: Page, email: str) -> bool:
    """
    HUMAN FLOW:
    1. Look at current visible page
    2. Find visible newsletter buttons/forms
    3. Click buttons naturally (even if multi-step)
    4. Fill visible forms only
    5. NO HONEYPOT TRAPS
    """
    print("\n" + "=" * 70)
    print("🤖 NEWSLETTER AUTOMATION - HUMAN MODE (Anti-Honeypot)")
    print("=" * 70)
    
    # Natural landing delay
    await asyncio.sleep(random.uniform(1.5, 2.5))
    
    # STEP 1: Check for visible form immediately
    print("\n" + "=" * 70)
    print("STEP 1: Looking for visible newsletter form on current page...")
    print("=" * 70)
    
    email_elem, submit_elem, checkbox_elem, fname_elem, lname_elem = await find_visible_newsletter_form(page)
    
    if email_elem:
        print("\n✅ Visible form found immediately!")
        return await fill_and_submit(page, email_elem, submit_elem, checkbox_elem, fname_elem, lname_elem, email)
    
    # STEP 2: Look for visible newsletter buttons/links
    print("\n" + "=" * 70)
    print("STEP 2: No visible form, looking for newsletter buttons...")
    print("=" * 70)
    
    triggers = await find_visible_newsletter_triggers(page)
    
    if not triggers:
        print("\n❌ No visible triggers found on current viewport")
        
        # STEP 3: Try scrolling down once naturally
        print("\n" + "=" * 70)
        print("STEP 3: Scrolling down to look for more content...")
        print("=" * 70)
        
        await natural_scroll_down(page)
        
        # Try again
        triggers = await find_visible_newsletter_triggers(page)
        
        if not triggers:
            print("\n❌ Still no visible triggers after scroll")
            return False
    
    # STEP 4: Click first visible trigger
    print(f"\n✅ Found {len(triggers)} visible trigger(s)")
    print("   → Clicking first trigger...")
    
    trigger_elem, trigger_text = triggers[0]
    clicked = await human_click(trigger_elem)
    
    if not clicked:
        print("\n❌ Could not click trigger naturally")
        return False
    
    print(f"   ✅ Clicked: '{trigger_text[:50]}'")
    
    # Wait for page to load/modal to appear
    await asyncio.sleep(random.uniform(1.5, 2.5))
    await page.wait_for_load_state('domcontentloaded', timeout=5000)
    
    # STEP 5: Look for form again (might be new page or modal)
    print("\n" + "=" * 70)
    print("STEP 5: Looking for form after clicking trigger...")
    print("=" * 70)
    
    email_elem, submit_elem, checkbox_elem, fname_elem, lname_elem = await find_visible_newsletter_form(page)
    
    if email_elem:
        print("\n✅ Form appeared after click!")
        return await fill_and_submit(page, email_elem, submit_elem, checkbox_elem, fname_elem, lname_elem, email)
    
    # STEP 6: Maybe it's another button? Try clicking again
    print("\n⚠️ No form yet, looking for more triggers on new page...")
    
    triggers = await find_visible_newsletter_triggers(page)
    
    if triggers:
        print(f"   → Found {len(triggers)} more trigger(s), clicking first...")
        trigger_elem, trigger_text = triggers[0]
        clicked = await human_click(trigger_elem)
        
        if clicked:
            print(f"   ✅ Clicked: '{trigger_text[:50]}'")
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Final attempt
            email_elem, submit_elem, checkbox_elem, fname_elem, lname_elem = await find_visible_newsletter_form(page)
            
            if email_elem:
                print("\n✅ Form found after second click!")
                return await fill_and_submit(page, email_elem, submit_elem, checkbox_elem, fname_elem, lname_elem, email)
    
    print("\n" + "=" * 70)
    print("❌ FAILED: Could not find visible newsletter form")
    print("=" * 70)
    return False