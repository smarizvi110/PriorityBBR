# logger.py
import csv
import datetime
import threading

class CSVLogger:
    def __init__(self, filename_prefix="run_log"):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.sender_log_file = f"{filename_prefix}_sender_{self.timestamp}.csv"
        self.receiver_log_file = f"{filename_prefix}_receiver_{self.timestamp}.csv"
        self._lock = threading.Lock() # For thread-safe writing


    def initialize_sender_log(self):
        with self._lock:
            with open(self.sender_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "EventType", "SeqNum", "Priority", 
                    "PayloadSize", "QueueSource", "CWND", "InFlight",
                    "RetryAttempt", "Info"
                ])

    def initialize_receiver_log(self):
        with self._lock:
            with open(self.receiver_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "EventType", "SeqNum", "Priority", 
                    "PayloadSize", "SenderAddr", "Info"
                ])

    def log_sender_event(self, event_type, seq_num, priority, payload_size, 
                         queue_source="", cwnd=0, in_flight=0, retry_attempt=0, info=""):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with self._lock:
            try:
                with open(self.sender_log_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp, event_type, seq_num, priority, payload_size,
                        queue_source, cwnd, in_flight, retry_attempt, info
                    ])
            except Exception as e:
                print(f"Error writing to sender log: {e}")


    def log_receiver_event(self, event_type, seq_num, priority, payload_size, 
                           sender_addr_str="", info=""):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with self._lock:
            try:
                with open(self.receiver_log_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp, event_type, seq_num, priority, payload_size,
                        sender_addr_str, info
                    ])
            except Exception as e:
                print(f"Error writing to receiver log: {e}")

# Global logger instance (can be imported by other modules)
# main_logger = CSVLogger() # Initialize when needed, e.g., in main app scripts