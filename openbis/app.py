import io
import json
import os
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

import jinja2
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

PORT = 5001

ORIGINAL_DATA = deepcopy(DATA)
ORIGINAL_IDS = deepcopy(IDS)
ORIGINAL_MAPPING = deepcopy(MAPPING)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/shared/<path:path>")
def serve_shared_content(path):
    file = Path(app.config["SHARED_PATH"]) / path
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
    temp_dir = Path(app.config["UPLOAD_FOLDER"])

    crate = ROCrate()

    filename = "response.json"
    filepath = temp_dir / filename

    with filepath.open("w") as file:
        json.dump(list(MAPPING.keys()), file, indent=4)

    crate.add_file(
        filepath,
        f"./{filename}",
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

    temp_dir = Path(app.config["UPLOAD_FOLDER"])

    crate = ROCrate()

    filename = "response.json"
    filepath = temp_dir / filename

    with filepath.open("w") as file:
        objects = [
            _contextualize_data(item)
            for item in DATA
            if item["ontology"].lower() == ontology.lower()
        ]
        json.dump(objects, file, indent=4)

    crate.add_file(
        filepath,
        f"./{filename}",
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
    try:
        new_data = request.json

        if any(item["title"] == new_data["title"] for item in DATA):
            return jsonify({"message": "The item already exists."}), 409

        ontology = new_data["ontology"]
        context = CONTEXT.get(ontology, {})

        if context:
            object_type = MAPPING[ontology]
            if ctx := context.get("@context", {}):
                expanded = jsonld.expand(
                    {
                        "@context": new_data["@context"],
                        **new_data["metadata"],
                    },
                )
                metadata = jsonld.compact(expanded, ctx)
                metadata.pop("@context")
            else:
                metadata = new_data["metadata"]
        else:
            object_type = "@openBIS.Object"
            MAPPING[ontology] = object_type
            CONTEXT[ontology] = {"@context": new_data["@context"]}
            metadata = new_data["metadata"]

        object_id = IDS[object_type]
        object_id["counter"] += 1

        new_data = {
            "id": f"{object_id['prefix']}-{object_id['counter']}",
            "type": object_type,
            "title": new_data["title"],
            "metadata": metadata,
            "ontology": ontology,
        }

        DATA.append(new_data)

        return jsonify({"message": "Data imported successfully."}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


def _contextualize(item):
    return {**CONTEXT.get(item["ontology"], {}), **item}


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


@app.route("/receive", methods=["POST"])
def receive_data():
    data = request.json
    print("Data received:", data)
    return jsonify({"message": "Data received successfully", "yourData": data}), 200


@app.route("/receive_zip", methods=["POST"])
def receive_zip():
    print(request.files["file"])
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files["file"]
    print(file.filename)
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    if file and file.filename.endswith(".zip"):
        try:
            # Make sure to get the correct file stream
            # `file.stream` might not work properly directly, so use BytesIO
            byte_stream = io.BytesIO(
                file.read()
            )  # Read the file stream into a BytesIO buffer

            # Now use the BytesIO object with zipfile
            zip_file = zipfile.ZipFile(byte_stream, "r")
            print(
                zip_file.namelist()
            )  # List contents of the zip to confirm successful opening

            with zip_file.open("ro-crate-metadata.json") as f:
                data = f.read()
                print(json.loads(data))

            # Assuming there's a specific file you want to read from the zip
            with zip_file.open("query.json") as f:
                print(type(f))
                data = f.read()
                print(json.loads(data))  # Output the contents of the data.json file
                json_data = json.loads(data)
                _id = json_data["id"]
                [*filter(lambda d: d["id"] == _id, DATA)][0].update(json_data)
                # OPENBIS_DATA.append(json_data)

            return jsonify({"message": "Zip file processed successfully"}), 200
        except zipfile.BadZipFile:
            return jsonify({"message": "Invalid zip file"}), 400
    else:
        return jsonify({"message": "Unsupported file type"}), 400


if __name__ == "__main__":
    app.run(port=PORT, debug=True)
