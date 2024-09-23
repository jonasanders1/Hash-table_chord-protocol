import time
import requests
import random
import string
import sys
import matplotlib.pyplot as plt

def generate_random_string(length=8):
    """Generates a random string of given length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def perform_put_requests(node_address, num_operations):
    """Performs a series of PUT requests to the Chord node."""
    keys = []
    start_time = time.time()
    for _ in range(num_operations):
        key = generate_random_string()
        value = generate_random_string(16)
        response = requests.put(f"http://{node_address}/storage/{key}", data=value)
        if response.status_code != 200:
            print(f"Failed PUT request for key: {key}")
        keys.append(key)
    elapsed_time = time.time() - start_time
    return elapsed_time, keys

def perform_get_requests(node_address, keys):
    """Performs a series of GET requests to the Chord node."""
    start_time = time.time()
    for key in keys:
        response = requests.get(f"http://{node_address}/storage/{key}")
        if response.status_code != 200:
            print(f"Failed GET request for key: {key}")
    elapsed_time = time.time() - start_time
    return elapsed_time

def run_experiment(node_addresses, num_operations):
    """Runs the experiment for the given nodes and operations, and measures time."""
    total_put_time = 0
    total_get_time = 0

    for node_address in node_addresses:
        print(f"Measuring PUT time for node {node_address}...")
        put_time, keys = perform_put_requests(node_address, num_operations)
        total_put_time += put_time

        print(f"Measuring GET time for node {node_address}...")
        get_time = perform_get_requests(node_address, keys)
        total_get_time += get_time

    avg_put_time = total_put_time / len(node_addresses)
    avg_get_time = total_get_time / len(node_addresses)

    print(f"Average PUT Time: {avg_put_time} seconds")
    print(f"Average GET Time: {avg_get_time} seconds")

    return avg_put_time, avg_get_time

def plot_results(node_counts, put_times, get_times):
    """Plots the elapsed time for PUT and GET operations vs. the number of nodes."""
    plt.plot(node_counts, put_times, 'r-o', label='PUT Time (s)')
    plt.plot(node_counts, get_times, 'b-o', label='GET Time (s)')
    plt.xlabel("Number of Nodes")
    plt.ylabel("Time (seconds)")
    plt.title("PUT/GET Time vs. Number of Nodes")
    plt.legend()
    plt.grid(True)
    plt.savefig("time_vs_nodes_plot.png")
    plt.show()
    print("Plot saved as time_vs_nodes_plot.png")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python experiment.py <node1> <node2> ...")
        sys.exit(1)

    # Parse node addresses and the number of operations
    node_addresses = sys.argv[1:-1]
    num_operations = 1000

    print(f"Running experiment with nodes: {node_addresses} and {num_operations} operations.")

    # Run the experiment for 1, 2, 4, 8, and 16 nodes
    node_counts = [1, 2, 4, 8, 16]
    put_times = []
    get_times = []

    for node_count in node_counts:
        print(f"Testing with {node_count} node(s)...")
        selected_nodes = node_addresses[:node_count]  # Select the number of nodes
        put_time, get_time = run_experiment(selected_nodes, num_operations)
        put_times.append(put_time)
        get_times.append(get_time)

    # Plot the results
    plot_results(node_counts, put_times, get_times)
