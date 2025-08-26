import pyaudio
import wave
import speech_recognition as sr
import threading
import queue
import time
import logging
import numpy as np
from collections import deque

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
        
        # Thread control
        self.is_monitoring = False
        self.audio_thread = None
        
        # Audio data for visualization (thread-safe)
        self.audio_data_lock = threading.Lock()
        self.current_rms = 0
        self.rms_history = deque(maxlen=100)
        self.max_rms_seen = 1000
        self.threshold_level = 300
        
        # Speech detection
        self.speech_queue = queue.Queue()
        self.speech_buffer = []
        self.silence_duration = 1.0
        self.min_speech_length = 0.5
        self.last_speech_time = 0
        
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
        # If monitoring is active, don't try to use the microphone separately
        if self.is_monitoring:
            return None
            
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
            
    def start_audio_monitoring(self):
        """Start continuous audio monitoring in dedicated thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.audio_thread = threading.Thread(target=self._dedicated_audio_thread, daemon=True)
            self.audio_thread.start()
            self.logger.info("Audio monitoring thread started")
            
    def stop_audio_monitoring(self):
        """Stop audio monitoring"""
        self.is_monitoring = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)  # Wait up to 2 seconds
        self.logger.info("Audio monitoring stopped")
        
    def _dedicated_audio_thread(self):
        """Dedicated thread for audio capture - handles both microphone and system audio"""
        self.logger.info("Starting dedicated audio capture thread")
        
        stream = None
        try:
            # Open audio stream
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.logger.info("Audio stream opened successfully")
            
            while self.is_monitoring:
                try:
                    # Read audio data (non-blocking)
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    if not data:
                        continue
                        
                    # Convert to numpy array
                    audio_np = np.frombuffer(data, dtype=np.int16)
                    if len(audio_np) == 0:
                        continue
                    
                    # Calculate RMS safely
                    rms = self._calculate_rms(audio_np)
                    
                    # Update visualization data (thread-safe)
                    with self.audio_data_lock:
                        self.current_rms = rms
                        self.rms_history.append(rms)
                        
                        # Update max RMS for dynamic scaling
                        if rms > self.max_rms_seen:
                            self.max_rms_seen = rms * 1.2
                    
                    # Handle speech detection
                    self._process_speech_detection(audio_np, rms)
                    
                    # Small sleep to prevent overwhelming the system
                    time.sleep(0.01)  # 100Hz sampling rate
                    
                except Exception as e:
                    if self.is_monitoring:
                        self.logger.error(f"Audio processing error: {e}")
                        time.sleep(0.1)  # Longer sleep on error
                        
        except Exception as e:
            self.logger.error(f"Audio thread setup error: {e}")
        finally:
            # Clean up stream
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                    self.logger.info("Audio stream closed")
                except Exception as e:
                    self.logger.error(f"Error closing audio stream: {e}")
                    
    def _calculate_rms(self, audio_data):
        """Calculate RMS safely"""
        try:
            audio_float = audio_data.astype(np.float64)
            mean_square = np.mean(audio_float**2)
            
            if np.isnan(mean_square) or np.isinf(mean_square) or mean_square < 0:
                return 0
            
            rms = np.sqrt(mean_square)
            return 0 if np.isnan(rms) or np.isinf(rms) else rms
            
        except (ValueError, RuntimeWarning):
            return 0
            
    def _process_speech_detection(self, audio_data, rms):
        """Process speech detection in audio thread"""
        try:
            current_time = time.time()
            
            if rms > self.threshold_level:
                # Speech detected
                self.speech_buffer.extend(audio_data)
                self.last_speech_time = current_time
                
            elif self.speech_buffer and (current_time - self.last_speech_time) > self.silence_duration:
                # Silence detected after speech
                min_samples = int(self.rate * self.min_speech_length)
                if len(self.speech_buffer) > min_samples:
                    # Process speech segment
                    speech_data = np.array(self.speech_buffer, dtype=np.int16)
                    
                    # Add padding
                    padding_samples = int(self.rate * 0.1)
                    silence_padding = np.zeros(padding_samples, dtype=np.int16)
                    padded_audio = np.concatenate([silence_padding, speech_data, silence_padding])
                    
                    # Create AudioData and queue it
                    audio_bytes = padded_audio.tobytes()
                    audio_data_obj = sr.AudioData(audio_bytes, self.rate, 2)
                    
                    try:
                        self.speech_queue.put_nowait(audio_data_obj)
                    except queue.Full:
                        # Queue is full, skip this speech segment
                        pass
                
                # Clear buffer
                self.speech_buffer.clear()
                
        except Exception as e:
            self.logger.error(f"Speech detection error: {e}")
            
    def get_current_audio_level(self):
        """Get the current audio level (0-1)"""
        return self.audio_levels[-1] if self.audio_levels else 0.0
        
    def get_audio_levels_history(self):
        """Get the history of audio levels for visualization"""
        return list(self.audio_levels)
        
    def get_frequency_spectrum(self):
        """Get the current frequency spectrum for visualization"""
        return list(self.frequency_data[-1]) if self.frequency_data else [0] * 25
        
    def get_rms_history(self):
        """Get the RMS history for waveform visualization (thread-safe)"""
        with self.audio_data_lock:
            return list(self.rms_history)
        
    def get_current_rms(self):
        """Get the current RMS level (thread-safe)"""
        with self.audio_data_lock:
            return self.current_rms
        
    def get_max_rms_seen(self):
        """Get the maximum RMS seen for scaling (thread-safe)"""
        with self.audio_data_lock:
            return self.max_rms_seen
        
    def get_threshold_level(self):
        """Get the current threshold level for voice detection"""
        return self.threshold_level
        
    def set_threshold_level(self, threshold):
        """Set the threshold level for voice detection"""
        self.threshold_level = max(0, threshold)
        
    def get_speech_from_queue(self):
        """Get detected speech from the queue (non-blocking)"""
        try:
            return self.speech_queue.get_nowait()
        except queue.Empty:
            return None
            
    def process_speech_audio(self, audio_data):
        """Process speech audio data and return recognized text"""
        try:
            text = self.recognizer.recognize_google(audio_data)
            
            # Avoid duplicate processing
            if text != self.last_audio_text or time.time() - self.last_audio_time > 30:
                self.last_audio_text = text
                self.last_audio_time = time.time()
                return text
                
        except sr.UnknownValueError:
            # Could not understand audio
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Speech processing error: {e}")
            return None
            
        return None
        
    def cleanup(self):
        """Clean up audio resources"""
        try:
            self.stop_audio_monitoring()
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