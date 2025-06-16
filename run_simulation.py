# run_simulation.py - ENHANCED
import subprocess
import time
import os
import signal
import platform # For OS-specific termination

# --- Configuration ---
PYTHON_EXE = "python3" if platform.system() != "Windows" else "python" # More robust
RECEIVER_SCRIPT = "app_receiver.py"
SENDER_SCRIPT = "app_sender.py"
READY_FILE_NAME = ".receiver_ready" # File receiver creates to signal readiness
MAX_WAIT_FOR_RECEIVER = 30 # Seconds to wait for receiver to become ready

def cleanup_ready_file():
    if os.path.exists(READY_FILE_NAME):
        try:
            os.remove(READY_FILE_NAME)
            print(f"Cleaned up {READY_FILE_NAME}")
        except OSError as e:
            print(f"Error cleaning up ready file: {e}")

def main():
    print("Initializing simulation...")
    cleanup_ready_file() # Clean up from previous runs

    receiver_process = None
    sender_process = None

    # Determine the Popen arguments for hiding console window on Windows if desired
    # For now, we'll let console windows appear for easier debugging.
    # startupinfo = None
    # if platform.system() == "Windows":
    #     startupinfo = subprocess.STARTUPINFO()
    #     startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    #     startupinfo.wShowWindow = subprocess.SW_HIDE # To hide window

    try:
        # 1. Launch app_receiver.py
        print(f"Starting receiver ({RECEIVER_SCRIPT})...")
        receiver_process = subprocess.Popen([PYTHON_EXE, RECEIVER_SCRIPT],
                                            # startupinfo=startupinfo, # Uncomment for hiding window on Windows
                                            text=True, bufsize=1, universal_newlines=True) # Line buffered
        print(f"Receiver process started (PID: {receiver_process.pid}). Waiting for it to signal readiness via '{READY_FILE_NAME}'...")

        # 2. Wait for the receiver to create the ready file
        wait_start_time = time.time()
        receiver_ready = False
        while time.time() - wait_start_time < MAX_WAIT_FOR_RECEIVER:
            if os.path.exists(READY_FILE_NAME):
                receiver_ready = True
                print(f"Receiver signaled ready (found {READY_FILE_NAME}).")
                break
            # Optional: Check receiver stdout for specific ready message if ready file fails
            # if receiver_process.stdout: # Ensure stdout is captured
            #     try:
            #         line = receiver_process.stdout.readline() # This might block if not careful
            #         if line and "Receiver transport started" in line: # Or specific ready message
            #             print("Receiver confirmed ready via stdout.")
            #             receiver_ready = True
            #             break
            #     except Exception: # Handle potential blocking or errors
            #         pass
            time.sleep(0.5)

        if not receiver_ready:
            print(f"Receiver did not signal readiness within {MAX_WAIT_FOR_RECEIVER} seconds. Terminating.")
            if receiver_process.poll() is None:
                receiver_process.terminate()
                receiver_process.wait(timeout=5)
            return # Exit if receiver fails

        # 3. Launch app_sender.py
        print(f"Starting sender ({SENDER_SCRIPT})...")
        sender_process = subprocess.Popen([PYTHON_EXE, SENDER_SCRIPT],
                                          # startupinfo=startupinfo, # Uncomment for hiding window on Windows
                                          text=True, bufsize=1, universal_newlines=True)
        print(f"Sender process started (PID: {sender_process.pid}).")

        print("\n--- Simulation Running ---")
        print("Sender and Receiver logs will be generated in the current directory.")
        print("Launcher will terminate after sender completes. Press Ctrl+C in this terminal to stop earlier.")

        # 4. Wait for the sender process to complete
        if sender_process:
            sender_process.wait() # This blocks until the sender process finishes
            print("Sender process has finished.")
        
        # Optionally, wait for a short period to allow receiver to process final ACKs/data
        print("Waiting a moment for receiver to process final packets...")
        time.sleep(2)


    except KeyboardInterrupt:
        print("\nCtrl+C received. Terminating processes...")
    except Exception as e:
        print(f"An error occurred in the launcher: {e}")
    finally:
        print("Initiating cleanup...")
        if sender_process and sender_process.poll() is None:
            print("Terminating sender process...")
            if platform.system() == "Windows":
                sender_process.send_signal(signal.CTRL_C_EVENT) # Try graceful first on Windows
            else:
                sender_process.terminate()
            try:
                sender_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                sender_process.kill()
                sender_process.wait(timeout=5)
        
        if receiver_process and receiver_process.poll() is None:
            print("Terminating receiver process...")
            if platform.system() == "Windows":
                receiver_process.send_signal(signal.CTRL_C_EVENT)
            else:
                receiver_process.terminate()
            try:
                receiver_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                receiver_process.kill()
                receiver_process.wait(timeout=5)
        
        cleanup_ready_file()
        print("Simulation launcher finished.")

if __name__ == "__main__":
    main()