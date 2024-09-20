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
        self.known_nodes = []
        self.predecessor = None 
        self.successor = None



    def add_node(self, node):
        """Add a node to the network."""
        self.known_nodes.append(node)
        print(f"Known nodes updated: {self.known_nodes}")

    def get_known_nodes(self):
        """Return the list of known nodes."""
        return self.known_nodes

    def add_known_nodes(self, nodes):
        """Add multiple nodes to the network."""
        self.known_nodes.extend(nodes)
        self.update_successor_predecessor()
    
    def get_address_for_node(self, node_hash):
        """Find the address of a node by its hash."""
        for node in self.known_nodes:
            if hash_function(node) == node_hash:
                return node
        return None
        
    def get_responsible_nodes(self, key_hash):
        """Find the node responsible for a given key based on consistent hashing."""
        all_nodes = sorted([hash_function(node) for node in self.known_nodes] + [self.node_id])
        for node_hash in all_nodes:
            if key_hash <= node_hash:
                return node_hash
        return all_nodes[0]  # return the first node if key_hash > all_nodes

    def put(self, key, value):
        """Store a key-value pair using consistent hashing."""
        key_hash = hash_function(key)
        responsible_node = self.get_responsible_nodes(key_hash)

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
        responsible_node = self.get_responsible_nodes(key_hash)
        
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

    def find_successor(self, key_hash):
        """Find the successor node for a given key hash."""
        # if the key is on our range, we are responsible
        if self.predecessor is None or (self.predecessor < key_hash <= self.node_id):
            return self.address
        # otherwise, we look for the next node in the ring (successor)
        for node in self.known_nodes:
            node_hash = hash_function(node)
            if self.node_id < node_hash >= key_hash:
                return node
            # if we dont find a successor , return the first node (wrap-around)
            return self.successor
        
    def update_successor_predecessor(self):
        all_nodes = sorted([hash_function(node) for node in self.known_nodes] + [self.node_id])
        index = all_nodes.index(self.node_id)
        
        # update successor
        if index < len(all_nodes) - 1:
            self.successor = self.get_address_for_node(all_nodes[index + 1])
        else:
            self.successor = self.get_address_for_node(all_nodes[0])
            
        # update predecessor
        if index > 0:
            self.predecessor = self.get_address_for_node(all_nodes[index - 1])
        else:
            self.predecessor = self.get_address_for_node(all_nodes[-1])
            
        # LOG
        print(f"Node {self.address}: Successor set to {self.successor}, Predecessor set to {self.predecessor}")

# Initialize the node with a unique node ID and address
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Node.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])  # Get the port number from the command-line argument
    hostname = socket.gethostname()  # Get the actual hostname of the machine (e.g., c6-6)
    node1 = Node(node_id=hash_function(f"node-{port}"), address=f"{hostname}:{port}")

    # API route for getting the network
    @app.route('/network', methods=['GET'])
    def get_network():
        return jsonify({'nodes': node1.get_known_nodes()}), 200

    # API route to receive a list of known nodes
    @app.route('/network', methods=['POST'])
    def add_known_nodes():
        nodes = request.get_json()
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

    # API route for helloworld test
    @app.route('/helloworld', methods=['GET'])
    def helloworld():
        return node1.address, 200




    # ! TESTING ENDPOINTS
    @app.route('/stored_keys', methods=['GET'])
    def get_stored_keys():
        return jsonify({'keys': list(node1.data_store.keys())}), 200


    # API route to get the successor of a node
    @app.route('/successor', methods=['GET'])
    def get_successor():
        return jsonify({'successor': node1.successor}), 200

    # API route to get the predecessor of a node
    @app.route('/predecessor', methods=['GET'])
    def get_predecessor():
        return jsonify({'predecessor': node1.predecessor}), 200

    # Run the Flask server on the specified port
    app.run(host="0.0.0.0", port=port)