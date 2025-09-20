# ADB File Transfer Tool

A user-friendly CLI tool for copying files from your Android phone to PC using ADB (Android Debug Bridge). Navigate your phone's filesystem, select multiple files, choose your destination, and copy with real-time progress display.

## ✨ Features

- 📱 **Intuitive phone browsing** starting from internal storage
- ✅ **Multi-file selection** with visual checkboxes `[✓]`
- 💻 **Smart PC navigation** showing only partitions, Downloads, and Desktop
- ⚡ **Real-time transfer progress** with ADB's native progress bars
- 🎯 **Cross-platform support** (Windows, Linux, macOS)
- 🔄 **Easy directory navigation** with keyboard shortcuts

## 📋 Requirements

- **Python 3.6+**
- **ADB (Android Debug Bridge)** installed and available in PATH
- **Android device** with USB debugging enabled
- **USB cable** connection between phone and PC

## 🚀 Installation

1. **Install ADB** (if not already installed):
   - **Windows**: Download [Android SDK Platform-tools](https://developer.android.com/studio/releases/platform-tools)
   - **macOS**: `brew install android-platform-tools`
   - **Linux**: `sudo apt install adb` (Ubuntu/Debian) or equivalent for your distro

2. **Enable USB Debugging** on your Android device:
   - Go to Settings → About Phone → Tap "Build number" 7 times
   - Go to Settings → Developer Options → Enable "USB Debugging"

3. **Download the tool**:
   ```bash
   wget https://github.com/AnjanaMadu/ADB-File-Transfer/raw/refs/heads/main/adbcopy.py
   # or download manually and save as adbcopy.py
   ```

4. **Make it executable**:
   ```bash
   chmod +x adbcopy.py
   ```

## 📱 Usage

### Quick Start

1. **Connect your Android device** via USB
2. **Run the tool**:
   ```bash
   python3 adbcopy.py
   # or
   ./adbcopy.py
   ```
3. **Allow USB debugging** when prompted on your phone
4. Start browsing and copying files!

### Step-by-Step Workflow

1. **📱 Phone Mode**: Browse your device's files
   - Navigate using arrow keys or `j`/`k`
   - Press `Enter` to enter directories
   - Press `s` to select/deselect files (shows `[✓]`)
   - Press `Esc` to go back to parent directory

2. **💻 Destination Mode**: Choose where to copy
   - Press `d` to switch to PC destination mode
   - Navigate to Downloads, Desktop, or drive partitions
   - Enter directories with `Enter` key

3. **⚡ Copy Files**: Execute the transfer
   - Press `e` to start copying selected files
   - Watch real-time progress from ADB
   - Files are copied to your current PC directory

## ⌨️ Controls

| Key | Action |
|-----|--------|
| `↑↓` / `j``k` | Navigate up/down through files |
| `Enter` | Enter directory |
| `s` | Select/deselect files (phone mode only) |
| `d` | Switch between phone and PC modes |
| `e` | Execute copy operation |
| `Esc` | Go back to parent directory |
| `q` | Quit application |

## 🖥️ Interface Preview

```
📱 ADB File Transfer - Android Device
Current directory: /storage/emulated/0/Pictures
Selected files: 3
------------------------------------------------------------
→ [✓] 📁 Camera                    
  [ ] 📄 photo1.jpg               (2.1MB)
  [✓] 📄 photo2.jpg               (1.8MB)
  [✓] 📄 screenshot.png           (856KB)
------------------------------------------------------------
Controls: ↑↓/jk=navigate, Enter=enter dir, s=select, d=destination, e=copy, Esc=back, q=quit
```

## 🚨 Troubleshooting

### ADB Not Found
```bash
# Check if ADB is installed
adb version

# If not found, install ADB and add to PATH
export PATH=$PATH:/path/to/platform-tools
```

### No Device Connected
- Ensure USB debugging is enabled
- Check USB connection
- Try different USB cable/port
- Run `adb devices` to verify connection

### Permission Denied
- Some Android directories require root access
- Try accessing `/storage/emulated/0/` instead of `/sdcard/`
- Check if your device requires additional permissions

### File Transfer Fails
- Ensure destination directory has write permissions
- Check available disk space on PC
- Verify file isn't currently in use on phone

## 🛠️ Advanced Usage

### Custom Starting Directory
Modify the script to start from a different directory:
```python
self.current_phone_dir = "/storage/emulated/0/DCIM"  # Start in camera folder
```

### Batch Operations
- Select multiple files across different directories
- Selections persist when navigating
- Copy all selected files to one destination

## 🤝 Contributing

Found a bug or have a feature request? 

1. Check existing issues
2. Create a new issue with detailed description
3. Submit pull requests for improvements

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

## 👨‍💻 Author

Created by Claude (Anthropic) - An AI assistant focused on helpful, harmless, and honest interactions.

---

**⭐ If this tool helped you, please consider starring the repository!**
