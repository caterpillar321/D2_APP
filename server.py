from flask import Flask, request, jsonify, send_file, abort
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil
import subprocess

app = Flask(__name__)

BASE_DIR = os.path.abspath("data")
TEMP_DIR = os.path.abspath("temp")


@app.route("/download/", defaults={"subpath": ""}, methods=["GET"])
@app.route("/download/<path:subpath>", methods=["GET"])
def download_file(subpath):
    file_path = os.path.join(BASE_DIR, subpath)
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404, description="File not found.")


@app.route("/downloadThumb/", defaults={"subpath": ""}, methods=["GET"])
@app.route("/downloadThumb/<path:subpath>", methods=["GET"])
def download_thumb(subpath):
    file_path = os.path.join(TEMP_DIR, subpath)
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404, description="File not found.")


@app.route("/upload/", defaults={"subpath": ""}, methods=["POST"])
@app.route("/upload/<path:subpath>", methods=["POST"])
def upload_file(subpath):
    if 'file' not in request.files:
        abort(400, description="File not found.")
    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        abort(400, description="Empty file name.")
    save_path = os.path.abspath(os.path.join(BASE_DIR, subpath))

    if not save_path.startswith(BASE_DIR):
        abort(403, description="Forbidden.")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    uploaded_file.save(save_path)

    return f"File saved successfully: {save_path}", 201


@app.route("/uploadThumb/", defaults={"subpath": ""}, methods=["POST"])
@app.route("/uploadThumb/<path:subpath>", methods=["POST"])
def upload_thumb(subpath):
    if 'file' not in request.files:
        abort(400, description="File not found.")
    uploaded_file = request.files['file']
    
    if uploaded_file.filename == '':
        abort(400, description="Empty file name.")
    save_path = os.path.abspath(os.path.join(TEMP_DIR, subpath))

    if not save_path.startswith(TEMP_DIR):
        abort(403, description="Forbidden.")   
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    uploaded_file.save(save_path)

    return f"Thumbnail saved successfully: {save_path}", 201


@app.route("/mkdir/", defaults={"subpath": ""}, methods=["POST"])
@app.route("/mkdir/<path:subpath>", methods=["POST"])
def make_directory(subpath):
    target_dir = os.path.abspath(os.path.join(BASE_DIR, subpath))
    if not target_dir.startswith(BASE_DIR):
        abort(403, description="Forbidden.")
    try:
        os.makedirs(target_dir, exist_ok=True)
        return jsonify({
            "status": "success",
            "message": f"Directory is created: {subpath}"
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error on creating Directory: {str(e)}"
        }), 500


@app.route("/list/", defaults={"subpath": ""}, methods=["GET"], strict_slashes=False)
@app.route("/list/<path:subpath>", methods=["GET"])
def list_directory(subpath):
    target_dir = os.path.abspath(os.path.join(BASE_DIR, subpath))
    if not target_dir.startswith(BASE_DIR):
        abort(403, description="Forbidden.")
    if not os.path.isdir(target_dir):
        abort(404, description="Directory not found.")

    contents = []
    for name in os.listdir(target_dir):
        full_path = os.path.join(target_dir, name)
        item_type = "directory" if os.path.isdir(full_path) else "file"
        size = os.path.getsize(full_path) if item_type == "file" else None
        modified_time = os.path.getmtime(full_path)
        contents.append({
            "name": name,
            "type": item_type,
            "size": size, 
            "modified": datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(contents)


@app.route("/delete/", defaults={"subpath": ""}, methods=["DELETE"])
@app.route("/delete/<path:subpath>", methods=["DELETE"])
def delete_path(subpath):
    target_path = os.path.abspath(os.path.join(BASE_DIR, subpath))
    if not target_path.startswith(BASE_DIR):
        abort(403, description="Forbidden.")

    if os.path.isfile(target_path):
        os.remove(target_path)
        return jsonify({"status": "success", "message": f"File delete completed: {subpath}"})
    elif os.path.isdir(target_path):
        shutil.rmtree(target_path)
        return jsonify({"status": "success", "message": f"File and Directory delete completed: {subpath}"})
    else:
        abort(404, description="File or Directory not found.")


@app.route("/deleteThumb/", defaults={"subpath": ""}, methods=["DELETE"])
@app.route("/deleteThumb/<path:subpath>", methods=["DELETE"])
def delete_thumb(subpath):
    target_path = os.path.abspath(os.path.join(TEMP_DIR, subpath))
    if not target_path.startswith(TEMP_DIR):
        abort(403, description="Forbidden.")

    if os.path.isfile(target_path):
        os.remove(target_path)
        return jsonify({"status": "success", "message": f"Thumbnail delete completed: {subpath}"})
    else:
        abort(404, description="File not found.")

@app.route("/set_time", methods=["POST"])
def set_time():
    data = request.json
    try:
        date_string = f"{data['month']:02}{data['day']:02}{data['hour']:02}{data['minute']:02}{data['year']}.{data['second']:02}"
        subprocess.run(["sudo", "date", date_string], check=True)
        #subprocess.run(["sudo", "hwclock", "--systohc"], check=True)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

FILE_PATH = 'password.txt'

@app.route('/password', methods=['POST'])
def password_check():
    try:
        data = request.get_json()
        received_text = data.get('text')
        if received_text is None:
            return jsonify({'response': 'Invalid request: No text field'}), 400

        with open(FILE_PATH, 'r', encoding='utf-8') as file:
            expected_text = file.read().strip()

        if received_text == expected_text:
            result = "Pass"
        else:
            result = "Fail"

        return jsonify({'response': result})

    except FileNotFoundError:
        return jsonify({'response': 'Error: 기준 파일이 없습니다.'}), 500
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
