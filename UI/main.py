import sys
import cv2
import datetime
import os
import json
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QComboBox,
                               QMenuBar, QMenu, QStatusBar, QGroupBox, QDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction

from src.core.video_thread import VideoThread
from src.core.detection_engine import DetectionEngine
from src.ui.video_widget import VideoWidget
from src.ui.dialogs import (DetectionSettingsDialog, 
                           DefectsWindow,
                           RelaySetupDialog)
from src.utils.database_manager import DatabaseManager
from src.utils.camera_manager import CameraManager
from src.utils.relay_controller import RelayController
from hardware_config import hardware_config

class VideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Misaligned Boards Application")
        self.setGeometry(100, 100, 1600, 900)
        
        self.video_thread = None
        self.camera_index = None
        self.defects = []
        self.defects_window = None
        
        self.detection_engine = DetectionEngine()
        self.database_manager = DatabaseManager()
        self.camera_manager = CameraManager()
        
        # Performance and stability settings (hardware optimised)
        self.detection_enabled = False
        self.last_detection_time = 0
        self.detection_interval = hardware_config.get_detection_interval()
        self.max_defects_per_second = hardware_config.get_max_defects_per_second()
        self.last_defect_time = 0
        self.defect_count_this_second = 0
        self.current_second = int(time.time())
        

        

        
        # Relay controller setup
        self.relay_controller = None
        self.relay_config = {
            'port': 'COM4',
            'baudrate': 9600,
            'timeout': 1.0,
            'trigger_duration': 0.5
        }
        self.relay_enabled = False
        
        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        self.setup_ui()
        self.setup_menu()
        
        # Setup performance monitoring timer
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)  # Update FPS every second
        
        # Setup relay connection maintenance timer
        self.relay_maintenance_timer = QTimer()
        self.relay_maintenance_timer.timeout.connect(self.maintain_relay_connection)
        self.relay_maintenance_timer.start(10000)  # Check relay connection every 10 seconds
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        toolbar = QWidget()
        toolbar.setFixedWidth(200)
        toolbar_layout = QVBoxLayout(toolbar)
        
        roi_group = QGroupBox("ROI Tools")
        roi_layout = QVBoxLayout()
        
        self.btn_select_roi = QPushButton("Select ROI")
        self.btn_select_roi.clicked.connect(self.enable_roi_selection)
        roi_layout.addWidget(self.btn_select_roi)
        
        self.btn_clear_roi = QPushButton("Clear ROI")
        self.btn_clear_roi.clicked.connect(self.clear_roi_selection)
        roi_layout.addWidget(self.btn_clear_roi)
        
        self.btn_toggle_roi = QPushButton("Hide ROI")
        self.btn_toggle_roi.clicked.connect(self.toggle_roi_visibility)
        roi_layout.addWidget(self.btn_toggle_roi)
        
        roi_group.setLayout(roi_layout)
        toolbar_layout.addWidget(roi_group)
        
        detection_group = QGroupBox("Detection")
        detection_layout = QVBoxLayout()
        
        self.btn_toggle_detection = QPushButton("Start Detection")
        self.btn_toggle_detection.clicked.connect(self.toggle_detection)
        detection_layout.addWidget(self.btn_toggle_detection)
        
        self.detection_status_label = QLabel("Detection: Disabled")
        detection_layout.addWidget(self.detection_status_label)
        
        detection_group.setLayout(detection_layout)
        toolbar_layout.addWidget(detection_group)
        
        relay_group = QGroupBox("Relay")
        relay_layout = QVBoxLayout()
        
        self.btn_test_relay = QPushButton("Test Relay")
        self.btn_test_relay.clicked.connect(self.test_relay_connection)
        relay_layout.addWidget(self.btn_test_relay)
        
        self.btn_find_ports = QPushButton("Find Ports")
        self.btn_find_ports.clicked.connect(self.find_available_ports)
        relay_layout.addWidget(self.btn_find_ports)
        
        self.btn_release_port = QPushButton("Release Port")
        self.btn_release_port.clicked.connect(self.force_release_port)
        relay_layout.addWidget(self.btn_release_port)
        
        self.relay_status_label = QLabel("Relay: Disconnected")
        relay_layout.addWidget(self.relay_status_label)
        
        relay_group.setLayout(relay_layout)
        toolbar_layout.addWidget(relay_group)
        
        performance_group = QGroupBox("Performance")
        performance_layout = QVBoxLayout()
        
        self.fps_label = QLabel("FPS: 0")
        performance_layout.addWidget(self.fps_label)
        
        self.detection_interval_label = QLabel(f"Detection Interval: {self.detection_interval}s")
        performance_layout.addWidget(self.detection_interval_label)
        
        performance_group.setLayout(performance_layout)
        toolbar_layout.addWidget(performance_group)
        
        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar)
        
        self.video_widget = VideoWidget()
        self.video_widget.roi_selected_signal.connect(self.on_roi_selected)
        main_layout.addWidget(self.video_widget)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Initialize relay after UI is set up
        self.initialize_relay()
        
    def update_fps(self):
        current_time = time.time()
        if current_time - self.last_fps_time > 0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.fps_label.setText(f"FPS: {self.current_fps:.1f}")
        self.frame_count = 0
        self.last_fps_time = current_time
        
        # Reset defect counter for new second
        current_second = int(current_time)
        if current_second != self.current_second:
            self.defect_count_this_second = 0
            self.current_second = current_second
        
    def toggle_detection(self):
        if self.detection_enabled:
            self.detection_enabled = False
            self.btn_toggle_detection.setText("Start Detection")
            self.detection_status_label.setText("Detection: Disabled")
            self.status_bar.showMessage("Detection stopped")
        else:
            if self.video_widget.roi_selected:
                self.detection_enabled = True
                self.btn_toggle_detection.setText("Stop Detection")
                self.detection_status_label.setText("Detection: Enabled")
                self.status_bar.showMessage("Detection started")
            else:
                self.status_bar.showMessage("Please select ROI first")
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        
        select_video_action = QAction("Select Video", self)
        select_video_action.triggered.connect(self.select_video)
        file_menu.addAction(select_video_action)
        
        select_camera_action = QAction("Select Camera", self)
        select_camera_action.triggered.connect(self.select_camera)
        file_menu.addAction(select_camera_action)
        
        upload_image_action = QAction("Upload Image", self)
        upload_image_action.triggered.connect(self.upload_image)
        file_menu.addAction(upload_image_action)
        

        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        settings_menu = menubar.addMenu("Settings")
        
        detection_settings_action = QAction("Detection Settings", self)
        detection_settings_action.triggered.connect(self.open_detection_settings)
        settings_menu.addAction(detection_settings_action)
        
        view_menu = menubar.addMenu("View")
        
        view_defects_action = QAction("View Defects", self)
        view_defects_action.triggered.connect(self.open_defects_window)
        view_menu.addAction(view_defects_action)
        
        relay_menu = menubar.addMenu("Relay")
        
        setup_relay_action = QAction("Setup Relay", self)
        setup_relay_action.triggered.connect(self.open_relay_setup)
        relay_menu.addAction(setup_relay_action)
        

        
    def select_video(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            try:
                if self.video_thread is not None:
                    self.video_thread.stop()
                    self.video_thread.wait()
                
                self.video_thread = VideoThread()
                self.video_thread.set_video_file(file_path)
                self.video_thread.frame_ready.connect(self.process_frame)
                self.video_thread.error_occurred.connect(self.handle_camera_error)
                self.video_thread.start()
                
                self.status_bar.showMessage(f"Playing video: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Video Error", f"Error opening video: {str(e)}")
                
    def select_camera(self):
        camera_index = self.camera_manager.select_camera_dialog(self)
        if camera_index is not None:
            self.start_camera(camera_index)
            
    def start_camera(self, camera_index):
        try:
            if self.video_thread is not None:
                self.video_thread.stop()
                self.video_thread.wait()
                
            self.video_thread = VideoThread(camera_index)
            self.video_thread.frame_ready.connect(self.process_frame)
            self.video_thread.error_occurred.connect(self.handle_camera_error)
            self.video_thread.start()
            
            self.camera_index = camera_index
            self.status_bar.showMessage(f"Connected to Camera {camera_index}")
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Camera Error", f"Error starting camera: {str(e)}")
            
    def process_frame(self, frame):
        self.frame_count += 1
        
        # Create a copy of the frame for processing
        frame_copy = frame.copy()
        
        # Only run detection if enabled, ROI is selected, and enough time has passed
        if (self.detection_enabled and 
            self.video_widget.roi_selected and 
            self.video_widget.roi_start and 
            self.video_widget.roi_end):
            
            current_time = time.time()
            if current_time - self.last_detection_time >= self.detection_interval:
                try:
                    self.run_detection(frame_copy)
                    self.last_detection_time = current_time
                except Exception as e:
                    print(f"Detection error: {str(e)}")
                    self.status_bar.showMessage(f"Detection error: {str(e)}")
        
        # Add visual indicator if detection is enabled
        if self.detection_enabled and self.video_widget.roi_selected:
            self.draw_detection_indicator(frame_copy)
            
        # Display the processed frame (with lines if detection was run)
        frame_rgb = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
        self.video_widget.set_frame(frame_rgb)
        
    def run_detection(self, frame):
        """Run detection on the ROI with proper error handling"""
        try:
            # Convert widget coordinates to frame coordinates
            frame_start = self.video_widget.widget_to_frame_coordinates(self.video_widget.roi_start)
            frame_end = self.video_widget.widget_to_frame_coordinates(self.video_widget.roi_end)
            
            if frame_start is None or frame_end is None:
                return
                
            x1, y1 = frame_start
            x2, y2 = frame_end
            
            # Ensure ROI has minimum size
            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                return
            
            # Extract ROI
            roi = frame[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]
            
            if roi.size == 0:
                return
                
            # Run detection
            processed_roi, defects = self.detection_engine.detect_and_draw_lines_with_angles(roi)
            
            # Update the frame with processed ROI
            frame[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)] = processed_roi
            
            # Show status message about detection
            if len(defects) > 0:
                self.status_bar.showMessage(f"Detected {len(defects)} defects in ROI")
            else:
                self.status_bar.showMessage("No defects detected in ROI")
            
            # Process defects with rate limiting
            self.process_defects(defects)
            
        except Exception as e:
            print(f"ROI detection error: {str(e)}")
            
    def process_defects(self, defects):
        """Process defects with rate limiting to prevent overwhelming the system"""
        current_time = time.time()
        
        # Rate limiting: max defects per second
        if current_time - self.last_defect_time < 1.0:
            if self.defect_count_this_second >= self.max_defects_per_second:
                return
        else:
            self.defect_count_this_second = 0
            self.last_defect_time = current_time
            
        for defect in defects:
            try:
                self.defect_count_this_second += 1
                
                # Log to database
                self.database_manager.log_fault(
                    fault_type="Board Alignment",
                    image_index=1,
                    details=defect['details'],
                    measurement=defect['angle']
                )
                
                self.defects.append((defect['timestamp'], defect['angle'], defect['image_path']))
                
                # Update defects window if open
                if self.defects_window is not None:
                    self.defects_window.update_defects(self.defects)
                
                # Trigger relay if enabled
                if self.relay_enabled and self.relay_controller:
                    # Check connection health before triggering
                    if self.relay_controller.maintain_connection():
                        try:
                            success = self.relay_controller.trigger(duration=self.relay_config['trigger_duration'])
                            if success:
                                self.status_bar.showMessage(f"✅ Relay triggered for defect: {defect['angle']:.1f}°")
                                print(f"✅ Relay triggered successfully for defect: {defect['angle']:.1f}°")
                            else:
                                self.status_bar.showMessage(f"❌ Relay trigger failed for defect: {defect['angle']:.1f}°")
                                print(f"❌ Relay trigger failed for defect: {defect['angle']:.1f}°")
                        except Exception as e:
                            error_msg = f"Relay trigger error: {str(e)}"
                            self.status_bar.showMessage(f"❌ {error_msg}")
                            print(f"❌ {error_msg}")
                    else:
                        print(f"⚠️ Relay connection unhealthy - attempting to reconnect...")
                        self.status_bar.showMessage(f"⚠️ Relay connection lost, attempting to reconnect...")
                else:
                    print(f"⚠️ Relay not available - enabled: {self.relay_enabled}, controller: {self.relay_controller is not None}")
                        
            except Exception as e:
                print(f"❌ Error processing defect: {str(e)}")
                
    def initialize_relay(self):
        """Initialize relay connection on startup"""
        try:
            self.relay_controller = RelayController(
                port=self.relay_config['port'],
                baudrate=self.relay_config['baudrate'],
                timeout=self.relay_config['timeout']
            )
            
            if self.relay_controller.connect():
                self.relay_enabled = True
                self.status_bar.showMessage(f"✅ Relay connected on {self.relay_config['port']}")
                print(f"✅ Relay connected successfully on {self.relay_config['port']}")
                if hasattr(self, 'relay_status_label'):
                    self.relay_status_label.setText("Relay: Connected")
                self._last_relay_status = 'connected'
            else:
                self.relay_enabled = False
                self.status_bar.showMessage(f"⚠️ Relay not connected - use Relay Setup to configure")
                print(f"⚠️ Relay not connected - use Relay Setup to configure")
                if hasattr(self, 'relay_status_label'):
                    self.relay_status_label.setText("Relay: Not Connected")
                self._last_relay_status = 'disconnected'
                
        except Exception as e:
            self.relay_enabled = False
            error_msg = f"Relay initialization error: {str(e)}"
            self.status_bar.showMessage(f"⚠️ Relay not available - use Relay Setup to configure")
            print(f"⚠️ {error_msg}")
            if hasattr(self, 'relay_status_label'):
                self.relay_status_label.setText("Relay: Error")
            self._last_relay_status = 'error'
    
    def handle_camera_error(self, error_message):
        self.status_bar.showMessage(error_message)
        
    def draw_detection_indicator(self, frame):
        """Draw a visual indicator that detection is active"""
        try:
            # Draw a small indicator in the top-left corner
            cv2.rectangle(frame, (10, 10), (30, 30), (0, 255, 0), -1)  # Green square
            cv2.putText(frame, "DET", (35, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Add relay status indicator
            if self.relay_enabled and self.relay_controller and self.relay_controller.is_connected():
                cv2.rectangle(frame, (10, 40), (30, 60), (0, 255, 0), -1)  # Green square
                cv2.putText(frame, "REL", (35, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            else:
                cv2.rectangle(frame, (10, 40), (30, 60), (0, 0, 255), -1)  # Red square
                cv2.putText(frame, "REL", (35, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error drawing detection indicator: {str(e)}")
    
    def test_relay_connection(self):
        """Test the relay connection"""
        if self.relay_controller:
            # Ensure connection is healthy before testing
            if self.relay_controller.maintain_connection():
                try:
                    success = self.relay_controller.test_relay(cycles=1, on_duration=0.1, off_duration=0.1)
                    if success:
                        self.status_bar.showMessage("✅ Relay test successful")
                        print("✅ Relay test completed successfully")
                    else:
                        self.status_bar.showMessage("❌ Relay test failed")
                        print("❌ Relay test failed")
                except Exception as e:
                    error_msg = f"Relay test error: {str(e)}"
                    self.status_bar.showMessage(f"❌ {error_msg}")
                    print(f"❌ {error_msg}")
            else:
                self.status_bar.showMessage("❌ Relay connection unhealthy")
                print("❌ Relay connection unhealthy for testing")
        else:
            self.status_bar.showMessage("❌ Relay controller not available")
            print("❌ Relay controller not available for testing")
    
    def find_available_ports(self):
        """Find available COM ports"""
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            if ports:
                port_list = [port.device for port in ports]
                print(f"Available COM ports: {port_list}")
                self.status_bar.showMessage(f"Available ports: {', '.join(port_list)}")
                return port_list
            else:
                print("No COM ports found")
                self.status_bar.showMessage("No COM ports found")
                return []
        except Exception as e:
            print(f"Error finding ports: {str(e)}")
            self.status_bar.showMessage("Error finding COM ports")
            return []
    
    def force_release_port(self):
        """Force release the current relay port"""
        try:
            if self.relay_controller:
                print(f"🔄 Force releasing {self.relay_config['port']}...")
                self.relay_controller.disconnect()
                time.sleep(0.5)  # Give extra time for port release
                print(f"✅ Force released {self.relay_config['port']}")
                self.status_bar.showMessage(f"✅ Force released {self.relay_config['port']}")
            else:
                print(f"🔄 Force releasing {self.relay_config['port']} (no controller)...")
                try:
                    import serial
                    temp_serial = serial.Serial(self.relay_config['port'], timeout=0.1)
                    temp_serial.close()
                    time.sleep(0.2)
                    print(f"✅ Force released {self.relay_config['port']}")
                    self.status_bar.showMessage(f"✅ Force released {self.relay_config['port']}")
                except:
                    print(f"⚠️ Could not force release {self.relay_config['port']}")
                    self.status_bar.showMessage(f"⚠️ Could not force release {self.relay_config['port']}")
        except Exception as e:
            print(f"❌ Error force releasing port: {str(e)}")
            self.status_bar.showMessage(f"❌ Error force releasing port")
    
    def maintain_relay_connection(self):
        """Maintain relay connection health"""
        if self.relay_controller and self.relay_enabled:
            try:
                # Get current connection state
                is_connected = self.relay_controller.is_connected()
                
                # Update UI based on actual connection state
                if is_connected:
                    if hasattr(self, 'relay_status_label'):
                        self.relay_status_label.setText("Relay: Connected")
                    # Only show status message if it changed
                    if not hasattr(self, '_last_relay_status') or self._last_relay_status != 'connected':
                        self.status_bar.showMessage(f"✅ Relay connected to {self.relay_config['port']}")
                        self._last_relay_status = 'connected'
                else:
                    if hasattr(self, 'relay_status_label'):
                        self.relay_status_label.setText("Relay: Disconnected")
                    # Only show status message if it changed
                    if not hasattr(self, '_last_relay_status') or self._last_relay_status != 'disconnected':
                        self.status_bar.showMessage(f"❌ Relay disconnected from {self.relay_config['port']}")
                        self._last_relay_status = 'disconnected'
                    
            except Exception as e:
                print(f"⚠️ Error maintaining relay connection: {str(e)}")
        
    def enable_roi_selection(self):
        self.video_widget.selecting_roi = True
        self.video_widget.roi_start = None
        self.video_widget.roi_end = None
        self.video_widget.roi_selected = False
        self.detection_enabled = False  # Stop detection during ROI selection
        self.btn_toggle_detection.setText("Start Detection")
        self.detection_status_label.setText("Detection: Disabled")
        self.status_bar.showMessage("Click and drag to select ROI")
        self.btn_select_roi.setText("ROI Selection Active")
        self.btn_select_roi.setStyleSheet("background-color: yellow;")
        
    def clear_roi_selection(self):
        self.video_widget.clear_roi()
        self.detection_enabled = False
        self.btn_toggle_detection.setText("Start Detection")
        self.detection_status_label.setText("Detection: Disabled")
        self.status_bar.showMessage("ROI cleared")
        
    def on_roi_selected(self):
        self.btn_select_roi.setText("Select ROI")
        self.btn_select_roi.setStyleSheet("")
        self.status_bar.showMessage("ROI selected - Click 'Start Detection' to begin")
        
    def toggle_roi_visibility(self):
        self.video_widget.toggle_roi_visibility()
        if self.video_widget.roi_visible:
            self.btn_toggle_roi.setText("Hide ROI")
        else:
            self.btn_toggle_roi.setText("Show ROI")
            

        
    def upload_image(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            image = cv2.imread(file_path)
            if image is not None:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.video_widget.set_frame(image_rgb)
                self.status_bar.showMessage(f"Image loaded: {file_path}")
                

                
    def open_detection_settings(self):
        dialog = DetectionSettingsDialog(self)
        dialog.standard_angle_spin.setValue(self.detection_engine.standard_angle)
        dialog.tolerance_spin.setValue(self.detection_engine.tolerance)
        dialog.min_defect_angle_spin.setValue(self.detection_engine.min_defect_angle)
        dialog.max_defect_angle_spin.setValue(self.detection_engine.max_defect_angle)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.detection_engine.set_detection_settings(
                dialog.standard_angle_spin.value(),
                dialog.tolerance_spin.value(),
                dialog.min_defect_angle_spin.value(),
                dialog.max_defect_angle_spin.value()
            )
            

        
    def open_relay_setup(self):
        dialog = RelaySetupDialog(self)
        
        # Set current values
        dialog.port_entry.setText(self.relay_config['port'])
        dialog.baudrate_combo.setCurrentText(str(self.relay_config['baudrate']))
        dialog.timeout_spin.setValue(self.relay_config['timeout'])
        dialog.trigger_duration_spin.setValue(self.relay_config['trigger_duration'])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update configuration
            config = dialog.get_config()
            self.relay_config.update(config)
            
            # Reinitialize relay controller with new settings
            try:
                if self.relay_controller:
                    self.relay_controller.disconnect()
                
                self.relay_controller = RelayController(
                    port=self.relay_config['port'],
                    baudrate=self.relay_config['baudrate'],
                    timeout=self.relay_config['timeout']
                )
                
                if self.relay_controller.connect():
                    self.relay_enabled = True
                    self.status_bar.showMessage(f"✅ Relay connected on {self.relay_config['port']}")
                    print(f"✅ Relay reconnected successfully on {self.relay_config['port']}")
                    if hasattr(self, 'relay_status_label'):
                        self.relay_status_label.setText("Relay: Connected")
                    self._last_relay_status = 'connected'
                else:
                    self.relay_enabled = False
                    self.status_bar.showMessage(f"❌ Failed to connect to relay on {self.relay_config['port']}")
                    print(f"❌ Failed to reconnect to relay on {self.relay_config['port']}")
                    if hasattr(self, 'relay_status_label'):
                        self.relay_status_label.setText("Relay: Failed")
                    self._last_relay_status = 'disconnected'
                    
            except Exception as e:
                self.relay_enabled = False
                error_msg = f"Relay setup error: {str(e)}"
                self.status_bar.showMessage(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
        

            
    def open_defects_window(self):
        if self.defects_window is None or not self.defects_window.isVisible():
            self.defects_window = DefectsWindow(self)
            self.defects_window.update_defects(self.defects)
        self.defects_window.show()
        self.defects_window.raise_()
        
    def closeEvent(self, event):
        print("🔄 Application shutting down - cleaning up resources...")
        
        # Stop video thread
        if self.video_thread is not None:
            print("🔄 Stopping video thread...")
            self.video_thread.stop()
            self.video_thread.wait()
            print("✅ Video thread stopped")
        
        # Disconnect relay properly
        if self.relay_controller:
            print("🔄 Disconnecting relay...")
            try:
                self.relay_controller.disconnect()
                print("✅ Relay disconnected")
            except Exception as e:
                print(f"⚠️ Error disconnecting relay: {str(e)}")
        
        # Force cleanup of any remaining serial connections
        try:
            import serial
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            for port in ports:
                if port.device == self.relay_config['port']:
                    print(f"🔄 Force closing {port.device}...")
                    try:
                        # Try to force close any remaining connection
                        temp_serial = serial.Serial(port.device)
                        temp_serial.close()
                        print(f"✅ Force closed {port.device}")
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Error during port cleanup: {str(e)}")
            
        print("✅ Application shutdown complete")
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VideoApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 