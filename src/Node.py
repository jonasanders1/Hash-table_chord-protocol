import requests
import sys
from flask import Flask, request, jsonify, Response
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
        self.known_nodes = []

    def update_successor_predecessor(self, node_list):
        self.known_nodes = node_list
        all_nodes = sorted([hash_function(node) for node in node_list] + [self.node_id])
        index = all_nodes.index(self.node_id)
        self.successor = node_list[(index + 1) % len(node_list)] if len(node_list) > 1 else self.address
        self.predecessor = node_list[(index - 1) % len(node_list)] if len(node_list) > 1 else None
        print(f"Updated node {self.address}: Successor: {self.successor}, Predecessor: {self.predecessor}", flush=True)
        self.update_finger_table()

    def update_finger_table(self):
        m = 160
        self.finger_table = []
        for i in range(m):
            start = (self.node_id + 2**i) % (2**m)
            successor = self.find_successor(start)
            if successor and successor not in self.finger_table:
                self.finger_table.append(successor)
        print(f"Finger table for node {self.address} updated: {self.finger_table}", flush=True)

    def find_successor(self, key_hash):
        if self.predecessor is None or (hash_function(self.predecessor) < key_hash <= self.node_id):
            return self.address
        else:
            for node in sorted(self.known_nodes, key=hash_function):
                node_hash = hash_function(node)
                if self.node_id < node_hash >= key_hash:
                    return node
            return self.successor if self.successor != self.address else None

    def put(self, key, value):
        key_hash = hash_function(key)
        print(f"Storing key: {key}, hash: {key_hash} at node {self.address}", flush=True)
        if self.successor == self.address or (self.predecessor is None) or (self.node_id < key_hash <= hash_function(self.successor)):
            self.data_store[key_hash] = value
            print(f"Data stored locally at {self.address} for key_hash: {key_hash}", flush=True)
            return "Stored locally"
        try:
            if self.successor != self.address:
                print(f"Forwarding PUT request to {self.successor} for key {key}", flush=True)
                response = requests.put(f"http://{self.successor}/storage/{key}", data=value)
                print(f"Response from successor {self.successor}: {response.text}", flush=True)
                return response.text  # Use response.text for plain text response
            else:
                return "Error: Successor is the same as this node, stopping recursion."
        except Exception as e:
            print(f"Error forwarding to {self.successor}: {e}", flush=True)
            return str(e)

    def get(self, key):
        key_hash = hash_function(key)
        print(f"Retrieving key: {key}, hash: {key_hash} from node {self.address}", flush=True)
        if key_hash in self.data_store:
            print(f"Found key {key} in node {self.address}", flush=True)
            return self.data_store[key_hash]
        try:
            if self.successor != self.address:
                print(f"Forwarding GET request to {self.successor} for key {key}", flush=True)
                response = requests.get(f"http://{self.successor}/storage/{key}", timeout=5)
                response.raise_for_status()
                return response.text  # Use response.text for plain text response
            else:
                print(f"Stopping forwarding to {self.successor} to avoid recursion.", flush=True)
                return None
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
    node1 = Node(node_id=hash_function(f"node-{port}"), address=f"{hostname}:{port}")
    app.run(host="0.0.0.0", port=port)
