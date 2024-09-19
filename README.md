# Cluster Comands

### Start cluster server
```ssh joand4770@ificluster.ifi.uit.no```
### List nodes available right now
```/share/ifi/available-nodes.sh```
### List the cluster hardware
```/share/ifi/list-cluster-static.sh```
List nodes by load
```/share/ifi/list-nodes-by-load.sh```
### List all your processes
```/share/ifi/list-cluster-my-processes.sh```
### Clean out all your processes
```/share/ifi/cleanup.sh```

### List all the nodes in the cluster along with their hardware details
```/share/ifi/list-cluster-static.sh```
### Shows witch nodes currently available
```/share/ifi/available-nodes.sh```
### This will display the name of the current node you are logged into
```echo $HOSTNAME```

## 1. Navigate to node and create project
  - List all nodes and navigate to an available node.
    - ```ssh c11-10```
  - Verify which node im on:
    - ```echo $HOSTNAMe —> c11-10.ifi.uit.no```
  - Create a project directory
    - ```mkdir joand4770```
    - ```cd joand4770```

## 2. Connect to the Cluster Using VS Code:
  - Open VS Code.
  - Press  ```Cmd + Shift + P``` to open the Command Palette.
  - Type Remote-SSH: Connect to Host... and select it.
  - Enter your cluster’s SSH address (e.g., your_username@ificluster.ifi.uit.no) and your password.

## 3. Open project in vs code within the cluster:
  - run the python server script
  - ```python server.py (python3 -m http.server 5000)```
  -  --—> Server running on ificluster.ifi.uit.no:37059
  - ```curl http://ificluster.ifi.uit.no:44993```

## 4.Run run shell script
  - ```./run.sh 3```
  - --—> [ "c6-6:27458", "c7-12:43456", "c11-5:56776" ]
  — ```python3 testscript.py '[ "c6-6:27458", "c7-12:43456", "c11-5:56776" ]'```
  - ---> [ "c6-6:27458", "c7-12:43456", "c11-5:56776" ]
  — ———> Success!

## Terminal commands for Putting a value and Getting a value based on keys (Locally with a single node)
### PUT 
```curl -X PUT -H "Content-Type: text/plain" -d 'my test value' http://127.0.0.1:3000/storage/mytestkey```
### GET 
```curl http://127.0.0.1:3000/storage/mytestkey```
### GET Network
```curl http://127.0.0.1:3000/network```

## Terminal commands for Putting a value and Getting a value based on keys (with run.sh script)

### Run the server
```bash run.sh 3```
### PUT 
```curl -X PUT -H "Content-Type: text/plain" -d 'my test value' http://172.21.21.222:10468/storage/mytestkey```
### GET 
```curl  http://172.21.21.222:10468/storage/mytestkey```
### GET Network
```curl http://127.0.0.1:3000/network```