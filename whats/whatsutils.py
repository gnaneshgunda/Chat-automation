"""
whats/whatsutils.py — Core WhatsApp Web automation helpers.

Root-cause fix for "contact opens but message not sent":
  - Added handling for the "Continue to chat" dialog (appears for unknown contacts).
  - Multiple fallback selectors for the message input box (aria-label varies by
    WhatsApp version / browser locale).
  - Click send button explicitly instead of relying solely on Keys.RETURN.
  - Added small sleep after typing so WhatsApp registers the text before sending.
  - Replaced implicitly_wait(100) with WebDriverWait(30) everywhere.
"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import logging
import time
import os
import shutil
import tempfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Attach button: WhatsApp Web has changed this selector repeatedly ──────────
# Strategy A: click the button, then pick file from the hidden input
# Strategy B: JS-inject the file directly into the hidden input (bypasses menu)
_ATTACH_BTN_SELECTORS = [
    '//span[@data-icon="attach-menu-plus"]/..',          # current WA Web (2024–25)
    '//*[@data-icon="attach-menu-plus"]',
    '//span[@data-icon="clip"]/..',
    '//button[@aria-label="Attach"]',                   # older versions
    '//div[@title="Attach"]',
]

# ── "Photos & Videos" menu item inside the attach popup ───────────────────────
# Clicking this explicitly ensures we take the PHOTO path, not the sticker path.
_PHOTOS_BTN_SELECTORS = [
    '//span[text()="Photos & Videos"]',
    '//span[text()="Photos & videos"]',
    '//div[text()="Photos & Videos"]',
    '//div[text()="Photos & videos"]',
    '//span[contains(text(),"Photo") and contains(text(),"Video")]',
    '//li[.//span[contains(text(),"Photo")]]',
    '//span[contains(text(),"Photo")]',
    '//li[contains(.,"Photo")]',
]

# ── Photo/video file inputs ────────────────────────────────────────────────────
# NOTE: WA Web has MULTIPLE hidden file inputs in DOM at all times:
#   • Photo/Video input  — accept="image/*,video/mp4,..." (with multiple video types)
#   • Sticker input      — accept="image/webp" or "image/*" only
#   • Document input     — accept="*" or doc-only mime types
# We must target the photo input specifically. data-testid selectors are most
# reliable; accept-attribute selectors are fallbacks.
# NOTE: In Chrome 148 / WA Web June 2025, the photo input accept is:
#   "image/*,video/mp4,video/3gpp,video/quicktime,video/webm,video/x-matroska"
_PHOTO_INPUT_SELECTORS = [
    # data-testid (most stable across updates)
    '//input[@data-testid="photo-picker-input"]',
    '//input[@data-testid="media-input"]',
    '//input[@data-testid="photo-video-input"]',
    # Current WA Web (Chrome 148, June 2025) — exact accept string
    '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime,video/webm,video/x-matroska"]',
    # Older exact strings
    '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]',
    '//input[@accept="image/*,video/*"]',
    # Any input with multiple video types (photo/video, not sticker)
    '//input[contains(@accept,"video/mp4") and contains(@accept,"image")]',
    '//input[contains(@accept,"video/") and contains(@accept,"image")]',
]

# Keep for Strategy B/C fallback
_FILE_INPUT_ACCEPT = [
    'image/*,video/mp4,video/3gpp,video/quicktime,video/webm,video/x-matroska',
    'image/*,video/mp4,video/3gpp,video/quicktime',
    'image/*,video/*',
    'image/*',
]

# ── Message input: try these in order until one works ─────────────────────────
_MSG_INPUT_SELECTORS = [
    '//div[@aria-label="Type a message" and @contenteditable="true"]',
    '//div[@aria-label="Message" and @contenteditable="true"]',
    '//div[@title="Type a message" and @contenteditable="true"]',
    '//footer//div[@contenteditable="true"]',
    '//div[@data-tab="10" and @contenteditable="true"]',   # older WA Web fallback
]

# ── Send button: try these in order ───────────────────────────────────────────
_SEND_BTN_SELECTORS = [
    '//button[@aria-label="Send"]',
    '//span[@data-icon="send"]',
    '//div[@aria-label="Send"]',
]

# ── "Continue to chat" dialog (appears for unknown / unsaved contacts) ────────
_CONTINUE_SELECTORS = [
    '//span[text()="Continue to chat"]',
    '//div[text()="Continue to chat"]',
    '//button[contains(.,"Continue to chat")]',
]

# ── Invalid number error text ──────────────────────────────────────────────────
_INVALID_PHONE_XPATHS = [
    '//div[contains(text(),"Phone number shared via url is invalid")]',
    '//div[contains(text(),"phone number is not valid")]',
]

# ── Caption box: EXCLUSIVE to the media preview panel ────────────────────────
# WA Web 2025 uses Lexical editor (data-lexical-editor="true") for caption too.
# The compose box has data-testid="conversation-compose-box-input".
# We exclude that to ensure we're targeting the MEDIA PANEL caption only.
_CAPTION_SELECTORS = [
    # data-testid based (ideal)
    '//div[@data-testid="photo-picker-media-caption-input"]',
    '//div[@data-testid="media-caption-input-container"]//div[@contenteditable="true"]',
    # aria-label based
    '//div[@aria-label="Add a caption" and @contenteditable="true"]',
    '//div[@aria-label="Add a caption..." and @contenteditable="true"]',
    '//div[@aria-label="Caption" and @contenteditable="true"]',
    '//div[contains(@aria-label,"caption") and @contenteditable="true"]',
    '//div[contains(@aria-label,"Caption") and @contenteditable="true"]',
    # aria-placeholder based (Lexical editor uses this instead of aria-label)
    '//div[@aria-placeholder="Add a caption" and @contenteditable="true"]',
    '//div[@aria-placeholder="Add a caption..." and @contenteditable="true"]',
    '//div[contains(@aria-placeholder,"caption") and @contenteditable="true"]',
    '//div[contains(@aria-placeholder,"Caption") and @contenteditable="true"]',
    # Lexical editor div that is NOT the compose box
    '//div[@data-lexical-editor="true" and @contenteditable="true" and not(@data-testid="conversation-compose-box-input")]',
    # role=textbox that is NOT the compose box
    '//div[@role="textbox" and @contenteditable="true" and not(@data-testid="conversation-compose-box-input")]',
]


def _copy_profile(src: str) -> str:
    """Copy a browser profile to a temp dir so the original isn't locked."""
    tmp = tempfile.mkdtemp(prefix="wa_profile_")
    shutil.copytree(src, os.path.join(tmp, "Default"), dirs_exist_ok=True)
    return tmp


def get_browser(browser_choice: str):
    """
    Launch a browser pre-loaded with the user's existing WhatsApp Web session.

    ┌─────────────────────────────────────────────────────────────────────────┐
    │  Browser Notes                                                          │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  Chrome  — chromedriver must match your Chrome version.                 │
    │  Edge    — msedgedriver must match your Edge version.                   │
    │  Firefox — geckodriver must be in your PATH.  WhatsApp may show a      │
    │            "use a supported browser" banner — this is cosmetic only,    │
    │            sending still works.  Close Firefox before running or the    │
    │            profile copy will fail with a "profile in use" error.        │
    └─────────────────────────────────────────────────────────────────────────┘
    """
    if browser_choice == "Chrome":
        src = os.path.expanduser("~/.config/google-chrome/Default")
        if not os.path.exists(src):
            raise FileNotFoundError(
                "Chrome profile not found at ~/.config/google-chrome/Default.\n"
                "Open Chrome, go to web.whatsapp.com, and scan the QR code first."
            )
        opts = webdriver.ChromeOptions()
        opts.add_argument(f"--user-data-dir={_copy_profile(src)}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        return webdriver.Chrome(options=opts)

    elif browser_choice == "Firefox":
        # ⚠️ Needs geckodriver in PATH: https://github.com/mozilla/geckodriver/releases
        profile_base = os.path.expanduser("~/.mozilla/firefox")
        opts = webdriver.FirefoxOptions()
        if os.path.exists(profile_base):
            profiles = [
                d for d in os.listdir(profile_base)
                if "default" in d.lower() and os.path.isdir(os.path.join(profile_base, d))
            ]
            if profiles:
                src = os.path.join(profile_base, profiles[0])
                tmp = tempfile.mkdtemp(prefix="wa_ff_profile_")
                shutil.copytree(src, tmp, dirs_exist_ok=True)
                opts.add_argument("--profile")   # ← correct flag (not -profile)
                opts.add_argument(tmp)
            else:
                logger.warning("No Firefox default profile found — you will need to scan QR code.")
        # Firefox does NOT support excludeSwitches / useAutomationExtension
        return webdriver.Firefox(options=opts)

    else:  # Edge (default)
        src = os.path.expanduser("~/.config/microsoft-edge/Default")
        if not os.path.exists(src):
            raise FileNotFoundError(
                "Edge profile not found at ~/.config/microsoft-edge/Default.\n"
                "Open Edge, go to web.whatsapp.com, and scan the QR code first."
            )
        opts = webdriver.EdgeOptions()
        opts.add_argument(f"--user-data-dir={_copy_profile(src)}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        return webdriver.Edge(options=opts)


def _find_element_any(driver, selectors: list, timeout: int = 20):
    """Try each XPath selector in order; return the first match or None."""
    per = max(1, timeout / len(selectors))
    for xpath in selectors:
        try:
            el = WebDriverWait(driver, per).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            logger.debug(f"Selector matched: {xpath}")
            return el
        except Exception:
            continue
    return None


def _attach_photo_file(webd, abs_path: str) -> bool:
    """
    After the attach menu is open, click 'Photos & Videos' then inject the file.
    Returns True if the file was successfully injected into the PHOTO input.
    Returns False if the photo file input could not be found/used.

    This is separated so Strategy A can call it after opening the menu.
    """
    # Step 1: Try to click "Photos & Videos" menu item to ensure we're on
    # the photo path (not sticker/document path).
    photos_btn = _find_element_any(webd, _PHOTOS_BTN_SELECTORS, timeout=4)
    if photos_btn:
        logger.info("Clicking 'Photos & Videos' menu item…")
        webd.execute_script("arguments[0].click();", photos_btn)
        time.sleep(0.8)
    else:
        logger.debug("'Photos & Videos' menu item not found — file input may appear directly")

    # Step 2: Find the photo/video file input using specific selectors
    file_input = None
    for xpath in _PHOTO_INPUT_SELECTORS:
        try:
            file_input = webd.find_element(By.XPATH, xpath)
            logger.debug(f"Photo file input found via: {xpath}")
            break
        except Exception:
            pass

    if not file_input:
        logger.debug("Photo-specific input not found — trying generic accept-attribute search")
        for accept in _FILE_INPUT_ACCEPT:
            try:
                file_input = webd.find_element(By.XPATH, f'//input[@accept="{accept}"]')
                logger.debug(f"Generic file input found with accept='{accept}'")
                break
            except Exception:
                pass

    if not file_input:
        return False

    webd.execute_script("arguments[0].style.display='block';", file_input)
    file_input.send_keys(abs_path)
    return True


def _photo_preview_opened(webd, wait_seconds: int = 8) -> bool:
    """
    Return True if the photo preview panel opened (caption box visible).
    This distinguishes a successful photo attach from a sticker attach
    (stickers are sent instantly with no preview panel).
    """
    for _ in range(max(1, wait_seconds // 2)):
        cb = _find_element_any(webd, _CAPTION_SELECTORS, timeout=2)
        if cb:
            return True
        time.sleep(1)
    return False


def _send_image(webd, wait, image_path: str, message: str) -> bool:
    """
    Attach and send an image in WhatsApp Web.

    Three strategies tried in order:

    Strategy A — Click attach button → click 'Photos & Videos' → photo file input
    Strategy B — JS direct inject into photo-specific file input (no menu click)
    Strategy C — Try all image file inputs, verify preview panel opened after each

    After each strategy succeeds at file injection, _photo_preview_opened() checks
    that the photo preview panel (caption box) appeared. If not (i.e. the image was
    sent as a sticker), the strategy is considered failed and the next is tried.
    """
    abs_path = os.path.abspath(image_path)

    # ── Strategy A: attach menu → Photos & Videos → file input ───────────────
    logger.info("Image Strategy A: click attach button…")
    attach_btn = _find_element_any(webd, _ATTACH_BTN_SELECTORS, timeout=10)

    if attach_btn:
        try:
            webd.execute_script("arguments[0].click();", attach_btn)
            time.sleep(1.2)  # wait for attach menu to open

            photos_clicked = False
            photos_btn = _find_element_any(webd, _PHOTOS_BTN_SELECTORS, timeout=5)
            if photos_btn:
                logger.info("Clicking 'Photos & Videos' menu item…")
                webd.execute_script("arguments[0].click();", photos_btn)
                time.sleep(1.0)
                photos_clicked = True

            # Find and inject into photo file input
            file_input = None
            for xpath in _PHOTO_INPUT_SELECTORS:
                try:
                    file_input = webd.find_element(By.XPATH, xpath)
                    logger.debug(f"Photo input found via: {xpath}")
                    break
                except Exception:
                    pass

            if not file_input:
                for accept in _FILE_INPUT_ACCEPT:
                    try:
                        file_input = webd.find_element(By.XPATH, f'//input[@accept="{accept}"]')
                        logger.debug(f"Fallback input found (accept='{accept}')")
                        break
                    except Exception:
                        pass

            if file_input:
                webd.execute_script("arguments[0].style.display='block';", file_input)
                file_input.send_keys(abs_path)
                accept_used = file_input.get_attribute("accept") or "unknown"
                logger.info(f"Strategy A — file injected (accept='{accept_used}', photos_menu={'yes' if photos_clicked else 'no'})")
                # Give the preview panel ample time to render
                time.sleep(6)
                # Proceed directly to finish — _finish_image_send handles the case
                # where the caption box is not found via its active-element guard.
                return _finish_image_send(webd, message)
            else:
                logger.debug("Strategy A: no suitable file input found")

        except Exception as e:
            logger.warning(f"Strategy A failed: {e}")

    # ── Strategy B: JS-inject directly into photo-specific file input ─────────
    logger.info("Image Strategy B: direct inject into photo-specific file input…")
    try:
        file_input = None
        for xpath in _PHOTO_INPUT_SELECTORS:
            try:
                file_input = webd.find_element(By.XPATH, xpath)
                webd.execute_script("arguments[0].style.display='block';", file_input)
                file_input.send_keys(abs_path)
                logger.info(f"Strategy B injected via: {xpath}")
                time.sleep(3)
                if _photo_preview_opened(webd, wait_seconds=10):
                    logger.info("Strategy B succeeded — photo preview panel confirmed ✓")
                    return _finish_image_send(webd, message)
                else:
                    logger.warning(f"Strategy B: preview panel not opened for {xpath}, trying next…")
                    file_input = None  # reset and try next selector
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Strategy B failed: {e}")

    # ── Strategy C: try ALL file inputs, verify preview opens after each ──────
    logger.info("Image Strategy C: try all file inputs with preview validation…")
    try:
        all_inputs = webd.find_elements(By.XPATH, '//input[@type="file"]')
        logger.info(f"Strategy C: found {len(all_inputs)} file input(s) on page")
        for fi in all_inputs:
            accept_val = fi.get_attribute("accept") or ""
            # Skip sticker-only inputs (webp only, no video types)
            if "video" not in accept_val and "image" not in accept_val:
                continue
            if accept_val in ("image/webp", ".webp", "image/gif"):
                logger.debug(f"Strategy C: skipping sticker input (accept='{accept_val}')")
                continue
            try:
                webd.execute_script("arguments[0].style.display='block';", fi)
                fi.send_keys(abs_path)
                logger.info(f"Strategy C injected via input (accept='{accept_val}'), checking preview…")
                time.sleep(3)
                if _photo_preview_opened(webd, wait_seconds=10):
                    logger.info("Strategy C succeeded — photo preview panel confirmed ✓")
                    return _finish_image_send(webd, message)
                else:
                    logger.warning(f"Strategy C: preview not opened for accept='{accept_val}', trying next…")
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Strategy C failed: {e}")

    logger.error(
        "All image send strategies failed. WhatsApp Web may have updated its DOM. "
        "Try sending without an image, or inspect whatsapp.com manually for new selectors."
    )
    return False


def _finish_image_send(webd, message: str) -> bool:
    """
    After image is attached to WhatsApp Web, type optional caption and click Send.

    Core strategy (2025 WA Web):
    ─────────────────────────────
    The OLD approach (page-wide send button search) had a critical bug:
    when the media panel didn't match a dialog selector, it fell back to any
    send button on the page — which is the COMPOSE BOX send button.
    That sent TEXT-ONLY without the image.

    NEW approach — anchor on the caption box:
    1. Find the CAPTION BOX — it is EXCLUSIVE to the media preview panel.
       Finding it confirms the panel is open and gives a DOM anchor.
    2. Focus & type optional caption.
    3. Press Enter IN the caption box → sends image (primary, most reliable).
    4. If Enter fails, walk UP the DOM from the caption box and click the send
       button found WITHIN the panel subtree only (never page-wide).
    5. If the caption box isn't found at all, press Enter on the active element
       ONLY IF it is NOT the chat compose box (safety guard).
    """
    time.sleep(4)  # give the media panel time to fully render

    logger.info("Waiting for media preview caption box (panel anchor)…")
    caption_box = None
    # Retry up to ~16 seconds total (4 attempts × up to 4s per attempt)
    for attempt in range(4):
        caption_box = _find_element_any(webd, _CAPTION_SELECTORS, timeout=4)
        if caption_box:
            break
        logger.debug(f"Caption box not found yet (attempt {attempt + 1}/4), retrying…")
        time.sleep(1)

    # ── PATH A: Caption box found → we know the media panel is open ───────────
    if caption_box:
        logger.info("Media preview caption box found ✓")

        # Focus the caption box
        try:
            caption_box.click()
        except Exception:
            webd.execute_script("arguments[0].click();", caption_box)
        time.sleep(0.2)

        # Type caption if provided
        if message.strip():
            _type_multiline(caption_box, message)
            time.sleep(0.4)

        # Step 1: Enter key in caption box (primary, most reliable send method)
        try:
            caption_box.send_keys(Keys.RETURN)
            logger.info("Image sent via Enter in caption box ✓")
            time.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"Enter in caption box failed: {e} — trying anchored button search")

        # Step 2: Walk UP the DOM from caption box, find send button INSIDE panel only
        try:
            container = caption_box
            for level in range(12):
                container = webd.execute_script("return arguments[0].parentElement;", container)
                if container is None:
                    break
                for sel in (
                    './/button[@data-testid="send"]',
                    './/*[@data-testid="send"]',
                    './/span[@data-icon="send-white"]/..',
                    './/span[@data-icon="send"]/..',
                    './/button[@aria-label="Send"]',
                    './/*[@data-icon="send-white"]',
                    './/*[@data-icon="send"]',
                ):
                    try:
                        btn = container.find_element(By.XPATH, sel)
                        if btn and btn.is_displayed():
                            try:
                                btn.click()
                            except Exception:
                                webd.execute_script("arguments[0].click();", btn)
                            logger.info(f"Image send clicked via anchored DOM walk (level {level}, {sel}) ✓")
                            time.sleep(2)
                            return True
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Anchored DOM walk failed: {e}")

        # Step 3: JS visible icon scan (still safer than page-wide XPath)
        for icon_name in ("send-white", "send"):
            try:
                spans = webd.find_elements(By.CSS_SELECTOR, f'span[data-icon="{icon_name}"]')
                logger.info(f"JS icon scan: {len(spans)} '{icon_name}' span(s)")
                for span in spans:
                    try:
                        if span.is_displayed():
                            webd.execute_script("arguments[0].parentElement.click();", span)
                            logger.info(f"Image send clicked via JS visible '{icon_name}' span ✓")
                            time.sleep(2)
                            return True
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"JS icon scan '{icon_name}' failed: {e}")

    # ── PATH B: Caption box NOT found → cautious active-element fallback ───────
    else:
        logger.warning(
            "Caption box not found — media panel may not have opened. "
            "Checking active element before attempting keyboard send…"
        )
        try:
            active_el = webd.switch_to.active_element
            testid = (active_el.get_attribute("data-testid") or "").lower()
            tag = active_el.tag_name.lower()
            # Only press Enter if we are NOT in the main chat compose text box
            if "conversation-compose" not in testid and tag not in ("body",):
                active_el.send_keys(Keys.RETURN)
                logger.info("Image sent via Enter on active element (media panel assumed focused) ✓")
                time.sleep(2)
                return True
            else:
                logger.error(
                    "Active element is the chat compose box (or body) — aborting to prevent "
                    "text-only send. The media preview panel did not open properly."
                )
                return False
        except Exception as e:
            logger.error(f"Active element check failed: {e}")
            return False

    # ── Debug screenshot ──────────────────────────────────────────────────────
    try:
        screenshot_path = os.path.abspath("wa_send_debug.png")
        webd.save_screenshot(screenshot_path)
        logger.error(
            f"Could not send image. Screenshot saved: {screenshot_path} — "
            "open it to inspect the actual WA Web media panel."
        )
    except Exception:
        logger.error("Could not send image. WhatsApp Web media panel selectors may have changed.")
    return False


def _dismiss_alerts(webd):
    """
    Dismiss any browser-level alert/confirm dialogs (e.g. Chrome's
    'Leave site?' popup that appears when navigating away mid-upload).
    Call this BEFORE webd.get() to avoid 'element click intercepted' errors.
    """
    try:
        alert = webd.switch_to.alert
        alert.accept()
        logger.info("Dismissed browser alert before navigation")
        time.sleep(0.3)
    except Exception:
        pass  # no alert present — that's fine


def send_whatsapp_message(webd, phone_no: str, message: str, image_path: str = None) -> bool:
    """
    Open a WhatsApp chat via direct URL and send a message (optionally with image).

    Returns True on success, False on any failure.

    Fix log:
      v1 (broken) — used data-tab="3" search box + data-tab="10" message box.
                     WhatsApp removed data-tab attrs → every send silently failed.
      v2 (current) — direct URL + aria-label selectors + continue-dialog handling.
    """
    wait = WebDriverWait(webd, 30)

    try:
        # ── 1. Dismiss any lingering browser alerts (e.g. 'Leave site?') ────────
        _dismiss_alerts(webd)

        # ── 2. Build & navigate to chat URL ─────────────────────────────────────
        clean = phone_no.strip().replace(" ", "").replace("-", "")
        url_num = clean.lstrip("+")
        url = f"https://web.whatsapp.com/send?phone={url_num}&text=&app_absent=0"
        logger.info(f"Navigating to chat: {url}")
        webd.get(url)
        time.sleep(4)   # let the page settle before checking for dialogs

        # ── 3. Detect invalid phone ──────────────────────────────────────────────
        for xpath in _INVALID_PHONE_XPATHS:
            try:
                el = webd.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    logger.error(f"WhatsApp reports invalid phone: {phone_no}")
                    return False
            except Exception:
                pass

        # ── 4. Handle "Continue to chat" dialog (unsaved contacts) ───────────────
        continue_btn = _find_element_any(webd, _CONTINUE_SELECTORS, timeout=6)
        if continue_btn:
            logger.info("Clicking 'Continue to chat' dialog…")
            continue_btn.click()
            time.sleep(2)

        # ── 4a. Send with image ──────────────────────────────────────────────────
        if image_path:
            try:
                if not _send_image(webd, wait, image_path, message):
                    return False
            except Exception as e:
                logger.error(f"Image send failed for {phone_no}: {e}", exc_info=True)
                return False

        # ── 4b. Send text only ───────────────────────────────────────────────────
        else:
            msg_box = _find_element_any(webd, _MSG_INPUT_SELECTORS, timeout=20)
            if msg_box is None:
                logger.error(
                    f"Message input box not found for {phone_no}. "
                    "WhatsApp Web may have updated its selectors, or the chat didn't load."
                )
                return False

            msg_box.click()
            time.sleep(0.3)
            _type_multiline(msg_box, message)
            time.sleep(0.5)   # wait for WhatsApp to register the typed text

            # Prefer clicking the Send button; fall back to Enter key
            send_btn = _find_element_any(webd, _SEND_BTN_SELECTORS, timeout=5)
            if send_btn:
                send_btn.click()
            else:
                msg_box.send_keys(Keys.RETURN)

            time.sleep(1)

        logger.info(f"✅ Message sent to {phone_no}")
        return True

    except Exception as e:
        logger.error(f"Unexpected error sending to {phone_no}: {e}", exc_info=True)
        return False


def _type_multiline(element, text: str):
    """Type text with newlines using Shift+Enter for line breaks."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        element.send_keys(line)
        if i != len(lines) - 1:
            element.send_keys(Keys.SHIFT, Keys.ENTER)
