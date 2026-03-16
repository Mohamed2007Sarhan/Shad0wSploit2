import argparse
import json
import traceback

def main():
    parser = argparse.ArgumentParser(description="Captures and analyzes the next N network packets using scapy.")
    parser.add_argument("--count", type=int, default=10, help="Number of packets to capture")
    parser.add_argument("--interface", type=str, help="Network interface to sniff on")
    args = parser.parse_args()

    try:
        from scapy.all import sniff, IP, TCP, UDP
        
        captured = []
        
        def packet_callback(packet):
            pkt_info = {
                "summary": packet.summary(),
                "time": float(packet.time),
                "length": len(packet)
            }
            
            if IP in packet:
                pkt_info["src_ip"] = packet[IP].src
                pkt_info["dst_ip"] = packet[IP].dst
                pkt_info["protocol"] = packet[IP].proto
                
            if TCP in packet:
                pkt_info["src_port"] = packet[TCP].sport
                pkt_info["dst_port"] = packet[TCP].dport
                pkt_info["tcp_flags"] = str(packet[TCP].flags)
                
            elif UDP in packet:
                pkt_info["src_port"] = packet[UDP].sport
                pkt_info["dst_port"] = packet[UDP].dport
                
            captured.append(pkt_info)
            
        # Start sniffing
        kwargs = {"prn": packet_callback, "count": args.count, "store": 0}
        if args.interface:
            kwargs["iface"] = args.interface
            
        sniff(**kwargs)
        
        result = {
            "status": "success",
            "capture_count": len(captured),
            "packets": captured
        }
        print(json.dumps(result))
        
    except ImportError:
        error_result = {
            "status": "error",
            "message": "Scapy library is not installed. Run 'pip install scapy'."
        }
        print(json.dumps(error_result))
    except PermissionError:
        error_result = {
            "status": "error",
            "message": "Permission denied. Packet sniffing usually requires root/Administrator privileges."
        }
        print(json.dumps(error_result))
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
