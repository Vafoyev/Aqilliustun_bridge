import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

endpoints = [
    "/ISAPI/VideoIntercom/pressButtonToCall",
    "/ISAPI/VideoIntercom/callTarget",
    "/ISAPI/VideoIntercom/dialPlan",
    "/ISAPI/VideoIntercom/buttonPlan",
    "/ISAPI/VideoIntercom/bindSIP",
    "/ISAPI/VideoIntercom/sipNumber",
    "/ISAPI/VideoIntercom/callingChannel"
]

for ep in endpoints:
    try:
        r = requests.get(host + ep, auth=auth, timeout=3)
        print(f"=== {ep} (Status: {r.status_code}) ===")
        if r.status_code == 200:
            print(r.text)
    except Exception as e:
        print(f"=== {ep} ERROR: {e} ===")
