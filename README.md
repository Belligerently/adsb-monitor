# ADS-B Feeder Monitor

A simple GTK4 desktop app for keeping an eye on your [adsb.im](https://adsb.im) feeder without needing a browser tab open.

Shows aircraft stats, message rates, and aggregator status in a native Linux app.

## Requirements

- Python 3.8+
- GTK 4
- libadwaita

## Install

### Arch (AUR)

```bash
yay -S adsb-monitor
```

### Arch (manual)

```bash
sudo pacman -S python-gobject gtk4 libadwaita
```

### Ubuntu/Debian (24.04+)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

### Fedora

```bash
sudo dnf install python3-gobject gtk4 libadwaita
```

## Run

```bash
python3 adsb_monitor.py
```

Or use the install script to set it up system-wide:

```bash
./install.sh
```

## Config

Hit the menu button → Settings to change:

- Feeder URL (default: `http://adsb-feeder.local`)
- Refresh interval

## License

MIT

