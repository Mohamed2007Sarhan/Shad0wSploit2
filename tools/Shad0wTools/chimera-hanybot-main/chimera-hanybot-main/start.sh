
#!/bin/bash

# تعريف الألوان للطباعة
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}
==============================================
   CHIMERA ELITE DEFENSE SYSTEM - DEPLOYER
   Target: Automated Docker Deployment
==============================================
${NC}"

# 1. التأكد من صلاحيات الـ Root
if [ "$EUID" -ne 0 ]
  then echo -e "${RED}[!] Please run as ROOT (sudo ./deploy.sh)${NC}"
  exit
fi

# 2. تنظيف الساحة (إيقاف وحذف أي نسخة قديمة)
echo -e "${YELLOW}[*] Cleaning up old containers...${NC}"
docker stop chimera-defense 2>/dev/null
docker rm chimera-defense 2>/dev/null

# 3. بناء الصورة (Build)
echo -e "${YELLOW}[*] Building the weapon (Docker Image)...${NC}"
docker build -t chimera-elite .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[+] Build Successful!${NC}"
else
    echo -e "${RED}[!] Build Failed. Check your Dockerfile or chimera.py${NC}"
    exit 1
fi

# 4. التشغيل (Run)
echo -e "${GREEN}[*] LAUNCHING CHIMERA DEFENSE SYSTEM...${NC}"
echo -e "${YELLOW}[!] Mapping Ports: 22->2222, 80->8080, 21->2121, 9999->9999${NC}"
echo -e "${YELLOW}[!] Activating NET_ADMIN capabilities...${NC}"

# تشغيل الأمر النهائي
docker run -it --rm \
  --cap-add=NET_ADMIN \
  -p 22:2222 \
  -p 80:8080 \
  -p 21:2121 \
  -p 9999:9999 \
  --name chimera-defense \
  chimera-elite


# ... (بعد كود تشغيل الكونتينر)

echo -e "${YELLOW}[*] Securing Network Perimeter (Firewall Rules)...${NC}"

# 1. الحصول على الـ Subnet الخاص بشبكة الدوكر
DOCKER_SUBNET=$(docker inspect chimera-defense --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' | cut -d'.' -f1-3).0/24

# 2. حماية شبكتك المحلية (Private Ranges)
# لن نسمح للكونتينر بالاتصال بالروتر أو أجهزتك الأخرى
# (DOCKER-USER هي السلسلة المخصصة لتعديلات المستخدم في دوكر)

# منع الاتصال بـ 192.168.x.x (الشبكات المنزلية المعتادة)
sudo iptables -I DOCKER-USER -s $DOCKER_SUBNET -d 192.168.0.0/16 -j DROP

# منع الاتصال بـ 10.x.x.x (شبكات الشركات والـ VPN الداخلية لو كانت تبعك)
sudo iptables -I DOCKER-USER -s $DOCKER_SUBNET -d 10.0.0.0/8 -j DROP

# 3. السماح بالرد (Established) والهجوم المضاد (New Outbound to non-private)
# القواعد الافتراضية ستسمح بالباقي، مما يعني أن الهجوم المضاد سيعمل فقط 
# إذا كان المهاجم ليس في نفس الشبكة المحلية الخاصة بك.

echo -e "${GREEN}[+] Network Isolation Active: Container cannot touch your LAN.${NC}"


# sudo docker build -t chimera-elite .
# sudo docker run -it --rm --cap-add=NET_ADMIN -p 22:2222 -p 80:8080 -p 21:2121 -p 9999:9999 --name chimera-defense chimera-elite


