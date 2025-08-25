import tkinter as tk
import win32gui
import win32con
import win32api
import logging
from typing import Optional

class StealthWindow:
    """
    Handles stealth mode functionality to hide window from screen sharing
    while keeping it visible to the user
    """
    
    def __init__(self, root_window):
        self.root = root_window
        self.logger = logging.getLogger(__name__)
        self.is_stealth_enabled = False
        self.original_window_style = None
        
        # Get window handle
        self.hwnd = None
        self.root.after(100, self.get_window_handle)
        
    def get_window_handle(self):
        """Get the window handle for the tkinter window"""
        try:
            # Get window handle using the window title
            self.hwnd = win32gui.FindWindow(None, self.root.title())
            if self.hwnd:
                self.logger.info(f"Window handle obtained: {self.hwnd}")
                self.original_window_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            else:
                self.logger.warning("Could not obtain window handle")
                # Try again after a short delay
                self.root.after(500, self.get_window_handle)
        except Exception as e:
            self.logger.error(f"Error getting window handle: {e}")
            
    def enable_stealth_mode(self):
        """Enable stealth mode - hide from screen capture"""
        if not self.hwnd:
            self.logger.warning("Cannot enable stealth mode: no window handle")
            return False
            
        try:
            # Set WS_EX_LAYERED style to enable transparency effects
            current_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            new_style = current_style | win32con.WS_EX_LAYERED
            
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, new_style)
            
            # Set the window to be excluded from screen capture
            # This uses the WDA_EXCLUDEFROMCAPTURE flag (Windows 10 2004+)
            try:
                import ctypes
                from ctypes import wintypes
                
                # Define the SetWindowDisplayAffinity function
                user32 = ctypes.windll.user32
                WDA_EXCLUDEFROMCAPTURE = 0x00000011
                
                result = user32.SetWindowDisplayAffinity(self.hwnd, WDA_EXCLUDEFROMCAPTURE)
                if result:
                    self.is_stealth_enabled = True
                    self.logger.info("Stealth mode enabled successfully")
                    return True
                else:
                    self.logger.warning("Failed to set display affinity")
                    
            except Exception as e:
                self.logger.error(f"Error setting display affinity: {e}")
                
            # Alternative method: Make window topmost and use specific styles
            self.root.attributes('-topmost', True)
            self.is_stealth_enabled = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling stealth mode: {e}")
            return False
            
    def disable_stealth_mode(self):
        """Disable stealth mode - make window capturable again"""
        if not self.hwnd:
            return False
            
        try:
            # Reset display affinity
            import ctypes
            user32 = ctypes.windll.user32
            WDA_NONE = 0x00000000
            
            user32.SetWindowDisplayAffinity(self.hwnd, WDA_NONE)
            
            # Restore original window style
            if self.original_window_style:
                win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, self.original_window_style)
                
            self.is_stealth_enabled = False
            self.logger.info("Stealth mode disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling stealth mode: {e}")
            return False
            
    def toggle_stealth_mode(self):
        """Toggle stealth mode on/off"""
        if self.is_stealth_enabled:
            return self.disable_stealth_mode()
        else:
            return self.enable_stealth_mode()
            
    def set_window_transparency(self, alpha: int = 240):
        """Set window transparency (0-255, where 255 is opaque)"""
        if not self.hwnd:
            return False
            
        try:
            # Ensure layered window style is set
            current_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            if not (current_style & win32con.WS_EX_LAYERED):
                win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, 
                                     current_style | win32con.WS_EX_LAYERED)
            
            # Set transparency
            win32gui.SetLayeredWindowAttributes(self.hwnd, 0, alpha, win32con.LWA_ALPHA)
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting transparency: {e}")
            return False
            
    def make_click_through(self, enable: bool = True):
        """Make window click-through (mouse events pass through)"""
        if not self.hwnd:
            return False
            
        try:
            current_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            
            if enable:
                new_style = current_style | win32con.WS_EX_TRANSPARENT
            else:
                new_style = current_style & ~win32con.WS_EX_TRANSPARENT
                
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, new_style)
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting click-through: {e}")
            return False
            
    def hide_from_taskbar(self):
        """Hide window from taskbar"""
        if not self.hwnd:
            return False
            
        try:
            current_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            new_style = current_style | win32con.WS_EX_TOOLWINDOW
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, new_style)
            return True
            
        except Exception as e:
            self.logger.error(f"Error hiding from taskbar: {e}")
            return False
            
    def get_window_info(self):
        """Get current window information for debugging"""
        if not self.hwnd:
            return None
            
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
            ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            
            return {
                'hwnd': self.hwnd,
                'rect': rect,
                'style': style,
                'ex_style': ex_style,
                'is_visible': win32gui.IsWindowVisible(self.hwnd),
                'stealth_enabled': self.is_stealth_enabled
            }
            
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return None


class ScreenCaptureDetector:
    """
    Detect when screen capture applications are running
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.known_capture_apps = [
            'zoom.exe', 'teams.exe', 'skype.exe', 'discord.exe',
            'obs64.exe', 'obs32.exe', 'xsplit.exe', 'streamlabs obs.exe',
            'googlemeet', 'webex', 'gotomeeting'
        ]
        
    def is_screen_sharing_active(self):
        """Check if any known screen sharing applications are running"""
        try:
            import psutil
            
            for process in psutil.process_iter(['name']):
                process_name = process.info['name'].lower()
                if any(app in process_name for app in self.known_capture_apps):
                    self.logger.info(f"Screen sharing app detected: {process_name}")
                    return True
                    
            return False
            
        except ImportError:
            self.logger.warning("psutil not available for process detection")
            return False
        except Exception as e:
            self.logger.error(f"Error detecting screen sharing: {e}")
            return False