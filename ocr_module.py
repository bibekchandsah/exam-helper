import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab, Image
import logging
import time
import os
import platform
import subprocess

class OCRCapture:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_captured_text = ""
        self.last_capture_time = 0
        self.tesseract_available = False
        
        # Configure tesseract path
        self.setup_tesseract()
        
    def setup_tesseract(self):
        """Setup Tesseract OCR path and check availability"""
        try:
            # First, try to run tesseract to see if it's in PATH
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.tesseract_available = True
                self.logger.info("Tesseract found in PATH")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # If not in PATH, try common installation locations
        if platform.system() == "Windows":
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
                r'C:\tesseract\tesseract.exe'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_available = True
                    self.logger.info(f"Tesseract found at: {path}")
                    return
                    
        elif platform.system() == "Darwin":  # macOS
            possible_paths = [
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
                '/usr/bin/tesseract'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_available = True
                    self.logger.info(f"Tesseract found at: {path}")
                    return
                    
        else:  # Linux
            possible_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_available = True
                    self.logger.info(f"Tesseract found at: {path}")
                    return
        
        # If we get here, Tesseract wasn't found
        self.logger.error("Tesseract OCR not found. Please install Tesseract OCR.")
        self.tesseract_available = False
        
    def capture_screen_text(self):
        """Capture text from the entire screen using OCR"""
        if not self.tesseract_available:
            return None
            
        try:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            # Convert to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(screenshot_cv)
            
            # Perform OCR
            text = pytesseract.image_to_string(processed_image, config='--psm 6')
            
            # Clean and filter text
            cleaned_text = self.clean_text(text)
            
            # Avoid duplicate processing
            if cleaned_text != self.last_captured_text or time.time() - self.last_capture_time > 30:
                self.last_captured_text = cleaned_text
                self.last_capture_time = time.time()
                return cleaned_text
                
            return None
            
        except Exception as e:
            self.logger.error(f"OCR capture error: {e}")
            return None
            
    def capture_screen_text_immediate(self):
        """Capture text from screen immediately without duplicate checking"""
        if not self.tesseract_available:
            return None
            
        try:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            # Convert to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(screenshot_cv)
            
            # Perform OCR with different config for better accuracy
            text = pytesseract.image_to_string(processed_image, config='--psm 3')
            
            # Clean and filter text
            cleaned_text = self.clean_text(text)
            
            return cleaned_text if cleaned_text else None
            
        except Exception as e:
            self.logger.error(f"Immediate OCR capture error: {e}")
            return None
            
    def preprocess_image(self, image):
        """Preprocess image for better OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
        
    def clean_text(self, text):
        """Clean and filter extracted text"""
        if not text:
            return ""
            
        # Remove extra whitespace and newlines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = ' '.join(lines)
        
        # Remove very short text (likely noise)
        if len(cleaned_text) < 10:
            return ""
            
        return cleaned_text
        
    def capture_region_text(self, x, y, width, height):
        """Capture text from a specific screen region"""
        if not self.tesseract_available:
            return None
            
        try:
            # Capture specific region
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # Convert to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Preprocess and OCR
            processed_image = self.preprocess_image(screenshot_cv)
            text = pytesseract.image_to_string(processed_image, config='--psm 6')
            
            return self.clean_text(text)
            
        except Exception as e:
            self.logger.error(f"Region OCR capture error: {e}")
            return None
            
    def get_tesseract_status(self):
        """Get the current status of Tesseract OCR"""
        return {
            'available': self.tesseract_available,
            'path': getattr(pytesseract.pytesseract, 'tesseract_cmd', 'default'),
            'version': self.get_tesseract_version() if self.tesseract_available else None
        }
        
    def get_tesseract_version(self):
        """Get Tesseract version"""
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.split('\n')[0]
        except:
            pass
        return "Unknown"