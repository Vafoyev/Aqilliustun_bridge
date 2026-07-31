import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
u = "http://192.168.0.176/ISAPI/VideoIntercom/keyCfg/1"

xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
<KeyCfg version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<id>1</id>
<module>main</module>
<callMethod>callCenter</callMethod>
<callNumber>100</callNumber>
<enableCallCenter>true</enableCallCenter>
<templateNo>1</templateNo>
</KeyCfg>"""

r = requests.put(u, auth=auth, data=xml_payload.encode('utf-8'), headers={"Content-Type": "application/xml"})
print(f"PUT {u} Status: {r.status_code}")
print(r.text)

r_get = requests.get("http://192.168.0.176/ISAPI/VideoIntercom/keyCfg", auth=auth)
print("\nGET Status:", r_get.status_code)
print(r_get.text)
