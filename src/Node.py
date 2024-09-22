import requests
import sys
from flask import Flask, request, jsonify, Response
import hashlib
import socket

app = Flask(__name__)

def hash_function(value):
    """Hashes the given value using SHA-1 and returns an integer."""
    print(f"Hashing value: {value}", flush=True)
    return int(hashlib.sha1(value.encode()).hexdigest(), 16)

class Node:
    def __init__(self, address):
        self.node_id = hash_function(address)
        self.address = address
        self.successor = None
        self.predecessor = None
        self.data_store = {}
        self.finger_table = []
        self.known_nodes = []
        self.node_hashes = {}  # Cache for node hashes

        # Log the current node's initialization
        print(f"Initializing node with address {self.address} and ID hash {self.node_id}", flush=True)
    
    def update_successor_predecessor(self, node_list):
        """Update successor and predecessor based on the sorted node list."""
        self.known_nodes = node_list

        # Cache node hashes to avoid redundant hashing
        for node in self.known_nodes:
            if node not in self.node_hashes:
                self.node_hashes[node] = hash_function(node)

        # Ensure the current node's address is part of the known nodes
        if self.address not in self.known_nodes:
            print(f"Adding current node {self.address} to the known nodes list.", flush=True)
            self.known_nodes.append(self.address)
            self.node_hashes[self.address] = self.node_id  # Cache the current node's hash

        # Log the known nodes
        print(f"Known nodes: {self.known_nodes}", flush=True)

        # Sort all nodes based on their hash values
        sorted_node_hashes = sorted(self.node_hashes.values())

        # Log the sorted node hashes
        print(f"Sorted node hashes: {sorted_node_hashes}", flush=True)

        # Find the hash of the current node
        self_hash = self.node_id
        print(f"Current node hash: {self_hash}", flush=True)

        # Single node case: point successor and predecessor to itself
        if len(self.known_nodes) == 1:
            self.successor = self.address
            self.predecessor = self.address
            print(f"Single-node case: Successor and Predecessor set to {self.address}", flush=True)
            return

        # Find the position of the current node in the sorted list
        index = sorted_node_hashes.index(self_hash)

        # Assign successor and predecessor
        successor_index = (index + 1) % len(sorted_node_hashes)
        predecessor_index = (index - 1) % len(sorted_node_hashes)

        self.successor = self.get_address_by_hash(sorted_node_hashes[successor_index])
        self.predecessor = self.get_address_by_hash(sorted_node_hashes[predecessor_index])

        # Cache predecessor and successor hashes if missing
        if self.successor not in self.node_hashes:
            self.node_hashes[self.successor] = hash_function(self.successor)

        if self.predecessor not in self.node_hashes:
            self.node_hashes[self.predecessor] = hash_function(self.predecessor)

        print(f"Updated node {self.address}: Successor: {self.successor}, Predecessor: {self.predecessor}", flush=True)

        # Update the finger table after setting successor and predecessor
        self.update_finger_table()





    def get_address_by_hash(self, node_hash):
        """Helper function to get the address corresponding to a node hash."""
        for node, hashed_value in self.node_hashes.items():
            if hashed_value == node_hash:
                return node
        return None

    def update_finger_table(self):
        """Updates the finger table for the current node."""
        m = 160
        self.finger_table = []
        for i in range(m):
            start = (self.node_id + 2**i) % (2**m)
            successor = self.find_successor(start)
            if successor and successor not in self.finger_table:
                self.finger_table.append(successor)
        print(f"Finger table for node {self.address} updated: {self.finger_table}", flush=True)

    def find_successor(self, key_hash):
        """Find the successor of the given key hash."""
        # Ensure predecessor hash exists
        if self.predecessor and self.predecessor not in self.node_hashes:
            self.node_hashes[self.predecessor] = hash_function(self.predecessor)

        if self.predecessor is None or (self.node_hashes[self.predecessor] < key_hash <= self.node_id):
            return self.address
        else:
            for node in sorted(self.known_nodes, key=lambda n: self.node_hashes[n]):
                node_hash = self.node_hashes[node]
                if self.node_id < node_hash >= key_hash:
                    return node
            return self.successor if self.successor != self.address else None

    def put(self, key, value):
        key_hash = hash_function(key)
        print(f"Storing key: {key}, hash: {key_hash} at node {self.address}", flush=True)

        # Determine if the current node is responsible for storing the key
        # A node is responsible if its predecessor's hash is less than key_hash
        # and the key_hash is less than or equal to the current node's hash
        if (self.predecessor is None or 
            (hash_function(self.predecessor) < key_hash <= self.node_id) or 
            (self.node_id < hash_function(self.predecessor) and (key_hash > hash_function(self.predecessor) or key_hash <= self.node_id))):
            self.data_store[key_hash] = value
            print(f"Data stored locally at {self.address} for key_hash: {key_hash}", flush=True)
            return "Stored locally"

        # Single node case
        if self.successor == self.address:
            print(f"Stopping recursion at {self.address}. No further forwarding needed.", flush=True)
            self.data_store[key_hash] = value
            return "Error: Successor is the same as this node, stopping recursion."

        try:
            # Forward the PUT request to the successor
            print(f"Forwarding PUT request to {self.successor} for key {key}", flush=True)
            response = requests.put(f"http://{self.successor}/storage/{key}", data=value)
            print(f"Response from successor {self.successor}: {response.text}", flush=True)
            return response.text
        except Exception as e:
            print(f"Error forwarding to {self.successor}: {e}", flush=True)
            return str(e)



    def get(self, key):
        """Retrieve the value for a given key from the DHT."""
        key_hash = hash_function(key)
        print(f"Retrieving key: {key}, hash: {key_hash} from node {self.address}", flush=True)
        if key_hash in self.data_store:
            print(f"Found key {key} in node {self.address}", flush=True)
            return self.data_store[key_hash]
        
        # Single node case: return None if not found locally
        if self.successor == self.address:
            print(f"Stopping forwarding to {self.successor} in single-node case.", flush=True)
            return None
        
        
        try:
            print(f"Forwarding GET request to {self.successor} for key {key}", flush=True)
            response = requests.get(f"http://{self.successor}/storage/{key}", timeout=5)
            response.raise_for_status()
            return response.text  # Use response.text for plain text response
        except requests.exceptions.Timeout:
            print(f"Request to {self.successor} timed out.", flush=True)
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request to {self.successor}: {e}", flush=True)
            return None
    


# Flask Routes
@app.route('/network', methods=['POST'])
def network_update():
    node_list = request.json['nodes']

    # Ensure the current node's address is in the list
    if node1.address not in node_list:
        print(f"Adding current node {node1.address} to node_list.", flush=True)
        node_list.append(node1.address)
    
    # Log the node list and their hashes for debugging
    print(f"Received node list: {node_list}", flush=True)
    hashed_nodes = [hash_function(node) for node in node_list]
    print(f"Hashes of the received nodes: {hashed_nodes}", flush=True)

    # Call update successor and predecessor
    node1.update_successor_predecessor(node_list)
    
    return jsonify({'message': 'Updated network'}), 200


@app.route('/storage/<key>', methods=['PUT'])
def put_value(key):
    value = request.data.decode('utf-8')
    response = node1.put(key, value)
    return Response(response, content_type='text/plain'), 200  # Return plain text response

@app.route('/storage/<key>', methods=['GET'])
def get_value(key):
    value = node1.get(key)
    if value is not None:
        return Response(value, content_type='text/plain'), 200  # Return plain text response
    else:
        return Response("Key not found", content_type='text/plain'), 404

@app.route('/successor', methods=['GET'])
def get_successor():
    return jsonify({'successor': node1.successor}), 200

@app.route('/predecessor', methods=['GET'])
def get_predecessor():
    return jsonify({'predecessor': node1.predecessor}), 200

@app.route('/fingertable', methods=['GET'])
def get_finger_table():
    return jsonify({'fingertable': node1.finger_table}), 200

@app.route('/helloworld', methods=['GET'])
def helloworld():
    return node1.address, 200

if __name__ == '__main__':
    port = int(sys.argv[1])
    hostname = socket.gethostname().split('.')[0]
    node_address = f"{hostname}:{port}"
    node1 = Node(address=node_address)  # Use node_address for consistent hashing
    print(f"Initializing node with address: {node_address}", flush=True)
    app.run(host="0.0.0.0", port=port)
