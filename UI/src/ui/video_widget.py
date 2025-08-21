import cv2
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtCore import QRect

class VideoWidget(QWidget):
    roi_selected_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1280, 720)
        self.roi_start = None
        self.roi_end = None
        self.roi_selected = False
        self.selecting_roi = False
        self.dragging_corner = None
        self.roi_visible = True
        self.current_frame = None
        
    def set_frame(self, frame):
        self.current_frame = frame
        self.update()
        
    def paintEvent(self, event):
        if self.current_frame is not None:
            painter = QPainter(self)
            
            height, width, channel = self.current_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(self.current_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled_pixmap)
            
            if self.roi_visible and self.roi_start and self.roi_end:
                pen = QPen(QColor(0, 255, 0), 2)
                painter.setPen(pen)
                painter.drawRect(QRect(self.roi_start, self.roi_end))
                
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.selecting_roi:
                self.roi_start = event.pos()
                self.roi_end = event.pos()
                self.roi_selected = False
            elif self.roi_selected:
                if self.is_near_corner(event.pos(), self.roi_start):
                    self.dragging_corner = 'start'
                elif self.is_near_corner(event.pos(), self.roi_end):
                    self.dragging_corner = 'end'
                    
    def mouseMoveEvent(self, event):
        if self.selecting_roi:
            self.roi_end = event.pos()
            self.update()
        elif self.dragging_corner:
            if self.dragging_corner == 'start':
                self.roi_start = event.pos()
            elif self.dragging_corner == 'end':
                self.roi_end = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selecting_roi:
            self.roi_end = event.pos()
            self.roi_selected = True
            self.selecting_roi = False
            if hasattr(self, 'roi_selected_signal'):
                self.roi_selected_signal.emit()
        self.dragging_corner = None
        
    def is_near_corner(self, pos, corner):
        if corner is None:
            return False
        return abs(pos.x() - corner.x()) < 10 and abs(pos.y() - corner.y()) < 10
        
    def clear_roi(self):
        self.roi_start = None
        self.roi_end = None
        self.roi_selected = False
        self.update()
        
    def toggle_roi_visibility(self):
        self.roi_visible = not self.roi_visible
        self.update()
        
    def get_scaled_pixmap_rect(self):
        """Get the rectangle where the scaled pixmap is drawn"""
        if self.current_frame is None:
            return None
            
        height, width, channel = self.current_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(self.current_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Calculate the position where the scaled pixmap is drawn
        x_offset = (self.width() - scaled_pixmap.width()) // 2
        y_offset = (self.height() - scaled_pixmap.height()) // 2
        
        return QRect(x_offset, y_offset, scaled_pixmap.width(), scaled_pixmap.height())
        
    def widget_to_frame_coordinates(self, widget_pos):
        """Convert widget coordinates to frame coordinates"""
        if self.current_frame is None:
            return None
            
        scaled_rect = self.get_scaled_pixmap_rect()
        if scaled_rect is None:
            return None
            
        # Check if the point is within the scaled image area
        if not scaled_rect.contains(widget_pos):
            return None
            
        # Calculate the scale factors
        scale_x = self.current_frame.shape[1] / scaled_rect.width()
        scale_y = self.current_frame.shape[0] / scaled_rect.height()
        
        # Convert coordinates
        frame_x = int((widget_pos.x() - scaled_rect.x()) * scale_x)
        frame_y = int((widget_pos.y() - scaled_rect.y()) * scale_y)
        
        # Ensure coordinates are within frame bounds
        frame_x = max(0, min(frame_x, self.current_frame.shape[1] - 1))
        frame_y = max(0, min(frame_y, self.current_frame.shape[0] - 1))
        
        return (frame_x, frame_y) 