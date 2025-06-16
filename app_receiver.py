# app_receiver.py
import time
import datetime
import config
from transport_receiver import TransportReceiver
from logger import CSVLogger # Add import

READY_FILE_NAME = ".receiver_ready" 

def handle_received_data(payload: bytes, priority: int, seq_num: int):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    prio_str = "HIGH" if priority == config.HIGH_PRIORITY else "LOW"
    try:
        decoded_payload = payload.decode('latin-1')
    except UnicodeDecodeError:
        decoded_payload = f"[Undecodable bytes: {len(payload)}]"

    print(f"[{timestamp}] [App Receiver] <<<< PRIO:{prio_str} (Seq:{seq_num}) -- Data: {decoded_payload}")

def main():
    # log_prefix = "priority_bbr_sim_receiver_app" # Example
    # main_logger = CSVLogger(filename_prefix=log_prefix)
    # Your logger initialization based on your corrected code
    # Ensure this doesn't conflict if launcher script tries to manage filenames too

    # For logger to be instantiated here as per your fixed structure:
    main_logger = CSVLogger(filename_prefix="priority_bbr_sim_receiver_app")

    receiver_transport = TransportReceiver(
        logger=main_logger, 
        remote_ip=config.RECEIVER_IP, # Assuming these are defined in config.py
        remote_port_ack=config.SENDER_PORT # Assuming these are defined in config.py
    )
    receiver_transport.set_data_callback(handle_received_data)
    
    try:
        receiver_transport.start() # This prints "Receiver transport started..."
        
        # --- Create the ready file ---
        with open(READY_FILE_NAME, 'w') as f:
            f.write("ready")
        print(f"Receiver signaled ready by creating {READY_FILE_NAME}")
        # ---

        print("Application Receiver running. Press Ctrl+C to stop.")
        while True:
            # Check if transport thread is still alive; exit if not (graceful shutdown)
            if not receiver_transport.receive_thread.is_alive():
                print("Receiver transport thread has stopped. Exiting app.")
                break
            time.sleep(1) 
    except KeyboardInterrupt:
        print("Application Receiver interrupted by Ctrl+C.")
    except Exception as e:
        print(f"An error occurred in receiver app: {e}")
    finally:
        print("Application Receiver stopping transport...")
        receiver_transport.stop()
        
        # --- Clean up the ready file ---
        import os # Add this import if not already present
        if os.path.exists(READY_FILE_NAME):
            try:
                os.remove(READY_FILE_NAME)
            except OSError:
                pass # Ignore error if file is already gone
        # ---
        print("Application Receiver finished.")

if __name__ == "__main__":
    main()