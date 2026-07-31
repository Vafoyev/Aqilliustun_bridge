import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
url = "http://192.168.0.176/ISAPI/System/Network/SIP"

xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<SIPServerList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<SIPServer>
<id>1</id>
<Standard>
<enabled>true</enabled>
<proxy>195.158.8.44</proxy>
<proxyPort>5070</proxyPort>
<userName>100</userName>
<displayName>KV6114</displayName>
<authID>100</authID>
<password>Q112233q</password>
<expires>60</expires>
</Standard>
</SIPServer>
</SIPServerList>"""

r = requests.put(url, auth=auth, data=xml_data.encode('utf-8'), headers={"Content-Type": "application/xml"})
print("PUT Status:", r.status_code)
print("PUT Response:", r.text)

r_get = requests.get(url, auth=auth)
print("\nGET Response:\n", r_get.text)
