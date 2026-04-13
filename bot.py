import requests
import time
from datetime import datetime

API_KEY = "b35bef69477140590f4b29ab2cff9ee9"
BOT_TOKEN = "8539407839:AAG7KHMls5wIcL-N63io9RABFR63oK1PKbM"

VIP_CHAT = "-1003893309545"
FREE_CHAT = "-1003873380608"

SPORTS = ["soccer_epl", "basketball_nba", "esports_csgo"]

TOTAL_STAKE = 100
MIN_PROFIT = 2.0

VIP_LIMIT = 20
FREE_LIMIT = 2

vip_count = 0
free_count = 0

seen = set()
current_day = datetime.now().day


# ---------------- TELEGRAM ----------------
def send(chat, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat, "text": text})


# ---------------- RESET DAILY ----------------
def reset_daily():
    global vip_count, free_count, current_day
    today = datetime.now().day

    if today != current_day:
        vip_count = 0
        free_count = 0
        current_day = today


# ---------------- API ----------------
def get_data(sport):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    return requests.get(url, params=params).json()


# ---------------- MATH ----------------
def calc_profit(odds):
    inv = sum(1 / o for o in odds)
    return (1 - inv) * 100


def calc_stakes(odds):
    inv = sum(1 / o for o in odds)
    return [(1 / o) / inv for o in odds]


# ---------------- PROCESS EVENT ----------------
def process_event(event):
    try:
        match_id = event["id"]

        if match_id in seen:
            return None

        best_odds = {}
        best_books = {}

        for b in event["bookmakers"]:
            book = b["title"]

            for m in b["markets"]:
                for o in m["outcomes"]:
                    name = o["name"]
                    odd = o["price"]

                    if name not in best_odds or odd > best_odds[name]:
                        best_odds[name] = odd
                        best_books[name] = book

        # mora biti više ishoda
        if len(best_odds) < 2:
            return None

        # ❗ FILTER: mora biti više različitih kladionica
        if len(set(best_books.values())) < 2:
            return None

        odds = list(best_odds.values())
        profit = calc_profit(odds)

        if profit < MIN_PROFIT:
            return None

        stakes = calc_stakes(odds)

        msg = f"""🔥 SUREBETBALKAN 🔥

📊 Profit: {profit:.2f}%

💰 ULOG: {TOTAL_STAKE}€

📌 STAKE:
"""

        for i, (team, odd) in enumerate(best_odds.items()):
            book = best_books[team]
            msg += f"- {team} → {book} @ {odd} → {stakes[i]*TOTAL_STAKE:.2f}€ ({stakes[i]*100:.1f}%)\n"

        msg += "\n⏱ Update svake 5 minute"

        seen.add(match_id)
        return msg

    except:
        return None


# ---------------- MAIN LOOP (HARD LIMIT FIXED) ----------------
while True:
    reset_daily()

    sent_this_cycle = False

    for sport in SPORTS:
        data = get_data(sport)

        for event in data:
            msg = process_event(event)

            if msg:

                # VIP LIMIT HARD STOP
                if vip_count < VIP_LIMIT:
                    send(VIP_CHAT, msg)
                    vip_count += 1

                # FREE LIMIT HARD STOP
                if free_count < FREE_LIMIT:
                    send(FREE_CHAT, msg)
                    free_count += 1

                sent_this_cycle = True
                break

        if sent_this_cycle:
            break

    time.sleep(300)  # 5 min