# Platform-agnostic interoperability demo

A demonstration of the platform-agnostic interoperability principles and specifications in action

# Flask RO-Crate Application

This Python application is built using Flask to handle file uploads and work with RO-Crates, along with a simple data filtering and listing feature.

## Prerequisites

- Python 3.x
- Flask
- Flask-CORS
- ro-crate-py

## Installation

1. Clone the repository to your local machine or download the source code.

2. Navigate to the application directory.

3. Install the required Python packages using pip:
   ```bash
   pip install Flask Flask-CORS ro-crate-py
   ```

## Configuration

Before running the application, you can modify the `app.config` settings in `app.py`, to suit your environment:
- `UPLOAD_FOLDER`: Directory to store uploaded files.
- `RO_CRATE_FOLDER`: Directory to store generated RO-Crate files.
- `MAX_CONTENT_LENGTH`: Maximum allowed file size for uploads.

## Running the Application

To run each application, use the following command in two terminals:
```bash
python app.py
```
This will start the Flask server on defined port. (5001 and 5002)

## Usage

Once the application is running, you can access the following endpoints:

- **GET /**: Renders the main page from `templates/index.html`.
- **GET /data**: Returns all predefined data as JSON.
- **GET /data/filter?type=[type]**: Returns filtered data based on the 'type' query parameter.
- **POST /upload_rocrate**: Allows uploading a RO-Crate zip file, processes it, and returns its contents.
- **GET /data/types**: Generates and downloads a RO-Crate containing types of data.
- **POST /upload**: Allows uploading a file and saving its type.
- **GET /files**: Lists all files in the upload directory with their types.
- **GET /export**: Prepares and provides a RO-Crate for download based on uploaded files.
- **GET /download**: Downloads the prepared RO-Crate.


## Notes

Ensure that the directories specified in `UPLOAD_FOLDER` and `RO_CRATE_FOLDER` exist or are created by the application before uploading or exporting files.