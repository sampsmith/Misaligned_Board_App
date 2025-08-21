import cv2
import numpy as np
import datetime
import os
import json
import socket
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
                               QSlider, QCheckBox, QComboBox, QMessageBox,
                               QTextEdit, QListWidget, QInputDialog, QScrollArea,
                               QGroupBox, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

class CameraSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Camera Settings")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        resolution_group = QGroupBox("Resolution")
        resolution_layout = QVBoxLayout()
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080"])
        resolution_layout.addWidget(self.resolution_combo)
        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)
        
        exposure_group = QGroupBox("Exposure")
        exposure_layout = QVBoxLayout()
        self.auto_exposure_check = QCheckBox("Auto Exposure")
        exposure_layout.addWidget(self.auto_exposure_check)
        
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setRange(-10, 0)
        self.exposure_slider.setValue(-4)
        exposure_layout.addWidget(QLabel("Exposure"))
        exposure_layout.addWidget(self.exposure_slider)
        exposure_group.setLayout(exposure_layout)
        layout.addWidget(exposure_group)
        
        gain_group = QGroupBox("Gain")
        gain_layout = QVBoxLayout()
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, 100)
        self.gain_slider.setValue(0)
        gain_layout.addWidget(self.gain_slider)
        gain_group.setLayout(gain_layout)
        layout.addWidget(gain_group)
        
        fps_group = QGroupBox("FPS")
        fps_layout = QVBoxLayout()
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 120)
        self.fps_slider.setValue(30)
        fps_layout.addWidget(self.fps_slider)
        fps_group.setLayout(fps_layout)
        layout.addWidget(fps_group)
        
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class DetectionSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detection Settings")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Standard Angle"))
        self.standard_angle_spin = QDoubleSpinBox()
        self.standard_angle_spin.setRange(0, 180)
        self.standard_angle_spin.setValue(90)
        layout.addWidget(self.standard_angle_spin)
        
        layout.addWidget(QLabel("Tolerance"))
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 90)
        self.tolerance_spin.setValue(5)
        layout.addWidget(self.tolerance_spin)
        
        layout.addWidget(QLabel("Minimum Defect Angle"))
        self.min_defect_angle_spin = QDoubleSpinBox()
        self.min_defect_angle_spin.setRange(0, 180)
        self.min_defect_angle_spin.setValue(80)
        layout.addWidget(self.min_defect_angle_spin)
        
        layout.addWidget(QLabel("Maximum Defect Angle"))
        self.max_defect_angle_spin = QDoubleSpinBox()
        self.max_defect_angle_spin.setRange(0, 180)
        self.max_defect_angle_spin.setValue(100)
        layout.addWidget(self.max_defect_angle_spin)
        
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class SocketSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Socket Setup")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Host"))
        self.host_entry = QLineEdit()
        self.host_entry.setText("localhost")
        layout.addWidget(self.host_entry)
        
        layout.addWidget(QLabel("Port"))
        self.port_entry = QLineEdit()
        self.port_entry.setText("12345")
        layout.addWidget(self.port_entry)
        
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.connect_socket)
        layout.addWidget(connect_button)
        
        self.setLayout(layout)
        
    def connect_socket(self):
        host = self.host_entry.text()
        try:
            port = int(self.port_entry.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Please enter a valid port number")
            return
            
        if self.ping_host(host, port):
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet("color: green;")
            self.accept()
        else:
            self.status_label.setText("Status: Connection Failed")
            self.status_label.setStyleSheet("color: red;")
            
    def ping_host(self, host, port):
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

class PalletSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pallet Setup")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Low Signal Duration (seconds)"))
        self.low_signal_duration_spin = QDoubleSpinBox()
        self.low_signal_duration_spin.setRange(0.1, 10.0)
        self.low_signal_duration_spin.setValue(1.0)
        self.low_signal_duration_spin.setSingleStep(0.1)
        layout.addWidget(self.low_signal_duration_spin)
        
        layout.addWidget(QLabel("Target Board Count"))
        self.target_board_count_spin = QSpinBox()
        self.target_board_count_spin.setRange(1, 100)
        self.target_board_count_spin.setValue(5)
        layout.addWidget(self.target_board_count_spin)
        
        button_layout = QHBoxLayout()
        save_template_button = QPushButton("Save as Template")
        save_template_button.clicked.connect(self.save_template)
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_template_button)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def save_template(self):
        name, ok = QInputDialog.getText(self, "Template Name", "Enter a name for the template:")
        if ok and name:
            template = {
                "low_signal_duration": self.low_signal_duration_spin.value(),
                "target_board_count": self.target_board_count_spin.value()
            }
            with open(f"{name}.json", "w") as file:
                json.dump(template, file)
            QMessageBox.information(self, "Success", f"Template saved as {name}.json")

class DefectsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Defects")
        self.setModal(False)
        self.resize(600, 400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        self.defects_widget = QWidget()
        self.defects_layout = QVBoxLayout(self.defects_widget)
        scroll_area.setWidget(self.defects_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
        
    def update_defects(self, defects):
        for i in reversed(range(self.defects_layout.count())):
            self.defects_layout.itemAt(i).widget().setParent(None)
            
        for i, (timestamp, angle, image_path) in enumerate(defects):
            defect_label = QLabel(f"Defect {i+1}: {angle:.2f}° at {timestamp}")
            self.defects_layout.addWidget(defect_label)
            
            view_button = QPushButton("View Image")
            view_button.clicked.connect(lambda checked, path=image_path: self.show_image(path))
            self.defects_layout.addWidget(view_button)
            
    def show_image(self, image_path):
        if os.path.exists(image_path):
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                image_window = QDialog(self)
                image_window.setWindowTitle("Defect Image")
                image_window.resize(800, 600)
                
                layout = QVBoxLayout()
                image_label = QLabel()
                image_label.setPixmap(pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                layout.addWidget(image_label)
                image_window.setLayout(layout)
                image_window.show() 

class RelaySetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relay Setup")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Port configuration
        layout.addWidget(QLabel("Serial Port"))
        self.port_entry = QLineEdit()
        self.port_entry.setText("COM4")
        layout.addWidget(self.port_entry)
        
        # Baud rate configuration
        layout.addWidget(QLabel("Baud Rate"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        layout.addWidget(self.baudrate_combo)
        
        # Timeout configuration
        layout.addWidget(QLabel("Timeout (seconds)"))
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 10.0)
        self.timeout_spin.setValue(1.0)
        self.timeout_spin.setSingleStep(0.1)
        layout.addWidget(self.timeout_spin)
        
        # Trigger duration configuration
        layout.addWidget(QLabel("Trigger Duration (seconds)"))
        self.trigger_duration_spin = QDoubleSpinBox()
        self.trigger_duration_spin.setRange(0.1, 5.0)
        self.trigger_duration_spin.setValue(0.5)
        self.trigger_duration_spin.setSingleStep(0.1)
        layout.addWidget(self.trigger_duration_spin)
        
        # Status display
        self.status_label = QLabel("Status: Not Connected")
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(test_button)
        
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.accept)
        button_layout.addWidget(apply_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def test_connection(self):
        """Test the relay connection."""
        try:
            from src.utils.relay_controller import RelayController
            
            port = self.port_entry.text()
            baudrate = int(self.baudrate_combo.currentText())
            timeout = self.timeout_spin.value()
            
            relay = RelayController(port=port, baudrate=baudrate, timeout=timeout)
            
            if relay.connect():
                self.status_label.setText("Status: Connected")
                self.status_label.setStyleSheet("color: green;")
                
                # Test the relay
                if relay.test_relay(cycles=1, on_duration=0.2, off_duration=0.2):
                    QMessageBox.information(self, "Success", "Relay connection and test successful!")
                else:
                    QMessageBox.warning(self, "Warning", "Relay connected but test failed.")
                
                relay.disconnect()
            else:
                self.status_label.setText("Status: Connection Failed")
                self.status_label.setStyleSheet("color: red;")
                QMessageBox.critical(self, "Error", "Failed to connect to relay.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error testing relay: {str(e)}")
    
    def get_config(self):
        """Get the relay configuration."""
        return {
            'port': self.port_entry.text(),
            'baudrate': int(self.baudrate_combo.currentText()),
            'timeout': self.timeout_spin.value(),
            'trigger_duration': self.trigger_duration_spin.value()
        } 