# MultiLogin-newsletter-automation
# MultiLogin Newsletter Automation

Automate newsletter signups using **MultiLogin** and **Playwright** with human-like behavior.  
Supports multi-language websites, smart form detection, and multiple submission strategies.

---

## Features

- Human-like typing (40–70 WPM)
- Multi-language support (EN, DE, FR, ES, IT, NL, PT, PL, SV, DA, NO)
- Smart form detection (inside and outside `<form>` tags)
- Multiple submission strategies (Enter key, click, JS click, form submit)
- Enhanced error handling
- Rotation of profiles and emails
- Logs results and saves to JSON

---

## Requirements

- Python 3.10+
- MultiLogin installed
- Playwright installed (Chromium)

Python dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
