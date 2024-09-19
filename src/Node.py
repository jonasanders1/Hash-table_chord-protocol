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
    self.data_store = {}  # Store key-value pairs
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
    key_hash = hash_function(key)  # Consistent key hashing
    print(f"Storing: key_hash={key_hash}, value={value}")  # Debugging log
    self.data_store[key_hash] = value
    return f"Stored key {key} at node {self.node_id}"

  def get(self, key):
    """Retrieve the value based on the hashed key."""
    key_hash = hash_function(key)  # Consistent key hashing
    print(f"Retrieving: key_hash={key_hash}")  # Debugging log
    return self.data_store.get(key_hash, None)
  


# ! GET a list of all known nodes
@app.route('/network', methods=['GET'])
def get_network():
    nodes = node1.get_known_nodes()
    return jsonify({'nodes' : nodes}), 200

# ! PUT key-value pair
@app.route('/storage/<key>', methods=['PUT'])
def put_value(key):
    """Handle PUT requests to store key-value pairs."""
    value = request.data.decode('utf-8')  # Decode raw bytes to string
    print(f"PUT received - key: {key}, value: {value}")  # Debugging log

    response = node1.put(key, value)  # Store the value in the node
    return jsonify({'message': response}), 200

# ! GET key-value pair
@app.route('/storage/<key>', methods=['GET'])
def get_value(key):
  """Handle GET requests to retrieve a value by key."""
  value = node1.get(key)
  print(f'Value: {value}')
  if value is not None:
      return jsonify({'value': value}), 200
  else:
      return jsonify({'error': 'Key not found'}), 404




# Initialize node
node1 = Node(node_id=hash_function("node1"), address="127.0.0.1:3000")

# Adding some know nodes for testing
node1.add_node({"node_id": hash_function("node2"), "address": "127.0.0.1:3001"})
node1.add_node({"node_id": hash_function("node3"), "address": "127.0.0.1:3002"})



if __name__ == "__main__":
    # Run the Flask server
    app.run(host="127.0.0.1", port=3000)
