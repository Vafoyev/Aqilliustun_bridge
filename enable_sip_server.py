import requests
from requests.auth import HTTPDigestAuth
import config

auth = HTTPDigestAuth(config.KV6114_USERNAME, config.KV6114_PASSWORD)
url = f"http://{config.KV6114_IP}/ISAPI/System/Network/SIP"

xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<SIPServerList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<SIPServer>
<id>1</id>
<Standard>
<enabled>true</enabled>
<proxy>192.0.0.64</proxy>
<proxyPort>5060</proxyPort>
<userName>100</userName>
<displayName>KV6114</displayName>
<authID>100</authID>
<password>Q112233q</password>
<expires>60</expires>
</Standard>
</SIPServer>
</SIPServerList>"""

r = requests.put(url, auth=auth, data=xml_data, headers={"Content-Type": "application/xml"})
print("PUT Status Code:", r.status_code)
print("Response text:", r.text)

r_get = requests.get(url, auth=auth)
print("\nGET Status after PUT:", r_get.status_code)
print("GET Response:", r_get.text)
