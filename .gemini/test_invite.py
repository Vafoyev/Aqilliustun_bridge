import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(4)

sip_invite = (
    "INVITE sip:100@195.158.8.44:5070 SIP/2.0\r\n"
    "Via: SIP/2.0/UDP 192.168.0.176:5060;rport;branch=z9hG4bKtestinvite1\r\n"
    "From: <sip:100@195.158.8.44>;tag=from123\r\n"
    "To: <sip:100@195.158.8.44>\r\n"
    "Call-ID: testinviteid123@192.168.0.176\r\n"
    "CSeq: 1 INVITE\r\n"
    "Contact: <sip:100@192.168.0.176:5060>\r\n"
    "Max-Forwards: 70\r\n"
    "Content-Type: application/sdp\r\n"
    "Content-Length: 135\r\n\r\n"
    "v=0\r\n"
    "o=KV6114 1000 1000 IN IP4 192.168.0.176\r\n"
    "s=Call\r\n"
    "c=IN IP4 192.168.0.176\r\n"
    "t=0 0\r\n"
    "m=audio 10000 RTP/AVP 0\r\n"
    "a=rtpmap:0 PCMU/8000\r\n"
)

try:
    sock.sendto(sip_invite.encode(), ('195.158.8.44', 5070))
    print("Test SIP INVITE sent. Waiting for response...")
    data, addr = sock.recvfrom(2048)
    print(f"RESPONSE 1 FROM {addr}:\n", data.decode('utf-8', errors='ignore'))
    data2, addr2 = sock.recvfrom(2048)
    print(f"RESPONSE 2 FROM {addr2}:\n", data2.decode('utf-8', errors='ignore'))
except socket.timeout:
    print("TIMEOUT on INVITE test!")
except Exception as e:
    print("Error:", e)
