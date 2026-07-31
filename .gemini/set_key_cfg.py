import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
url = "http://192.168.0.176/ISAPI/VideoIntercom/keyCfg"

xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
<KeyCfgList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<KeyCfg version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<id>1</id>
<module>main</module>
<callMethod>callNumber</callMethod>
<callNumber>100</callNumber>
<enableCallCenter>true</enableCallCenter>
<templateNo>1</templateNo>
</KeyCfg>
</KeyCfgList>"""

r = requests.put(url, auth=auth, data=xml_payload.encode('utf-8'), headers={"Content-Type": "application/xml"})
print("PUT Status:", r.status_code)
print("Response:", r.text)

# Also check GET after update
r_get = requests.get(url, auth=auth)
print("\nGET Status:", r_get.status_code)
print(r_get.text)
