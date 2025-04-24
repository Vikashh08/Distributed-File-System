from flask import Flask, render_template, request, redirect, send_file
from flask import Flask, render_template, request, redirect, url_for

import os
from file_manager import save_file, retrieve_file
import file_manager
from file_manager import get_all_files_by_node, save_file, retrieve_file, set_node_status, node_status


app = Flask(__name__)

from file_manager import save_file, retrieve_file, get_all_files_by_node

@app.route('/')
def index():
    files_by_node = get_all_files_by_node()
    return render_template('index.html', files_by_node=files_by_node)

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

if __name__ == '__main__':
    app.run(debug=True)


