import io
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
app.config['UPLOAD_FOLDER'] = 'temp_uploads/'  # Define where uploaded files will be stored
app.config['RO_CRATE_FOLDER'] = 'ro_crate/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit to 16MB

OPENBIS_DATA = [
    {"id": "20240424084127547-750", "type": "@as.dto.dataset.DataSet", "title": "Research in Ontology", "metadata": {"info":"1D image"}, "ontology": "@https://openbis.ont.ethz.ch/DataSet"},
    {"id": "20240424084127547-751", "type": "@as.dto.dataset.Dataset", "title": "Data related to Ontology Research", "metadata": {"info":"2D image"}, "ontology": "@https://openbis.ont.ethz.ch/DataSet"},
    {"id": "20240320011823235-1", "type": "@as.dto.experiment.Experiment", "title": "Experiment 1", "metadata": {"info":"Experiment on algea"}, "ontology": "@https://openbis.ont.ethz.ch/Experiment"},
    {"id": "20240320011823235-2", "type": "@as.dto.experiment.Experiment", "title": "Experiment 2", "metadata": None, "ontology": "@https://openbis.ont.ethz.ch/Experiment"},
    {"id": "20240402011823235-1280", "type": "@as.dto.object.Object", "title": "Protein", "metadata": {"hasBioPolymerSequence":"AAACCTTTGTACAATG"}, "ontology": "@https://schema.org/Protein"},
    {"id": "20240402011823235-1289", "type": "@as.dto.dataset.Object", "title": "Molecul", "metadata": {"inChIKey":"MTHN", 
                                                                                                            "iupacName": "Methane", 
                                                                                                            "molecularFormula":"CH4", 
                                                                                                            "molecularWeight": "16.043 g/mol-1"}, "ontology": "@https://schema.org/MolecularEntity"}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def get_all_data():
    return jsonify(OPENBIS_DATA)

@app.route('/data/filter', methods=['GET'])
def filter_data():
    #format = request.args.get('format')
    filter_type = request.args.get('type')
    if not filter_type:
        return "Type parameter is required for filtering.", 400
    if filter_type == "all":
        return jsonify(OPENBIS_DATA)
    filtered_data = [item for item in OPENBIS_DATA if item['ontology'].lower() == filter_type.lower()]
    return jsonify(filtered_data)

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

@app.route('/data/types', methods=['GET'])
def get_all_types():
    temp_dir = app.config['UPLOAD_FOLDER']
    # Create a new RO-Crate in the temporary directory
    crate = ROCrate()

    # Create the JSON content
    response_file_path = os.path.join(temp_dir, 'response.json')
    with open(response_file_path, 'w') as f:
        json.dump([item['ontology'] for item in OPENBIS_DATA], f, indent=4)
    
    # Add the JSON file to the crate
    crate.add_file(response_file_path, './response.json', properties={"@type": "RESPONSE"})

    # Write the crate to the temporary directory
    crate_dir = os.path.join(temp_dir, 'ro_crate')
    crate.write_zip(crate_dir)
    
    return send_file('temp_uploads/ro_crate.zip', as_attachment=True, download_name='ro_crate.zip')

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

@app.route('/receive', methods=['POST'])
def receive_data():
    data = request.json
    print("Data received:", data)
    return jsonify({"message": "Data received successfully", "yourData": data}), 200

@app.route('/receive_zip', methods=['POST'])
def receive_zip():
    print(request.files['file'])
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    print(file.filename)
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file and file.filename.endswith('.zip'):
        try:
            # Make sure to get the correct file stream
            # `file.stream` might not work properly directly, so use BytesIO
            byte_stream = io.BytesIO(file.read())  # Read the file stream into a BytesIO buffer

            # Now use the BytesIO object with zipfile
            zip_file = zipfile.ZipFile(byte_stream, 'r')
            print(zip_file.namelist())  # List contents of the zip to confirm successful opening

            with zip_file.open('ro-crate-metadata.json') as f:
                data = f.read()
                print(json.loads(data))
            
            # Assuming there's a specific file you want to read from the zip
            with zip_file.open('query.json') as f:
                print(type(f))
                data = f.read()
                print(json.loads(data))  # Output the contents of the data.json file
                OPENBIS_DATA.append(json.loads(data))

            return jsonify({"message": "Zip file processed successfully"}), 200
        except zipfile.BadZipFile:
            return jsonify({"message": "Invalid zip file"}), 400
    else:
        return jsonify({"message": "Unsupported file type"}), 400

if __name__ == '__main__':
    app.run(port=5001, debug=True)
