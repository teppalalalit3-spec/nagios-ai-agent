import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

NAGIOS_URL = os.getenv("NAGIOS_STATUSJSON_URL")  # .../statusjson.cgi
NAGIOS_USER = os.getenv("NAGIOS_USER")
NAGIOS_PASS = os.getenv("NAGIOS_PASS")
NAGIOS_BASE = NAGIOS_URL.split("statusjson.cgi")[0]  # Base URL

# Status code mappings (from Nagios statusjson API)
STATUS_MAP = {
    0: "OK",
    1: "WARNING", 
    2: "OK",
    8: "UNKNOWN",
    16: "CRITICAL"
}

# Cache for host IPs
_ip_cache = {}


def fetch_servicelist() -> dict:
    """
    Calls: statusjson.cgi?query=servicelist
    Returns parsed JSON dict.
    """
    auth = HTTPBasicAuth(NAGIOS_USER, NAGIOS_PASS)
    r = requests.get(NAGIOS_URL, params={"query": "servicelist"}, auth=auth, timeout=10)
    r.raise_for_status()
    return r.json()


def get_host_ip(hostname: str) -> str:
    """
    Get IP address from Nagios objectjson API
    """
    if hostname in _ip_cache:
        return _ip_cache[hostname]
    
    try:
        auth = HTTPBasicAuth(NAGIOS_USER, NAGIOS_PASS)
        url = NAGIOS_BASE + "objectjson.cgi"
        r = requests.get(url, params={"query": "host", "hostname": hostname}, auth=auth, timeout=10)
        r.raise_for_status()
        
        data = r.json()
        host_data = data.get("data", {}).get("host", {})
        ip = host_data.get("address", "Unknown")
        
        _ip_cache[hostname] = ip
        return ip
    except Exception as e:
        print(f"Error getting IP for {hostname}: {e}")
        return "Unknown"


def extract_critical_services(servicelist_json: dict) -> list[dict]:
    """
    Extracts all services with WARNING or CRITICAL status.
    Returns list of dicts: {host, service, state, state_name, output, perf_data}
    """
    critical = []

    # Expected structure from statusjson.cgi:
    # data -> servicelist -> host -> service -> state_code
    data = servicelist_json.get("data", {})
    servicelist = data.get("servicelist", {})

    for host, services in servicelist.items():
        # services is a dict keyed by service description
        for svc_name, state in services.items():
            # state is directly the integer status code
            try:
                state = int(state)
            except Exception:
                continue

            # Map state to name
            state_name = STATUS_MAP.get(state, "OK")
            
            # Only include WARNING (1) and CRITICAL (16)
            if state in [1, 16]:
                critical.append({
                    "host": host,
                    "service": svc_name,
                    "state": state,
                    "state_name": state_name,
                    "output": f"{host} - {svc_name}",
                    "perf_data": ""
                })

    return critical
