import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

endpoints = [
    "/ISAPI/System/Network/SIP",
    "/ISAPI/VideoIntercom/ringtone",
    "/ISAPI/VideoIntercom/callPlan",
    "/ISAPI/VideoIntercom/callerInfo"
]

for ep in endpoints:
    try:
        r = requests.get(host + ep, auth=auth, timeout=3)
        print(f"=== {ep} (Status: {r.status_code}) ===")
        print(r.text[:500])
        print("\n")
    except Exception as e:
        print(f"=== {ep} ERROR: {e} ===")
