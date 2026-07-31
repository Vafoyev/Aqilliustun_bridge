import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

eps = [
    "/ISAPI/VideoIntercom/callerInfo",
    "/ISAPI/VideoIntercom/ringParam",
    "/ISAPI/VideoIntercom/callLinkage",
    "/ISAPI/VideoIntercom/buttonLinkage",
    "/ISAPI/VideoIntercom/dialNo",
    "/ISAPI/VideoIntercom/sipServerList",
    "/ISAPI/VideoIntercom/callingChannel",
    "/ISAPI/VideoIntercom/callRule",
    "/ISAPI/VideoIntercom/callingRule"
]

for ep in eps:
    r = requests.get(host + ep, auth=auth)
    if r.status_code == 200:
        print(f"FOUND 200: {ep}")
        print(r.text[:500])
    else:
        print(f"{ep}: {r.status_code}")
