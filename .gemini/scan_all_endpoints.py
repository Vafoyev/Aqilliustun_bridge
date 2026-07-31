import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

test_paths = [
    "/ISAPI/VideoIntercom/SIP/roomList",
    "/ISAPI/VideoIntercom/sipNoList",
    "/ISAPI/VideoIntercom/roomNo",
    "/ISAPI/VideoIntercom/callingNo",
    "/ISAPI/VideoIntercom/callTarget",
    "/ISAPI/VideoIntercom/callParam",
    "/ISAPI/VideoIntercom/deviceNo",
    "/ISAPI/VideoIntercom/capabilities",
    "/ISAPI/VideoIntercom/callingType",
    "/ISAPI/VideoIntercom/SIP/callPlan",
    "/ISAPI/VideoIntercom/SIP/callSchedule",
    "/ISAPI/VideoIntercom/callSchedule",
    "/ISAPI/VideoIntercom/callingChannel"
]

for path in test_paths:
    try:
        r = requests.get(host + path, auth=auth)
        if r.status_code != 404:
            print(f"FOUND ({r.status_code}): {path}")
            print(r.text[:400])
    except Exception as e:
        pass
