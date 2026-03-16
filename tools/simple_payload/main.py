import requests
import re

url = "https://raw.githubusercontent.com/shad0w2000/shad0w-conn/main/main.json"

def get_remote_vars():
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        text_data = response.text
        
        host_match = re.search(r"HOST\s*=\s*['\"]([^'\"]+)['\"]", text_data)
        port_match = re.search(r"PORT\s*=\s*(\d+)", text_data)
        
        if host_match and port_match:
            host = host_match.group(1)
            port = int(port_match.group(1))
            return host, port
        else:
            print("[-] لم يتم العثور على المتغيرات داخل الملف.")
            return None, None

    except Exception as e:
        print(f"❌ حدث خطأ: {e}")
        return None, None

HOST, PORT = get_remote_vars()

if HOST and PORT:
    print(f"✅ تم جلب البيانات بنجاح!")
    print(f"الـ HOST هو: {HOST}")
    print(f"الـ PORT هو: {PORT}")
else:
    print("[-] فشل استخراج البيانات.")