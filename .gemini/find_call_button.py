import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

# Test various Hikvision button/dialing endpoints
endpoints = [
    "/ISAPI/VideoIntercom/callButton",
    "/ISAPI/VideoIntercom/pressButtonToCall",
    "/ISAPI/VideoIntercom/callParam",
    "/ISAPI/VideoIntercom/sipParam",
    "/ISAPI/VideoIntercom/callPriority",
    "/ISAPI/VideoIntercom/workMode",
    "/ISAPI/System/deviceInfo"
]

for ep in endpoints:
    try:
        r = requests.get(host + ep, auth=auth, timeout=3)
        print(f"=== {ep} (Status: {r.status_code}) ===")
        if r.status_code == 200:
            print(r.text[:600])
    except Exception as e:
        print(f"=== {ep} ERROR: {e} ===")
