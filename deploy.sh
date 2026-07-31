#!/usr/bin/env bash

# ====================================================================
# AqilUstun Bridge — Deployment & Server Management Script
# ====================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Ushbu buyruqni root huquqlari bilan bajarish kerak (masalan: sudo ./deploy.sh $1)"
        exit 1
    fi
}

install_system_deps() {
    print_info "Tizim paketlarini tekshirish va o'rnatish..."
    if command -v apt-get &> /dev/null; then
        apt-get update -qq
        apt-get install -y -qq python3 python3-venv python3-pip ufw git
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip git
    fi
}

setup_env() {
    print_info "Python Virtual Muhitini (venv) sozlash..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "venv yaratildi."
    fi

    print_info "Kutubxonalarni o'rnatish (pip install)..."
    ./venv/bin/pip install --upgrade pip -q
    ./venv/bin/pip install -r requirements.txt -q
    print_success "Kutubxonalar muvaffaqiyatli o'rnatildi."

    if [ ! -f "config.py" ]; then
        print_warning "config.py fayli topilmadi. config.example.py dan nusxa olinmoqda..."
        cp config.example.py config.py
        print_warning "DIQQAT: config.py faylini tahrirlab, SERVER_IP va GEMINI_API_KEY qiymatlarini kiriting!"
    fi
}

setup_services() {
    print_info "Systemd servislari yaratilmoqda va sozlanmoqda..."

    # Create aqilustun-bridge.service dynamically
    cat <<EOF > /etc/systemd/system/aqilustun-bridge.service
[Unit]
Description=AqilUstun SIP Bridge & Gemini Live AI Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/venv/bin/python3 ai_call_server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    # Create aqilustun-dashboard.service dynamically
    cat <<EOF > /etc/systemd/system/aqilustun-dashboard.service
[Unit]
Description=AqilUstun Web Admin Dashboard Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/venv/bin/python3 dashboard.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable aqilustun-bridge aqilustun-dashboard
    systemctl restart aqilustun-bridge aqilustun-dashboard

    print_success "Systemd servislari muvaffaqiyatli o'rnatildi va ishga tushirildi!"
}

setup_firewall() {
    SIP_P=$(grep -E "^SIP_PORT\s*=" config.py 2>/dev/null | cut -d'=' -f2 | tr -d ' "' || echo "5060")
    RTP_P=$(grep -E "^RTP_PORT\s*=" config.py 2>/dev/null | cut -d'=' -f2 | tr -d ' "' || echo "10000")
    DASH_P=$(grep -E "^DASHBOARD_PORT\s*=" config.py 2>/dev/null | cut -d'=' -f2 | tr -d ' "' || echo "8000")

    SIP_P=${SIP_P:-5060}
    RTP_P=${RTP_P:-10000}
    DASH_P=${DASH_P:-8000}

    if command -v ufw &> /dev/null; then
        print_info "UFW Firewall portlarini ochish ($SIP_P/udp, $RTP_P/udp, $DASH_P/tcp)..."
        ufw allow "${SIP_P}/udp" comment 'SIP Signalling'
        ufw allow "${RTP_P}/udp" comment 'RTP Audio Stream'
        ufw allow "${DASH_P}/tcp" comment 'Web Dashboard'
        ufw allow 22/tcp comment 'SSH'
        print_success "Firewall portlari (${SIP_P}/udp, ${RTP_P}/udp, ${DASH_P}/tcp) sozlandi."
    fi
}

cmd_setup() {
    check_root "setup"
    print_info "=================================================="
    print_info " AqilUstun Bridge — To'liq Serverga O'rnatish "
    print_info "=================================================="
    install_system_deps
    setup_env
    setup_services
    setup_firewall
    print_success "O'rnatish yakunlandi! Servislar holatini ko'rish uchun: ./deploy.sh status"
}

cmd_update() {
    print_info "Loyihani yangilash (Git pull & pip install & restart)..."
    if [ -d ".git" ]; then
        git pull
    fi
    setup_env
    if [ "$EUID" -eq 0 ]; then
        systemctl restart aqilustun-bridge aqilustun-dashboard
        print_success "Servislar qayta ishga tushirildi!"
    else
        print_warning "Servislarni qayta ishga tushirish uchun sudo kerak: sudo systemctl restart aqilustun-bridge aqilustun-dashboard"
    fi
}

cmd_start() {
    check_root "start"
    systemctl start aqilustun-bridge aqilustun-dashboard
    print_success "Servislar ishga tushirildi."
}

cmd_stop() {
    check_root "stop"
    systemctl stop aqilustun-bridge aqilustun-dashboard
    print_success "Servislar to'xtatildi."
}

cmd_restart() {
    check_root "restart"
    systemctl restart aqilustun-bridge aqilustun-dashboard
    print_success "Servislar qayta ishga tushirildi."
}

cmd_status() {
    print_info "--- aqilustun-bridge holati ---"
    systemctl status aqilustun-bridge --no-pager || true
    echo ""
    print_info "--- aqilustun-dashboard holati ---"
    systemctl status aqilustun-dashboard --no-pager || true
}

cmd_logs() {
    SERVICE=${2:-bridge}
    if [ "$SERVICE" == "dashboard" ]; then
        print_info "Dashboard jonli loglari (Chiqish uchun Ctrl+C):"
        journalctl -u aqilustun-dashboard -f
    else
        print_info "Bridge SIP/RTP server jonli loglari (Chiqish uchun Ctrl+C):"
        journalctl -u aqilustun-bridge -f
    fi
}

cmd_enable_sip() {
    print_info "Hikvision Domofon SIP sozlamalarini yuborish..."
    if [ -f "venv/bin/python3" ]; then
        ./venv/bin/python3 enable_sip_server.py
    else
        python3 enable_sip_server.py
    fi
}

show_help() {
    echo -e "${GREEN}AqilUstun Bridge — Boshqaruv Skripti${NC}"
    echo ""
    echo "Foydalanish: ./deploy.sh [BUYRUQ]"
    echo ""
    echo "Buyruqlar:"
    echo "  setup        - Serverga to'liq birinchi marta o'rnatish (root kerak)"
    echo "  update       - Git o'zgarishlarni tortib olish, venv yangilash va qayta ishga tushirish"
    echo "  start        - Servislarni ishga tushirish (root kerak)"
    echo "  stop         - Servislarni to'xtatish (root kerak)"
    echo "  restart      - Servislarni qayta ishga tushirish (root..."
    echo "  status       - Servislar holatini ko'rish"
    echo "  logs [b|d]   - Jonli loglarni kuzatish (b: bridge, d: dashboard)"
    echo "  enable-sip   - Domofonga SIP server sozlamalarini yuborish"
    echo "  help         - Ushbu yordam oynasini ko'rsatish"
    echo ""
}

case "$1" in
    setup)       cmd_setup ;;
    update)      cmd_update ;;
    start)       cmd_start ;;
    stop)        cmd_stop ;;
    restart)     cmd_restart ;;
    status)      cmd_status ;;
    logs)        cmd_logs "$@" ;;
    enable-sip)  cmd_enable_sip ;;
    help|*)      show_help ;;
esac
