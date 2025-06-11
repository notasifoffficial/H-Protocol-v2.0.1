import os
import sys
import json
import time
import random
import logging
import requests
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table

# Constants
BASE_URL = "https://testnet.humanity.org"
TOKEN_FILE = "tokens.txt"
LOG_FILE = "log.txt"

# Rich console setup
console = Console()

# Logging setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)

def load_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

if not os.path.exists(TOKEN_FILE):
    console.print("[bold red]❌ File tokens.txt not found![/bold red]")
    sys.exit(1)

TOKENS = load_file_lines(TOKEN_FILE)

def log_error(message):
    logging.error(message)

def show_banner():
    banner_text = Text("Auto Claim Humanity Protocol 🚀", style="bold cyan", justify="center")
    panel = Panel(banner_text, expand=False, border_style="cyan", title="Start", subtitle="By Notasifofficial")
    console.print(panel)

def call(endpoint, token, method="POST", body=None):
    url = BASE_URL + endpoint
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "token": token,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    session = requests.Session()
    try:
        if method.upper() == "GET":
            resp = session.get(url, headers=headers, timeout=15)
        else:
            resp = session.post(url, headers=headers, json=body or {}, timeout=15)

        try:
            response_data = resp.json()
        except json.JSONDecodeError as e:
            raise Exception(f"Received non-JSON data: {str(e)}")

        if not resp.ok:
            message = response_data.get("message", "Unknown error")
            raise Exception(f"{resp.status_code} {resp.reason}: {message}")

        return response_data

    except Exception as e:
        raise Exception(f"Request failed ({endpoint}): {str(e)}")

def process_token(token, index):
    console.rule(f"[cyan]🔹 Token Execution #{index + 1}")
    try:
        user_info = call("/api/user/userInfo", token)
        user_data = user_info.get("data", {})
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Info Wallet", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("✅ Nickname", user_data.get("nickName", "Unknown"))
        table.add_row("✅ Wallet", user_data.get("ethAddress", "Unknown"))
        console.print(table)

        balance = call("/api/rewards/balance", token, method="GET")
        console.print(f"[yellow]💰 Point HP :[/yellow] {balance.get('balance', {}).get('total_rewards', 0)}")

        reward_status = call("/api/rewards/daily/check", token)
        console.print(f"[blue]📊 Status:[/blue] {reward_status.get('message', '-')}")

        if not reward_status.get("available", False):
            console.print("[orange1]⏳ Done claim, skip[/orange1]")
            return

        claim = call("/api/rewards/daily/claim", token)
        claim_data = claim.get("data", {})
        if claim_data and claim_data.get("amount"):
            console.print(f"[green]🎉 Claim successful, HP Point: {claim_data['amount']}[/green]")
        elif claim.get("message") and "successfully claimed" in claim.get("message", ""):
            console.print("[green]🎉 You have successfully claimed HP Points today.[/green]")
        else:
            console.print(f"[red]❌ Claim failed, data does not match: {claim}[/red]")
            return

        updated_balance = call("/api/rewards/balance", token, method="GET")
        if updated_balance.get("balance"):
            console.print(f"[green]💰 HP Point after claim:[/green] {updated_balance['balance']['total_rewards']}")
        else:
            console.print(f"[red]❌ Failed to update HP Point: {updated_balance}[/red]")

    except Exception as err:
        console.print(f"[bold red]❌ Error: {err}[/bold red]")
        log_error(f"Token #{index + 1} gagal: {err}")

    delay = random.randint(15000, 20000) / 1000
    console.print(f"[yellow]⏳ Waiting {delay:.2f} seconds before continuing...[/yellow]")
    time.sleep(delay)

def countdown(seconds, on_finish):
    try:
        with Live(refresh_per_second=1) as live:
            while seconds >= 0:
                hours, rem = divmod(seconds, 3600)
                minutes, secs = divmod(rem, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                live.update(Text(f"⏳ Claim after {time_str} this hours...", style="bold yellow"))
                time.sleep(1)
                seconds -= 1
        console.print("[bold green]\n⏳ Countdown is over, starting a new round...[/bold green]")
        on_finish()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 The program was closed by the user.[/bold red]")
        sys.exit(0)

def start_round():
    console.print(f"\n[bold green]🚀 Accounts total : {len(TOKENS)} akun...[/bold green]")
    for i, token in enumerate(TOKENS):
        process_token(token, i)
    console.print("[bold green]✅ Claim done, next claim waiting 24 hours...[/bold green]")
    countdown(24 * 60 * 60, start_round)

def batch_run():
    show_banner()
    start_round()

if __name__ == "__main__":
    batch_run()
