#!/bin/bash
cd /opt/nagios-ai-agent
source venv/bin/activate
curl -s -X POST http://localhost:8000/scan >> /var/log/nagios-ai-scan.log 2>&1
