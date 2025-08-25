import tkinter as tk
from PIL import ImageGrab, Image
import io
import base64
import logging
import time
import win32gui
import win32con

class ScreenshotCapture:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def capture_screen_excluding_window(self, exclude_window_title="Exam Helper"):
        """Capture screenshot excluding the specified window"""
        try:
            # Get the window handle of the window to exclude
            exclude_hwnd = None
            try:
                exclude_hwnd = win32gui.FindWindow(None, exclude_window_title)
            except:
                pass
            
            # If we found the window to exclude, minimize it temporarily
            was_minimized = False
            if exclude_hwnd and win32gui.IsWindowVisible(exclude_hwnd):
                # Check if window is already minimized
                placement = win32gui.GetWindowPlacement(exclude_hwnd)
                if placement[1] != win32con.SW_SHOWMINIMIZED:
                    # Minimize the window
                    win32gui.ShowWindow(exclude_hwnd, win32con.SW_MINIMIZE)
                    was_minimized = True
                    # Wait a bit for the window to minimize
                    time.sleep(0.2)
            
            # Capture the screen
            screenshot = ImageGrab.grab()
            
            # Restore the window if we minimized it
            if was_minimized and exclude_hwnd:
                win32gui.ShowWindow(exclude_hwnd, win32con.SW_RESTORE)
                # Bring it back to front
                win32gui.SetForegroundWindow(exclude_hwnd)
            
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Screenshot capture error: {e}")
            # Fallback to regular screenshot
            return ImageGrab.grab()
    
    def capture_screen_region(self, x, y, width, height):
        """Capture a specific region of the screen"""
        try:
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox=bbox)
            return screenshot
        except Exception as e:
            self.logger.error(f"Region screenshot error: {e}")
            return None
    
    def screenshot_to_base64(self, screenshot, format='PNG', quality=85):
        """Convert PIL Image to base64 string"""
        try:
            # Convert to RGB if necessary
            if screenshot.mode != 'RGB':
                screenshot = screenshot.convert('RGB')
            
            # Save to bytes buffer
            buffer = io.BytesIO()
            
            if format.upper() == 'JPEG':
                screenshot.save(buffer, format='JPEG', quality=quality, optimize=True)
            else:
                screenshot.save(buffer, format='PNG', optimize=True)
            
            # Get base64 string
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            self.logger.error(f"Base64 conversion error: {e}")
            return None
    
    def get_screenshot_info(self, screenshot):
        """Get information about the screenshot"""
        try:
            return {
                'size': screenshot.size,
                'mode': screenshot.mode,
                'format': screenshot.format,
                'width': screenshot.width,
                'height': screenshot.height
            }
        except Exception as e:
            self.logger.error(f"Screenshot info error: {e}")
            return None
    
    def resize_screenshot(self, screenshot, max_width=1024, max_height=1024):
        """Resize screenshot to reduce API costs while maintaining quality"""
        try:
            width, height = screenshot.size
            
            # Calculate scaling factor
            scale_w = max_width / width if width > max_width else 1
            scale_h = max_height / height if height > max_height else 1
            scale = min(scale_w, scale_h)
            
            if scale < 1:
                new_width = int(width * scale)
                new_height = int(height * scale)
                screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logger.info(f"Resized screenshot from {width}x{height} to {new_width}x{new_height}")
            
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Screenshot resize error: {e}")
            return screenshot
    
    def capture_and_encode(self, exclude_window_title="Exam Helper", resize=True, format='PNG'):
        """Capture screen and return base64 encoded image"""
        try:
            # Capture screenshot excluding our window
            screenshot = self.capture_screen_excluding_window(exclude_window_title)
            
            if screenshot is None:
                return None
            
            # Resize if requested to reduce API costs
            if resize:
                screenshot = self.resize_screenshot(screenshot)
            
            # Convert to base64
            base64_image = self.screenshot_to_base64(screenshot, format)
            
            if base64_image:
                self.logger.info(f"Screenshot captured and encoded successfully")
                return base64_image
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Capture and encode error: {e}")
            return None


class WindowManager:
    """Helper class for window management during screenshot capture"""
    
    @staticmethod
    def find_window_by_title(title):
        """Find window handle by title"""
        try:
            return win32gui.FindWindow(None, title)
        except:
            return None
    
    @staticmethod
    def minimize_window(hwnd):
        """Minimize a window"""
        try:
            if hwnd and win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                return True
        except:
            pass
        return False
    
    @staticmethod
    def restore_window(hwnd):
        """Restore a minimized window"""
        try:
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return True
        except:
            pass
        return False
    
    @staticmethod
    def get_window_rect(hwnd):
        """Get window rectangle"""
        try:
            if hwnd:
                return win32gui.GetWindowRect(hwnd)
        except:
            pass
        return None