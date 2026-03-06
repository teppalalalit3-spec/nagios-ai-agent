import os
import requests

SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack(alert_info, result):
    """
    Send formatted alert to Slack with alert metadata and AI analysis
    
    alert_info: dict with host, service, ip, status
    result: dict with AI analysis results
    """
    
    # Emoji based on status
    status_emoji = "⚠️" if alert_info.get('status') == "WARNING" else "🚨"
    
    message = f"""
{status_emoji} *Nagios AI Alert*

*Status:* {alert_info.get('status', 'N/A')}
*Host:* {alert_info.get('host', 'N/A')}
*Service:* {alert_info.get('service', 'N/A')}
*IP:* {alert_info.get('ip', 'N/A')}

*Root Cause:* {result['root_cause']}
*Pattern:* {result['pattern']}
*Prediction:* {result['prediction']}
*Action:* {result['recommended_action']}
*Playbook:* `{result['playbook_type']}`
*Confidence:* {result['confidence']}
"""

    requests.post(SLACK_URL, json={"text": message})
