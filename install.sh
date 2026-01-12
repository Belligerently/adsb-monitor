#!/bin/bash
# ADS-B Feeder Monitor Installer

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║     ADS-B Feeder Monitor - Installer         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Detect package manager and install dependencies
install_dependencies() {
    echo "📦 Installing system dependencies..."
    
    if command -v apt &> /dev/null; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y python3-gobject gtk4 libadwaita
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -S --noconfirm python-gobject gtk4 libadwaita
    elif command -v zypper &> /dev/null; then
        # openSUSE
        sudo zypper install -y python3-gobject gtk4 libadwaita
    else
        echo "❌ Unsupported package manager. Please install dependencies manually:"
        echo "   - python3-gi (PyGObject)"
        echo "   - GTK 4"
        echo "   - libadwaita"
        exit 1
    fi
}

# Install application
install_app() {
    echo ""
    echo "📁 Installing application..."
    
    # Create installation directory
    sudo mkdir -p /opt/adsb-monitor
    
    # Copy files
    sudo cp adsb_monitor.py /opt/adsb-monitor/
    sudo chmod +x /opt/adsb-monitor/adsb_monitor.py
    
    # Install desktop file
    sudo cp adsb-monitor.desktop /usr/share/applications/
    
    # Create symlink for easy command-line access
    sudo ln -sf /opt/adsb-monitor/adsb_monitor.py /usr/local/bin/adsb-monitor
    
    echo ""
    echo "✅ Installation complete!"
    echo ""
    echo "You can now:"
    echo "  • Launch from your application menu (search for 'ADS-B')"
    echo "  • Run from terminal: adsb-monitor"
    echo ""
}

# Main installation
echo "This will install ADS-B Feeder Monitor on your system."
echo ""
read -p "Continue? [Y/n] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

install_dependencies
install_app

echo "🛫 Happy tracking!"
