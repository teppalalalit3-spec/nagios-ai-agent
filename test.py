from nagios_client import fetch_servicelist, extract_critical_services

data = fetch_servicelist()

critical = extract_critical_services(data)

print("\n=== DASHBOARD-LIKE CRITICALS ===")
print(f"COUNT: {len(critical)}\n")

for c in critical:
    print(f"{c['host']} - {c['service']} → {c['output']}")

print("\n===============================")
