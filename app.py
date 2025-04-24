from flask import Flask, render_template, request, redirect, send_file
from flask import Flask, render_template, request, redirect, url_for
import shutil  
from file_manager import UPLOAD_FOLDER  # Add this with other imports
import file_manager  
from flask import Flask, render_template, request, redirect, url_for
from file_manager import (
    save_file, 
    retrieve_file, 
    get_all_files_by_node,
    load_metadata  # Add this
)
import os
from file_manager import save_file, retrieve_file
import file_manager
from file_manager import get_all_files_by_node, save_file, retrieve_file, set_node_status, node_status


app = Flask(__name__)

from file_manager import save_file, retrieve_file, get_all_files_by_node

@app.route('/')
def index():
    files_by_node = get_all_files_by_node()
    metadata = load_metadata() 
    return render_template('index.html', 
                          files_by_node=files_by_node,
                          metadata=metadata)  

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    save_file(file)
    return redirect('/')

@app.route('/download/<filename>')
def download(filename):
    from file_manager import retrieve_file
    return retrieve_file(filename)

@app.route('/toggle_node/<node_name>', methods=['POST'])
def toggle_node(node_name):
    from file_manager import set_node_status, node_status
    current_status = node_status.get(node_name, True)
    set_node_status(node_name, not current_status)
    return redirect(url_for('index'))

@app.route('/delete/<node>/<filename>', methods=['POST'])
def delete_file(node, filename):
    from file_manager import UPLOAD_FOLDER  # Ensure proper import
    
    # Construct full file path
    node_clean = node.split()[0]  # Handle "node1 (Active)" format
    file_path = os.path.join(UPLOAD_FOLDER, node_clean, filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted {filename} from {node_clean}")  # Debug log
    except Exception as e:
        print(f"Delete error: {str(e)}")  # Error handling
    
    # Update metadata
    metadata = file_manager.load_metadata()
    if filename in metadata:
        if node_clean in metadata[filename]["nodes"]:
            metadata[filename]["nodes"].remove(node_clean)
            file_manager.save_metadata(metadata)
            print(f"Updated metadata for {filename}")  # Debug log
    
    # Trigger recovery
    file_manager.check_and_recover_files()
    return redirect(url_for('index'))

@app.route('/clear_node/<node_name>', methods=['POST'])
def clear_node(node_name):
    # Delete all files from the node
    node_path = os.path.join(file_manager.UPLOAD_FOLDER, node_name)
    if os.path.exists(node_path):
        shutil.rmtree(node_path)
        os.makedirs(node_path, exist_ok=True)
    
    # Update metadata
    metadata = file_manager.load_metadata()
    for filename, data in metadata.items():
        if node_name in data["nodes"]:
            data["nodes"].remove(node_name)
    file_manager.save_metadata(metadata)
    
    # Trigger recovery if needed
    file_manager.check_and_recover_files()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

import threading
import time

def background_recovery():
    while True:
        time.sleep(10)  # Check every 10 seconds
        file_manager.check_and_recover_files()

if __name__ == '__main__':
    # Start the background recovery thread
    recovery_thread = threading.Thread(target=background_recovery)
    recovery_thread.daemon = True  # Terminate with the main thread
    recovery_thread.start()
    app.run(debug=True, use_reloader=False)  # Disable reloader to avoid duplicate threads
