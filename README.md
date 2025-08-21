# Industrial Board Alignment Detection System

A professional computer vision application for detecting misaligned boards in industrial manufacturing processes. This system provides real-time line detection, angle analysis, and automated relay triggering for quality control.

## 🚀 Features

- **Real-time Video Processing**: Live camera feed with OpenCV-based line detection
- **Intelligent ROI Selection**: Interactive region of interest selection for targeted analysis
- **Angle-based Defect Detection**: Sophisticated algorithm to detect board misalignment
- **Industrial Hardware Integration**: Relay control for automated sorting/rejection
- **Performance Optimization**: Hardware-aware settings for different system capabilities
- **Database Logging**: Comprehensive defect tracking and reporting
- **Professional UI**: Modern PySide6 interface with real-time feedback

## 🛠️ Technical Stack

- **Python 3.8+**
- **OpenCV 4.x** - Computer vision and image processing
- **PySide6** - Qt-based GUI framework
- **SQLite** - Local database for defect logging
- **Serial Communication** - Industrial relay control
- **Multi-threading** - Real-time video processing

## 📋 Requirements

```bash
pip install -r requirements.txt
```

### Core Dependencies:
- `opencv-python>=4.8.0`
- `PySide6>=6.5.0`
- `pyserial>=3.5`
- `numpy>=1.21.0`
- `psutil>=5.9.0` (optional, for hardware detection)

### Build Dependencies:
- `pyinstaller>=5.0.0`

## 🏗️ Architecture

```
src/
├── core/
│   ├── detection_engine.py    # Line detection and angle analysis
│   └── video_thread.py        # Multi-threaded video capture
├── ui/
│   ├── video_widget.py        # Video display and ROI selection
│   └── dialogs.py             # Configuration dialogs
└── utils/
    ├── camera_manager.py      # Camera device management
    ├── database_manager.py    # SQLite defect logging
    ├── relay_controller.py    # Industrial relay control
    └── template_manager.py    # Detection template management
```

## 🎯 Usage

### Quick Start
1. **Launch Application**:
   ```bash
   python main.py
   ```

2. **Build Executable** (optional):
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --windowed main.py
   ```

2. **Select Video Source**:
   - File → Select Camera (for live feed)
   - File → Select Video (for recorded footage)
   - File → Upload Image (for single image analysis)

3. **Configure Detection**:
   - Click "Select ROI" and draw region of interest
   - Adjust detection settings via Settings → Detection Settings
   - Configure relay settings via Relay → Setup Relay

4. **Start Detection**:
   - Click "Start Detection" to begin real-time analysis
   - Monitor status indicators and detection results

### Key Controls

#### ROI Tools
- **Select ROI**: Draw region of interest for analysis
- **Clear ROI**: Remove current selection
- **Hide/Show ROI**: Toggle ROI visibility

#### Detection
- **Start/Stop Detection**: Control real-time analysis
- **Detection Settings**: Configure angle thresholds and sensitivity

#### Relay Control
- **Test Relay**: Verify relay functionality
- **Find Ports**: Discover available COM ports
- **Release Port**: Force release locked COM ports

## ⚙️ Configuration

### Detection Settings
- **Standard Angle**: Expected board alignment (default: 90°)
- **Tolerance**: Acceptable deviation range (default: ±5°)
- **Defect Range**: Min/max angles for defect classification

### Hardware Settings
- **Performance Profile**: Auto-detected based on system capabilities
- **Camera Settings**: Resolution, FPS, exposure optimization
- **Relay Configuration**: COM port, baud rate, trigger duration

## 🔧 Advanced Features

### Hardware Optimization
The system detects hardware capabilities and optimizes settings:
- **High Performance**: 8+ cores, 16GB+ RAM
- **Medium Performance**: 4+ cores, 8GB+ RAM  
- **Low Performance**: Basic systems with limited resources

### Connection Management
- **Robust Reconnection**: Handles relay connection issues
- **Port Management**: COM port allocation and management
- **Error Recovery**: Handles connection failures gracefully

### Defect Analysis
- **Real-time Processing**: Live angle calculation and classification
- **Database Logging**: Defect tracking with timestamps
- **Image Capture**: Saves defect images automatically
- **Statistical Analysis**: Defect rate monitoring and reporting

## 📊 Performance

### Detection Capabilities
- **Processing Speed**: 15-30 FPS (hardware dependent)
- **Detection Accuracy**: Configurable sensitivity levels
- **Response Time**: <100ms for defect detection
- **Memory Usage**: Optimized for long-running sessions

### Supported Hardware
- **Cameras**: USB, IP cameras, video files
- **Relays**: Standard serial relay modules
- **Systems**: Windows, Linux, macOS

## 🐛 Troubleshooting

### Common Issues

#### Camera Not Detected
- Check camera permissions
- Verify camera is not in use by other applications
- Try different camera index in camera selection

#### Relay Connection Issues
- Use "Find Ports" to verify available COM ports
- Check relay device is powered and connected
- Use "Release Port" if port is locked
- Verify baud rate and COM port settings

#### Performance Issues
- Reduce detection interval in settings
- Lower camera resolution
- Close other resource-intensive applications
- Check hardware optimization settings

### Debug Information
- Enable debug logging in console output
- Monitor FPS and detection statistics
- Check database for defect logging
- Review relay connection status

## 📝 License

This project is proprietary software. All rights reserved. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add feature description'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## 📞 Support

For technical support or feature requests:
- Create an issue in the GitHub repository
- Include system specifications and error logs
- Provide detailed description of the problem


---

**Note**: This system is designed for industrial use. Ensure proper safety protocols when integrating with manufacturing equipment. 
