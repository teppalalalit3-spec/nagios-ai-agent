from fastapi import FastAPI
from dotenv import load_dotenv
import json
import os

from collector import collect_data
from analyzer import analyze
from slackbot import send_slack
from nagios_client import fetch_servicelist, extract_critical_services, get_host_ip

load_dotenv()
app = FastAPI()

STATE_FILE = "alert_state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(list(state), f)


last_sent = load_state()


@app.post("/scan")
async def scan_nagios_and_alert():

    global last_sent

    try:
        raw = fetch_servicelist()
        critical_services = extract_critical_services(raw)

        sent = 0
        current_criticals = set()

        for alert in critical_services:

            key = f"{alert['host']}|{alert['service']}"
            current_criticals.add(key)

            if key not in last_sent:
                print(f"NEW ALERT: {key} - {alert['state_name']}")

                logs = collect_data(alert)
                ai_result = analyze(alert, logs)
                
                # Prepare alert info for Slack - get IP from Nagios
                alert_info = {
                    "host": alert['host'],
                    "service": alert['service'],
                    "ip": get_host_ip(alert['host']),
                    "status": alert['state_name']
                }
                
                send_slack(alert_info, ai_result)

                last_sent.add(key)
                sent += 1
            else:
                print(f"SKIPPED: {key}")

        # Remove recovered
        last_sent = last_sent.intersection(current_criticals)

        save_state(last_sent)

        return {
            "status": "ok",
            "critical_found": len(critical_services),
            "messages_sent": sent
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}
