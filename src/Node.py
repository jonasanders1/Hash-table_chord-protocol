import requests
import sys
from flask import Flask, request, jsonify
import hashlib
import json
import socket

# Flask application
app = Flask(__name__)

# Helper function for consistent hashing
def hash_function(value):
    return int(hashlib.sha1(value.encode()).hexdigest(), 16)

class Node:
    def __init__(self, node_id, address):
        self.node_id = node_id
        self.address = address
        self.data_store = {}
        self.finger_table = []
        self.predecessor = None
        self.successor = None

    def get_address_for_node(self, node_hash):
        """Find the address of a node by its hash in the finger table."""
        for node in self.finger_table:
            if hash_function(node) == node_hash:
                return node
        return None

    def find_successor(self, key_hash):
        """Find the successor node for a given key hash."""
        if self.predecessor is None or (self.predecessor < key_hash <= self.node_id):
            return self.address
        for node in self.finger_table:
            node_hash = hash_function(node)
            if self.node_id < node_hash >= key_hash:
                return node
        return self.successor

    def put(self, key, value):
        """Store a key-value pair using consistent hashing and finger table."""
        key_hash = hash_function(key)
        responsible_node = self.find_successor(key_hash)

        if responsible_node == self.node_id:
            print(f"Storing locally: key_hash={key_hash}, value={value}")
            self.data_store[key_hash] = value
            return f"Stored key {key} at node {self.node_id}"
        else:
            responsible_node_address = self.get_address_for_node(responsible_node)
            if responsible_node_address:
                print(f"Forwarding PUT request to {responsible_node_address} for key_hash={key_hash}")
                try:
                    response = requests.put(f'http://{responsible_node_address}/storage/{key}', data=value, timeout=5)
                    response.raise_for_status()
                    return response.json().get('message')
                except requests.exceptions.RequestException as e:
                    print(f"Error during PUT request to {responsible_node_address}: {e}")
                    return "Error forwarding request"
            else:
                print(f"No valid responsible node address found for key_hash={key_hash}")
                return "Error: No responsible node found"

    def get(self, key):
        """Retrieve a key-value pair using consistent hashing."""
        key_hash = hash_function(key)
        responsible_node = self.find_successor(key_hash)
        
        if responsible_node == self.node_id:
            print(f"Retrieving locally: key_hash={key_hash}")
            return self.data_store.get(key_hash, None)
        else:
            responsible_node_address = self.get_address_for_node(responsible_node)
            if responsible_node_address:
                print(f"Forwarding GET request to {responsible_node_address} for key_hash={key_hash}")
                try:
                    response = requests.get(f"http://{responsible_node_address}/storage/{key}", timeout=5)
                    response.raise_for_status()
                    return response.json().get('value', None)
                except requests.exceptions.RequestException as e:
                    print(f"Error during GET request to {responsible_node_address}: {e}")
                    return None
            else:
                print(f"No valid responsible node address found for key_hash={key_hash}")
                return None

    def update_successor_predecessor(self):
        """Update successor and predecessor based on the finger table."""
        all_nodes = sorted([hash_function(node) for node in self.finger_table] + [self.node_id])
        index = all_nodes.index(self.node_id)
    
        # Update successor
        self.successor = all_nodes[(index + 1) % len(all_nodes)]
            
        # Update predecessor
        self.predecessor = all_nodes[(index - 1) % len(all_nodes)]
            
        print(f"Node {self.address}: Successor set to {self.successor}, Predecessor set to {self.predecessor}")

    def update_finger_table(self):
        """Populate or update the finger table."""
        m = 160  # Number of bits in SHA-1
        self.finger_table = []
        for i in range(m):
            start = (self.node_id + 2**i) % (2**m)
            successor = self.find_successor(start)
            self.finger_table.append(successor)
        print(f"Finger table for node {self.address} populated: {self.finger_table}")

    def find_closest_preceding_node(self, key_hash):
        """Find the closest preceding node in the finger table."""
        for node in reversed(self.finger_table):
            if self.node_id < hash_function(node) < key_hash:
                return node
        return self.successor  # If no closer node, return the successor

# Initialize the node with a unique node ID and address
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Node.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])  # Get the port number from the command-line argument
    hostname = socket.gethostname().split(".")[0]  # Get the short hostname
    print(f"DEBUG: The hostname is {hostname}", flush=True)
    node1 = Node(node_id=hash_function(f"node-{port}"), address=f"{hostname}:{port}")

    # API route for getting the network
    @app.route('/network', methods=['GET'])
    def get_network():
        return jsonify({'nodes': node1.finger_table}), 200

    # API route to receive a list of known nodes
    @app.route('/network', methods=['POST'])
    def add_known_nodes():
        nodes = request.get_json()
        print(f"Received known nodes: {nodes}")
        node1.finger_table = nodes  # Replace the finger table with the new nodes
        node1.update_successor_predecessor()
        node1.update_finger_table()
        return jsonify({'message': 'Finger table updated successfully'}), 200

    # API route for storing key-value pairs
    @app.route('/storage/<key>', methods=['PUT'])
    def put_value(key):
        value = request.data.decode('utf-8')
        response = node1.put(key, value)
        return jsonify({'message': response}), 200

    # API route for retrieving key-value pairs
    @app.route('/storage/<key>', methods=['GET'])
    def get_value(key):
        value = node1.get(key)
        if value is not None:
            return jsonify({'value': value}), 200
        else:
            return jsonify({'error': 'Key not found'}), 404

    # API route for helloworld test
    @app.route('/helloworld', methods=['GET'])
    def helloworld():
        return node1.address, 200

    # API route to get the successor of a node
    @app.route('/successor', methods=['GET'])
    def get_successor():
        return jsonify({'successor': node1.successor}), 200

    # API route to get the predecessor of a node
    @app.route('/predecessor', methods=['GET'])
    def get_predecessor():
        return jsonify({'predecessor': node1.predecessor}), 200

    @app.route('/fingertable', methods=['GET'])
    def get_finger_table():
        return jsonify({'fingertable': node1.finger_table}), 200

    # Run the Flask server on the specified port
    app.run(host="0.0.0.0", port=port, debug=True)
