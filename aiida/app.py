import json
import os
import shutil
import tempfile
import uuid
import zipfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import jinja2
import requests
from data import CONTEXT, DATA, IDS, MAPPING, PLATFORMS
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from pyld import jsonld
from rocrate.rocrate import ROCrate
from werkzeug.utils import secure_filename

app = Flask(
    __name__,
    static_url_path="",
    static_folder="assets",
)

CORS(app)

app.config["UPLOAD_FOLDER"] = "temp_uploads/"
app.config["RO_CRATE_FOLDER"] = "ro_crate/"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SHARED_PATH"] = "../shared"

app.jinja_loader = jinja2.ChoiceLoader(
    [
        jinja2.FileSystemLoader("templates"),
        jinja2.FileSystemLoader("../shared/templates"),
    ]
)

PORT = 5002

ORIGINAL_DATA = deepcopy(DATA)
ORIGINAL_IDS = deepcopy(IDS)
ORIGINAL_MAPPING = deepcopy(MAPPING)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/shared/<path:filename>")
def serve_shared_content(filename):
    file = Path(app.config["SHARED_PATH"]) / filename
    return send_file(file)


@app.route("/platforms", methods=["GET"])
def get_platforms():
    return jsonify(PLATFORMS)


@app.route("/data", methods=["GET"])
def get_data():
    return jsonify([_contextualize(item) for item in DATA])


@app.route("/data/filter", methods=["GET"])
def filter_data():
    filter_type = request.args.get("type")

    if not filter_type:
        return "Type parameter is required for filtering.", 400

    return jsonify(
        [
            _contextualize(item)
            for item in DATA
            if item["type"].lower() == filter_type.lower()
        ]
    )


@app.route("/data/reset", methods=["GET"])
def reset_data():
    global DATA, IDS, MAPPING
    DATA = deepcopy(ORIGINAL_DATA)
    IDS = deepcopy(ORIGINAL_IDS)
    MAPPING = deepcopy(ORIGINAL_MAPPING)
    return jsonify({"message": "Data reset successfully."}), 200


@app.route("/data/types", methods=["GET"])
def get_types():
    types = list(MAPPING.keys())

    temp_dir = Path(app.config["UPLOAD_FOLDER"])

    crate = ROCrate()
    content = json.dumps(types, indent=4)
    file = BytesIO(content.encode())
    crate.add_file(
        file,
        "./response.json",
        properties={
            "@type": "RESPONSE",
        },
    )

    crate_dir = temp_dir / "ontologies"
    crate.write_zip(crate_dir)
    crate.write(crate_dir)

    zipped_crate_path = crate_dir.with_suffix(".zip")

    return send_file(
        zipped_crate_path,
        as_attachment=True,
        download_name=zipped_crate_path.name,
    )


@app.route("/data/ontology", methods=["GET"])
def get_objects_by_ontological_type():
    ontology = request.args.get("type")

    if not ontology:
        return "Missing ontological type.", 400

    objects = [
        _contextualize(item)
        for item in DATA
        if item["ontology"].lower() == ontology.lower()
    ]

    temp_dir = Path(app.config["UPLOAD_FOLDER"])

    crate = ROCrate()
    content = json.dumps(objects, indent=4)
    file = BytesIO(content.encode())
    crate.add_file(
        file,
        "./response.json",
        properties={
            "@type": "RESPONSE",
        },
    )

    crate_dir = temp_dir / "objects_by_ontology"
    crate.write_zip(crate_dir)
    crate.write(crate_dir)

    zipped_crate_path = crate_dir.with_suffix(".zip")

    return send_file(
        zipped_crate_path,
        as_attachment=True,
        download_name=zipped_crate_path.name,
    )


@app.route("/data/import", methods=["POST"])
def import_data():
    port = request.args.get("port")
    data = request.json
    if any(item["title"] == data["title"] for item in DATA):
        return jsonify({"message": "The item already exists."}), 409
    try:
        object_type, metadata = _transform_against_context(data)
        metadata["was_imported"] = {  # type: ignore
            "from": int(port),
            "with_id": data["id"],
        }
        object_id = IDS[object_type]
        object_id["counter"] += 1
        data = {
            "id": f"{object_id['prefix']}-{object_id['counter']}",
            "type": object_type,
            "title": data["title"],
            "metadata": metadata,
            "ontology": data["ontology"],
        }
        DATA.append(data)
        return jsonify({"message": "Data imported successfully."}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route("/data/run_simulation", methods=["GET"])
def run_simulation():
    try:
        selected_object_id = request.args.get("id")
        selected_object = next(
            (item for item in DATA if item["id"] == selected_object_id),
            None,
        )

        if selected_object is None:
            return jsonify({"message": "Selected object not found"}), 404

        object_type = "@aiida.Simulation"
        object_id = IDS[object_type]
        object_id["counter"] += 1

        new_simulation = {
            "id": f"{object_id['prefix']}-{object_id['counter']}",
            "type": object_type,
            "title": f"New Simulation on {selected_object_id}",
            "metadata": {
                "uuid": str(uuid.uuid1()),
                "creation_parameters": {
                    "entities_starting_set": {"node": str(uuid.uuid1())},
                    "include_authinfos": False,
                    "include_comments": True,
                },
                "aiida_version": "2.4.3",
                "has_parent": {
                    "id": selected_object_id,
                },
            },
            "ontology": "https://aiida.net/Simulation",
        }

        if "has_children" not in selected_object["metadata"]:
            selected_object["metadata"]["has_children"] = []

        simulations: list = selected_object["metadata"]["has_children"]
        simulations.append(new_simulation["id"])

        DATA.append(new_simulation)

        return jsonify(selected_object["id"]), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500


def _contextualize(item):
    return {**CONTEXT.get(item["ontology"], {}), **item}


def _transform_against_context(data):
    ontology = data["ontology"]
    if context := CONTEXT.get(ontology, {}):
        object_type = MAPPING[ontology]
        if ctx := context.get("@context", {}):
            expanded = jsonld.expand(
                {
                    "@context": data["@context"],
                    **data["metadata"],
                },
            )
            metadata = jsonld.compact(expanded, ctx)
            metadata.pop("@context")
        else:
            metadata = data["metadata"]
    else:
        object_type = "@aiida.Object"
        MAPPING[ontology] = object_type
        CONTEXT[ontology] = {"@context": data["@context"]}
        metadata = data["metadata"]
    return object_type, metadata


@app.route("/download")
def download():
    # Send the file to the user
    response = send_file("ro_crate.zip", as_attachment=True)

    # Clean up ro_crate_output directory after download
    def after_request(response):
        uploads_dir = app.config["UPLOAD_FOLDER"]
        try:
            shutil.rmtree("ro_crate.zip")
            # Clean up uploads directory after creating the RO-Crate
            shutil.rmtree(uploads_dir)
            os.makedirs(uploads_dir)  # Recreate the directory for future uploads
        except Exception as e:
            app.logger.error("Error cleaning up ro_crate_output directory", exc_info=e)
        return response

    response.call_on_close(lambda: after_request(response))
    return response


@app.route("/upload_rocrate", methods=["POST"])
def upload_rocrate():
    if "file" not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"})
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        response_content = extract_and_read_rocrate(file_path)
        if response_content:
            return jsonify(response_content)
        else:
            return jsonify(
                {
                    "message": "No RESPONSE type file found in the RO-Crate or failed to read."
                }
            )


def extract_and_read_rocrate(file_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip the file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Process the unzipped directory
        crate = ROCrate(temp_dir)
        for entity in crate.get_entities():
            print(entity)
            if entity["@type"] == "RESPONSE":
                response_file_path = os.path.join(temp_dir, entity["@id"])
                with open(response_file_path, "r") as file:
                    return json.load(file)
        return None


@app.route("/files", methods=["GET"])
def list_files():
    files_info = []
    uploads_dir = app.config["UPLOAD_FOLDER"]
    for filename in os.listdir(uploads_dir):
        if filename.endswith(".type"):
            continue  # Skip type files
        file_type_path = os.path.join(uploads_dir, f"{filename}.type")
        file_type = "Unknown"
        if os.path.exists(file_type_path):
            with open(file_type_path, "r") as type_file:
                file_type = type_file.read().strip()
        files_info.append({"filename": filename, "type": file_type})
    return jsonify(files_info)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    file_type = request.form["type"]
    if file.filename == "":
        return "No selected file", 400
    if file and file_type:
        filename = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)  # type: ignore
        file.save(filename)
        # Save file type in a simple way, by creating a text file for each uploaded file
        with open(f"{filename}.type", "w") as type_file:
            type_file.write(file_type)
        return jsonify(
            {
                "message": "File uploaded successfully",
                "filename": file.filename,
                "type": file_type,
            }
        ), 200


@app.route("/export", methods=["GET"])
def export_data():
    crate = ROCrate()
    uploads_dir = app.config["UPLOAD_FOLDER"]
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Adding all files from the uploads directory to the RO-Crate
    for filename in os.listdir(uploads_dir):
        if not filename.endswith(".type"):
            file_path = os.path.join(uploads_dir, filename)
            type_path = f"{file_path}.type"
            if os.path.exists(type_path):
                with open(type_path, "r") as type_file:
                    file_type = type_file.read().strip()
                crate.add_file(file_path, properties={"@type": file_type})

    output_dir = app.config["RO_CRATE_FOLDER"]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    crate.write_zip(output_dir)

    # Clean up uploads directory after creating the RO-Crate
    # shutil.rmtree(uploads_dir)
    # os.makedirs(uploads_dir)  # Recreate the directory for future uploads

    # Optionally, list all files in the crate
    file_paths = [
        os.path.join(root, file)
        for root, dirs, files in os.walk(output_dir)
        for file in files
    ]

    return jsonify(
        {"message": "RO-Crate prepared for download.", "file_paths": file_paths}
    )


@app.route("/api/export", methods=["POST"])
def send_data():
    objectToExport = request.json
    temp_dir = app.config["RO_CRATE_FOLDER"]
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    crate = ROCrate()

    # Create the JSON content
    response_file_path = os.path.join(temp_dir, "query.json")
    with open(response_file_path, "w") as f:
        json.dump(objectToExport, f, indent=4)

    # Add the JSON file to the crate
    crate.add_file(response_file_path, "./query.json", properties={"@type": "PUT"})

    # Write the crate to the temporary directory
    crate_dir = os.path.join(temp_dir, "ro_crate")
    crate_path = crate.write_zip(crate_dir)
    crate.write(crate_dir)

    # shutil.rmtree(temp_dir)

    # url = 'http://localhost:5001/receive'
    # response = requests.post(url, json=crate)

    # Create a zip file in memory
    """ memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for e in crate.get_entities():
            print(e)
            if(e.type != "Dataset"):
                # Adding a file named 'data.json' with content 'data'
                zf.write(e.id)

    # Important: move the cursor back to the beginning of the BytesIO buffer
    memory_file.seek(0) """

    url = "http://localhost:5001/receive_zip"

    files = {"file": ("filename.zip", open(crate_path, "rb"), "application/zip")}
    # files = {'file': ('ro_crate.zip', memory_file, 'application/zip')}

    response = requests.post(url, files=files)

    if response.status_code == 200:
        return jsonify(
            {
                "message": "Data sent to openBIS successfully",
                "responseFromopenBIS": response.json(),
            }
        ), 200
    else:
        return jsonify({"message": "Failed to send data to openBIS"}), 500


if __name__ == "__main__":
    app.run(port=PORT, debug=True)
