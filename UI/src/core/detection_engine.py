import cv2
import numpy as np
import datetime
import os
import sqlite3
import time

class DetectionEngine:
    def __init__(self):
        self.standard_angle = 90
        self.tolerance = 5
        self.min_defect_angle = 80
        self.max_defect_angle = 100
        
        # Import hardware config
        try:
            from hardware_config import hardware_config
            detection_settings = hardware_config.get_optimised_detection_settings()
            
            # Performance settings (hardware optimised) - using more sensitive settings for testing
            self.min_line_length = 20  # More sensitive - detect shorter lines
            self.max_line_gap = 10     # More sensitive - allow smaller gaps
            self.canny_low = 30        # More sensitive - detect more edges
            self.canny_high = 100      # More sensitive - detect more edges
            self.hough_threshold = 50  # More sensitive - detect more lines
            self.max_defect_images = detection_settings['max_defect_images']
        except ImportError:
            # Fallback settings if hardware config not available - using more sensitive settings
            self.min_line_length = 20
            self.max_line_gap = 10
            self.canny_low = 30
            self.canny_high = 100
            self.hough_threshold = 50
            self.max_defect_images = 100
            
        # Memory management
        self.defect_image_count = 0
        
    def set_detection_settings(self, standard_angle, tolerance, min_defect_angle, max_defect_angle):
        self.standard_angle = standard_angle
        self.tolerance = tolerance
        self.min_defect_angle = min_defect_angle
        self.max_defect_angle = max_defect_angle
        
    def detect_and_draw_lines_with_angles(self, frame):
        """Detect lines and calculate angles with improved error handling"""
        try:
            if frame is None or frame.size == 0:
                return frame, []
                
            # Ensure frame is in correct format
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame.copy()
                
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection with optimised parameters
            edges = cv2.Canny(blurred, self.canny_low, self.canny_high)
            
            # Line detection with hardware-friendly parameters
            lines = cv2.HoughLinesP(
                edges, 
                1, 
                np.pi/180, 
                threshold=self.hough_threshold, 
                minLineLength=self.min_line_length, 
                maxLineGap=self.max_line_gap
            )
            
            # Debug: Print detection parameters
            print(f"Detection parameters: min_length={self.min_line_length}, max_gap={self.max_line_gap}, threshold={self.hough_threshold}")
            print(f"Canny parameters: low={self.canny_low}, high={self.canny_high}")

            defects = []
            if lines is not None and len(lines) > 0:
                # Limit the number of lines processed to prevent performance issues
                max_lines = min(len(lines), 20)
                lines = lines[:max_lines]
                
                print(f"Detected {len(lines)} lines in ROI")
                
                for line in lines:
                    try:
                        x1, y1, x2, y2 = line[0]
                        
                        # Validate line coordinates
                        if (x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0 or
                            x1 >= frame.shape[1] or y1 >= frame.shape[0] or
                            x2 >= frame.shape[1] or y2 >= frame.shape[0]):
                            continue
                            
                        # Calculate angle
                        angle = self.calculate_line_angle(x1, y1, x2, y2)
                        
                        # Check if angle is within defect range
                        if self.is_defect_angle(angle):
                            # Draw defect lines in red
                            cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            defect_info = self.create_defect_info(angle, frame)
                            if defect_info:
                                defects.append(defect_info)
                        else:
                            # Draw normal lines in green
                            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                
                    except Exception as e:
                        print(f"Error processing line: {str(e)}")
                        continue
            else:
                print("No lines detected in ROI")

            return frame, defects
            
        except Exception as e:
            print(f"Detection error: {str(e)}")
            return frame, []
            
    def calculate_line_angle(self, x1, y1, x2, y2):
        """Calculate the angle of a line with proper error handling"""
        try:
            # Calculate angle in degrees
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # Normalise angle to 0-90 degrees
            if angle > 90:
                angle = 180 - angle
                
            return angle
            
        except Exception as e:
            print(f"Angle calculation error: {str(e)}")
            return 0
            
    def is_defect_angle(self, angle):
        """Check if angle indicates a defect"""
        try:
            # Check if angle deviates from standard by more than tolerance
            angle_deviation = abs(angle - self.standard_angle)
            
            # Also check if angle is within the defect range
            return (angle_deviation > self.tolerance and 
                   self.min_defect_angle <= angle <= self.max_defect_angle)
                   
        except Exception as e:
            print(f"Defect angle check error: {str(e)}")
            return False
            
    def create_defect_info(self, angle, frame):
        """Create defect information with memory management"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Only save image if we haven't exceeded the limit
            image_path = None
            if self.defect_image_count < self.max_defect_images:
                image_path = self.save_defect_frame(frame.copy(), timestamp)
                self.defect_image_count += 1
            else:
                # Clean up old images if we've reached the limit
                self.cleanup_old_defect_images()
                image_path = self.save_defect_frame(frame.copy(), timestamp)
                self.defect_image_count = 1
                
            defect_info = {
                'timestamp': timestamp,
                'angle': angle,
                'image_path': image_path,
                'details': f"Board angle {angle:.1f}° deviates from standard {self.standard_angle}° by {abs(angle - self.standard_angle):.1f}°"
            }
            
            return defect_info
            
        except Exception as e:
            print(f"Error creating defect info: {str(e)}")
            return None
        
    def save_defect_frame(self, frame, timestamp):
        """Save defect frame with error handling"""
        try:
            if not os.path.exists("defect_images"):
                os.makedirs("defect_images")

            filename = f"defect_images/defect_{timestamp.replace(':', '-')}.png"
            
            # Ensure frame is in BGR format for saving
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                # Already in BGR format
                cv2.imwrite(filename, frame)
            else:
                # Convert to BGR if needed
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                cv2.imwrite(filename, frame_bgr)
                
            return filename
            
        except Exception as e:
            print(f"Error saving defect frame: {str(e)}")
            return None
            
    def cleanup_old_defect_images(self):
        """Clean up old defect images to prevent disk space issues"""
        try:
            defect_dir = "defect_images"
            if not os.path.exists(defect_dir):
                return
                
            # Get all defect image files
            files = [f for f in os.listdir(defect_dir) if f.startswith("defect_") and f.endswith(".png")]
            
            if len(files) > self.max_defect_images:
                # Sort by modification time (oldest first)
                files.sort(key=lambda x: os.path.getmtime(os.path.join(defect_dir, x)))
                
                # Remove oldest files
                files_to_remove = files[:-self.max_defect_images]
                for file in files_to_remove:
                    try:
                        os.remove(os.path.join(defect_dir, file))
                    except Exception as e:
                        print(f"Error removing old defect image {file}: {str(e)}")
                        
        except Exception as e:
            print(f"Error cleaning up defect images: {str(e)}")
        
    def log_fault_to_database(self, fault_type, image_index, details, measurement=None):
        """Log fault to database with error handling"""
        try:
            conn = sqlite3.connect('faults.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO faults (timestamp, fault_type, image_index, details, measurement)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                  fault_type, image_index, details, measurement))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database logging error: {str(e)}") 