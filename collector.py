import subprocess

def run(cmd: str) -> str:
    return subprocess.getoutput(cmd)


def collect_data(alert: dict) -> dict:
    service = alert.get("service")

    service_status = ""
    if service:
        service_status = run(f"systemctl status {service}")

    return {
        "journal": run("journalctl -n 200"),
        "dmesg": run("dmesg | tail -50"),
        "disk": run("df -h"),
        "cpu": run("top -b -n1 | head -20"),
        "service": service_status
    }
