#!/usr/bin/env python3
"""
ADS-B Feeder Monitor
A native desktop application for monitoring your ADS-B feeder
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio, Gdk
import json
import urllib.request
import urllib.error
import threading
import re
from datetime import datetime

APP_ID = "com.adsb.monitor"
DEFAULT_URL = "http://adsb-feeder.local"


class AggregatorRow(Gtk.Box):
    """A row displaying aggregator status"""
    def __init__(self, name, enabled=False, data=False, mlat=False, status="unknown"):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        
        # Name
        name_label = Gtk.Label(label=name)
        name_label.set_halign(Gtk.Align.START)
        name_label.set_hexpand(True)
        name_label.set_width_chars(20)
        self.append(name_label)
        
        # Enabled indicator
        enabled_icon = Gtk.Image()
        if enabled == "warning":
            enabled_icon.set_from_icon_name("dialog-warning-symbolic")
            enabled_icon.add_css_class("warning-icon")
            enabled_icon.set_tooltip_text("Degraded")
        elif enabled:
            enabled_icon.set_from_icon_name("object-select-symbolic")
            enabled_icon.add_css_class("success-icon")
            enabled_icon.set_tooltip_text("Enabled")
        else:
            enabled_icon.set_from_icon_name("process-stop-symbolic")
            enabled_icon.add_css_class("error-icon")
            enabled_icon.set_tooltip_text("Disabled")
        self.append(enabled_icon)
        
        # Data indicator
        data_icon = Gtk.Image()
        if data == "warning":
            data_icon.set_from_icon_name("dialog-warning-symbolic")
            data_icon.add_css_class("warning-icon")
            data_icon.set_tooltip_text("Data Degraded")
        elif data:
            data_icon.set_from_icon_name("list-add-symbolic")
            data_icon.add_css_class("success-icon")
            data_icon.set_tooltip_text("Sending Data")
        else:
            data_icon.set_from_icon_name("list-remove-symbolic")
            data_icon.add_css_class("neutral-icon")
            data_icon.set_tooltip_text("No Data")
        data_icon.set_margin_start(24)
        self.append(data_icon)
        
        # MLAT indicator
        mlat_icon = Gtk.Image()
        if mlat == "warning":
            mlat_icon.set_from_icon_name("dialog-warning-symbolic")
            mlat_icon.add_css_class("warning-icon")
            mlat_icon.set_tooltip_text("MLAT Degraded")
        elif mlat == "error":
            mlat_icon.set_from_icon_name("process-stop-symbolic")
            mlat_icon.add_css_class("error-icon")
            mlat_icon.set_tooltip_text("MLAT Down")
        elif mlat:
            mlat_icon.set_from_icon_name("list-add-symbolic")
            mlat_icon.add_css_class("success-icon")
            mlat_icon.set_tooltip_text("MLAT Active")
        else:
            mlat_icon.set_from_icon_name("list-remove-symbolic")
            mlat_icon.add_css_class("neutral-icon")
            mlat_icon.set_tooltip_text("MLAT Not Available")
        mlat_icon.set_margin_start(24)
        self.append(mlat_icon)
        
        # Status/Link icon
        status_icon = Gtk.Image()
        status_icon.set_from_icon_name("web-browser-symbolic")
        status_icon.add_css_class("link-icon")
        status_icon.set_margin_start(24)
        self.append(status_icon)


class StatCard(Gtk.Box):
    """A card displaying a statistic"""
    def __init__(self, title, value, subtitle="", icon_name=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add_css_class("card")
        self.add_css_class("stat-card")
        self.set_margin_start(6)
        self.set_margin_end(6)
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        
        inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        inner_box.set_margin_start(16)
        inner_box.set_margin_end(16)
        inner_box.set_margin_top(12)
        inner_box.set_margin_bottom(12)
        self.append(inner_box)
        
        # Header with icon
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        inner_box.append(header_box)
        
        if icon_name:
            icon = Gtk.Image(icon_name=icon_name)
            icon.add_css_class("dim-label")
            header_box.append(icon)
        
        title_label = Gtk.Label(label=title)
        title_label.add_css_class("dim-label")
        title_label.add_css_class("caption")
        title_label.set_halign(Gtk.Align.START)
        header_box.append(title_label)
        
        # Value
        self.value_label = Gtk.Label(label=value)
        self.value_label.add_css_class("title-1")
        self.value_label.set_halign(Gtk.Align.START)
        inner_box.append(self.value_label)
        
        # Subtitle
        if subtitle:
            self.subtitle_label = Gtk.Label(label=subtitle)
            self.subtitle_label.add_css_class("dim-label")
            self.subtitle_label.add_css_class("caption")
            self.subtitle_label.set_halign(Gtk.Align.START)
            inner_box.append(self.subtitle_label)
        else:
            self.subtitle_label = None
    
    def update(self, value, subtitle=None):
        self.value_label.set_text(str(value))
        if subtitle and self.subtitle_label:
            self.subtitle_label.set_text(subtitle)


class ADSBMonitorWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.set_title("ADS-B Feeder Monitor")
        self.set_default_size(900, 700)
        
        self.feeder_url = DEFAULT_URL
        self.refresh_interval = 5000  # 5 seconds
        self.refresh_timeout_id = None
        
        # Create main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)
        
        # Create header bar
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)
        
        # Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_label = Gtk.Label(label="ADS-B Feeder Monitor")
        title_label.add_css_class("heading")
        title_box.append(title_label)
        self.header.set_title_widget(title_box)
        
        # Refresh button
        self.refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        self.refresh_btn.set_tooltip_text("Refresh Now")
        self.refresh_btn.connect("clicked", self.on_refresh_clicked)
        self.header.pack_start(self.refresh_btn)
        
        # Open in browser button
        browser_btn = Gtk.Button(icon_name="globe-symbolic")
        browser_btn.set_tooltip_text("Open in Browser")
        browser_btn.connect("clicked", self.on_open_browser)
        self.header.pack_start(browser_btn)
        
        # Menu button
        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_btn.set_tooltip_text("Menu")
        menu = Gio.Menu()
        menu.append("Settings", "win.settings")
        menu.append("About", "win.about")
        menu_btn.set_menu_model(menu)
        self.header.pack_end(menu_btn)
        
        # Loading spinner
        self.spinner = Gtk.Spinner()
        self.header.pack_end(self.spinner)
        
        # Create scrolled content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_box.append(scrolled)
        
        # Content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(24)
        scrolled.set_child(content_box)
        
        # Connection status banner
        self.status_banner = Adw.Banner()
        self.status_banner.set_title("Connecting to ADS-B Feeder...")
        self.status_banner.set_button_label("Retry")
        self.status_banner.connect("button-clicked", self.on_refresh_clicked)
        content_box.append(self.status_banner)
        
        # Feeder name header
        self.feeder_name_label = Gtk.Label(label="ADS-B Feeder")
        self.feeder_name_label.add_css_class("title-1")
        self.feeder_name_label.set_halign(Gtk.Align.START)
        self.feeder_name_label.set_margin_top(12)
        self.feeder_name_label.set_margin_bottom(6)
        content_box.append(self.feeder_name_label)
        
        # Stats cards row
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        stats_box.set_homogeneous(True)
        stats_box.set_margin_top(12)
        stats_box.set_margin_bottom(12)
        content_box.append(stats_box)
        
        self.planes_card = StatCard("Aircraft Now", "—", "tracking", "airplane-mode-symbolic")
        stats_box.append(self.planes_card)
        
        self.planes_today_card = StatCard("Aircraft Today", "—", "total seen", "view-list-symbolic")
        stats_box.append(self.planes_today_card)
        
        self.msg_rate_card = StatCard("Message Rate", "—", "msg/sec", "network-transmit-symbolic")
        stats_box.append(self.msg_rate_card)
        
        self.pos_rate_card = StatCard("Position Rate", "—", "pos/sec", "find-location-symbolic")
        stats_box.append(self.pos_rate_card)
        
        # System stats row - only show what we can get from the API
        sys_stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        sys_stats_box.set_homogeneous(True)
        sys_stats_box.set_margin_bottom(24)
        content_box.append(sys_stats_box)
        
        self.temp_card = StatCard("Temperature", "—", "", "weather-clear-symbolic")
        sys_stats_box.append(self.temp_card)
        
        self.uptime_card = StatCard("Uptime", "—", "", "preferences-system-time-symbolic")
        sys_stats_box.append(self.uptime_card)
        
        # Aggregators section
        agg_header = Gtk.Label(label="Feeding Status")
        agg_header.add_css_class("title-2")
        agg_header.set_halign(Gtk.Align.START)
        agg_header.set_margin_top(12)
        agg_header.set_margin_bottom(12)
        content_box.append(agg_header)
        
        # Aggregators list container
        self.aggregators_frame = Gtk.Frame()
        self.aggregators_frame.add_css_class("card")
        content_box.append(self.aggregators_frame)
        
        self.aggregators_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.aggregators_frame.set_child(self.aggregators_box)
        
        # Column headers for aggregators
        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_row.set_margin_start(12)
        header_row.set_margin_end(12)
        header_row.set_margin_top(12)
        header_row.set_margin_bottom(8)
        header_row.add_css_class("dim-label")
        self.aggregators_box.append(header_row)
        
        name_header = Gtk.Label(label="Aggregator")
        name_header.set_halign(Gtk.Align.START)
        name_header.set_hexpand(True)
        name_header.set_width_chars(20)
        header_row.append(name_header)
        
        enabled_header = Gtk.Label(label="Enabled")
        header_row.append(enabled_header)
        
        data_header = Gtk.Label(label="Data")
        data_header.set_margin_start(24)
        header_row.append(data_header)
        
        mlat_header = Gtk.Label(label="MLAT")
        mlat_header.set_margin_start(24)
        header_row.append(mlat_header)
        
        status_header = Gtk.Label(label="Link")
        status_header.set_margin_start(24)
        header_row.append(status_header)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.aggregators_box.append(separator)
        
        # Placeholder for aggregator rows
        self.aggregator_rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.aggregators_box.append(self.aggregator_rows_box)
        
        # Status bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.set_margin_start(12)
        status_bar.set_margin_end(12)
        status_bar.set_margin_top(12)
        status_bar.set_margin_bottom(6)
        self.main_box.append(status_bar)
        
        self.connection_label = Gtk.Label(label="Connecting...")
        self.connection_label.add_css_class("dim-label")
        self.connection_label.set_halign(Gtk.Align.START)
        self.connection_label.set_hexpand(True)
        status_bar.append(self.connection_label)
        
        self.last_update_label = Gtk.Label(label="")
        self.last_update_label.add_css_class("dim-label")
        status_bar.append(self.last_update_label)
        
        # Setup actions
        self.setup_actions()
        
        # Apply CSS
        self.apply_css()
        
        # Initial data load
        GLib.timeout_add(500, self.start_refresh)
    
    def setup_actions(self):
        """Setup window actions"""
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.on_settings_clicked)
        self.add_action(settings_action)
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
    
    def apply_css(self):
        """Apply custom CSS styling"""
        css_provider = Gtk.CssProvider()
        css = """
            .stat-card {
                min-width: 140px;
            }
            .success-icon {
                color: #57e389;
            }
            .warning-icon {
                color: #f8e45c;
            }
            .error-icon {
                color: #ed333b;
            }
            .neutral-icon {
                color: #9a9996;
            }
            .link-icon {
                color: #99c1f1;
            }
            .title-big {
                font-size: 2.5em;
                font-weight: bold;
            }
            .accent-text {
                color: @accent_color;
            }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def start_refresh(self):
        """Start the refresh cycle"""
        self.fetch_data()
        self.refresh_timeout_id = GLib.timeout_add(self.refresh_interval, self.fetch_data)
        return False
    
    def fetch_data(self):
        """Fetch data from the ADS-B feeder in a background thread"""
        self.spinner.start()
        thread = threading.Thread(target=self._fetch_data_thread)
        thread.daemon = True
        thread.start()
        return True
    
    def _fetch_json(self, endpoint):
        """Fetch JSON from an endpoint"""
        try:
            url = f"{self.feeder_url}{endpoint}"
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
        except:
            return None
    
    def _fetch_data_thread(self):
        """Background thread to fetch data"""
        data = {}
        error = None
        
        try:
            # Fetch adsb.im specific API endpoints
            # Stage2 stats contains planes, message rate, position rate
            stage2_stats = self._fetch_json("/api/stage2_stats")
            if stage2_stats and len(stage2_stats) > 0:
                data['stage2_stats'] = stage2_stats[0]
            
            # Temperature data
            temps = self._fetch_json("/api/get_temperatures.json")
            if temps:
                data['temperatures'] = temps
            
            # Aggregator statuses - adsb.im uses /api/status/{aggregator}
            aggregators = [
                ("adsblol", "adsb.lol"),
                ("flyitaly", "Fly Italy ADSB"),
                ("avdelphi", "AVDelphi"),
                ("planespotters", "Planespotters"),
                ("theairtraffic", "TheAirTraffic"),
                ("adsbfi", "adsb.fi"),
                ("adsbx", "ADSBExchange"),
                ("hpradar", "HPRadar"),
                ("alive", "airplanes.live"),
                ("flightradar", "flightradar24"),
                ("radarbox", "RadarBox"),
                ("planewatch", "Plane.watch"),
                ("adsbhub", "ADSBHub"),
                ("opensky", "OpenSky"),
                ("radarplane", "RadarPlane"),
                ("tat", "TheAirTraffic"),
            ]
            
            agg_data = []
            for agg_id, agg_name in aggregators:
                status = self._fetch_json(f"/api/status/{agg_id}")
                if status and "0" in status:
                    agg_info = status["0"]
                    agg_data.append({
                        'id': agg_id,
                        'name': agg_name,
                        'beast': agg_info.get('beast', 'unknown'),
                        'mlat': agg_info.get('mlat', 'unknown'),
                    })
            
            if agg_data:
                data['aggregators'] = agg_data
            
            # Also fetch HTML to get feeder name
            try:
                req = urllib.request.Request(self.feeder_url)
                with urllib.request.urlopen(req, timeout=5) as response:
                    html = response.read().decode()
                    data['html'] = html
                    data['connected'] = True
            except:
                pass
        
        except Exception as e:
            error = str(e)
        
        # Update UI on main thread
        GLib.idle_add(self._update_ui, data, error)
    
    def _update_ui(self, data, error):
        """Update the UI with fetched data (called on main thread)"""
        self.spinner.stop()
        
        if error and not data:
            self.status_banner.set_title(f"Connection failed: {error}")
            self.status_banner.set_revealed(True)
            self.connection_label.set_text("Disconnected")
            return
        
        # Connected successfully
        self.status_banner.set_revealed(False)
        self.connection_label.set_text(f"Connected to {self.feeder_url}")
        self.last_update_label.set_text(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Extract feeder name from HTML
        if 'html' in data:
            name_match = re.search(r'Homepage for (\w+)', data['html'])
            if name_match:
                self.feeder_name_label.set_text(f"ADS-B Feeder: {name_match.group(1)}")
        
        # Update from stage2_stats API (adsb.im specific)
        if 'stage2_stats' in data:
            stats = data['stage2_stats']
            
            # Aircraft counts
            if 'planes' in stats:
                self.planes_card.update(str(stats['planes']), "tracking")
            if 'tplanes' in stats:
                self.planes_today_card.update(str(stats['tplanes']), "total seen")
            
            # Message rates
            if 'mps' in stats:
                self.msg_rate_card.update(str(stats['mps']), "msg/sec")
            if 'pps' in stats:
                self.pos_rate_card.update(str(stats['pps']), "pos/sec")
            
            # Uptime
            if 'uptime' in stats:
                uptime_secs = stats['uptime']
                days = uptime_secs // 86400
                hours = (uptime_secs % 86400) // 3600
                mins = (uptime_secs % 3600) // 60
                if days > 0:
                    uptime_str = f"{days}d {hours}h"
                elif hours > 0:
                    uptime_str = f"{hours}h {mins}m"
                else:
                    uptime_str = f"{mins}m"
                self.uptime_card.update(uptime_str, "")
        
        # Update temperature
        if 'temperatures' in data:
            temps = data['temperatures']
            if 'cpu' in temps:
                self.temp_card.update(f"{temps['cpu']}°C", "")
        
        # Update aggregators from API data
        if 'aggregators' in data:
            self._update_aggregators_from_api(data['aggregators'])
    
    def _parse_html_data(self, html):
        """Parse feeder data from HTML page"""
        self.feeder_name_label.set_text("ADS-B Feeder")
        
        # Try to find feeder name
        name_match = re.search(r'Homepage for (\w+)', html)
        if name_match:
            self.feeder_name_label.set_text(f"ADS-B Feeder: {name_match.group(1)}")
        
        # Try to find stats
        pos_match = re.search(r'([\d.]+)\s*pos\s*/\s*([\d.]+)\s*msg per sec', html)
        if pos_match:
            self.pos_rate_card.update(pos_match.group(1), "pos/sec")
            self.msg_rate_card.update(pos_match.group(2), "msg/sec")
        
        planes_match = re.search(r'(\d+)\s*planes?\s*/\s*(\d+)\s*today', html)
        if planes_match:
            self.planes_card.update(planes_match.group(1), "tracking")
            self.planes_today_card.update(planes_match.group(2), "total seen")
        
        # Parse CPU temp
        cpu_match = re.search(r'CPU[:\s]*(\d+)°?C?', html, re.IGNORECASE)
        if cpu_match:
            self.temp_card.update(f"{cpu_match.group(1)}°C", "")
        
        # Parse aggregators from HTML
        self._parse_aggregators_from_html(html)
    
    def _update_aggregators_from_api(self, aggregators):
        """Update aggregators list from adsb.im API data"""
        # Clear existing rows
        while True:
            child = self.aggregator_rows_box.get_first_child()
            if child:
                self.aggregator_rows_box.remove(child)
            else:
                break
        
        for agg in aggregators:
            name = agg.get('name', 'Unknown')
            beast_status = agg.get('beast', 'unknown')
            mlat_status = agg.get('mlat', 'unknown')
            
            # Determine overall "Enabled" status (combines beast and mlat)
            # good + good = good (green check)
            # good + bad/disconnected = warning (yellow !)
            # bad/disconnected + anything = bad (red X)
            beast_good = beast_status == 'good'
            mlat_good = mlat_status == 'good'
            mlat_bad = mlat_status in ('disconnected', 'down', 'bad', 'error')
            
            if beast_good and mlat_good:
                enabled = True  # All good - green check
            elif beast_good and mlat_bad:
                enabled = "warning"  # Beast ok but MLAT issues - yellow !
            elif beast_good:
                enabled = True  # Beast good, MLAT unknown/not applicable
            else:
                enabled = False  # Beast not good - red X
            
            # Data indicator (based on beast status)
            if beast_status == 'good':
                data = True
            elif beast_status in ('degraded', 'intermittent'):
                data = "warning"
            else:
                data = False
            
            # MLAT indicator
            if mlat_status == 'good':
                mlat = True
            elif mlat_status in ('degraded', 'intermittent'):
                mlat = "warning"
            elif mlat_status in ('disconnected', 'down', 'bad', 'error'):
                mlat = "error"
            else:
                mlat = False  # unknown or not applicable
            
            row = AggregatorRow(name, enabled, data, mlat)
            self.aggregator_rows_box.append(row)
    
    def _update_aggregators(self, aggregators):
        """Update aggregators list from API data"""
        # Clear existing rows
        while True:
            child = self.aggregator_rows_box.get_first_child()
            if child:
                self.aggregator_rows_box.remove(child)
            else:
                break
        
        for agg in aggregators:
            name = agg.get('name', 'Unknown')
            enabled = agg.get('enabled', False)
            data_ok = agg.get('data', False)
            mlat = agg.get('mlat', False)
            
            row = AggregatorRow(name, enabled, data_ok, mlat)
            self.aggregator_rows_box.append(row)
    
    def _parse_aggregators_from_html(self, html):
        """Parse aggregator info from HTML page"""
        # Clear existing rows
        while True:
            child = self.aggregator_rows_box.get_first_child()
            if child:
                self.aggregator_rows_box.remove(child)
            else:
                break
        
        # Common aggregator names to look for
        aggregators = [
            ("adsb.lol", "adsb.lol"),
            ("Fly Italy ADSB", "flyitalyadsb"),
            ("AVDelphi", "avdelphi"),
            ("Planespotters", "planespotters"),
            ("TheAirTraffic", "theairtraffic"),
            ("adsb.fi", "adsb.fi"),
            ("ADSBExchange", "adsbexchange"),
            ("HPRadar", "hpradar"),
            ("flightradar24", "flightradar24"),
            ("FlightAware", "flightaware"),
            ("RadarBox", "radarbox"),
            ("ADSB Hub", "adsbhub"),
        ]
        
        for display_name, search_name in aggregators:
            if search_name.lower() in html.lower():
                enabled = True
                data_ok = True
                mlat = False
                
                row = AggregatorRow(display_name, enabled, data_ok, mlat)
                self.aggregator_rows_box.append(row)
    
    def on_refresh_clicked(self, button):
        """Manual refresh"""
        self.fetch_data()
    
    def on_open_browser(self, button):
        """Open the feeder URL in the default browser"""
        Gtk.show_uri(self, self.feeder_url, Gdk.CURRENT_TIME)
    
    def on_settings_clicked(self, action, param=None):
        """Show settings dialog"""
        dialog = Adw.PreferencesWindow(transient_for=self)
        dialog.set_title("Settings")
        
        # General page
        general_page = Adw.PreferencesPage()
        general_page.set_title("General")
        general_page.set_icon_name("emblem-system-symbolic")
        dialog.add(general_page)
        
        # Connection group
        connection_group = Adw.PreferencesGroup()
        connection_group.set_title("Connection")
        general_page.add(connection_group)
        
        # URL entry
        url_row = Adw.EntryRow()
        url_row.set_title("Feeder URL")
        url_row.set_text(self.feeder_url)
        url_row.connect("changed", self.on_url_changed)
        connection_group.add(url_row)
        
        # Refresh interval
        refresh_row = Adw.SpinRow.new_with_range(1, 60, 1)
        refresh_row.set_title("Refresh Interval")
        refresh_row.set_subtitle("Seconds between updates")
        refresh_row.set_value(self.refresh_interval / 1000)
        refresh_row.connect("changed", self.on_refresh_interval_changed)
        connection_group.add(refresh_row)
        
        dialog.present()
    
    def on_url_changed(self, row):
        """Handle URL change"""
        self.feeder_url = row.get_text()
    
    def on_refresh_interval_changed(self, row):
        """Handle refresh interval change"""
        self.refresh_interval = int(row.get_value() * 1000)
        
        # Restart refresh timer
        if self.refresh_timeout_id:
            GLib.source_remove(self.refresh_timeout_id)
        self.refresh_timeout_id = GLib.timeout_add(self.refresh_interval, self.fetch_data)
    
    def on_about(self, action, param=None):
        """Show about dialog"""
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="ADS-B Feeder Monitor",
            application_icon="airplane-mode-symbolic",
            developer_name="ADS-B Community",
            version="2.0.0",
            website="https://github.com/adsb-feeder",
            issue_url="https://github.com/adsb-feeder/issues",
            copyright="© 2026 ADS-B Monitor",
            license_type=Gtk.License.GPL_3_0,
            developers=["ADS-B Community"],
            comments="A native desktop application for monitoring your ADS-B feeder.\n\nTrack aircraft in your area with ease!"
        )
        about.present()


class ADSBMonitorApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        
    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ADSBMonitorWindow(application=self)
        win.present()
    
    def do_startup(self):
        Adw.Application.do_startup(self)
        
        # Add keyboard shortcuts
        self.set_accels_for_action("app.quit", ["<Control>q"])


def main():
    app = ADSBMonitorApp()
    return app.run(None)


if __name__ == "__main__":
    main()
