#!/bin/bash

# 1. Deploy multiple instances of HTTP servers on different nodes in the cluster
# 2. Input parameter specifying the number of servers to deploy
# 3. Start the servers on different nodes
# 4. Make sure each server runs on different ports
# 5. Return a JSON-formatted list with 'host:port' combos of the running servers

# Check to see if the shell script gets the number of servers as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <number_of_servers>"
  exit 1
fi

NUM_SERVERS=$1
HOSTS=($(/share/ifi/available-nodes.sh))  # Get available nodes in the cluster
HOST_PORTS=()  # Array to store 'host:port' combos

# Get the current working directory (full path)
PROJECT_DIR=$PWD

# Loop through all servers and deploy each one
for ((i=0; i<$NUM_SERVERS; i++)); do
  HOST=${HOSTS[$i % ${#HOSTS[@]}]}  # Round-robin through available nodes
  PORT=$(shuf -i 5000-60000 -n 1)  # Get random port between 5000 and 60000

  # Activate the venv (virituall environment)
  # Start the server on the current host and port
  ssh $HOST "source $PROJECT_DIR/venv/bin/activate && nohup python3 $PROJECT_DIR/Node.py $PORT > $PROJECT_DIR/server_$HOST_$PORT.log 2>&1 &"

  # Add the host:port combination to the array
  HOST_PORTS+=("$HOST:$PORT")
done

# Output the host:port combinations as a JSON list (array)
echo $(printf '%s\n' "${HOST_PORTS[@]}" | jq -R . | jq -s .)
