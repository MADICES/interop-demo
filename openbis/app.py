import json
import os
import shutil
import tempfile
import zipfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import jinja2
import requests
from data import CONTEXT, DATA, IDS, KEY_MAPPING, OBJECT_MAPPING, PLATFORMS
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

app.config["RO_CRATE_FOLDER"] = "temp_uploads/"
app.config["RO_CRATE_FOLDER"] = "ro_crates/"
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
ORIGINAL_OBJECT_MAPPING = deepcopy(OBJECT_MAPPING)
ORIGINAL_KEY_MAPPING = deepcopy(KEY_MAPPING)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/shared/<path:path>")
def serve_shared_content(path):
    file = Path(app.config["SHARED_PATH"]) / path
    return send_file(file)


@app.route("/crates")
def get_crates():
    return jsonify(
        [crate.name for crate in Path(app.config["RO_CRATE_FOLDER"]).iterdir()]
    )


@app.route("/crate", methods=["GET"])
def get_crate_content():
    name = request.args.get("name")
    path = Path(app.config["RO_CRATE_FOLDER"]) / name
    crate = ROCrate(path)
    return jsonify(crate.metadata.generate())


@app.route("/platforms", methods=["GET"])
def get_platforms():
    return jsonify(PLATFORMS)


@app.route("/data", methods=["GET"])
def get_data():
    return jsonify([_contextualize(item) for item in DATA])


@app.route("/data/filter", methods=["GET"])
def filter_data():
    return jsonify(
        [
            _contextualize(item)
            for item in DATA
            if item["type"].lower() == filter_type.lower()
        ]
    ) if (
        filter_type := request.args.get("type")
    ) else "Type parameter is required for filtering.", 400


@app.route("/data/reset", methods=["GET"])
def reset_data():
    global DATA, IDS, OBJECT_MAPPING, KEY_MAPPING
    DATA = deepcopy(ORIGINAL_DATA)
    IDS = deepcopy(ORIGINAL_IDS)
    OBJECT_MAPPING = deepcopy(ORIGINAL_OBJECT_MAPPING)
    KEY_MAPPING = deepcopy(ORIGINAL_KEY_MAPPING)
    shutil.rmtree(app.config["RO_CRATE_FOLDER"])
    Path(app.config["RO_CRATE_FOLDER"]).mkdir()
    return jsonify({"message": "Data reset successfully."}), 200


@app.route("/data/types", methods=["GET"])
def get_types():
    types = list(OBJECT_MAPPING.keys())
    temp_dir = Path(app.config["RO_CRATE_FOLDER"])
    crate = ROCrate()
    content = json.dumps(types, indent=4)
    file = BytesIO(content.encode())
    filename = "ontologies"
    crate.add_file(
        file,
        f"./{filename}.json",
        properties={
            "@type": "RESPONSE",
        },
    )
    crate_dir = temp_dir / filename
    crate.write_zip(crate_dir)
    zipped_crate_path = crate_dir.with_suffix(".zip")
    return send_file(
        zipped_crate_path,
        as_attachment=True,
        download_name=zipped_crate_path.name,
    )


@app.route("/data/ontology", methods=["GET"])
def get_objects_by_ontological_type():
    if not (ontology := request.args.get("type")):
        return "Missing ontological type.", 400
    objects = [
        _contextualize(item)
        for item in DATA
        if item["ontology"].lower() == ontology.lower()
    ]
    temp_dir = Path(app.config["RO_CRATE_FOLDER"])
    crate = ROCrate()
    content = json.dumps(objects, indent=4)
    file = BytesIO(content.encode())
    filename = "objects"
    crate.add_file(
        file,
        f"./{filename}.json",
        properties={
            "@type": "RESPONSE",
        },
    )
    crate_dir = temp_dir / filename
    crate.write_zip(crate_dir)
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
        metadata["wasImported"] = {  # type: ignore
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


@app.route("/data/export", methods=["POST"])
def export_data():
    port = request.args.get("port")
    object_id = request.json
    sample = next(
        (_contextualize(item) for item in DATA if item["id"] == object_id),
        None,
    )
    temp_dir = Path(app.config["RO_CRATE_FOLDER"])
    temp_dir.mkdir(exist_ok=True)
    crate = ROCrate()
    content = json.dumps(sample, indent=4)
    file = BytesIO(content.encode())
    filename = f"{object_id.lower()}.json"
    crate.add_file(
        file,
        f"./{filename}",
        properties={
            "@type": "EXPORT",
        },
    )
    crate_dir = temp_dir / "export"
    crate.write_zip(crate_dir)
    with crate_dir.with_suffix(".zip").open("rb") as file:
        filename = crate_dir.with_suffix(".zip").name
        response = requests.post(
            f"http://localhost:{port}/receive_zip?port={PORT}",
            files={"file": (filename, file, "application/zip")},
        )
    if response.status_code == 200:
        return jsonify(
            {
                "message": "Data sent to openBIS successfully",
                "responseFromOpenBIS": response.json(),
            }
        ), 200
    else:
        return jsonify({"message": "Failed to send data to openBIS"}), 500


@app.route("/receive_zip", methods=["POST"])
def receive_zip():
    if "file" not in request.files or not (file := request.files["file"]):
        return jsonify({"message": "Missing file"}), 400
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400
    if file.filename.endswith(".zip"):
        try:
            byte_stream = BytesIO(file.read())
            zip_file = zipfile.ZipFile(byte_stream, "r")
            if "ro-crate-metadata.json" not in zip_file.namelist():
                return jsonify({"message": "Missing crate manifest"}), 400
            if not (filename := _get_export_filename_from_crate(zip_file)):
                return jsonify({"message": "Missing export file"}), 400
            with zip_file.open(filename) as export_file:
                data: dict = json.load(export_file)
            object_type, metadata = _transform_against_context(data)
            if metadata.get("wasImported", {}).get("from") == PORT:
                local_id = metadata["wasImported"]["with_id"]  # type: ignore
                local_object: dict = next(
                    filter(lambda item: item["id"] == local_id, DATA),
                    None,
                )
                if not local_object:
                    return jsonify(
                        {"message": "The item was not found in the local database."}
                    ), 404
                metadata.pop("wasImported")
                local_object["metadata"].update(metadata)
            else:
                port = request.args.get("port")
                metadata["wasImported"] = {  # type: ignore
                    "from": int(port),
                    "with_id": data["id"],
                }
                object_id = IDS[object_type]
                object_id["counter"] += 1
                new_data = {
                    "id": f"{object_id['prefix']}-{object_id['counter']}",
                    "type": object_type,
                    "title": data["title"],
                    "metadata": metadata,
                    "ontology": data["ontology"],
                }
                DATA.append(new_data)
            return jsonify({"message": "Zip file processed successfully"}), 200
        except zipfile.BadZipFile:
            return jsonify({"message": "Invalid zip file"}), 400
    else:
        return jsonify({"message": "Unsupported file type"}), 400


def _contextualize(item):
    return {**CONTEXT.get(item["ontology"], {}), **item}


def _transform_against_context(data):
    ontology = data["ontology"]
    if context := CONTEXT.get(ontology, {}):
        object_type = OBJECT_MAPPING[ontology]
        if ctx := context.get("@context", {}):
            metadata = _translate(data, ctx)
        else:
            metadata = data["metadata"]
    else:
        object_type = "@openBIS.Object"
        OBJECT_MAPPING[ontology] = object_type
        new_context = {}
        for field, properties in data["@context"].items():
            if (iri := properties["@id"]) in KEY_MAPPING:
                field = KEY_MAPPING[iri]
            else:
                KEY_MAPPING[iri] = field
            new_context[field] = properties
        CONTEXT[ontology] = {"@context": new_context}
        metadata = _translate(data, new_context)
    return object_type, metadata


def _translate(data, ctx):
    expanded = jsonld.expand(
        {
            "@context": data["@context"],
            **data["metadata"],
        },
    )
    metadata = jsonld.compact(expanded, ctx)
    metadata.pop("@context")
    return metadata


def _get_export_filename_from_crate(zip_file: zipfile.ZipFile):
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_file.extractall(temp_dir)
        return next(
            (
                entity.id
                for entity in ROCrate(temp_dir).data_entities
                if entity.type == "EXPORT"
            ),
            None,
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


@app.route("/receive", methods=["POST"])
def receive_data():
    data = request.json
    print("Data received:", data)
    return jsonify({"message": "Data received successfully", "yourData": data}), 200


if __name__ == "__main__":
    app.run(port=PORT, debug=True)
