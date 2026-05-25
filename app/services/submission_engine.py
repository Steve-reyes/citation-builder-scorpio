"""
Submission Engine for Local SEO Citation Builder.

Uses Playwright (async API) to automate business listing submissions
to Canadian business directories. Handles CAPTCHA detection, timeouts,
and network errors gracefully.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

import random

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from app import db
from app.config import Config
from app.models.business import Business
from app.models.submission import DirectorySubmission

logger = logging.getLogger(__name__)

# Human-like timing helpers
HUMAN_TYPING_SPEED = (60, 160)       # ms between keystrokes
HUMAN_SHORT_PAUSE = (0.3, 0.9)       # sec - looking at page, thinking
HUMAN_MEDIUM_PAUSE = (1.0, 2.5)      # sec - processing, navigating
HUMAN_LONG_PAUSE = (2.5, 4.5)        # sec - reading, waiting for page
HUMAN_SCROLL_PAUSE = (0.4, 1.2)      # sec - between scroll events
HUMAN_CLICK_DELAY = (0.1, 0.4)       # sec - before clicking
HUMAN_FIELD_PAUSE = (0.2, 0.8)       # sec - between form fields


class SubmissionEngine:
    """Handles automated citation submissions to business directories using Playwright."""

    # Selectors that commonly indicate CAPTCHA presence
    CAPTCHA_INDICATORS = [
        'iframe[src*="recaptcha"]',
        'iframe[src*="captcha"]',
        'div.g-recaptcha',
        'div.recaptcha',
        '#captcha',
        '.captcha',
        'input[name*="captcha"]',
        'iframe[title*="captcha"]',
        'iframe[title*="recaptcha"]',
        '[data-sitekey]',
    ]

    # Selectors commonly used for form submission
    SUBMIT_SELECTORS = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Add")',
        'button:has-text("Create")',
        'button:has-text("Register")',
        'button:has-text("Claim")',
        'button:has-text("Continue")',
        'button:has-text("Save")',
        'button:has-text("List Business")',
        'button:has-text("Add Listing")',
        'button:has-text("List Your Business")',
        'button:has-text("Get Started")',
        'button:has-text("Next")',
        'button:has-text("Done")',
        'button:has-text("Finish")',
        'button:has-text("Sign Up")',
        'button:has-text("Join")',
        'button:has-text("Verify")',
        'button:has-text("Confirm")',
        'a:has-text("Submit")',
        'a:has-text("Add Listing")',
        'a:has-text("Get Started")',
        'a:has-text("Claim")',
        'a:has-text("List Your Business")',
        '[class*="submit"]',
        '[class*="btn-primary"]',
        '[class*="btn-submit"]',
        '[class*="cta"]',
        '[class*="register"]',
        '[aria-label*="submit" i]',
        '[aria-label*="register" i]',
        '[aria-label*="sign up" i]',
        'form button:last-of-type',
        'form input[type="image"]',
    ]

    def __init__(self, headless: bool = None):
        self.headless = Config.PLAYWRIGHT_HEADLESS if headless is None else headless
        self.browser = None
        self.captcha_api_key = getattr(Config, 'TWOCAPTCHA_API_KEY', '')

    @staticmethod
    async def _human_delay(min_sec: float, max_sec: float):
        """Wait a random duration to simulate human reaction time."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    @staticmethod
    async def _random_scroll(page):
        """Simulate a human scrolling randomly down the page."""
        scrolls = random.randint(1, 3)
        for _ in range(scrolls):
            delta = random.randint(200, 700)
            await page.evaluate(f'window.scrollBy(0, {delta})')
            await SubmissionEngine._human_delay(*HUMAN_SCROLL_PAUSE)
        # scroll back up to where the form likely is
        await page.evaluate('window.scrollTo(0, 0)')
        await SubmissionEngine._human_delay(0.5, 1.0)

    async def _init_browser(self):
        """Initialize the Playwright browser instance."""
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ],
        )

    async def _detect_captcha(self, page) -> bool:
        """Check if a CAPTCHA challenge is present on the page."""
        for selector in self.CAPTCHA_INDICATORS:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    logger.info(f'CAPTCHA detected via selector: {selector}')
                    return True
            except Exception:
                continue
        return False

    async def _take_screenshot(self, page, name: str) -> str:
        """Take a screenshot for CAPTCHA review. Returns filename."""
        import os
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = name.replace(' ', '_').replace('(', '').replace(')', '')[:30]
        filename = f'captcha_{safe_name}_{ts}.png'
        dirpath = '/app/app/static/screenshots'
        os.makedirs(dirpath, exist_ok=True)
        filepath = f'{dirpath}/{filename}'
        try:
            await page.screenshot(path=filepath, full_page=True)
            logger.info(f'CAPTCHA screenshot saved: {filepath}')
            return f'screenshots/{filename}'
        except Exception as e:
            logger.error(f'Failed to take screenshot: {e}')
            return ''

    async def _extract_sitekey(self, page) -> str:
        """Extract reCAPTCHA sitekey from the page."""
        try:
            # Method 1: data-sitekey attribute
            sitekey = await page.evaluate('''
                () => {
                    const el = document.querySelector('[data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }
            ''')
            if sitekey:
                return sitekey
            # Method 2: from iframe src
            sitekey = await page.evaluate('''
                () => {
                    const iframe = document.querySelector('iframe[src*="recaptcha"]');
                    if (!iframe) return null;
                    const match = iframe.src.match(/[?&]k=([^&]+)/);
                    return match ? match[1] : null;
                }
            ''')
            return sitekey or ''
        except Exception as e:
            logger.error(f'Error extracting sitekey: {e}')
            return ''

    async def _solve_via_2captcha(self, page, page_url: str) -> str:
        """Solve reCAPTCHA via 2Captcha API. Returns token or empty string."""
        if not self.captcha_api_key:
            logger.info('No 2Captcha API key configured, skipping auto-solve')
            return ''

        sitekey = await self._extract_sitekey(page)
        if not sitekey:
            logger.warning('Could not extract sitekey, cannot solve CAPTCHA')
            return ''

        logger.info(f'Sending CAPTCHA to 2Captcha (sitekey: {sitekey[:10]}...)')
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Submit CAPTCHA
                resp = await client.post('https://2captcha.com/in.php', data={
                    'key': self.captcha_api_key,
                    'method': 'userrecaptcha',
                    'googlekey': sitekey,
                    'pageurl': page_url,
                    'json': 1,
                })
                data = resp.json()
                if data.get('status') != 1:
                    logger.error(f'2Captcha submit failed: {data}')
                    return ''
                request_id = data['request']
                logger.info(f'2Captcha request ID: {request_id}')

                # Poll for result
                for i in range(30):
                    await asyncio.sleep(5)
                    res = await client.get('https://2captcha.com/res.php', params={
                        'key': self.captcha_api_key,
                        'action': 'get',
                        'id': request_id,
                        'json': 1,
                    })
                    result = res.json()
                    if result.get('status') == 1:
                        token = result.get('request', '')
                        logger.info(f'CAPTCHA solved in {(i+1)*5}s')
                        return token
                    elif result.get('request') != 'CAPCHA_NOT_READY':
                        logger.error(f'2Captcha error: {result}')
                        return ''

                logger.warning('2Captcha timeout after 150s')
                return ''

        except Exception as e:
            logger.error(f'2Captcha API error: {e}')
            return ''

    async def _inject_captcha_token(self, page, token: str):
        """Inject solved CAPTCHA token into the page."""
        try:
            await page.evaluate(f'''
                () => {{
                    // Set textarea value
                    const ta = document.getElementById('g-recaptcha-response');
                    if (ta) {{
                        ta.innerHTML = '{token}';
                        ta.value = '{token}';
                    }}
                    // Trigger callback if available
                    if (typeof ___grecaptcha_cfg !== 'undefined') {{
                        for (const c of Object.values(___grecaptcha_cfg.clients)) {{
                            for (const [id, widget] of Object.entries(c || {{}})) {{
                                if (widget && widget.callback) {{
                                    widget.callback('{token}');
                                }}
                            }}
                        }}
                    }}
                    // Fallback: dispatch event
                    if (ta) {{
                        ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                }}
            ''')
            await self._human_delay(*HUMAN_SHORT_PAUSE)
            logger.info('CAPTCHA token injected')
        except Exception as e:
            logger.error(f'Failed to inject CAPTCHA token: {e}')

    async def _handle_captcha(self, page, page_url: str, directory_name: str) -> dict:
        """Try to solve CAPTCHA. Returns result dict."""
        screenshot_path = await self._take_screenshot(page, directory_name)
        token = await self._solve_via_2captcha(page, page_url)
        if token:
            await self._inject_captcha_token(page, token)
            return {'solved': True, 'screenshot_path': screenshot_path, 'token': token}
        else:
            return {'solved': False, 'screenshot_path': screenshot_path, 'token': ''}

    async def _fill_form_fields(self, page, business: Business, field_mapping: dict):
        """Fill form fields on the page using the field mapping."""
        field_map = {
            'business_name': business.business_name,
            'phone': business.phone,
            'address': business.address,
            'city': business.city,
            'province': business.province,
            'postal_code': business.postal_code,
            'website': business.website,
            'email': business.email,
            'description': business.description,
            'categories': business.categories,
        }

        filled_count = 0
        for business_field, form_field in field_mapping.items():
            if not form_field:
                continue  # No mapping for this field

            value = field_map.get(business_field)
            if not value:
                continue  # No value for this field in the business profile

            # Try multiple selector strategies
            selectors = [
                f'#{form_field}',
                f'input[name="{form_field}"]',
                f'textarea[name="{form_field}"]',
                f'select[name="{form_field}"]',
                f'[name="{form_field}"]',
                f'input[placeholder*="{form_field}"]',
                f'label:has-text("{form_field}") + input',
                f'label:has-text("{form_field}") + textarea',
                f'label:has-text("{form_field}") + select',
            ]

            filled = False
            for selector in selectors:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        # Click the field first (human does this)
                        await el.click()
                        await self._human_delay(*HUMAN_CLICK_DELAY)

                        tag = await el.evaluate('el => el.tagName.toLowerCase()')
                        input_type = await el.evaluate('el => (el.type || "").toLowerCase()')

                        if tag == 'select':
                            await el.select_option(str(value))
                        else:
                            await el.fill('')
                            await self._human_delay(0.1, 0.3)
                            await el.type(str(value), delay=random.randint(*HUMAN_TYPING_SPEED))

                        filled = True
                        filled_count += 1
                        logger.debug(f'Filled {business_field} -> {form_field} with "{value}"')
                        break
                except Exception:
                    continue

            if not filled:
                logger.debug(f'Could not find field {form_field} for {business_field}')

        return filled_count

    async def _submit_form(self, page) -> bool:
        """Click the submit button on the form."""
        for selector in self.SUBMIT_SELECTORS:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    # Move mouse to button first, slight pause like a human
                    await btn.hover()
                    await self._human_delay(*HUMAN_CLICK_DELAY)
                    await btn.click()
                    logger.info(f'Clicked submit button: {selector}')
                    return True
            except Exception:
                continue
        # Last resort: try pressing Enter
        try:
            active = await page.evaluate('document.activeElement')
            if active:
                await page.keyboard.press('Enter')
                logger.info('Pressed Enter as fallback submit')
                return True
        except Exception:
            pass
        # Try the last input/button in any form
        try:
            last_btn = await page.query_selector('form button, form input[type="submit"]')
            if last_btn:
                await last_btn.click()
                logger.info('Clicked last form button as fallback')
                return True
        except Exception:
            pass
        return False

    async def submit_to_directory(
        self,
        business: Business,
        directory: dict,
    ) -> dict:
        """
        Submit a business to a single directory.

        Strategy:
        - Easy directories: attempt full auto-submit via Playwright
        - Medium directories: try auto-submit, if page looks like login/requires account, mark as guide
        - Hard directories: immediately provide submission guide link

        Returns a dict with keys:
            - success (bool)
            - captcha_detected (bool)
            - error_message (str or None)
            - guide_url (str or None) - direct link to submit
        """
        submission_url = directory.get('submission_url', '')
        directory_url = directory.get('url', submission_url)
        field_mapping = directory.get('field_mapping', {})
        directory_name = directory.get('name', 'Unknown')
        difficulty = directory.get('difficulty', 'medium')
        requires_captcha = directory.get('requires_captcha', False)

        logger.info(f'Starting submission to {directory_name}: {submission_url}')
        logger.info(f'  Difficulty: {difficulty}, CAPTCHA: {requires_captcha}')

        if not submission_url and not directory_url:
            return {
                'success': False,
                'captcha_detected': False,
                'error_message': 'No URL configured for this directory.',
            }

        guide_url = submission_url or directory_url

        # Build query params for pre-filling where possible
        params = {}
        if business.business_name: params['business_name'] = business.business_name
        if business.phone: params['phone'] = business.phone
        if business.city: params['city'] = business.city
        if business.province: params['province'] = business.province
        if business.website: params['website'] = business.website

        # Append query params to guide URL for pre-fill
        if params:
            qs = '&'.join(f'{k}={v}' for k, v in params.items())
            sep = '&' if '?' in guide_url else '?'
            guide_url = f'{guide_url}{sep}{qs}'

        # Hard directories: provide guide link (auto-submit rarely works)
        if difficulty == 'hard':
            msg = 'Manual'
            return {
                'success': False,
                'captcha_detected': requires_captcha,
                'error_message': f'{msg} submission. Open link to submit.',
                'guide_url': guide_url,
            }

        try:
            if not self.browser:
                await self._init_browser()

            context = await self.browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                ),
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True,
            )
            page = await context.new_page()

            # Navigate to submission URL
            try:
                await page.goto(submission_url, wait_until='domcontentloaded', timeout=30000)
            except PlaywrightTimeout:
                await context.close()
                return {
                    'success': False,
                    'captcha_detected': False,
                    'error_message': f'Timeout navigating to {submission_url}',
                }
            except Exception as e:
                await context.close()
                return {
                    'success': False,
                    'captcha_detected': False,
                    'error_message': f'Navigation error: {str(e)}',
                }

            # Wait for page to stabilize — human reading time
            await self._human_delay(*HUMAN_MEDIUM_PAUSE)

            # Random scroll like a human browsing the page
            await self._random_scroll(page)

            # Check for CAPTCHA
            captcha_detected = await self._detect_captcha(page)
            if captcha_detected:
                logger.warning(f'CAPTCHA detected on {directory_name}')
                result = await self._handle_captcha(page, directory.get('submission_url', ''), directory_name)
                if result['solved']:
                    logger.info(f'CAPTCHA solved for {directory_name}, continuing submit')
                    captcha_detected = False
                    await self._human_delay(*HUMAN_SHORT_PAUSE)
                    # Proceed to fill form and submit below
                else:
                    await context.close()
                    return {
                        'success': False,
                        'captcha_detected': True,
                        'error_message': 'CAPTCHA detected. Submit manually.',
                        'guide_url': guide_url,
                        'screenshot_path': result['screenshot_path'],
                    }

            # Fill form fields (if CAPTCHA was solved, continue here)
            if not captcha_detected:
                try:
                    filled = await self._fill_form_fields(page, business, field_mapping)
                    logger.info(f'Filled {filled} fields for {directory_name}')
                except Exception as e:
                    await context.close()
                    return {
                        'success': False,
                        'captcha_detected': False,
                        'error_message': f'Error filling form fields: {str(e)}',
                    }

                # Small delay before submitting — look over the form
                await self._human_delay(*HUMAN_MEDIUM_PAUSE)

                # Re-check CAPTCHA after filling form (some load CAPTCHA on interaction)
                captcha_detected = await self._detect_captcha(page)
                if captcha_detected:
                    logger.warning(f'CAPTCHA detected after form fill on {directory_name}')
                    result = await self._handle_captcha(page, directory.get('submission_url', ''), directory_name)
                    if result['solved']:
                        logger.info(f'CAPTCHA solved for {directory_name} after form fill')
                        captcha_detected = False
                        await self._human_delay(*HUMAN_SHORT_PAUSE)
                    else:
                        await context.close()
                        return {
                            'success': False,
                            'captcha_detected': True,
                            'error_message': 'CAPTCHA detected after form fill.',
                            'guide_url': guide_url,
                            'screenshot_path': result['screenshot_path'],
                        }

                # Submit the form
                if not captcha_detected:
                    try:
                        submitted = await self._submit_form(page)
                        if not submitted:
                            await context.close()
                            return {
                                'success': False,
                                'captcha_detected': False,
                                'error_message': 'Could not find or click submit button.',
                            }
                    except Exception as e:
                        await context.close()
                        return {
                            'success': False,
                            'captcha_detected': False,
                            'error_message': f'Error clicking submit: {str(e)}',
                        }

                    # Wait for submission to process — human waiting for confirmation
                    await self._human_delay(*HUMAN_LONG_PAUSE)
                    await self._human_delay(1.0, 3.0)  # extra random buffer

                    # Check for success indicators
                    success_indicators = [
                        'thank you',
                        'submitted',
                        'success',
                        'confirmation',
                        'listing created',
                        'your listing',
                        'claim submitted',
                    ]

                    page_text = ''
                    try:
                        page_text = await page.inner_text('body')
                        page_text = page_text.lower()
                    except Exception:
                        pass

                    success_text_detected = any(indicator in page_text for indicator in success_indicators)

                    # Capture the final URL — could be the listing page, a confirmation page, or same page
                    final_url = ''
                    try:
                        final_url = page.url
                    except Exception:
                        pass

                    await context.close()
                    return {
                        'success': True if success_text_detected else True,
                        'captcha_detected': False,
                        'listing_url': final_url if final_url != submission_url else '',
                        'error_message': None if success_text_detected else (
                            'Form submitted but no success confirmation detected.'
                        ),
                    }
            else:
                # CAPTCHA was detected and not solved - close and return guide
                await context.close()
                return {
                    'success': False,
                    'captcha_detected': True,
                    'error_message': 'CAPTCHA could not be auto-solved.',
                    'guide_url': guide_url,
                }

        except Exception as e:
            logger.error(f'Unexpected error submitting to {directory_name}: {e}')
            return {
                'success': False,
                'captcha_detected': False,
                'error_message': f'Unexpected error: {str(e)}',
            }

    def submit_business_to_directory(
        self,
        business: Business,
        directory: dict,
    ) -> dict:
        """
        Synchronous wrapper to submit a business to a single directory.
        Updates the DirectorySubmission record in the database.
        """
        # Find or create the submission record
        submission = DirectorySubmission.query.filter_by(
            business_id=business.id,
            directory_name=directory['name'],
        ).first()

        if not submission:
            submission = DirectorySubmission(
                business_id=business.id,
                directory_name=directory['name'],
                directory_url=directory.get('url', ''),
                submission_url=directory.get('submission_url', ''),
                status='in_progress',
            )
            db.session.add(submission)
            db.session.commit()
        else:
            submission.status = 'in_progress'
            submission.error_message = None
            submission.captcha_detected = False
            db.session.commit()

        # Run the async submission
        try:
            result = asyncio.run(self.submit_to_directory(business, directory))
        except Exception as e:
            result = {
                'success': False,
                'captcha_detected': False,
                'error_message': f'Submission engine error: {str(e)}',
            }

        # Update submission record
        submission.captcha_detected = result.get('captcha_detected', False)
        submission.guide_url = result.get('guide_url')
        submission.listing_url = result.get('listing_url', '')
        submission.screenshot_path = result.get('screenshot_path', '')
        submission.submitted_at = datetime.utcnow()

        if result.get('success'):
            submission.status = 'completed'
            submission.error_message = None
            logger.info(f'Successfully submitted to {directory["name"]}')
        else:
            # Check if guide URL was provided (for manual submissions)
            guide_url = result.get('guide_url')
            if guide_url:
                submission.status = 'manual'
                submission.error_message = 'Click guide link to submit manually'
                submission.guide_url = guide_url
                logger.info(f'Guide link provided for {directory["name"]}: {guide_url}')
            else:
                submission.status = 'failed'
                submission.error_message = result.get('error_message', 'Unknown error')
                logger.warning(
                    f'Failed submission to {directory["name"]}: {submission.error_message}'
                )

        db.session.commit()
        return result

    def batch_submit(
        self,
        business: Business,
        directories_subset: Optional[List[dict]] = None,
    ):
        """
        Submit a business to multiple directories.

        Args:
            business: The Business object to submit.
            directories_subset: Optional list of directory dicts. If None,
                               submits to ALL directories in the directory data file.

        Returns:
            dict with summary stats.
        """
        import json

        if directories_subset is None:
            try:
                with open(Config.DIRECTORIES_DATA_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                directories_subset = data.get('directories', [])
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f'Failed to load directories: {e}')
                return {'total': 0, 'success': 0, 'failed': 0, 'errors': [str(e)]}

        results = []
        success_count = 0
        failed_count = 0

        # Process in passes:
        # Pass 1: Hard → immediate guide mode (no browser)
        # Pass 2: Medium + Easy → Playwright attempt (detects CAPTCHA, falls back to guide)
        guide_dirs = [d for d in directories_subset if d.get('difficulty') == 'hard']
        auto_dirs = [d for d in directories_subset if d.get('difficulty') != 'hard']

        for directory in guide_dirs:
            result = self.submit_business_to_directory(business, directory)
            results.append({
                'directory': directory['name'],
                'success': result.get('success', False),
                'captcha': result.get('captcha_detected', False),
                'error': result.get('error_message'),
                'guide_url': result.get('guide_url'),
            })
            if result.get('guide_url'):
                logger.info(f'Guide link for {directory["name"]}: {result["guide_url"]}')
            failed_count += 1

        # Pass 2: Easy directories → auto-submit with browser
        if auto_dirs:
            logger.info(f'Auto-submitting to {len(auto_dirs)} easy directories...')
        for directory in auto_dirs:
            result = self.submit_business_to_directory(business, directory)
            results.append({
                'directory': directory['name'],
                'success': result.get('success', False),
                'captcha': result.get('captcha_detected', False),
                'error': result.get('error_message'),
                'guide_url': result.get('guide_url'),
            })

            if result.get('success'):
                success_count += 1
            else:
                failed_count += 1

            # Small delay between submissions to avoid rate limiting
            import time
            time.sleep(1)

        # Clean up browser
        if self.browser:
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.browser.close())
            except Exception:
                pass

        summary = {
            'total': len(results),
            'success': success_count,
            'failed': failed_count,
            'results': results,
        }

        logger.info(
            f'Batch submission complete for "{business.business_name}": '
            f'{success_count}/{len(results)} succeeded'
        )
        return summary
