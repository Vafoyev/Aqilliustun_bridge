import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth('admin', 'Q112233q')
host = "http://192.168.0.176"

r = requests.get(host + "/ISAPI/VideoIntercom/capabilities", auth=auth)
print(r.text)
