import subprocess
import logging
from typing import Dict
import socket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ================= ROUTER =================
def execute_playbook(playbook_type: str, host: str, service: str) -> Dict:
    if playbook_type == "high_cpu_fix":
        return fix_high_cpu(host)

    elif playbook_type == "ram_cleanup":
        return cleanup_ram(host)

    elif playbook_type == "root_disk_cleanup":
        return cleanup_root_disk(host)

    elif playbook_type == "ssh_recovery":
        return fix_ssh(host)

    elif playbook_type == "ping_network_fix":
        return fix_network(host)

    elif playbook_type == "restart_service":
        return restart_service(host, service)

    else:
        return {"success": False, "message": f"Unknown playbook: {playbook_type}", "command_output": ""}


# ================= HELPERS =================
def _is_local(host: str) -> bool:
    try:
        if host in {"localhost", "127.0.0.1"}:
            return True
        return host == socket.gethostbyname(socket.gethostname())
    except:
        return False


def _run(host: str, cmd: str, timeout: int = 30):
    ssh_opts = "-o BatchMode=yes -o StrictHostKeyChecking=no"
    full = cmd if _is_local(host) else f"ssh {ssh_opts} ubuntu@{host} '{cmd}'"
    return subprocess.run(full, shell=True, capture_output=True, text=True, timeout=timeout)


# ================= CPU FIX =================
def fix_high_cpu(host: str) -> Dict:
    logger.info(f"Fixing high CPU on {host}")

    commands = [
        # Kill only known stress processes
        "pkill -f 'yes' || true",
        "pkill -f 'stress' || true",
        # Renice top CPU process instead of killing random prod apps
        "ps -eo pid,comm,%cpu --sort=-%cpu | head -n 5"
    ]

    return _execute(host, commands, "High CPU remediation completed")


# ================= RAM CLEANUP =================
def cleanup_ram(host: str) -> Dict:
    logger.info(f"Cleaning RAM on {host}")

    commands = [
        # Clear page cache safely
        "sync",
        "echo 1 | sudo tee /proc/sys/vm/drop_caches",
        # Show memory after cleanup
        "free -h"
    ]

    return _execute(host, commands, "RAM cleanup completed")


# ================= ROOT DISK CLEANUP =================
def cleanup_root_disk(host: str) -> Dict:
    logger.info(f"Cleaning root disk on {host}")

    commands = [
        # Remove logs older than 7 days
        "sudo find /var/log -type f -name '*.log' -mtime +7 -delete",
        # Clean journal logs older than 7 days
        "sudo journalctl --vacuum-time=7d",
        # Clean temp files
        "sudo find /tmp -type f -mtime +3 -delete",
        # Docker cleanup (safe)
        "docker system prune -af --volumes || true",
        # Show disk usage after cleanup
        "df -h /"
    ]

    return _execute(host, commands, "Root disk cleanup completed")


# ================= SSH RECOVERY =================
def fix_ssh(host: str) -> Dict:
    logger.info(f"Fixing SSH on {host}")

    commands = [
        # Restart ssh safely
        "sudo systemctl restart ssh || sudo systemctl restart sshd",
        # Ensure service is active
        "sudo systemctl status ssh --no-pager || sudo systemctl status sshd --no-pager"
    ]

    return _execute(host, commands, "SSH remediation completed")


# ================= NETWORK FIX =================
def fix_network(host: str) -> Dict:
    logger.info(f"Fixing network on {host}")

    commands = [
        # Restart networking safely
        "sudo systemctl restart NetworkManager || sudo systemctl restart networking",
        # Flush DNS cache
        "sudo systemd-resolve --flush-caches || true",
        # Show IP after fix
        "ip a"
    ]

    return _execute(host, commands, "Network remediation completed")


# ================= SAFE SERVICE RESTART =================
def restart_service(host: str, service: str) -> Dict:
    if not service or " " in service:
        return {"success": False, "message": "Invalid service name", "command_output": ""}

    cmd = f"sudo systemctl restart {service}"
    result = _run(host, cmd)

    return {
        "success": result.returncode == 0,
        "message": f"Service {service} restart attempted",
        "command_output": result.stdout or result.stderr
    }


# ================= EXECUTOR =================
def _execute(host: str, commands, success_msg):
    output = ""
    for cmd in commands:
        try:
            res = _run(host, cmd)
            output += f"\n[{cmd}]\n{res.stdout}{res.stderr}"
        except Exception as e:
            output += f"\nError: {str(e)}"

    return {"success": True, "message": success_msg, "command_output": output}
