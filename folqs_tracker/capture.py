"""Drive a real browser to collect the week's Seller Center screenshots.

Authentication is by **saved session, never stored credentials**. You log in
once by hand (`folqs_tracker login`), including whatever 2FA TikTok asks for,
and the browser's cookies are saved to a session file that later runs reuse.
Nothing here ever sees or stores a password.

The single most important behaviour in this module is that an expired session
raises `SessionExpired` instead of continuing. A logged-out Seller Center still
renders a perfectly screenshot-able page -- the login form -- and a bot that
captured that, handed it to the extractor and wrote the result to the tracker
would produce a week of blank cells with no obvious cause. So every capture is
checked for login markers before it is kept.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .weeks import Week

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

SELLER_CENTER = "https://seller-us.tiktok.com"

# A page is treated as logged-out if the URL matches any of these, or if any of
# the DOM markers is present. Both are checked: TikTok sometimes renders the
# login form in place without changing the URL.
LOGIN_URL_MARKERS = ("/account/login", "/passport/", "/login", "accounts.tiktok.com")
LOGIN_DOM_MARKERS = ("input[type='password']", "text=Log in with phone")


class CaptureError(RuntimeError):
    """A screen could not be captured."""


class SessionExpired(CaptureError):
    """The saved login is no longer valid. A human must log in again."""


class WrongPage(CaptureError):
    """The page loaded, but it is not the screen we asked for.

    Proxy errors, TikTok's own "something went wrong", and empty states all
    render perfectly and screenshot perfectly. Without this check the run saves
    a plausible-looking image, the extractor reads no metrics from it, and the
    week reports blanks for a reason nobody can see.
    """


@dataclass
class CaptureTarget:
    """One screen to photograph.

    `url` may contain {start} and {end}, filled with the reporting week's dates
    using `date_format`. Where a screen's date range is not expressible in the
    URL, express it as `actions` instead -- a short click script.
    """

    key: str
    name: str
    url: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)
    wait_for: str = ""          # selector to await before shooting
    expect_text: str = ""       # text that MUST be on the page, else reject
    settle_ms: int = 2500       # dashboards animate their numbers in
    full_page: bool = True
    date_format: str = "%Y-%m-%d"
    calibrated: bool = False    # False = the URL/actions are a best guess

    def resolve_url(self, week: Week) -> str:
        if not self.url:
            return ""
        return self.url.format(start=week.start.strftime(self.date_format),
                               end=week.end.strftime(self.date_format))

    @classmethod
    def from_dict(cls, raw: dict) -> "CaptureTarget":
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(raw) - known
        if unknown:
            raise ValueError(f"unknown key(s) in capture target: {sorted(unknown)}")
        if not raw.get("key") or not raw.get("name"):
            raise ValueError("every capture target needs a 'key' and a 'name'")
        if not raw.get("url") and not raw.get("actions"):
            raise ValueError(f"target {raw.get('key')!r} has neither a url nor actions")
        return cls(**raw)


# The six screens the tracker needs, per data/tracking/inbox/README.md.
#
# These URLs are a STARTING POINT, not verified paths -- Seller Center is behind
# a login, its URLs carry account-specific ids, and TikTok reorganises it. Run
# `folqs_tracker calibrate` once to replace them with the real ones from your
# own account; that writes capture_plan.json, which then takes precedence.
DEFAULT_PLAN: list[CaptureTarget] = [
    CaptureTarget("shop_analytics", "Analytics -> Shop analytics",
                  url=f"{SELLER_CENTER}/compass/shop-analysis",
                  expect_text="GMV"),
    CaptureTarget("product_traffic", "Analytics -> Product analytics -> Product traffic",
                  url=f"{SELLER_CENTER}/compass/product-analysis",
                  expect_text="Impressions"),
    CaptureTarget("creator", "Analytics -> Creator",
                  url=f"{SELLER_CENTER}/compass/creator-analysis",
                  expect_text="Creator"),
    CaptureTarget("samples", "Orders -> free-sample order tag",
                  url=f"{SELLER_CENTER}/order",
                  actions=[{"note": "Calibrate: Awaiting Shipment -> All -> Filters "
                                    "-> Order Tag -> both free-sample options -> Apply"}]),
    CaptureTarget("ads", "Ads Manager -> GMV Max",
                  url="https://ads.tiktok.com/i18n/perf/campaign",
                  expect_text="Cost"),
    CaptureTarget("account_health", "Account Health -> Shop Performance Score",
                  url=f"{SELLER_CENTER}/account-health",
                  expect_text="Score"),
]

PLAN_FILE = Path("capture_plan.json")


def load_plan(path: Path = PLAN_FILE) -> list[CaptureTarget]:
    """The calibrated plan if one exists, else the uncalibrated defaults."""
    if not path.exists():
        return list(DEFAULT_PLAN)
    raw = json.loads(path.read_text(encoding="utf-8"))
    targets = raw.get("targets", raw) if isinstance(raw, dict) else raw
    if not isinstance(targets, list) or not targets:
        raise ValueError(f"{path} does not contain a list of capture targets")
    return [CaptureTarget.from_dict(t) for t in targets]


def save_plan(targets: list[CaptureTarget], path: Path = PLAN_FILE) -> Path:
    path.write_text(json.dumps(
        {"targets": [t.__dict__ for t in targets]}, indent=2), encoding="utf-8")
    return path


# ------------------------------------------------------------------ browser

def _launch(pw, headless: bool):
    kwargs: dict = {"headless": headless,
                    "args": ["--disable-blink-features=AutomationControlled"]}
    chrome = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if chrome:
        kwargs["executable_path"] = chrome
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if proxy:
        # Loopback must bypass the proxy, or a local page comes back as the
        # proxy's own error body -- which screenshots just fine and is worthless.
        kwargs["proxy"] = {"server": proxy, "bypass": "localhost,127.0.0.1,::1"}
        kwargs["args"].append("--ignore-certificate-errors")
    return pw.chromium.launch(**kwargs)


def _new_context(browser, session_file: Optional[Path]):
    kwargs: dict = {"user_agent": UA, "locale": "en-US",
                    "viewport": {"width": 1600, "height": 1200}}
    if session_file and session_file.exists():
        kwargs["storage_state"] = str(session_file)
    context = browser.new_context(**kwargs)
    context.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    return context


def looks_logged_out(url: str, page=None) -> bool:
    """True if this page is a login screen rather than the dashboard."""
    lowered = (url or "").lower()
    if any(marker in lowered for marker in LOGIN_URL_MARKERS):
        return True
    if page is None:
        return False
    for selector in LOGIN_DOM_MARKERS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def save_session(session_file: Path, *, timeout_minutes: int = 10) -> Path:
    """Open a real browser, wait for a human to log in, then save the session.

    Interactive by design. TikTok will usually demand 2FA, and a scheduled job
    cannot answer an SMS -- so a person does this once, and the saved cookies
    carry the scheduled runs until they expire.
    """
    from playwright.sync_api import sync_playwright

    session_file.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = _launch(pw, headless=False)
        context = _new_context(browser, session_file if session_file.exists() else None)
        page = context.new_page()
        page.goto(SELLER_CENTER, wait_until="domcontentloaded")

        print("\nA browser window has opened.")
        print("  1. Log in to TikTok Seller Center (complete any 2FA).")
        print("  2. Wait until you can see your dashboard.")
        print("  3. Come back here and press Enter.\n")
        input("Press Enter once you are logged in... ")

        if looks_logged_out(page.url, page):
            browser.close()
            raise SessionExpired(
                "That still looks like a login page, so nothing was saved. "
                "Log in fully, then run this again."
            )

        context.storage_state(path=str(session_file))
        browser.close()

    # Session cookies are credentials in every meaningful sense.
    os.chmod(session_file, stat.S_IRUSR | stat.S_IWUSR)
    return session_file


@dataclass
class CaptureResult:
    saved: list[Path]
    failed: list[tuple[str, str]]  # (screen name, why)


def capture_all(
    week: Week,
    output_dir: Path,
    session_file: Path,
    *,
    plan: Optional[list[CaptureTarget]] = None,
    headless: bool = True,
    only: Optional[list[str]] = None,
    settle_multiplier: float = 1.0,
) -> CaptureResult:
    """Photograph every screen in the plan for `week`.

    One screen failing does not abandon the rest -- five good captures plus a
    named gap is a better Friday than nothing at all. An expired session is the
    exception: every subsequent screen would fail the same way, so it stops.
    """
    from playwright.sync_api import sync_playwright
    from playwright.sync_api import Error as PlaywrightError

    if not session_file.exists():
        raise SessionExpired(
            f"No saved session at {session_file}. Run:  python -m folqs_tracker login"
        )

    targets = plan if plan is not None else load_plan()
    if only:
        wanted = set(only)
        targets = [t for t in targets if t.key in wanted]
        if not targets:
            raise CaptureError(f"no capture targets matched {sorted(wanted)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    failed: list[tuple[str, str]] = []

    with sync_playwright() as pw:
        browser = _launch(pw, headless=headless)
        context = _new_context(browser, session_file)
        page = context.new_page()
        page.set_default_timeout(45_000)

        try:
            for index, target in enumerate(targets, 1):
                print(f"  [{index}/{len(targets)}] {target.name}")
                try:
                    url = target.resolve_url(week)
                    if url:
                        page.goto(url, wait_until="domcontentloaded")

                    if looks_logged_out(page.url, page):
                        raise SessionExpired(
                            "the saved TikTok session has expired. "
                            "Run:  python -m folqs_tracker login"
                        )

                    _run_actions(page, target)

                    if target.wait_for:
                        page.wait_for_selector(target.wait_for)
                    page.wait_for_timeout(int(target.settle_ms * settle_multiplier))

                    # Re-check: an action may have navigated us to a login wall.
                    if looks_logged_out(page.url, page):
                        raise SessionExpired(
                            "the session expired part-way through. "
                            "Run:  python -m folqs_tracker login"
                        )

                    if target.expect_text:
                        body = page.locator("body").inner_text(timeout=10_000)
                        if target.expect_text.lower() not in body.lower():
                            raise WrongPage(
                                f"expected to see {target.expect_text!r} on this "
                                f"screen but did not -- got {body.strip()[:120]!r}"
                            )

                    path = output_dir / f"{index:02d}_{target.key}.png"
                    page.screenshot(path=str(path), full_page=target.full_page)
                    saved.append(path)
                    note = "" if target.calibrated else "  (uncalibrated URL)"
                    print(f"      saved {path.name}{note}")

                except SessionExpired:
                    raise
                except (PlaywrightError, CaptureError) as exc:
                    reason = str(exc).splitlines()[0][:160]
                    print(f"      FAILED: {reason}")
                    failed.append((target.name, reason))
        finally:
            browser.close()

    return CaptureResult(saved, failed)


def _run_actions(page, target: CaptureTarget) -> None:
    """Replay a target's click script.

    Deliberately tiny vocabulary. This exists to express flows a URL cannot --
    above all the samples screen, which is a filter dialog, not a page.
    """
    for step in target.actions:
        if "note" in step and len(step) == 1:
            raise CaptureError(
                f"{target.key} is not calibrated yet: {step['note']}. "
                "Run:  python -m folqs_tracker calibrate"
            )
        for action, value in step.items():
            if action == "click":
                page.click(value)
            elif action == "fill":
                page.fill(value["selector"], value["text"])
            elif action == "press":
                page.keyboard.press(value)
            elif action == "wait_for":
                page.wait_for_selector(value)
            elif action == "wait_ms":
                page.wait_for_timeout(int(value))
            elif action == "goto":
                page.goto(value, wait_until="domcontentloaded")
            elif action == "note":
                continue
            else:
                raise CaptureError(f"unknown action {action!r} in target {target.key!r}")


def calibrate(session_file: Path, plan_path: Path = PLAN_FILE) -> Path:
    """Walk through the screens with a human and record the real URLs.

    Seller Center URLs carry account-specific ids and change between releases,
    so guessing them is hopeless. Rather than guess, this asks once.
    """
    from playwright.sync_api import sync_playwright

    targets = load_plan(plan_path)
    with sync_playwright() as pw:
        browser = _launch(pw, headless=False)
        context = _new_context(browser, session_file if session_file.exists() else None)
        page = context.new_page()
        page.goto(SELLER_CENTER, wait_until="domcontentloaded")

        print("\nA browser window has opened. For each screen below:")
        print("  navigate to it (set the date range as you normally would),")
        print("  then come back here and press Enter. Type 's' to skip one.\n")

        for target in targets:
            answer = input(f"  Go to: {target.name}  [Enter when there / s to skip] ")
            if answer.strip().lower() == "s":
                print("      skipped")
                continue
            if looks_logged_out(page.url, page):
                print("      that is a login page -- log in first, then retry this screen")
                continue
            target.url = page.url
            target.calibrated = True
            print(f"      recorded {page.url[:100]}")

        context.storage_state(path=str(session_file))
        browser.close()

    saved = save_plan(targets, plan_path)
    print(f"\nWrote {saved}.")
    print("Any screen needing clicks (the samples filter) still needs its "
          "`actions` filled in by hand -- see the comments in that file.")
    return saved
