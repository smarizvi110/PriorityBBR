# Python Proof-of-Concept for TCP-Level Semantic Content Prioritization

This repository contains a Python-based proof-of-concept (PoC) demonstrating the core scheduling mechanics of a proposed transport-level semantic content prioritization scheme, tentatively named "PriorityBBR." This PoC simulates a simplified transport layer that prioritizes data segments based on application-defined importance, especially under simulated network bottleneck conditions.

**This is NOT a full TCP or BBR implementation.** It is a simplified model built using UDP sockets to illustrate the fundamental principles of:

1. Application-assigned data priorities.
2. A transport layer with priority-aware send queues.
3. Prioritized segment transmission when available bandwidth is constrained.

This PoC was developed as an initial step in the research outlined in the accompanying [research proposal document](Investigating_Transport_Level_Semantic_Content_Prioritization_via_TCP_Modification.pdf) (see "Research Proposal" section below).

## Core Idea

The internet has become indispensable, and user expectations for website loading speed are ever-increasing. While various optimization techniques exist, they often fall short under constrained bandwidth or when immediate access to core content is important.

This project explores introducing content prioritization at the Transmission Control Protocol (TCP) level. The proposal involves:

1. Assigning priorities to individual elements within a web page (or data chunks in other applications).
2. Modifying a TCP-like transport protocol (envisioned as an extension to TCP BBR) to facilitate differentiated delivery based on these priorities.
3. Ensuring that the most critical parts of a data stream are delivered first, followed by less essential resources as bandwidth permits, especially under network constraints.

This PoC simulates the sender-side transport logic responsible for making these prioritized sending decisions.

## Features Illustrated by this PoC

* **Application-Defined Priorities:** The sender application can assign HIGH or LOW priority to data chunks.
* **Segmentation:** Application data is broken into smaller, fixed-size segments.
* **Priority Queues:** The simulated sender transport layer maintains separate queues for high and low-priority segments.
* **Simulated Bottleneck Bandwidth:** The sender paces its transmissions to mimic a configurable network bottleneck.
* **Simplified Congestion Window (CWND):** A basic mechanism limits the amount of unacknowledged ("in-flight") data.
* **Prioritized Sending Logic:** The sender always attempts to send segments from the high-priority queue before the low-priority queue, provided sending is allowed by the pacing and CWND.
* **Basic ACK Mechanism:** The receiver sends acknowledgments for received data segments.
* **Simple Retransmission on Timeout:** The sender retransmits segments if an ACK is not received within a timeout period, prioritizing retransmissions.
* **CSV Logging:** Detailed logs of sender and receiver events are generated for analysis (timestamps, sequence numbers, priorities, event types, etc.).
* **Simulated Packet Loss:** The receiver can be configured to randomly drop incoming data segments to test retransmission logic.

## File Structure

* `run_simulation.py`: Main launcher script to start both the receiver and sender applications and manage the simulation.
* `app_sender.py`: Example application that generates data with different priorities and sends it via the transport layer.
* `app_receiver.py`: Example application that receives data and logs its arrival.
* `transport_sender.py`: Implements the sender-side logic of the simplified transport layer (priority queues, pacing, CWND, ACK handling).
* `transport_receiver.py`: Implements the receiver-side logic (receiving segments, sending ACKs).
* `segment.py`: Defines the `Segment` class used for data and ACK packets.
* `config.py`: Contains shared configuration parameters (IPs, ports, segment sizes, priorities, simulation settings).
* `logger.py`: Implements the `CSVLogger` class for writing simulation events to CSV files.
* `Investigating_Transport_Level_Semantic_Content_Prioritization_via_TCP_Modification.pdf` (Optional): The research proposal document.

## Prerequisites

* Python 3.x

## How to Run

1. Clone this repository:

    ```zsh
    git clone https://github.com/smarizvi110/PriorityBBR.git
    cd PriorityBBR
    ```

2. Ensure all Python files (`.py`) are in the same directory.
3. Execute the main launcher script from your terminal:

    ```zsh
    python run_simulation.py
    ```

    This script will:
    * Start the `app_receiver.py`.
    * Wait for the receiver to signal it's ready (by creating a `.receiver_ready` file).
    * Start the `app_sender.py`.
    * The simulation will run, printing console output and generating CSV log files (e.g., `priority_bbr_sim_sender_app_sender_YYYYMMDD_HHMMSS.csv` and `priority_bbr_sim_receiver_app_receiver_YYYYMMDD_HHMMSS.csv`) in the current directory.
    * The launcher will terminate automatically after the sender application finishes. You can also stop it earlier with `Ctrl+C`.

## Configuration

Key simulation parameters can be adjusted in `config.py`:

* `MAX_SEGMENT_PAYLOAD_SIZE`: Size of data in each segment.
* `HIGH_PRIORITY`, `LOW_PRIORITY`: Integer values for priorities.
* `INITIAL_CWND`, `MAX_CWND`: Congestion window parameters.
* `SIMULATED_BANDWIDTH_SPS`: Segments Per Second for the bottleneck.
* `SENDER_LOOP_INTERVAL`: Granularity of the sender's main loop.
* `ACK_TIMEOUT`, `MAX_RETRIES`: For retransmission logic.

The `app_sender.py` script can also be modified to change the data generation patterns (amount of high vs. low priority data, timing, etc.).

## Expected Output & Analysis

* **Console Output:** Both sender and receiver applications print status messages to the console, showing data being queued, sent, and received, along with priorities.
* **CSV Log Files:** These are the primary source for detailed analysis.
  * **Sender Log (`..._sender_app_sender_...csv`):** Contains events like `APP_QUEUE` (data given by app to transport), `SENT_NEW`, `SENT_RETRANSMIT`, `ACK_RX`, `MARK_RETRANSMIT`, `DROP_MAX_RETRY`. Includes timestamps, sequence numbers, priorities, CWND, in-flight counts.
  * **Receiver Log (`..._receiver_app_receiver_...csv`):** Contains events like `DATA_RX`, `ACK_TX`, `SIMULATED_DROP`. Includes timestamps, sequence numbers, priorities.
  * These logs can be imported into spreadsheet software or analyzed with Python (e.g., using Pandas and Matplotlib) to:
    * Visualize the order of segment transmission and reception.
    * Compare the end-to-end latency for high vs. low-priority segments.
    * Observe the effect of the simulated bottleneck and CWND.
    * Verify that high-priority data "jumps the queue" under contention.

## Limitations of this PoC

* **Not Real TCP/BBR:** This PoC uses UDP sockets and simulates transport layer behaviors. It does not implement the full TCP state machine, detailed BBR algorithms (like bandwidth probing, RTTmin tracking, DRAIN phase, etc.), or robust TCP options.
* **Simplified Congestion Control:** The CWND mechanism is very basic (additive increase on ACK, multiplicative decrease on loss).
* **Idealized Network:** Assumes a simple point-to-point link; no complex network topologies, cross-traffic, or router queue effects are modeled beyond the sender-side bottleneck simulation.
* **Basic Reliability:** ACK and retransmission logic is functional for demonstration but not as robust as production TCP.

## Next Steps (Research Direction)

The primary next step for this research, as outlined in the proposal, is to move towards a more rigorous simulation environment:

1. **Implementation in ns-3:** Implement the PriorityBBR concept by modifying the TCP BBR module within the ns-3 network simulator.
2. **Simulation on Standard Topologies:** Conduct experiments on dumbbell and parking lot topologies.
3. **Rigorous Fairness Analysis:** Evaluate inter-flow and intra-flow fairness against legacy TCP implementations.
4. **Performance Evaluation:** Compare against baseline BBR and potentially QUIC/HTTP/3 prioritization under various network conditions.

This Python PoC serves as a foundational step to understand and demonstrate the core scheduling logic before undertaking more complex ns-3 development.

## Research Proposal

The detailed research proposal outlining the motivation, technical design, challenges, and methodology for "PriorityBBR" can be found here:

* [**Investigating_Transport_Level_Semantic_Content_Prioritization_via_TCP_Modification.pdf**](Investigating_Transport_Level_Semantic_Content_Prioritization_via_TCP_Modification.pdf)

## Author

Syed Muhammad Aqdas Rizvi

* Email: <25100166@lums.edu.pk>
* GitHub: [https://github.com/smarizvi110](https://github.com/smarizvi110)

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3). For more details, see the [LICENSE.md](LICENSE.md) file.
