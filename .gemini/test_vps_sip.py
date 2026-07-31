import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)

sip_invite = (
    "INVITE sip:100@195.158.8.44:5060 SIP/2.0\r\n"
    "Via: SIP/2.0/UDP 192.168.0.176:5060;rport;branch=z9hG4bK12345\r\n"
    "From: <sip:100@195.158.8.44>;tag=test1234\r\n"
    "To: <sip:100@195.158.8.44>\r\n"
    "Call-ID: testcallid98765@192.168.0.176\r\n"
    "CSeq: 1 INVITE\r\n"
    "Contact: <sip:100@192.168.0.176:5060>\r\n"
    "Max-Forwards: 70\r\n"
    "Content-Type: application/sdp\r\n"
    "Content-Length: 0\r\n\r\n"
)

try:
    sock.sendto(sip_invite.encode(), ('195.158.8.44', 5060))
    print("Test SIP INVITE sent to 195.158.8.44:5060. Waiting for response...")
    data, addr = sock.recvfrom(1024)
    print(f"RECEIVED RESPONSE FROM {addr}:\n", data.decode('utf-8', errors='ignore'))
except socket.timeout:
    print("TIMEOUT! No response received from 195.158.8.44:5060 within 3 seconds.")
except Exception as e:
    print("Error:", e)
