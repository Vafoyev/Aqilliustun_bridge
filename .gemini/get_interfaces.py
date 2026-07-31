import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

r_get = requests.get(host + "/ISAPI/System/Network/interfaces", auth=auth)
print("GET Interfaces Status:", r_get.status_code)
print(r_get.text)
