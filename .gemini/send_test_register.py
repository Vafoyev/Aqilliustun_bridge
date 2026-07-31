import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sip_register = (
    "REGISTER sip:195.158.8.44:5070 SIP/2.0\r\n"
    "Via: SIP/2.0/UDP 192.168.0.176:5060;rport;branch=z9hG4bKregister123\r\n"
    "From: <sip:100@195.158.8.44>;tag=regtag123\r\n"
    "To: <sip:100@195.158.8.44>\r\n"
    "Call-ID: testregid12345@192.168.0.176\r\n"
    "CSeq: 1 REGISTER\r\n"
    "Contact: <sip:100@192.168.0.176:5060>\r\n"
    "Expires: 60\r\n"
    "Max-Forwards: 70\r\n"
    "Content-Length: 0\r\n\r\n"
)

sock.sendto(sip_register.encode(), ('195.158.8.44', 5070))
print("Sent test SIP REGISTER packet to 195.158.8.44:5070!")
