#!/bin/bash

# Check if the number of servers is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <number_of_servers>"
  exit 1
fi

NUM_SERVERS=$1
HOSTS=($(/share/ifi/available-nodes.sh))  # Get available nodes
HOST_PORTS=()  # Store 'host:port' combos
KNOWN_NODES=()  # To keep track of known nodes during the loop

# Get the current working directory (full path)
PROJECT_DIR=$PWD

# Loop through and deploy each server
for ((i=0; i<$NUM_SERVERS; i++)); do
  HOST=${HOSTS[$i % ${#HOSTS[@]}]}  # Round-robin through available nodes
  PORT=$(shuf -i 5000-60000 -n 1)  # Get random port between 5000 and 60000

  # Add this host:port to the known_nodes list
  HOST_PORT="$HOST:$PORT"
  KNOWN_NODES+=("$HOST_PORT")

  # SSH into the node and start the server in the background using nohup
  echo "Starting server on $HOST:$PORT"
  ssh -n -f $HOST "bash -c 'source $PROJECT_DIR/venv/bin/activate && nohup python3 $PROJECT_DIR/Node.py $PORT > $PROJECT_DIR/server_$HOST_$PORT.log 2>&1 &'"

  # Add the host:port combination to the array
  HOST_PORTS+=("$HOST_PORT")
done

# Convert known nodes to JSON array
KNOWN_NODES_JSON=$(printf '%s\n' "${KNOWN_NODES[@]}" | jq -R . | jq -s .)

# Output the host:port combinations as a JSON list
echo "Known Nodes JSON: $KNOWN_NODES_JSON"

# Now that all nodes are running, inform them of each other
for HOST_PORT in "${HOST_PORTS[@]}"; do
  IFS=":" read -r HOST PORT <<< "$HOST_PORT"
  echo "Updating node at $HOST:$PORT with known nodes"

  # Send POST request to update known nodes and capture response
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$KNOWN_NODES_JSON" http://$HOST:$PORT/network)
  
  if [ "$RESPONSE" -eq 200 ]; then
    echo "Successfully updated $HOST:$PORT"
  else
    echo "Failed to update $HOST:$PORT, HTTP status code: $RESPONSE"
    
    # Optionally retry the POST request once if it failed
    echo "Retrying update for $HOST:$PORT..."
    sleep 2
    RETRY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$KNOWN_NODES_JSON" http://$HOST:$PORT/network)
    if [ "$RETRY_RESPONSE" -eq 200 ]; then
      echo "Retry successful for $HOST:$PORT"
    else
      echo "Retry failed for $HOST:$PORT, HTTP status code: $RETRY_RESPONSE"
    fi
  fi
done

# Print the final host:port list
echo $(printf '%s\n' "${HOST_PORTS[@]}" | jq -R . | jq -s .)

# Ensure the script exits without hanging
exit 0
