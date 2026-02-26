import random
from datetime import datetime

# 50 users mapped to 50 IPs
USER_IP_MAP = {
    f"user{i}": f"192.168.1.{i}"
    for i in range(1, 51)
}

LEVELS = {
    0: {"name": "suspicious", "color": "#888888"},
    1: {"name": "low", "color": "#00FF00"},
    2: {"name": "medium", "color": "#FFFF00"},
    3: {"name": "high", "color": "#FFA500"},   # orange
    4: {"name": "critical", "color": "#FF0000"},  # red
}

STATUSES = [
    "logged",
    "investigating",
    "escalated",
    "contained"
]

# Weighted event types (low-level events much more common)
EVENT_TYPE_WEIGHTS = (
    ["port_scan_detected"] * 40 +            # suspicious
    ["failed_login_attempt"] * 30 +          # low
    ["privilege_escalation_attempt"] * 15 +  # medium
    ["suspicious_process"] * 10 +            # high
    ["malware_signature_match"] * 5          # critical
)

# Deterministic level mapping
EVENT_LEVEL_MAP = {
    "port_scan_detected": 0,
    "failed_login_attempt": 1,
    "privilege_escalation_attempt": 2,
    "suspicious_process": 3,
    "malware_signature_match": 4
}

def generate_event():
    user = random.choice(list(USER_IP_MAP.keys()))
    ip = USER_IP_MAP[user]

    event_type = random.choice(EVENT_TYPE_WEIGHTS)
    level = EVENT_LEVEL_MAP[event_type]

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "source": ip,
        "type": event_type,
        "level": level,
        "severity": LEVELS[level]["name"],
        "color": LEVELS[level]["color"],
        "status": random.choice(STATUSES)
    }
