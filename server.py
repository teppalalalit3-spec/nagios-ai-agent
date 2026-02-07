from fastapi import FastAPI
from dotenv import load_dotenv
from collector import collect_data
from analyzer import analyze
from slackbot import send_slack

load_dotenv()

app = FastAPI()


@app.post("/alert")
async def alert(alert: dict):
    try:
        print(f"Received alert: {alert}")

        logs = collect_data(alert)

        ai_result = analyze(alert, logs)

        print("AI analysis complete")

        send_slack(ai_result)

        print("Slack notification sent")

        return {"status": "analysis_sent"}

    except Exception as e:
        print("ERROR:", str(e))
        return {"status": "failed", "error": str(e)}
