import unittest
from unittest.mock import patch, mock_open
import json
import os
import sys
import tkinter as tk

# Adjust sys.path to allow importing SpyEye from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SpyEye import PortScannerGUI

class TestSpyEyeUtils(unittest.TestCase):

    def test_parse_port_range_valid(self):
        """Test _parse_port_range with valid inputs."""
        self.assertEqual(PortScannerGUI._parse_port_range("1-1024"), (1, 1024))
        self.assertEqual(PortScannerGUI._parse_port_range("80-80"), (80, 80))
        self.assertEqual(PortScannerGUI._parse_port_range("1-65535"), (1, 65535))

    def test_parse_port_range_invalid_format(self):
        """Test _parse_port_range with invalid formats."""
        with self.assertRaisesRegex(ValueError, "must be in 'start-end' format"):
            PortScannerGUI._parse_port_range("1_1024")
        with self.assertRaisesRegex(ValueError, "must be in 'start-end' format"):
            PortScannerGUI._parse_port_range("80")
        with self.assertRaisesRegex(ValueError, "must be in 'start-end' format"):
            PortScannerGUI._parse_port_range("1-1024-2000")
        with self.assertRaisesRegex(ValueError, "must be in 'start-end' format"):
            PortScannerGUI._parse_port_range("-")
        with self.assertRaisesRegex(ValueError, "must be in 'start-end' format"):
            PortScannerGUI._parse_port_range("1-")
        with self.assertRaisesRegex(ValueError, "must be in 'start-end' format"):
            PortScannerGUI._parse_port_range("-1024")


    def test_parse_port_range_non_integer_ports(self):
        """Test _parse_port_range with non-integer ports."""
        with self.assertRaisesRegex(ValueError, "must be integers"):
            PortScannerGUI._parse_port_range("abc-1024")
        with self.assertRaisesRegex(ValueError, "must be integers"):
            PortScannerGUI._parse_port_range("1-xyz")
        with self.assertRaisesRegex(ValueError, "must be integers"):
            PortScannerGUI._parse_port_range("a-b")

    def test_parse_port_range_out_of_bounds(self):
        """Test _parse_port_range with ports out of 1-65535 range."""
        with self.assertRaisesRegex(ValueError, "Ports must be between 1 and 65535"):
            PortScannerGUI._parse_port_range("0-1024")
        with self.assertRaisesRegex(ValueError, "Ports must be between 1 and 65535"):
            PortScannerGUI._parse_port_range("1-65536")
        with self.assertRaisesRegex(ValueError, "Ports must be between 1 and 65535"):
            PortScannerGUI._parse_port_range("-5-10") # also caught by format due to split

    def test_parse_port_range_start_greater_than_end(self):
        """Test _parse_port_range with start port greater than end port."""
        with self.assertRaisesRegex(ValueError, "Start port cannot be greater than end port"):
            PortScannerGUI._parse_port_range("1024-1")

    def test_parse_port_range_not_string(self):
        """Test _parse_port_range with non-string input."""
        with self.assertRaisesRegex(ValueError, "Port range must be a string"):
            PortScannerGUI._parse_port_range(123)


    @classmethod
    def setUpClass(cls):
        """Set up a dummy Tkinter root for GUI-independent tests if needed, and suppress window."""
        cls.root = tk.Tk()
        cls.root.withdraw() # Hide the main window

    @classmethod
    def tearDownClass(cls):
        """Destroy the dummy Tkinter root."""
        cls.root.destroy()

    def setUp(self):
        """Setup for each test: create a PortScannerGUI instance."""
        # Pass a dummy root window; it won't be used for these utils tests directly
        # but methods like load_scan_count are instance methods.
        self.app_gui = PortScannerGUI(root_window=self.root)
        # Define a dummy path for scan_data_file for tests
        self.app_gui.scan_data_file = "test_spyeye_demo.json"


    def tearDown(self):
        """Clean up: remove the dummy scan data file if it was created."""
        if os.path.exists(self.app_gui.scan_data_file):
            os.remove(self.app_gui.scan_data_file)


    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_scan_count(self, mock_json_dump, mock_file_open):
        """Test save_scan_count to ensure it writes correct data."""
        self.app_gui.scan_count = 5
        self.app_gui.save_scan_count()

        mock_file_open.assert_called_once_with(self.app_gui.scan_data_file, 'w')
        mock_json_dump.assert_called_once_with({'scan_count': 5}, mock_file_open())

    @patch("os.path.exists")
    def test_load_scan_count_file_exists_valid_json(self, mock_path_exists):
        """Test load_scan_count with existing file and valid JSON."""
        mock_path_exists.return_value = True
        mock_file_content = json.dumps({'scan_count': 2})
        with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
            self.app_gui.load_scan_count()
            self.assertEqual(self.app_gui.scan_count, 2)
            mock_file.assert_called_once_with(self.app_gui.scan_data_file, 'r')

    @patch("os.path.exists")
    def test_load_scan_count_file_exists_invalid_json(self, mock_path_exists):
        """Test load_scan_count with existing file but invalid JSON."""
        mock_path_exists.return_value = True
        mock_file_content = "this is not json"
        # Mock print to suppress console output during test
        with patch("builtins.open", mock_open(read_data=mock_file_content)), \
             patch("builtins.print") as mock_print:
            self.app_gui.load_scan_count()
            self.assertEqual(self.app_gui.scan_count, 0) # Should default to 0
            mock_print.assert_called() # Check that a warning was printed

    @patch("os.path.exists")
    def test_load_scan_count_file_not_found(self, mock_path_exists):
        """Test load_scan_count when the scan data file does not exist."""
        mock_path_exists.return_value = False
        with patch("builtins.print") as mock_print: # Suppress potential info print
            self.app_gui.load_scan_count()
            self.assertEqual(self.app_gui.scan_count, 0) # Should default to 0
            # No print expected if file simply doesn't exist (initial run state)

    @patch("os.path.exists")
    def test_load_scan_count_io_error(self, mock_path_exists):
        """Test load_scan_count when an IOError occurs during file open."""
        mock_path_exists.return_value = True
        with patch("builtins.open", side_effect=IOError("File access error")) as mock_file_open, \
             patch("builtins.print") as mock_print:
            self.app_gui.load_scan_count()
            self.assertEqual(self.app_gui.scan_count, 0) # Should default to 0
            mock_file_open.assert_called_once_with(self.app_gui.scan_data_file, 'r')
            mock_print.assert_called() # Check that a warning was printed

    @patch("os.path.exists")
    def test_load_scan_count_negative_value_in_file(self, mock_path_exists):
        """Test load_scan_count with a negative scan_count value in the file."""
        mock_path_exists.return_value = True
        mock_file_content = json.dumps({'scan_count': -1})
        with patch("builtins.open", mock_open(read_data=mock_file_content)), \
             patch("builtins.print") as mock_print:
            self.app_gui.load_scan_count()
            self.assertEqual(self.app_gui.scan_count, 0) # Should default to 0 if negative
            # A print might occur due to ValueError if int() conversion is strict or if logic handles it
            # The current implementation defaults negative values to 0 silently after int conversion.


if __name__ == "__main__":
    unittest.main()
