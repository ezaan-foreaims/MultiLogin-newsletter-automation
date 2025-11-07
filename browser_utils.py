import asyncio, random
from playwright.async_api import async_playwright

async def human_type(element, text, wpm=60):
    cps = (wpm*5)/60
    base_delay = 1000/cps
    for c in text:
        delay = base_delay*random.uniform(0.6,1.4)
        if c==' ': delay*=random.uniform(1.5,2.5)
        await element.type(c, delay=delay)
        if random.random()<0.02: await element.press('Backspace')

async def human_delay(min_ms=500,max_ms=2000):
    await asyncio.sleep(random.uniform(min_ms,max_ms)/1000)

async def connect_to_browser(cdp_endpoint, max_retries=12):
    for attempt in range(max_retries):
        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
            return pw, browser
        except:
            await asyncio.sleep(2+0.5*attempt)
    return None, None
