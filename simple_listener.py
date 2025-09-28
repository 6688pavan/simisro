#!/usr/bin/env python3
"""
Simple Command-Line Telemetry Listener
A lightweight version for quick testing and monitoring.
"""

import socket
import struct
import time
import sys

class SimpleTelemetryListener:
    """Simple command-line telemetry listener"""
    
    def __init__(self, group="239.0.0.1", port=12345):
        self.group = group
        self.port = port
        self.sock = None
        self.running = False
        
    def start_listening(self):
        """Start listening for multicast packets"""
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to multicast group
            self.sock.bind(('', self.port))
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(self.group), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            print(f"Listening on {self.group}:{self.port}")
            print("Press Ctrl+C to stop...")
            print("-" * 60)
            
            self.running = True
            packet_count = 0
            record_count = 0
            packets_buffer = []
            
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1400)
                    packet_count += 1
                    packets_buffer.append(data)
                    
                    # When we have 10 packets, parse as a complete record
                    if len(packets_buffer) >= 10:
                        self.parse_and_display_record(packets_buffer[:10], record_count)
                        record_count += 1
                        
                        # Keep only the last 9 packets for next record
                        packets_buffer = packets_buffer[-9:]
                    
                    # Print packet info every 10 packets
                    if packet_count % 10 == 0:
                        print(f"Received {packet_count} packets, {record_count} records")
                        
                except KeyboardInterrupt:
                    print("\nStopping listener...")
                    self.running = False
                except Exception as e:
                    print(f"Error receiving packet: {e}")
                    
        except Exception as e:
            print(f"Failed to start listening: {e}")
        finally:
            if self.sock:
                self.sock.close()
    
    def parse_and_display_record(self, packets, record_num):
        """Parse and display a complete record"""
        if len(packets) != 10:
            return
            
        print(f"\n--- Record {record_num + 1} ---")
        
        # Extract time from first packet
        time_field_offset = 24
        if len(packets[0]) > time_field_offset + 4:
            time_bytes = packets[0][time_field_offset:time_field_offset+4]
            record_time = struct.unpack('<f', time_bytes)[0]
            print(f"Record Time: {record_time:.3f}s")
        
        # Parse each packet for float values
        for packet_id, packet in enumerate(packets):
            print(f"Packet {packet_id}:")
            
            # Extract float values every 4 bytes
            for offset in range(0, min(len(packet), 100), 4):  # Show first 100 bytes
                if offset + 4 <= len(packet):
                    try:
                        value_bytes = packet[offset:offset+4]
                        float_value = struct.unpack('<f', value_bytes)[0]
                        
                        # Only show non-zero values to reduce noise
                        if abs(float_value) > 0.001:
                            print(f"  Offset {offset:3d}: {float_value:12.6f}")
                    except:
                        pass
        
        print("-" * 40)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        group = sys.argv[1]
    else:
        group = "239.0.0.1"
        
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = 12345
    
    listener = SimpleTelemetryListener(group, port)
    listener.start_listening()

if __name__ == "__main__":
    main()
