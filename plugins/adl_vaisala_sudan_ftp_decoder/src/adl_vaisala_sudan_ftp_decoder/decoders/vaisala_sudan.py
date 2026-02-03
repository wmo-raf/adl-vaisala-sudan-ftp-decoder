import re
from datetime import datetime

from adl_ftp_plugin.registries import FTPDecoder


class VaisalaSudanDecoder(FTPDecoder):
    """
    Decoder for Vaisala AWS stations (Sudan format).
    Parses semicolon-delimited key:value strings with checksum.
    
    Example format:
    2026-01-10 12:21:42.655, (S:ATB012;D:260110;T:141300;TAAVG1M:31.8;...)BB38EB4A
    """
    
    type = "vaisala_sudan"
    compat_type = "vaisala_sudan"
    display_name = "Vaisala (Sudan)"
    
    # Parameters that should remain as strings (not converted to float)
    STRING_PARAMS = {'S', 'STATUS', 'SENSORSTATUS', 'PTEND3H'}
    
    # Parameters with "/" as null value
    NULL_VALUE = '/'
    
    def decode(self, file_path):
        with open(file_path, "r", encoding="UTF-8") as f_in:
            data_values = []
            
            for line in f_in:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    parsed = self.parse_line(line)
                    if parsed:
                        data_values.append(parsed)
                except (ValueError, IndexError) as e:
                    # Log and skip malformed lines
                    continue
        
        return {
            "header": {"format": "vaisala_sudan"},
            "metadata": {},
            "values": data_values,
        }
    
    def parse_line(self, line):
        """
        Parse a single Vaisala message line.
        
        Format: "timestamp, (key:value;key:value;...)checksum"
        """
        # Split timestamp from message
        match = re.match(r'^([\d\-\s:\.]+),\s*\((.+)\)([A-F0-9]{8})$', line)
        if not match:
            raise ValueError(f"Invalid line format: {line[:50]}...")
        
        receipt_time_str, payload, checksum = match.groups()
        
        # Parse receipt timestamp
        receipt_time = datetime.strptime(
            receipt_time_str.strip(),
            "%Y-%m-%d %H:%M:%S.%f"
        )
        
        # Parse key:value pairs
        line_data = {
            "receipt_time": receipt_time,
            "checksum": checksum,
        }
        
        pairs = payload.split(';')
        for pair in pairs:
            if ':' not in pair:
                continue
            
            key, val = pair.split(':', 1)
            key = key.strip()
            val = val.strip()
            
            # Skip null values
            if val == self.NULL_VALUE or val == '':
                continue
            
            # Handle special fields
            if key == 'S':
                line_data['station_id'] = val
            elif key == 'D':
                # Date: YYMMDD
                line_data['obs_date'] = val
            elif key == 'T':
                # Time: HHMMSS
                line_data['obs_time'] = val
            elif key in self.STRING_PARAMS:
                line_data[key] = val
            else:
                # Try numeric conversion
                try:
                    line_data[key] = float(val)
                except ValueError:
                    line_data[key] = val
        
        # Build observation_time from D and T fields
        if 'obs_date' in line_data and 'obs_time' in line_data:
            try:
                obs_dt = datetime.strptime(
                    f"{line_data['obs_date']}{line_data['obs_time']}",
                    "%y%m%d%H%M%S"
                )
                line_data['observation_time'] = obs_dt
            except ValueError:
                pass
        
        return line_data
    
    def verify_checksum(self, payload, expected_checksum):
        """
        Verify the CRC32 checksum (optional validation).
        """
        import binascii
        calculated = format(binascii.crc32(payload.encode()) & 0xffffffff, '08X')
        return calculated == expected_checksum
