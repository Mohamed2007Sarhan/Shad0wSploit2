import argparse
import json
import subprocess
import traceback
import platform

def run_nslookup(domain, record_type):
    try:
        cmd = f"nslookup -type={record_type} {domain}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return process.stdout
    except Exception as e:
        return str(e)

def parse_nslookup(output, record_type):
    lines = output.splitlines()
    results = []
    
    # Very basic parsing, nslookup output varies by OS
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Server:") or line.startswith("Address:"):
            # skip the first two lines which are usually the DNS server used
            continue
            
        if record_type == "A" and "Address:" in line:
            parts = line.split("Address:")
            if len(parts) > 1:
                results.append(parts[1].strip())
        elif record_type == "MX" and "mail exchanger" in line:
            parts = line.split("exchanger =")
            if len(parts) > 1:
                results.append(parts[1].strip())
        elif record_type == "TXT" and "text =" in line:
            parts = line.split("text =")
            if len(parts) > 1:
                results.append(parts[1].strip().strip('"'))
                
    # fallback generic extraction if above fails
    if not results:
        results = [line for line in lines if line and not line.startswith("Server:") and "Address:" not in line[:20]]
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Retrieves A, MX, and TXT records for a domain.")
    parser.add_argument("--domain", type=str, required=True, help="Domain to lookup")
    args = parser.parse_args()

    try:
        # We can try to use socket for basic A record first
        import socket
        basic_a = []
        try:
            _, _, ipaddrlist = socket.gethostbyname_ex(args.domain)
            basic_a = ipaddrlist
        except socket.error:
            pass

        # Use dnspython if available, else fallback to nslookup
        try:
            import dns.resolver
            resolver = dns.resolver.Resolver()
            
            records = {"A": [], "MX": [], "TXT": []}
            
            for qtype in ["A", "MX", "TXT"]:
                try:
                    answers = resolver.resolve(args.domain, qtype)
                    for rdata in answers:
                        records[qtype].append(rdata.to_text().strip('"'))
                except Exception:
                    pass
                    
            if not records["A"] and basic_a:
                records["A"] = basic_a
                
        except ImportError:
            # Fallback to nslookup subprocess
            a_out = run_nslookup(args.domain, "A")
            mx_out = run_nslookup(args.domain, "MX")
            txt_out = run_nslookup(args.domain, "TXT")
            
            records = {
                "A": parse_nslookup(a_out, "A") if not basic_a else basic_a,
                "MX": parse_nslookup(mx_out, "MX"),
                "TXT": parse_nslookup(txt_out, "TXT"),
                "note": "Used nslookup fallback because dnspython is not installed."
            }

        result = {
            "status": "success",
            "domain": args.domain,
            "records": records
        }
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
