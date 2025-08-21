"""
Enhanced relay controller with better testing and error handling.
"""
import serial
import time
import logging
import threading
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RelayError(Exception):
    """Custom exception for relay-related errors."""
    pass

class RelayController:
    """Enhanced relay controller with better testing and error handling."""
    
    def __init__(self, port: str = 'COM4', baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize relay controller.
        Args:
            port: Serial port (e.g., 'COM4')
            baudrate: Baud rate for serial communication
            timeout: Timeout for serial operations
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.is_connected_flag = False
        self.test_mode = False
        self.test_thread = None
        self._connecting = False  # Prevent multiple simultaneous connection attempts
        logger.info(f"Relay controller initialized for port {port}")
    
    def connect(self) -> bool:
        """
        Connect to the relay with enhanced error handling.
        Returns:
            True if connection successful, False otherwise
        """
        # Prevent multiple simultaneous connection attempts
        if self._connecting:
            logger.warning("⚠️ Connection attempt already in progress, skipping...")
            return self.is_connected_flag
        
        if self.is_connected_flag and self.serial and self.serial.is_open:
            logger.info("✅ Already connected to relay")
            return True
            
        self._connecting = True
        
        try:
            # First, try to clean up any existing connection
            if self.serial and self.serial.is_open:
                self.serial.close()
                time.sleep(0.2)
            
            # Try to force release the port if it's locked
            self._force_release_port()
            
            # Attempt connection
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            if self._test_connection():
                self.is_connected_flag = True
                logger.info(f"✅ Connected to relay on {self.port}")
                return True
            else:
                self.disconnect()
                logger.error(f"❌ Connection test failed on {self.port}")
                return False
                
        except serial.SerialException as e:
            error_msg = str(e)
            if "PermissionError" in error_msg or "Access is denied" in error_msg:
                logger.warning(f"⚠️ Port {self.port} is busy or access denied - try different port or close other applications")
                # Try to force release the port
                self._force_release_port()
            else:
                logger.error(f"❌ Serial connection error on {self.port}: {error_msg}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to relay: {str(e)}")
            return False
        finally:
            self._connecting = False
    
    def _force_release_port(self):
        """Try to force release the COM port if it's locked."""
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            for port in ports:
                if port.device == self.port:
                    logger.info(f"🔄 Attempting to force release {self.port}...")
                    try:
                        # Try to open and immediately close to release the port
                        temp_serial = serial.Serial(self.port, timeout=0.1)
                        temp_serial.close()
                        time.sleep(0.2)
                        logger.info(f"✅ Successfully released {self.port}")
                    except:
                        logger.warning(f"⚠️ Could not force release {self.port}")
                    break
        except Exception as e:
            logger.debug(f"Error during port release attempt: {str(e)}")
    
    def _test_connection(self) -> bool:
        """Test the relay connection with a simple command."""
        try:
            if not self.serial or not self.serial.is_open:
                return False
            
            test_command = bytes([0xA0, 0x01, 0x00, 0xA1])
            self.serial.write(test_command)
            time.sleep(0.1)
            
            if self.serial.in_waiting > 0:
                response = self.serial.read(self.serial.in_waiting)
                logger.debug(f"Relay response: {response.hex()}")
            
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the relay with thorough cleanup."""
        try:
            # Stop any ongoing tests
            if self.test_mode:
                self.stop_test()
            
            # Turn off relay if connected
            if self.serial and self.serial.is_open:
                try:
                    self.turn_off()
                    time.sleep(0.1)
                except:
                    pass  # Ignore errors when turning off during disconnect
            
            # Close serial connection
            if self.serial:
                try:
                    self.serial.close()
                    time.sleep(0.2)  # Give time for port to release
                except:
                    pass  # Ignore errors during close
            
            # Reset connection flag
            self.is_connected_flag = False
            self.serial = None
            
            logger.info("✅ Relay disconnected and port released")
            
        except Exception as e:
            logger.error(f"Error during relay disconnect: {str(e)}")
            # Force reset even if there's an error
            self.is_connected_flag = False
            self.serial = None
    
    def is_connected(self) -> bool:
        """Check if relay is connected."""
        if not self.is_connected_flag or not self.serial:
            return False
            
        # Check if serial port is still open
        if not self.serial.is_open:
            logger.warning(f"⚠️ Serial port {self.port} was closed")
            self.is_connected_flag = False
            return False
        
        return True
    
    def turn_on(self) -> bool:
        """
        Turn the relay ON with enhanced error handling.
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.warning("❌ Not connected to relay")
            return False
        
        command = bytes([0xA0, 0x01, 0x01, 0xA2])
        try:
            self.serial.write(command)
            self.serial.flush()
            time.sleep(0.05)
            logger.info("✅ Relay turned ON")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to turn ON: {str(e)}")
            return False
    
    def turn_off(self) -> bool:
        """
        Turn the relay OFF with enhanced error handling.
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.warning("❌ Not connected to relay")
            return False
        
        command = bytes([0xA0, 0x01, 0x00, 0xA1])
        try:
            self.serial.write(command)
            self.serial.flush()
            time.sleep(0.05)
            logger.info("✅ Relay turned OFF")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to turn OFF: {str(e)}")
            return False
    
    def trigger(self, duration: float = 0.5) -> bool:
        """
        Trigger the relay for a specified duration.
        Args:
            duration: Duration in seconds to keep relay on
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("❌ Cannot trigger relay - not connected")
            return False
        
        try:
            if self.turn_on():
                time.sleep(duration)
                self.turn_off()
                logger.info(f"✅ Relay triggered for {duration} seconds")
                return True
            else:
                logger.error("❌ Failed to trigger relay")
                return False
        except Exception as e:
            logger.error(f"❌ Error during relay trigger: {str(e)}")
            return False
    
    def test_relay(self, cycles: int = 3, on_duration: float = 0.3, 
                   off_duration: float = 0.3) -> bool:
        """
        Test the relay with multiple on/off cycles.
        Args:
            cycles: Number of test cycles
            on_duration: Duration relay stays ON
            off_duration: Duration relay stays OFF
        Returns:
            True if test successful, False otherwise
        """
        if not self.is_connected():
            logger.error("❌ Cannot test relay - not connected")
            return False
        
        logger.info(f"🧪 Starting relay test: {cycles} cycles")
        try:
            for i in range(cycles):
                logger.info(f"🧪 Test cycle {i+1}/{cycles}")
                if not self.turn_on():
                    logger.error(f"❌ Failed ON in cycle {i+1}")
                    return False
                time.sleep(on_duration)
                if not self.turn_off():
                    logger.error(f"❌ Failed OFF in cycle {i+1}")
                    return False
                time.sleep(off_duration)
            
            logger.info("✅ Relay test completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error during relay test: {str(e)}")
            return False
    
    def continuous_test(self, duration: int = 10) -> bool:
        """
        Run a continuous test for a specified duration.
        Args:
            duration: Test duration in seconds
        Returns:
            True if test started successfully
        """
        if self.test_mode:
            logger.warning("⚠️ Test already running")
            return False
        
        self.test_mode = True
        self.test_thread = threading.Thread(target=self._continuous_test_thread, args=(duration,))
        self.test_thread.daemon = True
        self.test_thread.start()
        logger.info(f"🧪 Starting continuous test for {duration} seconds")
        return True
    
    def _continuous_test_thread(self, duration: int) -> None:
        """Thread for continuous relay testing."""
        start_time = time.time()
        cycle_count = 0
        
        try:
            while self.test_mode and (time.time() - start_time) < duration:
                if self.turn_on():
                    time.sleep(0.2)
                    if self.turn_off():
                        cycle_count += 1
                        time.sleep(0.2)
                    else:
                        break
                else:
                    break
        except Exception as e:
            logger.error(f"❌ Error in continuous test: {str(e)}")
        finally:
            self.test_mode = False
            logger.info(f"🧪 Continuous test completed: {cycle_count} cycles")
    
    def stop_test(self) -> None:
        """Stop continuous testing."""
        self.test_mode = False
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=1.0)
        self.turn_off()
        logger.info("🧪 Test stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get relay connection status."""
        return {
            'connected': self.is_connected(),
            'port': self.port,
            'test_mode': self.test_mode
        }
    
    def update_config(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> None:
        """Update relay configuration."""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        logger.info("Relay configuration updated")
    
    def check_connection_health(self) -> bool:
        """Check if the connection is healthy and try to fix if not."""
        try:
            if not self.is_connected_flag:
                logger.warning("⚠️ Connection flag is False, attempting to reconnect...")
                return self.connect()
            
            if not self.serial:
                logger.warning("⚠️ Serial object is None, attempting to reconnect...")
                return self.connect()
            
            if not self.serial.is_open:
                logger.warning("⚠️ Serial port is closed, attempting to reconnect...")
                return self.connect()
            
            # Try a simple test to see if the connection is responsive
            try:
                test_command = bytes([0xA0, 0x01, 0x00, 0xA1])
                self.serial.write(test_command)
                time.sleep(0.05)
                return True
            except Exception as e:
                logger.warning(f"⚠️ Connection test failed: {str(e)}, attempting to reconnect...")
                return self.connect()
                
        except Exception as e:
            logger.error(f"❌ Error checking connection health: {str(e)}")
            return False
    
    def maintain_connection(self) -> bool:
        """Maintain the connection by checking health periodically."""
        try:
            # If not connected, try to connect
            if not self.is_connected():
                logger.info(f"🔄 Connection lost, attempting to reconnect to {self.port}...")
                return self.connect()
            
            # If connected, test the connection health
            return self.check_connection_health()
            
        except Exception as e:
            logger.error(f"❌ Error maintaining connection: {str(e)}")
            return False 