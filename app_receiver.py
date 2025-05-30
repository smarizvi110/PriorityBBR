# app_receiver.py
import time
import datetime
import config
from transport_receiver import TransportReceiver
from logger import CSVLogger # Add import

def handle_received_data(payload: bytes, priority: int, seq_num: int):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    prio_str = "HIGH" if priority == config.HIGH_PRIORITY else "LOW"
    try:
        decoded_payload = payload.decode('latin-1')
    except UnicodeDecodeError:
        decoded_payload = f"[Undecodable bytes: {len(payload)}]"

    print(f"[{timestamp}] [App Receiver] <<<< PRIO:{prio_str} (Seq:{seq_num}) -- Data: {decoded_payload}")

def main():
    main_logger = CSVLogger(filename_prefix="priority_sim_receiver") # For receiver
    receiver_transport = TransportReceiver(logger=main_logger, remote_ip=config.RECEIVER_IP, remote_port_ack=config.SENDER_PORT) # Pass logger
    receiver_transport.set_data_callback(handle_received_data)
    receiver_transport.start()

    print("Application Receiver running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1) # Keep main thread alive
    except KeyboardInterrupt:
        print("Application Receiver interrupted.")
    finally:
        print("Application Receiver stopping transport...")
        receiver_transport.stop()
        print("Application Receiver finished.")

if __name__ == "__main__":
    main()