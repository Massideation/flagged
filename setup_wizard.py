#!/usr/bin/env python3
"""
Flagged Setup Wizard
───────────────────
Walks you through the entire Flagged setup interactively.
Run this once and you're done.
"""

import os
import sys
import json
import time
import shutil
import subprocess
import platform
import webbrowser
from pathlib import Path

# ── Colors ────────────────────────────────────────────────────────────────────
def supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = supports_color()

def c(text, code): return f"\033[{code}m{text}\033[0m" if USE_COLOR else text
def bold(t):    return c(t, "1")
def green(t):   return c(t, "92")
def yellow(t):  return c(t, "93")
def red(t):     return c(t, "91")
def cyan(t):    return c(t, "96")
def dim(t):     return c(t, "2")
def gold(t):    return c(t, "33")

# ── UI Helpers ────────────────────────────────────────────────────────────────
def header():
    print()
    print(gold(bold("  ██╗  ██╗███████╗██████╗  █████╗ ██╗     ██████╗ ")))
    print(gold(bold("  ██║  ██║██╔════╝██╔══██╗██╔══██╗██║     ██╔══██╗")))
    print(gold(bold("  ███████║█████╗  ██████╔╝███████║██║     ██║  ██║")))
    print(gold(bold("  ██╔══██║██╔══╝  ██╔══██╗██╔══██║██║     ██║  ██║")))
    print(gold(bold("  ██║  ██║███████╗██║  ██║██║  ██║███████╗██████╔╝")))
    print(gold(bold("  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ")))
    print()
    print(f"  {bold('Local AI Email Monitor')} — Setup Wizard")
    print(f"  {dim('Your inbox. Filtered by what actually matters.')}")
    print()

def section(title):
    print()
    print(cyan(f"── {title} {'─' * (50 - len(title))}"))
    print()

def step(n, total, text):
    print(f"  {dim(f'[{n}/{total}]')} {bold(text)}")

def ok(text):    print(f"  {green('✓')} {text}")
def warn(text):  print(f"  {yellow('!')} {text}")
def fail(text):  print(f"  {red('✗')} {text}")
def info(text):  print(f"  {dim('·')} {text}")

def ask(prompt, default=None, secret=False):
    if default:
        display = f"{prompt} {dim(f'[{default}]')}: "
    else:
        display = f"{prompt}: "

    print(f"  {cyan('?')} ", end="")
    try:
        if secret:
            import getpass
            val = getpass.getpass(display)
        else:
            val = input(display).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        print()
        warn("Setup cancelled. Run setup_wizard.py again to resume.")
        sys.exit(0)

    return val if val else default

def confirm(prompt, default=True):
    hint = "Y/n" if default else "y/N"
    print(f"  {cyan('?')} {prompt} {dim(f'[{hint}]')}: ", end="")
    try:
        val = input().strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)
    if not val:
        return default
    return val in ("y", "yes")

def pause(text="Press Enter to continue..."):
    print(f"\n  {dim(text)}", end="")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

def spinner(text, duration=1.5):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        print(f"\r  {cyan(frames[i % len(frames)])} {text}", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print(f"\r  {green('✓')} {text}     ")

# ── Checks ────────────────────────────────────────────────────────────────────
def check_python():
    section("Checking Requirements")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        fail(f"Python 3.9+ required. You have {v.major}.{v.minor}.")
        info("Install from https://python.org or via Homebrew: brew install python@3.11")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")
    return True

def check_pip():
    result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        fail("pip not found")
        sys.exit(1)
    ok("pip available")

def install_dependencies(base_dir: Path):
    req_file = base_dir / "requirements.txt"
    if not req_file.exists():
        warn("requirements.txt not found — skipping dependency install")
        return

    print(f"\n  {cyan('→')} Installing Python dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        fail("Dependency install failed:")
        print(red(result.stderr))
        sys.exit(1)
    ok("Dependencies installed")

def check_lm_studio():
    section("LM Studio Check")
    info("Flagged needs LM Studio running with its Local Server enabled.")
    info("Download: https://lmstudio.ai  (free)")
    print()

    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:1234/v1/models", timeout=3)
        ok("LM Studio Local Server is running")
        return True
    except Exception:
        warn("LM Studio Local Server not detected at localhost:1234")
        print()
        info("To fix this:")
        info("  1. Open LM Studio")
        info("  2. Click 'Local Server' in the left sidebar")
        info("  3. Load a model (Qwen2.5 3B Instruct recommended)")
        info("  4. Click 'Start Server'")
        print()
        if confirm("Open LM Studio download page?", default=False):
            webbrowser.open("https://lmstudio.ai")
        print()
        if not confirm("Continue setup anyway? (you can start LM Studio later)", default=True):
            sys.exit(0)
        return False

def get_lm_studio_models():
    """Try to fetch available models from LM Studio."""
    import urllib.request, json
    try:
        with urllib.request.urlopen("http://localhost:1234/v1/models", timeout=3) as r:
            data = json.loads(r.read())
            return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []

# ── Telegram Setup ────────────────────────────────────────────────────────────
def setup_telegram():
    section("Telegram Bot Setup")
    info("Flagged uses your existing Telegram bot to send alerts.")
    info("If you don't have one yet, create it via @BotFather in Telegram.")
    print()

    if confirm("Open Telegram BotFather to create/find your bot?", default=False):
        webbrowser.open("https://t.me/botfather")
        pause("After getting your bot token, press Enter to continue...")

    print()
    bot_token = ask("Paste your Telegram Bot Token", secret=True)
    while not bot_token or ":" not in bot_token:
        warn("That doesn't look right. Bot tokens look like: 7123456789:AAHxxxxxxxx")
        bot_token = ask("Paste your Telegram Bot Token", secret=True)

    print()
    info("Now get your Chat ID. Send any message to your bot in Telegram, then:")
    if confirm("Open @userinfobot to get your Chat ID?", default=True):
        webbrowser.open("https://t.me/userinfobot")
        pause("After getting your Chat ID, press Enter...")

    print()
    chat_id = ask("Paste your Telegram Chat ID")
    while not chat_id or not chat_id.lstrip("-").isdigit():
        warn("Chat IDs are numbers, like: 123456789")
        chat_id = ask("Paste your Telegram Chat ID")

    # Test the connection
    print()
    print(f"  {cyan('→')} Testing Telegram connection...")
    import urllib.request, urllib.error
    test_url = (
        f"https://api.telegram.org/bot{bot_token}/sendMessage"
        f"?chat_id={chat_id}"
        f"&text={urllib.parse.quote('✅ Flagged is connected! Setup in progress...')}"
        f"&parse_mode=Markdown"
    )
    import urllib.parse
    try:
        urllib.request.urlopen(test_url, timeout=10)
        ok("Telegram connected — check your phone for the test message!")
    except urllib.error.HTTPError as e:
        warn(f"Telegram test failed ({e.code}). Check your token and chat ID.")
        if not confirm("Continue anyway?", default=True):
            sys.exit(0)
    except Exception as e:
        warn(f"Could not reach Telegram: {e}")

    return bot_token, chat_id

# ── Google Cloud Setup ────────────────────────────────────────────────────────
def setup_google_credentials(base_dir: Path):
    section("Gmail API Setup")
    info("Flagged needs read-only access to your Gmail via Google's official API.")
    info("This requires a free Google Cloud project with one credentials file.")
    info("One file works for ALL your Gmail accounts.")
    print()

    creds_path = base_dir / "credentials.json"

    if creds_path.exists():
        ok(f"credentials.json already found at {creds_path}")
        return str(creds_path)

    print(f"  {bold('Here is exactly what to do:')} (takes about 5 minutes)")
    print()
    steps = [
        "Go to https://console.cloud.google.com",
        "Create a new project — name it 'Flagged'",
        "Go to APIs & Services → Enable APIs → search 'Gmail API' → Enable",
        "Go to APIs & Services → Credentials → Create Credentials → OAuth Client ID",
        "If asked, configure consent screen: External, add your email as test user",
        "Application type: Desktop App → Create",
        "Download the JSON → rename it credentials.json",
        f"Move credentials.json to: {base_dir}",
    ]
    for i, s in enumerate(steps, 1):
        print(f"  {dim(str(i) + '.')} {s}")

    print()
    if confirm("Open Google Cloud Console now?", default=True):
        webbrowser.open("https://console.cloud.google.com")

    print()
    pause(f"Once you've placed credentials.json in {base_dir}, press Enter...")

    attempts = 0
    while not creds_path.exists() and attempts < 3:
        # Let them specify a path
        manual = ask(
            f"credentials.json not found. Enter full path to the file (or press Enter to retry)",
            default=""
        )
        if manual and Path(manual).exists():
            shutil.copy(manual, creds_path)
            ok(f"Copied credentials.json to {base_dir}")
            break
        attempts += 1

    if not creds_path.exists():
        warn("credentials.json not found — you can add it manually later.")
        info(f"Place it at: {creds_path}")
    else:
        ok("credentials.json found")

    return str(creds_path)

# ── Account Setup ─────────────────────────────────────────────────────────────
def setup_accounts(base_dir: Path, creds_path: str):
    section("Gmail Account Setup")
    info("Add the Gmail accounts you want Flagged to monitor.")
    info("Each account gets a short label (e.g. Main, Work, Media).")
    print()

    accounts = []
    count = int(ask("How many Gmail accounts do you want to monitor?", default="1") or "1")

    for i in range(1, count + 1):
        print(f"\n  {bold(f'Account {i} of {count}')}")
        label = ask(f"  Label for account {i}", default=f"Account{i}")
        token_path = str(base_dir / f"token_{label.lower().replace(' ', '_')}.pkl")
        accounts.append({
            "label": label,
            "credentials_path": creds_path,
            "token_path": token_path
        })
        ok(f"Added: {label}")

    return accounts

# ── Model Selection ───────────────────────────────────────────────────────────
def setup_model():
    section("AI Model Selection")
    available = get_lm_studio_models()

    if available:
        ok(f"Found {len(available)} model(s) loaded in LM Studio:")
        for m in available:
            print(f"     {dim('·')} {m}")
        print()
        model = ask("Which model should Flagged use?", default=available[0])
    else:
        info("No models detected (LM Studio may not be running yet).")
        print()
        info("Recommended models for Flagged (fast + accurate):")
        recommendations = [
            ("Qwen2.5 3B Instruct",  "⭐ Default — best for classification, ~2GB RAM"),
            ("Qwen3 4B Instruct",     "Great — slightly more capable, ~3GB RAM"),
            ("Phi-3.5 Mini",          "Good — excellent reasoning, ~2.5GB RAM"),
            ("Llama 3.2 3B Instruct", "Reliable fallback — ~2GB RAM"),
            ("SmolLM3 3B",            "Newest option — strong benchmarks, ~2GB RAM"),
        ]
        for name, note in recommendations:
            print(f"     {dim('·')} {bold(name)} — {dim(note)}")
        print()
        model = ask("Enter your model name (must match exactly in LM Studio)", default="qwen2.5-3b-instruct")

    return model

# ── Score Threshold ───────────────────────────────────────────────────────────
def setup_threshold():
    section("Alert Sensitivity")
    info("Flagged scores each email 1–10. You only get alerted above your threshold.")
    print()
    info("  10 = Drop everything")
    info("   7 = Respond today (recommended default)")
    info("   5 = Worth a look")
    print()
    threshold = ask("Alert threshold (1-10)", default="7")
    try:
        threshold = max(1, min(10, int(threshold)))
    except ValueError:
        threshold = 7
    ok(f"Threshold set to {threshold}/10")
    return threshold

# ── Write Config ──────────────────────────────────────────────────────────────
def write_config(base_dir: Path, bot_token: str, chat_id: str,
                 model: str, accounts: list, threshold: int):
    section("Writing Configuration")
    config = {
        "score_threshold": threshold,
        "poll_interval_seconds": 300,
        "max_emails_per_check": 20,
        "lm_studio": {
            "url": "http://localhost:1234",
            "model": model
        },
        "telegram": {
            "bot_token": bot_token,
            "chat_id": chat_id
        },
        "accounts": accounts
    }
    config_path = base_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    ok(f"config.json written to {config_path}")
    return config_path

# ── macOS Service ─────────────────────────────────────────────────────────────
def setup_macos_service(base_dir: Path):
    section("Background Service (macOS)")
    info("Install Flagged as a macOS LaunchAgent so it runs 24/7 and survives reboots.")
    print()

    if not confirm("Install Flagged as a background service?", default=True):
        info("Skipped. Run manually anytime with: python3 flagged.py")
        return False

    plist_src = base_dir / "com.flagged.emailmonitor.plist"
    plist_dst = Path.home() / "Library" / "LaunchAgents" / "com.flagged.emailmonitor.plist"

    # Update plist with correct path
    if plist_src.exists():
        with open(plist_src) as f:
            content = f.read()
        # Replace placeholder path with actual path
        content = content.replace(
            "/Users/YOUR_USERNAME/email_monitor",
            str(base_dir)
        )
        with open(plist_src, "w") as f:
            f.write(content)

        shutil.copy(plist_src, plist_dst)

        result = subprocess.run(
            ["launchctl", "load", str(plist_dst)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            ok("LaunchAgent installed — Flagged will start on next login")
            subprocess.run(["launchctl", "start", "com.flagged.emailmonitor"],
                           capture_output=True)
            ok("Flagged service started now")
        else:
            warn(f"launchctl load failed: {result.stderr.strip()}")
            info("You can start Flagged manually with: python3 flagged.py")
    else:
        warn("Plist file not found — skipping service install")
        info("Run manually: python3 flagged.py")

    return True

# ── Gmail First Auth ──────────────────────────────────────────────────────────
def authorize_gmail_accounts(base_dir: Path, accounts: list):
    section("Authorizing Gmail Accounts")
    info("A browser window will open for each account.")
    info("Log in and click Allow — this is read-only access, Flagged cannot send or delete email.")
    print()

    flagged_py = base_dir / "flagged.py"
    if not flagged_py.exists():
        warn("flagged.py not found — skipping Gmail auth. Run it manually to authorize.")
        return

    if not confirm("Authorize Gmail accounts now?", default=True):
        info("Run 'python3 flagged.py' later to authorize.")
        return

    for account in accounts:
        token_path = Path(account["token_path"])
        if token_path.exists():
            ok(f"{account['label']} — already authorized")
            continue

        creds_path = Path(account["credentials_path"])
        if not creds_path.exists():
            warn(f"credentials.json not found for {account['label']} — skipping")
            continue

        print(f"\n  {cyan('→')} Authorizing {bold(account['label'])}...")
        info("Browser opening — log in with the correct Google account")
        pause("Press Enter when ready...")

        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
            import pickle
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
            ok(f"{account['label']} — authorized successfully")
        except Exception as e:
            warn(f"Authorization failed for {account['label']}: {e}")
            info("Try running 'python3 flagged.py' manually to re-authorize")

# ── Summary ───────────────────────────────────────────────────────────────────
def print_summary(base_dir: Path, accounts: list, model: str, threshold: int):
    section("Setup Complete")
    print(f"  {green(bold('Flagged is ready.'))}")
    print()
    print(f"  {dim('Location:')}   {base_dir}")
    print(f"  {dim('Model:')}      {model}")
    print(f"  {dim('Threshold:')}  {threshold}/10")
    print(f"  {dim('Accounts:')}   {', '.join(a['label'] for a in accounts)}")
    print()
    print(f"  {bold('Useful commands:')}")
    print(f"    {cyan('python3 flagged.py')}           — run manually")
    print(f"    {cyan('tail -f flagged.log')}          — watch live activity")
    print()
    print(f"  {bold('To tune what gets flagged:')}")
    print(f"    {cyan('nano PRIORITIES.md')}          — edit your priority context")
    print()
    print(f"  {dim('Built by Miguel Sanchez · github.com/Massideation/flagged')}")
    print()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    header()

    # Figure out where flagged.py lives
    base_dir = Path(__file__).parent.resolve()

    print(f"  Installing Flagged in: {bold(str(base_dir))}")
    print()

    if not confirm("Ready to begin setup?", default=True):
        sys.exit(0)

    # Steps
    check_python()
    check_pip()
    install_dependencies(base_dir)
    check_lm_studio()

    bot_token, chat_id = setup_telegram()
    creds_path = setup_google_credentials(base_dir)
    accounts = setup_accounts(base_dir, creds_path)
    model = setup_model()
    threshold = setup_threshold()

    write_config(base_dir, bot_token, chat_id, model, accounts, threshold)

    # Platform-specific service install
    if platform.system() == "Darwin":
        setup_macos_service(base_dir)
    elif platform.system() == "Linux":
        section("Background Service (Linux)")
        info("systemd service setup — see SETUP.md for instructions.")
        info("Or run manually: python3 flagged.py &")
    else:
        section("Background Service (Windows)")
        info("See SETUP.md for Task Scheduler setup.")
        info("Or run manually: python flagged.py")

    authorize_gmail_accounts(base_dir, accounts)
    print_summary(base_dir, accounts, model, threshold)


if __name__ == "__main__":
    import urllib.parse  # ensure available for Telegram test
    main()
