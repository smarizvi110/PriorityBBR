# transport_receiver.py
import socket
import threading

import config
from segment import Segment, SEGMENT_TYPE_DATA, SEGMENT_TYPE_ACK

class TransportReceiver:
    def __init__(self, local_ip="0.0.0.0", local_port=config.RECEIVER_PORT,
                 remote_ip=config.RECEIVER_IP, remote_port_ack=config.SENDER_PORT, logger=None): # remote_ip isn't strictly needed if just listening
        self.logger = logger # Add logger parameter
        self.logger.initialize_receiver_log() # Initialize receiver log
        self.listen_addr = (local_ip, local_port)
        self.ack_dest_addr = (remote_ip, remote_port_ack) # To send ACKs back to sender's listening port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.listen_addr)
        
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_data, daemon=True)
        
        self.on_data_received_callback = None # Application callback
        self.received_seq_nums = set() # To handle duplicate DATA segments

    def set_data_callback(self, callback):
        self.on_data_received_callback = callback

    def start(self):
        self.receive_thread.start()
        print(f"Receiver transport started. Listening on {self.listen_addr}")

    def stop(self):
        self.running = False
        # Send a dummy packet to unblock recvfrom if it's waiting
        try:
            dummy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dummy_sock.sendto(b'shutdown', self.listen_addr)
            dummy_sock.close()
        except Exception:
            pass # Ignore errors during shutdown signaling
            
        if self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)
        self.sock.close()
        print("Receiver transport stopped.")

    def _send_ack(self, seq_num_to_ack):
        ack_segment = Segment(type=SEGMENT_TYPE_ACK, priority=None, seq_num=None, ack_num=seq_num_to_ack)
        try:
            self.sock.sendto(ack_segment.to_bytes(), self.ack_dest_addr)
            # print(f"[Transport Receiver] Sent ACK for {seq_num_to_ack} to {self.ack_dest_addr}")
            if self.logger:
                self.logger.log_receiver_event( # Logging ACK sent
                    "ACK_TX", seq_num_to_ack, None, 0, 
                    sender_addr_str=str(self.ack_dest_addr)
                )
        except Exception as e:
            print(f"Error sending ACK: {e}")

    def _receive_data(self):
        while self.running:
            try:
                data, sender_addr = self.sock.recvfrom(2048) # Buffer size for segment
                if not self.running: break

                segment = Segment.from_bytes(data)

                if segment and segment.type == SEGMENT_TYPE_DATA:
                    # print(f"[Network->Transport Receiver] Received: {segment} from {sender_addr}")
                    
                    # Send ACK
                    self._send_ack(segment.seq_num)

                    if segment.seq_num not in self.received_seq_nums:
                        if self.logger:
                            self.logger.log_receiver_event(
                                "DATA_RX", segment.seq_num, segment.priority, len(segment.payload),
                                sender_addr_str=str(sender_addr),
                                info=""
                            )
                        self.received_seq_nums.add(segment.seq_num)
                        if self.on_data_received_callback:
                            # Pass priority along with payload to the app
                            self.on_data_received_callback(segment.payload, segment.priority, segment.seq_num)
                    else:
                        # print(f"[Transport Receiver] Duplicate DATA segment {segment.seq_num} received. ACKed again.")
                        if self.logger:
                            self.logger.log_receiver_event(
                                "DATA_RX", segment.seq_num, segment.priority, len(segment.payload),
                                sender_addr_str=str(sender_addr),
                                info="Duplicate"
                        )
                
            except socket.timeout: # This won't happen with default blocking sockets
                continue
            except OSError as e: # Catch errors like "Bad file descriptor" during shutdown
                 if self.running:
                    print(f"Socket error in receiver: {e}")
                 break
            except Exception as e:
                if self.running:
                    print(f"Error in receiver: {e}")
                break