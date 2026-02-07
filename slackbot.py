import os
import requests

SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack(result):

    message = f"""
🚨 *Nagios AI Analysis*

*Root Cause:* {result['root_cause']}
*Pattern:* {result['pattern']}
*Prediction:* {result['prediction']}
*Action:* {result['recommended_action']}
*Playbook:* `{result['playbook_type']}`
*Confidence:* {result['confidence']}
"""

    requests.post(SLACK_URL, json={"text": message})
