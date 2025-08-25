import pyaudio
import wave
import speech_recognition as sr
import threading
import queue
import time
import logging
import numpy as np

class AudioCapture:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.record_seconds = 5
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Calibrate microphone
        self.calibrate_microphone()
        
        # Last processed audio to avoid duplicates
        self.last_audio_text = ""
        self.last_audio_time = 0
        
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                self.logger.info("Microphone calibrated")
        except Exception as e:
            self.logger.error(f"Microphone calibration error: {e}")
            
    def listen_for_question(self):
        """Listen for audio questions from microphone"""
        try:
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                # Convert speech to text
                text = self.recognizer.recognize_google(audio)
                
                # Avoid duplicate processing
                if text != self.last_audio_text or time.time() - self.last_audio_time > 30:
                    self.last_audio_text = text
                    self.last_audio_time = time.time()
                    return text
                    
            return None
            
        except sr.WaitTimeoutError:
            # No audio detected, this is normal
            return None
        except sr.UnknownValueError:
            # Could not understand audio
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Audio capture error: {e}")
            return None
            
    def capture_system_audio(self):
        """Capture system audio (speaker output) - Windows specific"""
        try:
            # This is a simplified version - full implementation would require
            # more complex audio routing or third-party tools like VB-Cable
            
            # For now, we'll use a placeholder that could be extended
            # with proper system audio capture libraries
            self.logger.warning("System audio capture not fully implemented")
            return None
            
        except Exception as e:
            self.logger.error(f"System audio capture error: {e}")
            return None
            
    def record_audio_chunk(self, duration=5):
        """Record audio chunk for processing"""
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            frames = []
            for _ in range(0, int(self.rate / self.chunk * duration)):
                data = stream.read(self.chunk)
                frames.append(data)
                
            stream.stop_stream()
            stream.close()
            
            # Convert to audio data
            audio_data = b''.join(frames)
            return sr.AudioData(audio_data, self.rate, 2)
            
        except Exception as e:
            self.logger.error(f"Audio recording error: {e}")
            return None
            
    def is_speech_detected(self, audio_data, threshold=0.01):
        """Simple voice activity detection"""
        try:
            # Convert audio data to numpy array
            audio_np = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
            
            # Calculate RMS (Root Mean Square) energy
            rms = np.sqrt(np.mean(audio_np**2))
            
            # Normalize RMS
            normalized_rms = rms / 32768.0
            
            return normalized_rms > threshold
            
        except Exception as e:
            self.logger.error(f"Speech detection error: {e}")
            return False
            
    def cleanup(self):
        """Clean up audio resources"""
        try:
            self.audio.terminate()
        except Exception as e:
            self.logger.error(f"Audio cleanup error: {e}")


class SystemAudioCapture:
    """
    Extended class for system audio capture
    This would require additional setup with virtual audio cables
    or Windows WASAPI loopback recording
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def setup_loopback_recording(self):
        """Setup Windows WASAPI loopback recording"""
        # This would require pyaudio with WASAPI support
        # or alternative libraries like sounddevice
        pass
        
    def capture_speaker_output(self):
        """Capture what's playing through speakers"""
        # Implementation would depend on the audio setup
        # Could use VB-Cable or similar virtual audio driver
        pass