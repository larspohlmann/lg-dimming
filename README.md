# LG OLED Auto-Dimming Control

Disable auto-dimming (TPC/GSR) on LG OLED TVs to prevent automatic brightness reduction during dark scenes.

## Features

- 🔍 **Auto-discovery**: Automatically find LG TVs on your network
- 🖥️ **GUI Application**: Easy-to-use graphical interface
- ⌨️ **CLI Tool**: Command-line interface for automation
- 📝 **Logging**: Comprehensive logging for troubleshooting
- 💾 **Persistent Settings**: Saves TV pairing keys and configuration

## What is TPC/GSR?

- **TPC (Temporal Peak Luminance Control)**: Automatically dims the screen during static or dark content to prevent burn-in
- **GSR (Global Sticky Reduction)**: Reduces brightness of static elements like logos

While these features protect your OLED panel, they can cause noticeable and distracting dimming during movies, games, and TV shows. This tool allows you to disable them.

## Requirements

- Python 3.8 or higher
- LG WebOS TV (tested on LG OLED C5)
- TV and computer on the same network

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/lg-oled-dimming-control.git
cd lg-oled-dimming-control
```

### 2. Install dependencies

```bash
pip install bscpylgtv
```

### 3. (macOS only) Install Tkinter for GUI

If using Homebrew Python:
```bash
brew install python-tk
```

## Usage

### GUI Application

```bash
python3 lg_dimming_gui.py
```

1. Click **Scan** to auto-discover your TV (or enter IP manually)
2. Click **Connect & Check Status**
3. Accept the pairing request on your TV
4. Click **Disable Auto-Dimming** to turn off TPC and GSR

### Command Line

**Discover TVs on your network:**
```bash
python3 disable_autodimming.py --discover
```

**Disable auto-dimming (recommended):**
```bash
python3 disable_autodimming.py --ip 192.168.1.44
```

**Enable auto-dimming:**
```bash
python3 disable_autodimming.py --ip 192.168.1.44 --enable
```

## Troubleshooting

### Connection Issues

1. **Make sure your TV is on** and connected to the same network as your computer
2. **Check the log file** (`lg_dimming.log`) for detailed error messages
3. **Try discovering your TV** with `--discover` to verify it's reachable

### Permission Errors

You must **accept the pairing request on your TV screen** each time you connect. This is a security feature of LG WebOS TVs. The pairing key is stored in `lgtv_keys.db` (required by the library).

### Python Environment Issues

If you get `ModuleNotFoundError`:
- Make sure `bscpylgtv` is installed: `pip install bscpylgtv`
- If using multiple Python versions, use the full path to your Python executable

## Files Generated

- **lgtv_keys.db**: SQLite database storing pairing keys (required by bscpylgtv library)
- **lg_dimming.log**: Operation log with timestamps and errors
- **lg_config.json**: Saved IP configuration

## Disclaimer

⚠️ **Use at your own risk.** Disabling TPC and GSR may increase the risk of OLED burn-in. This tool modifies service menu settings on your TV.

## Credits

Built using [bscpylgtv](https://github.com/chros73/bscpylgtv) by chros73.

## License

MIT License - See LICENSE file for details.
