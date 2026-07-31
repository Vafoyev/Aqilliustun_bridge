import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

eps = [
    "/ISAPI/VideoIntercom/keyCfg",
    "/ISAPI/VideoIntercom/callPriority",
    "/ISAPI/VideoIntercom/phoneCfg",
    "/ISAPI/VideoIntercom/callCfg",
    "/ISAPI/VideoIntercom/keyCfg/capabilities"
]

for ep in eps:
    r = requests.get(host + ep, auth=auth)
    print(f"=== {ep} (Status: {r.status_code}) ===")
    if r.status_code == 200:
        print(r.text)
