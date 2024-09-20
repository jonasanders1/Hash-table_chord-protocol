#!/bin/bash

# Clean up any previous Flask processes
for HOST in "${HOSTS[@]}"; do
  echo "Killing previous Flask processes on $HOST"
  ssh $HOST "pkill -f Node.py"  # Kills any process running Node.py on the host
done

# Check if the number of servers is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <number_of_servers>"
  exit 1
fi

NUM_SERVERS=$1
HOSTS=($(/share/ifi/available-nodes.sh))  # Get available nodes
HOST_PORTS=()  # Store 'host:port' combos

# Get the current working directory (full path)
PROJECT_DIR=$PWD

# Loop through and deploy each server
for ((i=0; i<$NUM_SERVERS; i++)); do
  HOST=${HOSTS[$i % ${#HOSTS[@]}]}  # Round-robin through available nodes
  PORT=$(shuf -i 5000-60000 -n 1)  # Get random port between 5000 and 60000

  # SSH into the node and start the server in the background using nohup
  echo "Starting server on $HOST:$PORT"
  ssh -n -f $HOST "bash -c 'source $PROJECT_DIR/venv/bin/activate && nohup python3 $PROJECT_DIR/Node.py $PORT > $PROJECT_DIR/server_$HOST_$PORT.log 2>&1 &'"

  # Add the host:port combination to the array
  HOST_PORTS+=("$HOST:$PORT")
done

# Output the host:port combinations as a JSON list
echo "Deployed Nodes: $(printf '%s\n' "${HOST_PORTS[@]}" | jq -R . | jq -s .)"

# Ensure the script exits without hanging
exit 0
