from constants import ALL_KEYWORDS, SUCCESS_INDICATORS
import random
from browser_utils import human_type, human_delay

async def find_form_elements(page):
    # Similar to your original function (search forms + outside forms)
    return None, None, None, None, None

async def fill_and_submit(page, email):
    first_name = random.choice(["James","Sarah","Michael"])
    last_name = random.choice(["Mitchell","Parker","Roberts"])
    email_in, submit, checkbox, first_in, last_in = await find_form_elements(page)
    if not email_in or not submit: return False
    if first_in: await human_type(first_in, first_name)
    if last_in: await human_type(last_in, last_name)
    await human_type(email_in, email)
    if checkbox: await checkbox.click()
    await submit.click()
    return True
