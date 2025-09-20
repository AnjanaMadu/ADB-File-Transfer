#!/usr/bin/env python3
"""
ADB File Transfer Tool
A user-friendly CLI tool for copying files from Android phone to PC using ADB.

Requirements:
- Python 3.6+
- ADB (Android Debug Bridge) installed and in PATH
- Android device with USB debugging enabled

Controls:
- Arrow keys / j,k: Navigate up/down
- s: Select/deselect files
- d: Switch to PC destination mode
- e: Execute copy operation
- Esc: Go back to parent directory
- q: Quit

Author: Claude (Anthropic)
"""

import subprocess
import os
import sys
import json
import shutil
from pathlib import Path
import platform

# Cross-platform keyboard input
try:
    if platform.system() == "Windows":
        import msvcrt
    else:
        import termios
        import tty
except ImportError:
    print("Error: Required modules for keyboard input not available")
    sys.exit(1)

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'

def get_key():
    """Get single keypress from user (cross-platform)"""
    if platform.system() == "Windows":
        key = msvcrt.getch()
        if key == b'\xe0':  # Special keys on Windows
            key = msvcrt.getch()
            if key == b'H': return 'up'
            elif key == b'P': return 'down'
            elif key == b'K': return 'left'
            elif key == b'M': return 'right'
        elif key == b'\x1b':  # ESC
            return 'esc'
        elif key == b'\r':  # Enter
            return 'enter'
        return key.decode('utf-8', errors='ignore')
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
            if key == '\x1b':  # ESC sequence
                key += sys.stdin.read(2)
                if key == '\x1b[A': return 'up'
                elif key == '\x1b[B': return 'down'
                elif key == '\x1b[C': return 'right'
                elif key == '\x1b[D': return 'left'
                else: return 'esc'
            elif key == '\r' or key == '\n':
                return 'enter'
            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class ADBFileBrowser:
    def __init__(self):
        self.current_phone_dir = "/storage/emulated/0"  # More reliable than /sdcard
        self.current_pc_dir = str(Path.home())
        self.selected_files = set()
        self.cursor_pos = 0
        self.mode = "phone"  # "phone" or "pc"
        self.phone_files = []
        self.pc_files = []
        
    def check_adb(self):
        """Check if ADB is available and device is connected"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"{Colors.RED}Error: ADB not found. Please install ADB and add it to PATH{Colors.RESET}")
                return False
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            devices = [line for line in lines if line.strip() and 'device' in line]
            
            if not devices:
                print(f"{Colors.RED}Error: No Android device connected or authorized{Colors.RESET}")
                print("Please connect your device and enable USB debugging")
                return False
                
            print(f"{Colors.GREEN}✓ ADB connected to device{Colors.RESET}")
            return True
        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}Error: ADB command timed out{Colors.RESET}")
            return False
        except FileNotFoundError:
            print(f"{Colors.RED}Error: ADB not found. Please install Android SDK Platform-tools{Colors.RESET}")
            return False

    def list_phone_files(self, directory):
        """List files in Android directory using ADB"""
        try:
            # Try different listing approaches
            commands = [
                ['adb', 'shell', f'ls -1 "{directory}" 2>/dev/null'],
                ['adb', 'shell', f'find "{directory}" -maxdepth 1 -type f -o -type d 2>/dev/null | grep -v "^{directory}$"'],
                ['adb', 'shell', f'ls "{directory}" 2>/dev/null']
            ]
            
            files = []
            result = None
            
            # Try the first command (ls -1)
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and result.stdout.strip():
                        break
                except:
                    continue
            
            if not result or result.returncode != 0:
                return None
            
            lines = result.stdout.strip().split('\n')
            
            # Get file details for each entry
            for line in lines:
                line = line.strip()
                if not line or line in ['.', '..']:
                    continue
                
                # Clean up the filename (remove quotes, special chars)
                name = line.strip('"\'')
                if name.startswith('./'):
                    name = name[2:]
                if '/' in name and directory in name:
                    name = name.split('/')[-1]
                
                if not name:
                    continue
                
                # Check if it's a directory
                full_path = f"{directory.rstrip('/')}/{name}"
                try:
                    test_cmd = ['adb', 'shell', f'test -d "{full_path}" && echo "DIR" || echo "FILE"']
                    test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
                    is_dir = "DIR" in test_result.stdout
                except:
                    # Fallback: assume it's a file if we can't determine
                    is_dir = False
                
                # Get file size for files
                size = 0
                if not is_dir:
                    try:
                        size_cmd = ['adb', 'shell', f'stat -c %s "{full_path}" 2>/dev/null || wc -c < "{full_path}" 2>/dev/null']
                        size_result = subprocess.run(size_cmd, capture_output=True, text=True, timeout=5)
                        if size_result.stdout.strip().isdigit():
                            size = int(size_result.stdout.strip())
                    except:
                        size = 0
                
                files.append({
                    'name': name,
                    'is_dir': is_dir,
                    'size': size,
                    'permissions': 'drwxr-xr-x' if is_dir else '-rw-r--r--'
                })
            
            # Sort: directories first, then files, both alphabetically
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return files
            
        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}Timeout accessing {directory}{Colors.RESET}")
            return None
        except Exception as e:
            print(f"{Colors.RED}Error listing phone files: {e}{Colors.RESET}")
            return None

    def list_pc_files(self, directory):
        """List files in PC directory"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return None
                
            files = []
            
            # Add special directories only for home directory
            if directory == str(Path.home()):
                # Add Downloads folder
                downloads = Path.home() / 'Downloads'
                if downloads.exists():
                    files.append({
                        'name': '📁 Downloads',
                        'is_dir': True,
                        'path': str(downloads),
                        'size': 0
                    })
                
                # Add Desktop folder
                desktop = Path.home() / 'Desktop'
                if desktop.exists():
                    files.append({
                        'name': '🖥️ Desktop',
                        'is_dir': True,
                        'path': str(desktop),
                        'size': 0
                    })
                
                # Add drive letters/partitions on Windows
                if platform.system() == "Windows":
                    for drive in ['C:', 'D:', 'E:', 'F:', 'G:', 'H:']:
                        drive_path = Path(f"{drive}\\")
                        if drive_path.exists():
                            files.append({
                                'name': f'💾 {drive}\\',
                                'is_dir': True,
                                'path': str(drive_path),
                                'size': 0
                            })
                else:
                    # On Linux/macOS, show root filesystem
                    root_path = Path('/')
                    if root_path.exists():
                        files.append({
                            'name': '💾 / (Root)',
                            'is_dir': True,
                            'path': '/',
                            'size': 0
                        })
                
                # Sort special directories
                files.sort(key=lambda x: x['name'].lower())
                return files
            
            # For non-home directories, list regular files and directories
            for item in path.iterdir():
                try:
                    if item.is_dir():
                        files.append({
                            'name': f"📁 {item.name}",
                            'is_dir': True,
                            'path': str(item),
                            'size': 0
                        })
                    else:
                        size = item.stat().st_size
                        files.append({
                            'name': f"📄 {item.name}",
                            'is_dir': False,
                            'path': str(item),
                            'size': size
                        })
                except PermissionError:
                    continue
                    
            # Sort: directories first, then files
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return files
            
        except PermissionError:
            return None
        except Exception as e:
            print(f"{Colors.RED}Error listing PC files: {e}{Colors.RESET}")
            return None

    def format_size(self, size):
        """Format file size in human readable format"""
        if not size or size == 0:
            return ""
        
        try:
            size = int(size)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f}{unit}"
                size /= 1024
            return f"{size:.1f}TB"
        except:
            return str(size)

    def display_files(self):
        """Display current directory contents"""
        os.system('clear' if platform.system() != 'Windows' else 'cls')
        
        if self.mode == "phone":
            print(f"{Colors.BOLD}{Colors.CYAN}📱 ADB File Transfer - Android Device{Colors.RESET}")
            print(f"{Colors.YELLOW}Current directory: {self.current_phone_dir}{Colors.RESET}")
            files = self.phone_files
        else:
            print(f"{Colors.BOLD}{Colors.CYAN}💻 ADB File Transfer - PC Destination{Colors.RESET}")
            print(f"{Colors.YELLOW}Current directory: {self.current_pc_dir}{Colors.RESET}")
            files = self.pc_files
        
        print(f"{Colors.BLUE}Selected files: {len(self.selected_files)}{Colors.RESET}")
        print("-" * 60)
        
        if not files:
            print(f"{Colors.RED}Unable to access directory or directory is empty{Colors.RESET}")
            print("\nPress 'Esc' to go back")
            return
        
        # Display files with cursor and selection indicators
        for i, file_info in enumerate(files):
            cursor = "→ " if i == self.cursor_pos else "  "
            
            if self.mode == "phone":
                file_path = f"{self.current_phone_dir.rstrip('/')}/{file_info['name']}"
                selected = "[✓] " if file_path in self.selected_files else "[ ] "
                size_str = self.format_size(file_info.get('size', ''))
                size_display = f" ({size_str})" if size_str else ""
                
                # Color coding
                if file_info['is_dir']:
                    name_color = Colors.BLUE
                    icon = "📁 "
                else:
                    name_color = Colors.RESET
                    icon = "📄 "
                
                print(f"{cursor}{selected}{name_color}{icon}{file_info['name']}{size_display}{Colors.RESET}")
            else:
                # PC mode - no selection, just navigation
                cursor_color = Colors.GREEN if i == self.cursor_pos else ""
                print(f"{cursor_color}{cursor}{file_info['name']}{Colors.RESET}")
        
        # Display controls
        print("-" * 60)
        if self.mode == "phone":
            print(f"{Colors.CYAN}Controls: ↑↓/jk=navigate, Enter=enter dir, s=select, d=destination, e=copy, Esc=back, q=quit{Colors.RESET}")
        else:
            print(f"{Colors.CYAN}Controls: ↑↓/jk=navigate, Enter=enter dir, e=copy here, d=back to phone, Esc=back, q=quit{Colors.RESET}")

    def navigate_phone(self):
        """Handle navigation in phone mode"""
        self.phone_files = self.list_phone_files(self.current_phone_dir)
        if self.phone_files is None:
            self.phone_files = []
        self.cursor_pos = 0

    def navigate_pc(self):
        """Handle navigation in PC mode"""
        self.pc_files = self.list_pc_files(self.current_pc_dir)
        if self.pc_files is None:
            self.pc_files = []
        self.cursor_pos = 0

    def copy_files(self):
        """Copy selected files from phone to PC"""
        if not self.selected_files:
            print(f"{Colors.YELLOW}No files selected for copying{Colors.RESET}")
            input("Press Enter to continue...")
            return
        
        print(f"\n{Colors.BOLD}Starting file copy operation...{Colors.RESET}")
        print(f"Destination: {self.current_pc_dir}")
        print(f"Files to copy: {len(self.selected_files)}")
        print("-" * 60)
        
        success_count = 0
        fail_count = 0
        
        # Ensure destination directory exists
        os.makedirs(self.current_pc_dir, exist_ok=True)
        
        for phone_path in self.selected_files:
            filename = os.path.basename(phone_path)
            pc_path = os.path.join(self.current_pc_dir, filename)
            
            print(f"\n{Colors.CYAN}Copying: {filename}{Colors.RESET}")
            print("-" * 40)
            
            try:
                # Use ADB pull command - redirect output to terminal for progress
                cmd = ['adb', 'pull', phone_path, pc_path]
                result = subprocess.run(cmd, timeout=300)  # No capture_output to show progress
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✓ Successfully copied: {filename}{Colors.RESET}")
                    success_count += 1
                else:
                    print(f"{Colors.RED}✗ Failed to copy: {filename}{Colors.RESET}")
                    fail_count += 1
                    
            except subprocess.TimeoutExpired:
                print(f"{Colors.RED}✗ Timeout copying: {filename}{Colors.RESET}")
                fail_count += 1
            except Exception as e:
                print(f"{Colors.RED}✗ Error copying {filename}: {e}{Colors.RESET}")
                fail_count += 1
        
        print("\n" + "=" * 60)
        print(f"Copy operation completed!")
        print(f"{Colors.GREEN}Successful: {success_count}{Colors.RESET} | {Colors.RED}Failed: {fail_count}{Colors.RESET}")
        
        if success_count > 0:
            # Clear selections after successful copy
            self.selected_files.clear()
            print(f"{Colors.YELLOW}Selected files cleared{Colors.RESET}")
        
        print("=" * 60)
        input("\nPress Enter to continue...")

    def run(self):
        """Main application loop"""
        if not self.check_adb():
            return
        
        print(f"{Colors.GREEN}ADB File Transfer Tool initialized{Colors.RESET}")
        print("Loading phone files...")
        
        self.navigate_phone()
        
        while True:
            self.display_files()
            key = get_key()
            
            # Navigation
            if key in ['j', 'down']:
                if self.mode == "phone" and self.phone_files:
                    self.cursor_pos = min(self.cursor_pos + 1, len(self.phone_files) - 1)
                elif self.mode == "pc" and self.pc_files:
                    self.cursor_pos = min(self.cursor_pos + 1, len(self.pc_files) - 1)
                    
            elif key in ['k', 'up']:
                self.cursor_pos = max(self.cursor_pos - 1, 0)
            
            # Selection (phone mode only)
            elif key == 's' and self.mode == "phone" and self.phone_files:
                file_info = self.phone_files[self.cursor_pos]
                file_path = f"{self.current_phone_dir.rstrip('/')}/{file_info['name']}"
                
                if file_path in self.selected_files:
                    self.selected_files.remove(file_path)
                else:
                    self.selected_files.add(file_path)
            
            # Enter directory
            elif key == 'enter':
                if self.mode == "phone" and self.phone_files and self.cursor_pos < len(self.phone_files):
                    file_info = self.phone_files[self.cursor_pos]
                    if file_info['is_dir']:
                        new_dir = f"{self.current_phone_dir.rstrip('/')}/{file_info['name']}"
                        self.current_phone_dir = new_dir
                        self.navigate_phone()
                        
                elif self.mode == "pc" and self.pc_files and self.cursor_pos < len(self.pc_files):
                    file_info = self.pc_files[self.cursor_pos]
                    if file_info['is_dir']:
                        self.current_pc_dir = file_info['path']
                        self.navigate_pc()
            
            # Switch to destination mode
            elif key == 'd':
                if self.mode == "phone":
                    self.mode = "pc"
                    self.navigate_pc()
                else:
                    self.mode = "phone"
                    self.navigate_phone()
            
            # Execute copy
            elif key == 'e':
                if self.selected_files:
                    self.copy_files()
                else:
                    print(f"{Colors.YELLOW}No files selected for copying{Colors.RESET}")
                    input("Press Enter to continue...")
            
            # Go back
            elif key == 'esc':
                if self.mode == "phone":
                    if self.current_phone_dir not in ["/storage/emulated/0", "/sdcard", "/"]:
                        parent = "/".join(self.current_phone_dir.rstrip('/').split('/')[:-1])
                        if not parent:
                            parent = "/"
                        self.current_phone_dir = parent
                        self.navigate_phone()
                else:
                    parent = str(Path(self.current_pc_dir).parent)
                    if parent != self.current_pc_dir:  # Not at root
                        self.current_pc_dir = parent
                        self.navigate_pc()
            
            # Quit
            elif key == 'q':
                print(f"\n{Colors.GREEN}Thank you for using ADB File Transfer Tool!{Colors.RESET}")
                break

def main():
    """Entry point"""
    try:
        app = ADBFileBrowser()
        app.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        print("Please report this issue if it persists.")

if __name__ == "__main__":
    main()
