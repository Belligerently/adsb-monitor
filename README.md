# ADS-B Feeder Monitor

A native Linux desktop application for monitoring your [adsb.im](https://adsb.im) ADS-B feeder. Built with GTK4 and libadwaita for a beautiful GNOME-native experience.

## ✨ Features

- 🎨 **Native GTK4/libadwaita UI** - Beautiful design that fits right into your GNOME desktop
- 📊 **Real-time Stats** - Aircraft count, message rate, position rate, temperature, uptime
- 📡 **Aggregator Status** - See feeding status for all your aggregators at a glance
- 🔄 **Auto-refresh** - Data updates automatically (configurable interval)
- 🌐 **Quick Browser Access** - One-click to open full web interface
- ⚙️ **Configurable** - Change feeder URL and refresh interval in settings

## 📋 Requirements

- Linux with GTK4 support
- Python 3.8+
- GTK 4
- libadwaita 1.0+

## 🚀 Quick Install

```bash
git clone https://github.com/yourusername/adsb-monitor.git
cd adsb-monitor
chmod +x install.sh
./install.sh
```

## 📦 Manual Installation

### Ubuntu/Debian (24.04+)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

### Fedora

```bash
sudo dnf install python3-gobject gtk4 libadwaita
```

### Arch Linux

```bash
sudo pacman -S python-gobject gtk4 libadwaita
```

Then run:

```bash
python3 adsb_monitor.py
```

## 🖥️ Desktop Integration

To add to your application menu:

```bash
cp adsb-monitor.desktop ~/.local/share/applications/
```

## ⚙️ Configuration

Click the menu button (☰) → Settings to configure:

- **Feeder URL** - Default: `http://adsb-feeder.local`
- **Refresh Interval** - How often to update data (1-60 seconds)

## 📡 Supported Aggregators

The app shows status for these aggregators (when configured on your feeder):

- adsb.lol
- adsb.fi
- ADSBExchange
- FlightRadar24
- Planespotters
- airplanes.live
- AVDelphi
- TheAirTraffic
- HPRadar
- Fly Italy ADSB
- And more...

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [adsb.im](https://adsb.im) for the excellent ADS-B feeder image
- The GTK and GNOME teams for the amazing toolkit
