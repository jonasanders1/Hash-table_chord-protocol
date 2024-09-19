import requests
import sys
from flask import Flask, request, jsonify
import hashlib
import json

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
        self.known_nodes = []
        self.predecessor = None # Predecessor node in the ring

    def add_node(self, node):
        """Add a node to the network."""
        self.known_nodes.append(node)
        # ? DEBUG: Output the nodes that were added
        print(f"Known nodes updated: {self.known_nodes}")

    def get_known_nodes(self):
        """Return the list of known nodes."""
        return self.known_nodes

    def add_known_nodes(self, nodes):
        """Add multiple nodes to the network."""
        self.known_nodes.extend(nodes)
    
    # Function to find the address based on the node hash
    def get_address_for_node(self, node_hash):
        for node in self.known_nodes:
            if hash_function(node) == node_hash:
                return node
        return None
        
        
    def get_responsible_nodes(self, key_hash):
        all_nodes = sorted([hash_function(node) for node in self.known_nodes] + [self.node_id])
        
        for node_hash in all_nodes:
            if key_hash <= node_hash:
                return node_hash
        return all_nodes[0] # return the first node if the key_hash > all_nodes


    # Function to store the key-value pair based on consistent hashing
    def put(self, key, value):
        key_hash = hash_function(key)
        responsible_node = self.get_responsible_nodes(key_hash)
        
        if responsible_node == self.node_id:
            print(f"Storing locally: key_hash={key_hash}, value={value}")
            self.data_store[key_hash] = value
            return f"Stored key {key} at node {self.node_id}"
        else: 
            # store the key-value pair to the responsible node
            responsible_node_address = self.get_address_for_node(responsible_node) 
            print(f"Forwarding PUT request to {responsible_node_address} for key_hash={key_hash}")
            response = requests.put(f'http://{responsible_node_address}/storage/{key}', data=value)
            return response.json().get('message')


    # Function to get the key-value pair with consistent hashing
    def get(self, key):
        key_hash = hash_function(key)
        responsible_node = self.get_responsible_nodes(key_hash)
        if responsible_node == self.node_id:
            print(f"Retrieving locally: key_hash={key_hash}")
            return self.data_store.get(key_hash, None)
        else:
            # retrieve the key-value pair from the responsible node
            responsible_node_address = self.get_address_for_node(responsible_node)
            print(f"Forwarding GET request to {responsible_node_address} for key_hash={key_hash}")
            response = requests.get(f"http://{responsible_node_address}/storage/{key}")
            return response.json().get('value', None)
            


# Initialize the node with a unique node ID and address
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Node.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])  # Get the port number from the command-line argument
    node1 = Node(node_id=hash_function(f"node-{port}"), address=f"127.0.0.1:{port}")

    # API route for getting the network
    @app.route('/network', methods=['GET'])
    def get_network():
        return jsonify({'nodes': node1.get_known_nodes()}), 200

    # API route to receive a list of known nodes
    @app.route('/network', methods=['POST'])
    def add_known_nodes():
        nodes = request.get_json()
        # ? DEBUG: Output the nodes received in the POST request
        print(f"Received known nodes: {nodes}")
        node1.add_known_nodes(nodes)
        return jsonify({'message': 'Known nodes updated successfully'}), 200

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

    # Run the Flask server on the specified port
    app.run(host="0.0.0.0", port=port)
