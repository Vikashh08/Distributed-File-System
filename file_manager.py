import os
import shutil
from datetime import datetime
import json
from datetime import datetime
# Add this at the top
import shutil
def get_metadata_keys():
    metadata = load_metadata()
    return list(metadata.keys())

def remove_node_from_metadata(node_name):
    metadata = load_metadata()
    for filename, data in metadata.items():
        if node_name in data["nodes"]:
            data["nodes"].remove(node_name)
    save_metadata(metadata)

METADATA_FILE = 'metadata.json'

def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)


NODES = ['node1', 'node2', 'node3']
UPLOAD_FOLDER = 'uploads'

# Track node status (active/deactivated)
node_status = {node: True for node in NODES}

def set_node_status(node, status):
    node_status[node] = status

def save_file(file):
    filename = file.filename
    metadata = load_metadata()
    stored_nodes = []

    for node in NODES:
        if node_status[node]:
            path = os.path.join(UPLOAD_FOLDER, node)
            os.makedirs(path, exist_ok=True)
            file.save(os.path.join(path, filename))
            stored_nodes.append(node)

    metadata[filename] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nodes": stored_nodes
    }

    save_metadata(metadata)
    return f"{filename} uploaded to: {', '.join(stored_nodes)}"

    # Select two nodes for replication
    active_nodes = [node for node in NODES if node_status[node]]
    selected_nodes = active_nodes[:2] if len(active_nodes) >= 2 else active_nodes

    for node in selected_nodes:
        node_path = os.path.join(UPLOAD_FOLDER, node)
        os.makedirs(node_path, exist_ok=True)
        file.stream.seek(0)  # Reset stream for next write
        with open(os.path.join(node_path, unique_filename), 'wb') as f:
            shutil.copyfileobj(file.stream, f)

def get_all_files_by_node():
    files_by_node = {}
    for node in NODES:
        path = os.path.join(UPLOAD_FOLDER, node)
        if os.path.exists(path):
            files = os.listdir(path)
            label = f"{node} ({'Active' if node_status[node] else 'Inactive'})"
            files_by_node[label] = files
    return files_by_node


from flask import send_file

def retrieve_file(filename):
    for n in NODES:
        if node_status[n]:
            file_path = os.path.join(UPLOAD_FOLDER, n, filename)
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
    return "❌ File unavailable due to node failure or no replicas.", 404

def check_and_recover_files():
    metadata = load_metadata()
    desired_replicas = 2  # Minimum replicas required

    for filename, data in metadata.copy().items():
        # Physical file verification
        valid_nodes = []
        for node in data["nodes"]:
            node_path = os.path.join(UPLOAD_FOLDER, node, filename)
            if os.path.exists(node_path) and node_status.get(node, False):
                valid_nodes.append(node)
        
        # Update metadata with only valid nodes
        if len(valid_nodes) != len(data["nodes"]):
            metadata[filename]["nodes"] = valid_nodes
            save_metadata(metadata)

        current_replicas = len(valid_nodes)
        if current_replicas >= desired_replicas:
            continue

        # Find candidate nodes for replication
        candidate_nodes = [node for node in NODES if node_status[node] and node not in valid_nodes]
        needed = desired_replicas - current_replicas
        selected_nodes = candidate_nodes[:needed]

        if not selected_nodes:
            continue  # No available nodes

        # Find a valid source node
        source_node = next((node for node in valid_nodes if node_status[node]), None)
        if not source_node:
            continue  # No source available

        # Replicate to selected nodes
        source_path = os.path.join(UPLOAD_FOLDER, source_node, filename)
        for dest_node in selected_nodes:
            dest_dir = os.path.join(UPLOAD_FOLDER, dest_node)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(source_path, os.path.join(dest_dir, filename))
            metadata[filename]["nodes"].append(dest_node)

        save_metadata(metadata)
