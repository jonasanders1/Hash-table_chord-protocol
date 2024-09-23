import time
import requests
import random
import string
import sys
import matplotlib.pyplot as plt


def perform_put_requests(node_address, num_operations):
    keys = []
    # Start timer
    start_time = time.time()
    
    # Loop over the number of operations
    for i in range(num_operations):
        key = f'key-{i}'
        value = f'value-{i}'
        # PUT request
        response = requests.put(f"http://{node_address}/storage/{key}", data=value)
        if response.status_code != 200:
            print(f"Failed PUT request for key: {key}")
        keys.append(key)
    
    # Calculate time
    elapsed_time = time.time() - start_time
    
    return elapsed_time, keys

def perform_get_requests(node_address, keys):
    # Start timer
    start_time = time.time()
    # Loop over all the keys from 'perform_put_requests'
    for key in keys:
        # GET request
        response = requests.get(f"http://{node_address}/storage/{key}")
        if response.status_code != 200:
            print(f"Failed GET request for key: {key}")
    # Calculate time
    elapsed_time = time.time() - start_time
    return elapsed_time

def run_experiment(node_addresses, num_operations):
    # initialize PUT and GET times
    total_put_time = 0
    total_get_time = 0

    # Loop over all the nodes
    for node_address in node_addresses:
        print(f"Measuring PUT time for node {node_address}...")
        # Perform PUT requests
        put_time, keys = perform_put_requests(node_address, num_operations)
        # add time to the total time
        total_put_time += put_time

        print(f"Measuring GET time for node {node_address}...")
        # perform GET requests
        get_time = perform_get_requests(node_address, keys)
        # add time to the total time
        total_get_time += get_time

    # Calculate the average times
    avg_put_time = total_put_time / len(node_addresses)
    avg_get_time = total_get_time / len(node_addresses)

    print(f"Average PUT Time: {avg_put_time} seconds")
    print(f"Average GET Time: {avg_get_time} seconds")

    return avg_put_time, avg_get_time

def plot_results(node_counts, put_times, get_times):
    """Plots the elapsed time for PUT and GET operations vs. the number of nodes."""
  

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python experiment.py <node1> <node2> ...")
        sys.exit(1)

    node_addresses = sys.argv[1:-1]
    num_operations = 100

    print(f"Running experiment with nodes: {node_addresses} and {num_operations} operations.")

    # Run the experiment x number of nodes (1, 2, 4, 8 or 16)
    node_counts = [1, 2, 4, 8, 16]
    
    # initializing PUT and GET times
    put_times = []
    get_times = []

    for node_count in node_counts:
        print(f"Testing with {node_count} node(s)...")
        selected_nodes = node_addresses[:node_count]  # Select the number of nodes
        put_time, get_time = run_experiment(selected_nodes, num_operations)
        put_times.append(put_time)
        get_times.append(get_time)

    # Plotting the results with Matplotlib 
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
