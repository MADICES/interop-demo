from flask import Flask, render_template, request, jsonify, send_file
from rocrate.rocrate import ROCrate
from flask_cors import CORS
import os
import zipfile
import shutil
from werkzeug.utils import secure_filename
import json
import tempfile

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'aida/temp_uploads/'  # Define where uploaded files will be stored
app.config['RO_CRATE_FOLDER'] = 'aida/ro_crate/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit to 16MB

AIDA_DATA = [
    {"id": "AFRT-56", "type": "@as.dto.dataset.DataSet", "title": "Research xy"},
    {"id": "AFRT-51", "type": "@aiida.Simulation", "title": "Data related to xy"},
    {"id": "WFML-1", "type": "@aiida.Workflow", "title": "Experiment 1"},
    {"id": "WFML-2", "type": "@as.dto.experiment.Experiment", "title": "Experiment 2"},
    {"id": "M-89", "type": "@https://schema.org/MolecularEntity", "title": "Crystal"},
    {"id": "TPMS", "type": "@https://schema.org/Protein", "title": "Tropomyosin"}  
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def get_all_data():
    return jsonify(AIDA_DATA)

@app.route('/data/filter', methods=['GET'])
def filter_data():
    filter_type = request.args.get('type')
    if not filter_type:
        return "Type parameter is required for filtering.", 400
    filtered_data = [item for item in AIDA_DATA if item['type'].lower() == filter_type.lower()]
    return jsonify(filtered_data)

# Example data that you might want to include in the JSON file
data_types = ["@DataSet", "@Dataset", "@Experiment", "@Object"]

@app.route('/data/types', methods=['GET'])
def get_all_types():
    temp_dir = app.config['UPLOAD_FOLDER']
    # Create a new RO-Crate in the temporary directory
    crate = ROCrate()

    # Create the JSON content
    response_file_path = os.path.join(temp_dir, 'response.json')
    with open(response_file_path, 'w') as f:
        json.dump([item['type'] for item in AIDA_DATA], f, indent=4)
    
    # Add the JSON file to the crate
    crate.add_file(response_file_path, './response.json', properties={"@type": "RESPONSE"})

    # Write the crate to the temporary directory
    crate_dir = os.path.join(temp_dir, 'ro_crate')
    crate.write_zip(crate_dir)
    
    return send_file('temp_uploads/ro_crate.zip', as_attachment=True, download_name='ro_crate.zip')


def extract_and_read_rocrate(file_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip the file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Process the unzipped directory
        crate = ROCrate(temp_dir)
        for entity in crate.get_entities():
            print(entity)
            if entity['@type'] == 'RESPONSE':
                response_file_path = os.path.join(temp_dir, entity['@id'])
                with open(response_file_path, 'r') as file:
                    return json.load(file)
        return None

@app.route('/upload_rocrate', methods=['POST'])
def upload_rocrate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        response_content = extract_and_read_rocrate(file_path)
        if response_content:
            return jsonify(response_content)
        else:
            return jsonify({'message': 'No RESPONSE type file found in the RO-Crate or failed to read.'})

@app.route('/files', methods=['GET'])
def list_files():
    files_info = []
    uploads_dir = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(uploads_dir):
        if filename.endswith('.type'):
            continue  # Skip type files
        file_type_path = os.path.join(uploads_dir, f"{filename}.type")
        file_type = 'Unknown'
        if os.path.exists(file_type_path):
            with open(file_type_path, 'r') as type_file:
                file_type = type_file.read().strip()
        files_info.append({'filename': filename, 'type': file_type})
    return jsonify(files_info)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    file_type = request.form['type']
    if file.filename == '':
        return 'No selected file', 400
    if file and file_type:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        # Save file type in a simple way, by creating a text file for each uploaded file
        with open(f"{filename}.type", 'w') as type_file:
            type_file.write(file_type)
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename, 'type': file_type}), 200

@app.route('/export', methods=['GET'])
def export_data():
    crate = ROCrate()
    uploads_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Adding all files from the uploads directory to the RO-Crate
    for filename in os.listdir(uploads_dir):
        if not filename.endswith('.type'):
            file_path = os.path.join(uploads_dir, filename)
            type_path = f"{file_path}.type"
            if os.path.exists(type_path):
                with open(type_path, 'r') as type_file:
                    file_type = type_file.read().strip()
                crate.add_file(file_path, properties={"@type": file_type})

    output_dir = app.config['RO_CRATE_FOLDER']
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    crate.write_zip(output_dir)

    # Clean up uploads directory after creating the RO-Crate
    #shutil.rmtree(uploads_dir)
    #os.makedirs(uploads_dir)  # Recreate the directory for future uploads

    # Optionally, list all files in the crate
    file_paths = [os.path.join(root, file) for root, dirs, files in os.walk(output_dir) for file in files]

    return jsonify({'message': 'RO-Crate prepared for download.', 'file_paths': file_paths})

@app.route('/download')
def download():
    # Send the file to the user
    response = send_file('ro_crate.zip', as_attachment=True)
    
    # Clean up ro_crate_output directory after download
    def after_request(response):
        uploads_dir = app.config['UPLOAD_FOLDER']
        try:
            shutil.rmtree('ro_crate.zip')
            # Clean up uploads directory after creating the RO-Crate
            shutil.rmtree(uploads_dir)
            os.makedirs(uploads_dir)  # Recreate the directory for future uploads
        except Exception as e:
            app.logger.error('Error cleaning up ro_crate_output directory', exc_info=e)
        return response
    
    response.call_on_close(lambda: after_request(response))
    return response

if __name__ == '__main__':
    app.run(port=5002, debug=True)
