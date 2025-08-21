import cv2
import platform
from PySide6.QtWidgets import QInputDialog, QMessageBox

class CameraManager:
    def __init__(self):
        self.is_linux = platform.system() == 'Linux'
        
    def list_available_cameras(self):
        available_cameras = []
        try:
            # Try a range of camera indices with better error handling
            for i in range(4):  # Try more camera indices
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        # Try to read a frame to verify the camera works
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            name = f"Camera {i}"
                            path = str(i)
                            available_cameras.append((path, name))
                            print(f"Found camera: {name} at index {i}")
                        cap.release()
                    else:
                        cap.release()
                except Exception as e:
                    print(f"Error testing camera {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error listing cameras: {str(e)}")
        
        return available_cameras
        
    def select_camera_dialog(self, parent):
        available_cameras = self.list_available_cameras()
        if available_cameras:
            camera_names = [f"Camera {i}" for i in range(len(available_cameras))]
            camera_index, ok = QInputDialog.getItem(parent, "Select Camera", 
                                                  "Choose a camera:", 
                                                  camera_names, 
                                                  0, False)
            if ok:
                try:
                    camera_num = int(camera_index.split()[-1])
                    return camera_num
                except ValueError:
                    QMessageBox.warning(parent, "Error", "Invalid camera selection")
                    return None
        else:
            QMessageBox.warning(parent, "No Cameras", 
                              "No cameras found. Please check:\n"
                              "1. Camera is connected\n"
                              "2. Camera drivers are installed\n"
                              "3. No other application is using the camera")
            return None
            
    def get_camera_info(self, camera_index):
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                # Try to read a frame first
                ret, frame = cap.read()
                if not ret:
                    print(f"Camera {camera_index} opened but cannot read frames")
                    cap.release()
                    return None
                    
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                cap.release()
                return {
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'index': camera_index
                }
            else:
                print(f"Failed to open camera {camera_index}")
        except Exception as e:
            print(f"Error getting camera info: {str(e)}")
        return None
        
    def test_camera_connection(self, camera_index):
        """Test if a camera can be opened and read from"""
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                return ret and frame is not None
            else:
                return False
        except Exception as e:
            print(f"Error testing camera {camera_index}: {str(e)}")
            return False 