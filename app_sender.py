# app_sender.py
import time
import config
from transport_sender import TransportSender

def main():
    sender_transport = TransportSender()
    sender_transport.start()

    print("Application Sender starting...")
    try:
        msg_counter = 0
        total_loops = 20 # Send more data to see cwnd effects

        for i in range(total_loops):
            # Send a burst of low-priority data
            num_low_prio_burst = 5 # Send more low priority chunks
            for j in range(num_low_prio_burst):
                low_prio_msg = f"LOW_PRIO_DATA_CHUNK_{msg_counter}".encode('latin-1')
                # print(f"[App Sender] Queuing low prio: {low_prio_msg.decode('latin-1')[:20]}...")
                sender_transport.send_data(low_prio_msg * 2, config.LOW_PRIORITY) # Send slightly larger low prio msgs
                msg_counter += 1
                if j < num_low_prio_burst -1 : time.sleep(0.01) # Tiny gap between app queuing

            # Send one high-priority message
            high_prio_msg = f"HIGH_PRIO_IMPORTANT_MESSAGE_{i}".encode('latin-1')
            print(f"[App Sender] Queuing HIGH prio: {high_prio_msg.decode('latin-1')}")
            sender_transport.send_data(high_prio_msg, config.HIGH_PRIORITY)
            
            # App-level delay: Modulate this to see if sender transport can keep up or if buffers grow
            # A shorter sleep here will push more data to the transport layer quickly.
            time.sleep(0.2) # Example: wait a bit less than total time to send the burst at current bandwidth

        print("Application Sender: All initial data queued. Waiting for transport to complete...")
        # Wait longer to ensure all ACKs are processed and queues can drain
        time.sleep(config.SIMULATED_BANDWIDTH_SPS * 0.5) # Wait based on bandwidth
        # Keep alive a bit longer for final ACKs
        time.sleep(5)


    except KeyboardInterrupt:
        print("Application Sender interrupted.")
    finally:
        print("Application Sender stopping transport...")
        sender_transport.stop()
        print("Application Sender finished.")

if __name__ == "__main__":
    main()