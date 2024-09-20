import requests
import sys
from flask import Flask, request, jsonify
import hashlib
import socket

app = Flask(__name__)

def hash_function(value):
    return int(hashlib.sha1(value.encode()).hexdigest(), 16)

class Node:
    def __init__(self, node_id, address):
        self.node_id = node_id
        self.address = address
        self.successor = None
        self.predecessor = None
        self.data_store = {}
        self.finger_table = []
        self.known_nodes = []  # Initialize known nodes

    def update_successor_predecessor(self, node_list):
        """ Update successor and predecessor based on node list """
        self.known_nodes = node_list  # Update known nodes with new list
        all_nodes = sorted([hash_function(node) for node in node_list] + [self.node_id])
        index = all_nodes.index(self.node_id)

        # Successor is the next node in the sorted list
        self.successor = node_list[(index + 1) % len(node_list)]
        # Predecessor is the previous node in the sorted list
        self.predecessor = node_list[(index - 1) % len(node_list)]
        print(f"Updated node {self.address}: Successor: {self.successor}, Predecessor: {self.predecessor}")

        # Update finger table whenever the known nodes change
        self.update_finger_table()

    def update_finger_table(self):
        """Populate or update the finger table for faster lookups."""
        m = 160  # Number of bits in SHA-1
        self.finger_table = []
        
        # Calculate finger table entries
        for i in range(m):
            start = (self.node_id + 2**i) % (2**m)  # Find the start of each interval
            successor = self.find_successor(start)  # Find the successor responsible for this interval
            self.finger_table.append(successor)
        
        # LOG
        print(f"Finger table for node {self.address} populated: {self.finger_table}")

    def find_successor(self, key_hash):
        """Find the successor node for a given key hash."""
        if not self.known_nodes:
            return self.address  # Return self if no known nodes
        
        sorted_nodes = sorted([hash_function(node) for node in self.known_nodes] + [self.node_id])
        for node_hash in sorted_nodes:
            if key_hash <= node_hash:
                return self.get_address_by_hash(node_hash)
        
        return self.get_address_by_hash(sorted_nodes[0])  # Wrap around

    def get_address_by_hash(self, node_hash):
        """Helper function to get the address corresponding to a node hash."""
        if node_hash == self.node_id:
            return self.address
        for node in self.known_nodes:
            if hash_function(node) == node_hash:
                return node
        return None

    def put(self, key, value):
        """ Store a key-value pair """
        key_hash = hash_function(key)
        if self.successor and key_hash > self.node_id and key_hash <= hash_function(self.successor):
            # Store locally
            self.data_store[key] = value
            return "Stored locally"
        else:
            # Forward to successor
            try:
                response = requests.put(f"http://{self.successor}/storage/{key}", data=value)
                return response.json().get('message')
            except Exception as e:
                return str(e)

    def get(self, key):
        """ Retrieve a key-value pair """
        key_hash = hash_function(key)
        if key_hash in self.data_store:
            return self.data_store[key]
        else:
            try:
                response = requests.get(f"http://{self.successor}/storage/{key}")
                return response.json().get('value')
            except Exception as e:
                return None


# Flask Routes
@app.route('/network', methods=['POST'])
def network_update():
    node_list = request.json['nodes']
    node1.update_successor_predecessor(node_list)
    return jsonify({'message': 'Updated network'}), 200

@app.route('/storage/<key>', methods=['PUT'])
def put_value(key):
    value = request.data.decode('utf-8')
    response = node1.put(key, value)
    return jsonify({'message': response}), 200

@app.route('/storage/<key>', methods=['GET'])
def get_value(key):
    value = node1.get(key)
    if value is not None:
        return jsonify({'value': value}), 200
    else:
        return jsonify({'error': 'Key not found'}), 404

@app.route('/successor', methods=['GET'])
def get_successor():
    return jsonify({'successor': node1.successor}), 200

@app.route('/predecessor', methods=['GET'])
def get_predecessor():
    return jsonify({'predecessor': node1.predecessor}), 200

@app.route('/fingertable', methods=['GET'])
def get_finger_table():
    return jsonify({'fingertable': node1.finger_table}), 200

if __name__ == '__main__':
    port = int(sys.argv[1])
    hostname = socket.gethostname().split('.')[0]  # Simplified hostname
    node1 = Node(node_id=hash_function(f"node-{port}"), address=f"{hostname}:{port}")
    app.run(host="0.0.0.0", port=port)
