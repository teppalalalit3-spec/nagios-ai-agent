import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are an SRE assistant.

Return ONLY valid JSON.

Tasks:
1. Identify root cause
2. Detect recurring pattern
3. Predict next failure
4. Suggest safest remediation
5. Choose ONE playbook_type from:
   - disk_cleanup_nginx
   - restart_service
   - high_cpu_kill_process
   - unknown

Format:

{
  "root_cause": "...",
  "pattern": "...",
  "prediction": "...",
  "recommended_action": "...",
  "playbook_type": "...",
  "confidence": 0-1
}
"""


def summarize(data):
    """
    Safely summarize collected metrics.
    """

    return {
        "disk": str(data.get("disk", ""))[:800],
        "cpu": str(data.get("cpu", ""))[:800],
        "service": str(data.get("service", ""))[:800],
        "logs": str(data.get("journal", ""))[-1500:]
    }


def analyze(alert, raw):

    payload = {
        "alert": alert,
        "metrics_summary": summarize(raw)
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)}
            ]
        )

        content = response.choices[0].message.content

        return json.loads(content)

    except Exception as e:
        print("AI ERROR:", str(e))

        # Safe fallback so pipeline doesn't break
        return {
            "root_cause": "AI analysis failed",
            "pattern": "unknown",
            "prediction": "unknown",
            "recommended_action": "manual investigation",
            "playbook_type": "unknown",
            "confidence": 0.1
        }
