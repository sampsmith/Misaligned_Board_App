"""
Hardware Configuration Settings
This file contains optimised settings for different hardware capabilities.
"""

import platform
import cv2

# Try to import psutil, fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available, using default hardware settings")

class HardwareConfig:
    """Hardware-aware configuration settings"""
    
    def __init__(self):
        self.detect_hardware()
        self.set_optimised_settings()
        
    def detect_hardware(self):
        """Detect hardware capabilities"""
        if PSUTIL_AVAILABLE:
            self.cpu_count = psutil.cpu_count()
            self.memory_gb = psutil.virtual_memory().total / (1024**3)
        else:
            # Fallback values for when psutil is not available
            self.cpu_count = 4  # Default assumption
            self.memory_gb = 8.0  # Default assumption
            
        self.platform = platform.system()
        
        # Detect OpenCV capabilities
        self.opencv_version = cv2.__version__
        try:
            self.has_cuda = cv2.cuda.getCudaEnabledDeviceCount() > 0
        except:
            self.has_cuda = False
        
        print(f"Hardware Detection:")
        print(f"  CPU Cores: {self.cpu_count}")
        print(f"  Memory: {self.memory_gb:.1f} GB")
        print(f"  Platform: {self.platform}")
        print(f"  OpenCV: {self.opencv_version}")
        print(f"  CUDA Available: {self.has_cuda}")
        
    def set_optimised_settings(self):
        """Set optimised settings based on hardware"""
        
        # Performance profiles based on hardware
        if self.cpu_count >= 8 and self.memory_gb >= 16:
            self.performance_profile = "high"
        elif self.cpu_count >= 4 and self.memory_gb >= 8:
            self.performance_profile = "medium"
        else:
            self.performance_profile = "low"
            
        print(f"Performance Profile: {self.performance_profile}")
        
        # Detection settings based on performance profile
        if self.performance_profile == "high":
            self.detection_interval = 0.2  # 5 FPS detection
            self.max_defects_per_second = 10
            self.min_line_length = 30
            self.max_line_gap = 15
            self.hough_threshold = 60
            self.max_defect_images = 200
            self.camera_fps = 30
            self.resolution = (1920, 1080)
            
        elif self.performance_profile == "medium":
            self.detection_interval = 0.5  # 2 FPS detection
            self.max_defects_per_second = 5
            self.min_line_length = 50
            self.max_line_gap = 20
            self.hough_threshold = 80
            self.max_defect_images = 100
            self.camera_fps = 25
            self.resolution = (1280, 720)
            
        else:  # low performance
            self.detection_interval = 1.0  # 1 FPS detection
            self.max_defects_per_second = 3
            self.min_line_length = 80
            self.max_line_gap = 30
            self.hough_threshold = 100
            self.max_defect_images = 50
            self.camera_fps = 15
            self.resolution = (640, 480)
            
        # Camera settings
        self.camera_settings = {
            'exposure': -4,
            'gain': 0,
            'fps': self.camera_fps,
            'resolution': self.resolution,
            'global_shutter': True
        }
        
        # Video thread settings
        self.video_thread_settings = {
            'max_frame_rate': self.camera_fps,
            'max_consecutive_failures': 3,
            'reconnect_delay': 2.0,
            'frame_timeout': 5.0
        }
        
        # Detection engine settings
        self.detection_settings = {
            'min_line_length': self.min_line_length,
            'max_line_gap': self.max_line_gap,
            'canny_low': 50,
            'canny_high': 150,
            'hough_threshold': self.hough_threshold,
            'max_defect_images': self.max_defect_images
        }
        
    def get_optimised_camera_settings(self):
        """Get optimised camera settings"""
        return self.camera_settings.copy()
        
    def get_optimised_detection_settings(self):
        """Get optimised detection settings"""
        return self.detection_settings.copy()
        
    def get_optimised_video_thread_settings(self):
        """Get optimised video thread settings"""
        return self.video_thread_settings.copy()
        
    def get_detection_interval(self):
        """Get optimised detection interval"""
        return self.detection_interval
        
    def get_max_defects_per_second(self):
        """Get optimised max defects per second"""
        return self.max_defects_per_second
        
    def print_settings(self):
        """Print current optimised settings"""
        print(f"\nOptimised Settings for {self.performance_profile} performance:")
        print(f"  Detection Interval: {self.detection_interval}s")
        print(f"  Max Defects/Second: {self.max_defects_per_second}")
        print(f"  Camera FPS: {self.camera_fps}")
        print(f"  Resolution: {self.resolution}")
        print(f"  Min Line Length: {self.min_line_length}")
        print(f"  Max Line Gap: {self.max_line_gap}")
        print(f"  Hough Threshold: {self.hough_threshold}")
        print(f"  Max Defect Images: {self.max_defect_images}")

# Global hardware config instance
hardware_config = HardwareConfig()

if __name__ == "__main__":
    # Test the hardware configuration
    hardware_config.print_settings()
