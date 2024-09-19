import sys
from flask import Flask, request, jsonify
import hashlib

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

    def add_node(self, node):
        """Add a node to the network."""
        self.known_nodes.append(node)

    def get_known_nodes(self):
        """Return the list of known nodes."""
        return self.known_nodes

    def put(self, key, value):
        """Store the key-value pair."""
        key_hash = hash_function(key)
        print(f"Storing: key_hash={key_hash}, value={value}")
        self.data_store[key_hash] = value
        return f"Stored key {key} at node {self.node_id}"

    def get(self, key):
        """Retrieve the value based on the hashed key."""
        key_hash = hash_function(key)
        print(f"Retrieving: key_hash={key_hash}")
        return self.data_store.get(key_hash, None)


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
