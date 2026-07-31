import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
url = "http://192.168.0.176/ISAPI/System/Network/interfaces/1"

xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<NetworkInterface version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<id>1</id>
<IPAddress version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<ipVersion>dual</ipVersion>
<addressingType>static</addressingType>
<ipAddress>192.168.0.65</ipAddress>
<subnetMask>255.255.255.0</subnetMask>
<DefaultGateway>
<ipAddress>192.168.0.1</ipAddress>
</DefaultGateway>
<PrimaryDNS>
<ipAddress>8.8.8.8</ipAddress>
</PrimaryDNS>
<SecondaryDNS>
<ipAddress>8.8.4.4</ipAddress>
</SecondaryDNS>
</IPAddress>
</NetworkInterface>"""

r = requests.put(url, auth=auth, data=xml_data.encode('utf-8'), headers={"Content-Type": "application/xml"})
print("PUT Interfaces Status:", r.status_code)
print("Response:", r.text)
