import cv2
import numpy as np
import time
from PySide6.QtCore import QThread, Signal

class VideoThread(QThread):
    frame_ready = Signal(np.ndarray)
    error_occurred = Signal(str)
    
    def __init__(self, camera_index=None):
        super().__init__()
        self.camera_index = camera_index
        self.video_file = None
        self.cap = None
        self.running = False
        self.camera_settings = {
            'exposure': -4,
            'gain': 0,
            'fps': 30,
            'resolution': (1280, 720),
            'global_shutter': True
        }
        
        # Performance settings
        self.max_frame_rate = 30  # Limit frame rate to prevent overwhelming
        self.frame_interval = 1.0 / self.max_frame_rate
        self.last_frame_time = 0
        
        # Error handling
        self.max_consecutive_failures = 3
        self.reconnect_delay = 2.0
        self.frame_timeout = 5.0  # Timeout for frame reading
        
    def set_camera_settings(self, settings):
        self.camera_settings = settings
        self.max_frame_rate = settings.get('fps', 30)
        self.frame_interval = 1.0 / self.max_frame_rate
        
    def set_video_file(self, file_path):
        self.video_file = file_path
        self.camera_index = None
        
    def run(self):
        if self.camera_index is None and self.video_file is None:
            self.error_occurred.emit("No video source specified")
            return
            
        try:
            self.initialize_capture()
            if self.cap is None or not self.cap.isOpened():
                raise Exception("Failed to initialize video capture")
                
            self.running = True
            consecutive_failures = 0
            
            while self.running:
                try:
                    # Frame rate limiting
                    current_time = time.time()
                    if current_time - self.last_frame_time < self.frame_interval:
                        time.sleep(0.001)  # Small sleep to prevent busy waiting
                        continue
                        
                    # Read frame with timeout
                    ret, frame = self.read_frame_with_timeout()
                    
                    if ret and frame is not None:
                        consecutive_failures = 0
                        self.last_frame_time = current_time
                        
                        # Resize frame if needed
                        if frame.shape[:2] != self.camera_settings['resolution'][::-1]:
                            frame = cv2.resize(frame, self.camera_settings['resolution'])
                            
                        self.frame_ready.emit(frame)
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= self.max_consecutive_failures:
                            raise Exception("Failed to read frame multiple times")
                            
                except Exception as e:
                    print(f"Error in video processing: {str(e)}")
                    self.error_occurred.emit("Connection lost. Attempting to reconnect...")
                    
                    if not self.reconnect():
                        break
                        
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.001)
                
        except Exception as e:
            self.error_occurred.emit(f"Error starting: {str(e)}")
            
    def initialize_capture(self):
        """Initialize video capture with proper error handling"""
        try:
            if self.video_file is not None:
                self.cap = cv2.VideoCapture(self.video_file)
                if not self.cap.isOpened():
                    raise Exception("Failed to open video file")
                    
            elif self.camera_index is not None:
                self.cap = cv2.VideoCapture(int(self.camera_index))
                if not self.cap.isOpened():
                    raise Exception("Failed to open camera")
                    
                # Apply camera settings
                self.apply_camera_settings()
                
        except Exception as e:
            print(f"Capture initialization error: {str(e)}")
            self.cap = None
            
    def apply_camera_settings(self):
        """Apply camera settings with error handling"""
        try:
            if self.cap is None:
                return
                
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_settings['resolution'][0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_settings['resolution'][1])
            
            # Set frame rate
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_settings['fps'])
            
            # Set exposure settings
            if self.camera_settings['global_shutter']:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.camera_settings['exposure'])
            else:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Auto exposure
                
            # Set gain
            self.cap.set(cv2.CAP_PROP_GAIN, self.camera_settings['gain'])
            
            # Additional camera optimisations
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimise buffer size
            
        except Exception as e:
            print(f"Camera settings error: {str(e)}")
            
    def read_frame_with_timeout(self):
        """Read frame with timeout to prevent hanging"""
        try:
            # Set a timeout for frame reading
            start_time = time.time()
            
            while time.time() - start_time < self.frame_timeout:
                ret, frame = self.cap.read()
                if ret:
                    return ret, frame
                time.sleep(0.001)
                
            return False, None
            
        except Exception as e:
            print(f"Frame reading error: {str(e)}")
            return False, None
            
    def reconnect(self):
        """Attempt to reconnect to the video source"""
        try:
            print("Attempting to reconnect...")
            
            # Release current capture
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                
            # Wait before reconnecting
            time.sleep(self.reconnect_delay)
            
            # Reinitialize capture
            self.initialize_capture()
            
            if self.cap is not None and self.cap.isOpened():
                self.error_occurred.emit("Reconnected successfully")
                return True
            else:
                self.error_occurred.emit("Failed to reconnect")
                return False
                
        except Exception as e:
            print(f"Reconnection error: {str(e)}")
            self.error_occurred.emit(f"Reconnection failed: {str(e)}")
            return False
            
    def stop(self):
        """Stop the video thread safely"""
        self.running = False
        
        # Release capture
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            
        # Wait for thread to finish
        self.wait() 