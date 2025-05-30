# transport_sender.py - REVISED
import socket
import time
import threading
from collections import deque

import config
from segment import Segment, SEGMENT_TYPE_DATA, SEGMENT_TYPE_ACK

class TransportSender:
    def __init__(self, local_ip="0.0.0.0", local_port=config.SENDER_PORT,
                 remote_ip=config.RECEIVER_IP, remote_port=config.RECEIVER_PORT):
        self.remote_addr = (remote_ip, remote_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((local_ip, local_port))
        self.sock.settimeout(0.01) # Non-blocking for ACK reception

        self.send_buffer_high = deque()
        self.send_buffer_low = deque()
        
        self.next_seq_num = 0
        self.unacked_segments = {} # {seq_num: (segment, send_time, retries)}
        self.current_cwnd = config.INITIAL_CWND
        self.in_flight_count = 0 # Number of unacknowledged segments

        # Bandwidth simulation
        self.simulated_bandwidth_sps = config.SIMULATED_BANDWIDTH_SPS
        self.time_per_segment = 1.0 / self.simulated_bandwidth_sps if self.simulated_bandwidth_sps > 0 else float('inf')
        self.last_send_time = time.time()

        self.running = True
        self.ack_listener_thread = threading.Thread(target=self._listen_for_acks, daemon=True)
        self.sending_logic_thread = threading.Thread(target=self._sending_logic, daemon=True) # Renamed from _pace_sending

    def start(self):
        self.ack_listener_thread.start()
        self.sending_logic_thread.start()
        print(f"Sender transport started. Listening for ACKs on port {config.SENDER_PORT}")
        print(f"Sending to {self.remote_addr}. Simulated Bandwidth: {self.simulated_bandwidth_sps} seg/s. Initial CWND: {self.current_cwnd}")

    def stop(self):
        self.running = False
        if self.ack_listener_thread.is_alive():
            self.ack_listener_thread.join(timeout=1)
        if self.sending_logic_thread.is_alive():
            self.sending_logic_thread.join(timeout=1)
        self.sock.close()
        print("Sender transport stopped.")

    def send_data(self, app_data: bytes, priority: int):
        offset = 0
        segments_created_count = 0
        while offset < len(app_data):
            payload_chunk = app_data[offset:offset + config.MAX_SEGMENT_PAYLOAD_SIZE]
            segment = Segment(type=SEGMENT_TYPE_DATA,
                              priority=priority,
                              seq_num=self.next_seq_num,
                              payload=payload_chunk)
            
            if priority == config.HIGH_PRIORITY:
                self.send_buffer_high.append(segment)
            else:
                self.send_buffer_low.append(segment)
            
            self.next_seq_num += 1
            offset += config.MAX_SEGMENT_PAYLOAD_SIZE
            segments_created_count +=1
        # print(f"[Sender App->Transport] Queued {segments_created_count} segments (Prio:{priority}) for data size: {len(app_data)}")


    def _listen_for_acks(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                ack_segment = Segment.from_bytes(data)
                if ack_segment and ack_segment.type == SEGMENT_TYPE_ACK:
                    # print(f"[Transport Sender] RX ACK: {ack_segment.ack_num}")
                    if ack_segment.ack_num in self.unacked_segments:
                        del self.unacked_segments[ack_segment.ack_num]
                        self.in_flight_count = max(0, self.in_flight_count - 1)
                        
                        # Very basic CWND increase on ACK (like slow start)
                        if self.current_cwnd < config.MAX_CWND:
                            self.current_cwnd += 1 
                        # print(f"[Transport Sender] Segment {ack_segment.ack_num} ACKed. In-flight: {self.in_flight_count}, CWND: {self.current_cwnd}")
                    # else:
                        # print(f"[Transport Sender] RX duplicate/late ACK for {ack_segment.ack_num}")
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error in ACK listener: {e}")
                break

    def _handle_retransmissions(self):
        now = time.time()
        segments_to_retransmit = []
        for seq_num, (segment, send_time, retries) in list(self.unacked_segments.items()):
            if now - send_time > config.ACK_TIMEOUT:
                if retries < config.MAX_RETRIES:
                    print(f"[Transport Sender] Timeout for segment {seq_num}. Marking for Retransmit (Attempt {retries+1}).")
                    # Don't resend immediately, let the main sending logic pick it up with priority
                    # For simplicity, we'll re-queue it with high priority to ensure it's considered soon.
                    # A more complex system might have a separate retransmit queue or different logic.
                    retransmit_segment = Segment(type=segment.type, priority=config.HIGH_PRIORITY, # Force high priority for retransmits
                                                 seq_num=segment.seq_num, payload=segment.payload)
                    segments_to_retransmit.append(retransmit_segment)
                    self.unacked_segments[seq_num] = (segment, now, retries + 1) # Update send_time and retries
                else:
                    print(f"[Transport Sender] Max retries for segment {seq_num}. Giving up.")
                    del self.unacked_segments[seq_num]
                    self.in_flight_count = max(0, self.in_flight_count - 1)
                    # Basic CWND reduction on "loss"
                    self.current_cwnd = max(1, self.current_cwnd // 2)
                    print(f"[Transport Sender] Assumed loss for {seq_num}. CWND reduced to {self.current_cwnd}")
        
        # Add segments marked for retransmission to the front of the high priority queue
        for seg in reversed(segments_to_retransmit): # Add to front, so process oldest retransmit first
            self.send_buffer_high.appendleft(seg)


    def _sending_logic(self):
        while self.running:
            now = time.time()

            # Handle potential retransmissions by re-queueing them
            self._handle_retransmissions()

            # Pacing: Can we send based on bandwidth?
            if now - self.last_send_time < self.time_per_segment:
                time.sleep(max(0, self.time_per_segment - (now - self.last_send_time))) # Sleep until next send slot
                # time.sleep(config.SENDER_LOOP_INTERVAL / 10) # Avoid busy waiting if pacing allows send sooner than loop interval
                continue # Re-evaluate after sleep

            # CWND check: Can we send based on in-flight data?
            if self.in_flight_count >= self.current_cwnd:
                # print(f"[Transport Sender] CWND limit reached ({self.in_flight_count}/{self.current_cwnd}). Waiting for ACKs.")
                time.sleep(config.SENDER_LOOP_INTERVAL) # Wait for ACKs
                continue

            segment_to_send = None
            source_queue_name = ""

            # Prioritize sending
            if self.send_buffer_high:
                segment_to_send = self.send_buffer_high.popleft()
                source_queue_name = "HIGH_PRIO_BUF"
            elif self.send_buffer_low:
                segment_to_send = self.send_buffer_low.popleft()
                source_queue_name = "LOW_PRIO_BUF"

            if segment_to_send:
                try:
                    # If it's a new segment (not a retransmit already in unacked_segments with updated retry count)
                    # or if it's a retransmit being picked from queue
                    is_retransmit_from_queue = False
                    if segment_to_send.seq_num in self.unacked_segments:
                        # This means it was re-queued by _handle_retransmissions
                        # We use its existing retry count
                        _, _, retries = self.unacked_segments[segment_to_send.seq_num]
                        if retries > 0: # If retries > 0, it's a retransmit from queue
                             is_retransmit_from_queue = True
                             # print(f"[Transport Sender->Network] Resending from Q: {segment_to_send} (from {source_queue_name}, Attempt {retries})")


                    self.sock.sendto(segment_to_send.to_bytes(), self.remote_addr)
                    self.last_send_time = time.time() # Update last send time for pacing
                    
                    if not is_retransmit_from_queue: # Don't double print for retransmits from queue
                        print(f"[Transport Sender->Network] Sent: {segment_to_send} (from {source_queue_name})")
                    
                    # Add/Update in unacked_segments only if it's not already there with a higher retry count (from immediate resend logic)
                    # Or if it's a genuinely new send
                    if segment_to_send.seq_num not in self.unacked_segments or not is_retransmit_from_queue :
                        self.unacked_segments[segment_to_send.seq_num] = (segment_to_send, self.last_send_time, 0 if not is_retransmit_from_queue else retries) # Store original segment for potential later retransmit
                        self.in_flight_count += 1
                    
                    # print(f"[Transport Sender] In-flight: {self.in_flight_count}, CWND: {self.current_cwnd}")

                except Exception as e:
                    print(f"Error sending segment: {e}")
                    # Re-add to front of its queue if send fails? For simplicity, we don't here.
            else:
                # No data to send, sleep for a bit
                time.sleep(config.SENDER_LOOP_INTERVAL)