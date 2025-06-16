# config.py
RECEIVER_IP = "127.0.0.1"
RECEIVER_PORT = 12345
SENDER_PORT = 12346 # For ACKs

MAX_SEGMENT_PAYLOAD_SIZE = 100  # Bytes
HIGH_PRIORITY = 0
LOW_PRIORITY = 1

# --- Advanced Settings ---
INITIAL_CWND = 4  # Initial "congestion window" in terms of segments
MAX_CWND = 20     # Max "congestion window"

# Simulated Bottleneck Bandwidth (segments per second)
# Start with a relatively low bandwidth to make prioritization obvious
SIMULATED_BANDWIDTH_SPS = 10 # Segments Per Second

# How often the sender's pacing/sending loop runs (seconds)
# This should be smaller to allow finer-grained pacing
SENDER_LOOP_INTERVAL = 0.05

ACK_TIMEOUT = 0.5 # Seconds
MAX_RETRIES = 2

LOG_PREFIX = "priority_bbr_sim"