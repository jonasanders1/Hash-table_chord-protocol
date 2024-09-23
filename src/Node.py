import requests
import sys
from flask import Flask, request, jsonify, Response
import hashlib
import socket

app = Flask(__name__)


# Hash function
def hash_value(value):
    print(f"Hashing value: {value}", flush=True)
    # using SHA-1 hashing to assign a unique ID to each node or value 
    return int(hashlib.sha1(value.encode()).hexdigest(), 16)


# Represents a node in the DHT
class Node:
    
    # Initializing a node
    def __init__(self, address):
        self.node_id = hash_value(address)
        self.address = address
        self.successor = None
        self.predecessor = None
        self.data_store = {}
        self.finger_table = []
        self.known_nodes = [] 
        self.node_hashes = {}
        
        # Log the current node's initialization
        print(f"Initializing node with address {self.address} and ID hash {self.node_id}", flush=True)
    
    
    # Responsible for updating the nodes successor and predecessor
    def update_successor_predecessor(self, node_list):
        
        self.known_nodes = node_list
        # Cache node hashes to avoid redundant hashing
        for node in self.known_nodes:
            if node not in self.node_hashes:
                self.node_hashes[node] = hash_value(node)

        # Check to make sure that the current node`s address is part of the known nodes
        if self.address not in self.known_nodes:
            print(f"Adding current node {self.address} to the known nodes list.", flush=True)
            self.known_nodes.append(self.address)
            self.node_hashes[self.address] = self.node_id

        # Sort all nodes based on their hash values
        sorted_node_hashes = sorted(self.node_hashes.values())
        # Find the hash of the current node
        self_hash = self.node_id

        # Single node case: assign successor and predecessor to its own address
        if len(self.known_nodes) == 1:
            self.successor = self.address
            self.predecessor = self.address
            print(f"Single-node case: Successor and Predecessor set to {self.address}", flush=True)
            return

        # Find the position of the current node in the sorted list
        index = sorted_node_hashes.index(self_hash)

        # Assign successor and predecessor indexes
        successor_index = (index + 1) % len(sorted_node_hashes)
        predecessor_index = (index - 1) % len(sorted_node_hashes)

        # Assign successor and predecessor based on the indexes
        self.successor = self.get_address_by_hash(sorted_node_hashes[successor_index])
        self.predecessor = self.get_address_by_hash(sorted_node_hashes[predecessor_index])

        # Cache predecessor and successor hashes if missing
        if self.successor not in self.node_hashes:
            self.node_hashes[self.successor] = hash_value(self.successor)

        if self.predecessor not in self.node_hashes:
            self.node_hashes[self.predecessor] = hash_value(self.predecessor)

        print(f"Updated node {self.address}: Successor: {self.successor}, Predecessor: {self.predecessor}", flush=True)

        # Update the finger table after setting successor and predecessor
        self.update_finger_table()





    def get_address_by_hash(self, node_hash):
        for node, hashed_value in self.node_hashes.items():
            if hashed_value == node_hash:
                return node
        return None


    # function to update the finger table for a node
    def update_finger_table(self):
        m = 160 # 160 entries because of SHA-1 hashing
        
        self.finger_table = []
        
        # populating the finger table 
        # looping over all the possible entries
        for i in range(m):
            start = (self.node_id + 2**i) % (2**m)
            successor = self.find_successor(start)
            
            # if valid sucessor found and it`s not in the finger table --> append it
            if successor and successor not in self.finger_table:
                self.finger_table.append(successor)
        print(f"Finger table for node {self.address} updated: {self.finger_table}", flush=True)

    # Function to find the nodes successor based on a key`s hash
    def find_successor(self, key_hash):
        # check that predecessor hash exists
        if self.predecessor and self.predecessor not in self.node_hashes:
            self.node_hashes[self.predecessor] = hash_value(self.predecessor)
        
        #  Single node case check
        #  if so --> assign to itself
        if self.predecessor is None or (self.node_hashes[self.predecessor] < key_hash <= self.node_id):
            return self.address
        else:
            # looping over all know_nodes
            for node in sorted(self.known_nodes, key=lambda n: self.node_hashes[n]):
                node_hash = self.node_hashes[node]
                if self.node_id < node_hash >= key_hash:
                    return node
            # fallback 
            return self.successor if self.successor != self.address else None

    # function to store a key-value pair in the node
    def put(self, key, value):
        # hashing the key
        key_hash = hash_value(key)
        print(f"Storing key: {key}, hash: {key_hash} at node {self.address}", flush=True)

        # Check if the current node is responsible for storing the key
        if (self.predecessor is None or 
            (hash_value(self.predecessor) < key_hash <= self.node_id) or 
            (self.node_id < hash_value(self.predecessor) and (key_hash > hash_value(self.predecessor) or key_hash <= self.node_id))):
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


    # function to get a value based on a given key
    def get(self, key):
        # hashing the key
        key_hash = hash_value(key)
        
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
    hashed_nodes = [hash_value(node) for node in node_list]
    print(f"Hashes of the received nodes: {hashed_nodes}", flush=True)
    # Call update successor and predecessor
    node1.update_successor_predecessor(node_list)
    
    return jsonify({'message': 'Updated network'}), 200


@app.route('/storage/<key>', methods=['PUT'])
def put_value(key):
    value = request.data.decode('utf-8')
    response = node1.put(key, value)
    return Response(response, content_type='text/plain'), 200  

@app.route('/storage/<key>', methods=['GET'])
def get_value(key):
    value = node1.get(key)
    if value is not None:
        return Response(value, content_type='text/plain'), 200
    else:
        return Response("Key not found", content_type='text/plain'), 404


# ! Helper endpoints
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
    hostname = socket.gethostname().split('.')[0]   # Get the hostname without the domain (without .ifi.uit.no)
    node_address = f"{hostname}:{port}"
    node1 = Node(address=node_address) 
    print(f"Initializing node with address: {node_address}", flush=True)
    app.run(host="0.0.0.0", port=port)
