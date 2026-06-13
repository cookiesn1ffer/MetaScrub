"""MetaScrub - metadata scrubbing web app."""

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

import config
from db import logger
from scrubber import core

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.CLEANED_FOLDER, exist_ok=True)

logger.init_db(config.DB_PATH)


def _allowed_file(filename):
    ext = core.get_extension(filename)
    return ext != "" and ext in config.ALLOWED_EXTENSIONS


def _safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _build_download_name(original_name, ext):
    if "." in original_name:
        stem = original_name.rsplit(".", 1)[0]
    else:
        stem = original_name
    return f"{stem}_cleaned.{ext}"


def _job_to_status_payload(job):
    return {
        "status": job["status"],
        "original_name": job["original_name"],
        "file_type": job["file_type"],
        "stripped_fields": json.loads(job["stripped_fields"]),
        "timestamp": job["timestamp"],
        "error": job["error"],
    }


@app.route("/")
def index():
    return render_template("index.html", audience=config.AUDIENCE)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    original_name = file.filename

    if not _allowed_file(original_name):
        ext = core.get_extension(original_name) or "(none)"
        return (
            jsonify(
                {
                    "error": f"Unsupported file type: .{ext}",
                    "allowed_extensions": sorted(config.ALLOWED_EXTENSIONS),
                }
            ),
            415,
        )

    ext = core.get_extension(original_name)
    job_id = uuid.uuid4().hex
    input_path = os.path.join(config.UPLOAD_FOLDER, f"{job_id}_input.{ext}")
    output_path = os.path.join(config.CLEANED_FOLDER, f"{job_id}_cleaned.{ext}")
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        file.save(input_path)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Failed to save uploaded file: {exc}"}), 500

    file_type = core.get_file_type(original_name)
    logger.create_job(config.DB_PATH, job_id, original_name, file_type, timestamp)

    try:
        detected_type, stripped_fields = core.scrub_file(input_path, output_path, original_name)
    except ValueError as exc:
        logger.update_job_error(config.DB_PATH, job_id, str(exc))
        _safe_remove(input_path)
        _safe_remove(output_path)
        return jsonify({"error": f"Corrupt or unprocessable file: {exc}", "job_id": job_id}), 422
    except Exception as exc:  # noqa: BLE001
        logger.update_job_error(config.DB_PATH, job_id, str(exc))
        _safe_remove(input_path)
        _safe_remove(output_path)
        return jsonify({"error": f"Failed to process file: {exc}", "job_id": job_id}), 422

    logger.update_job_success(
        config.DB_PATH, job_id, stripped_fields, os.path.basename(output_path)
    )

    # Input is no longer needed once the cleaned copy exists.
    _safe_remove(input_path)

    return (
        jsonify(
            {
                "job_id": job_id,
                "status": "completed",
                "original_name": original_name,
                "file_type": detected_type,
                "stripped_fields": stripped_fields,
                "download_url": f"/download/{job_id}",
                "timestamp": timestamp,
            }
        ),
        200,
    )


@app.route("/download/<job_id>")
def download(job_id):
    job = logger.get_job(config.DB_PATH, job_id)
    if not job or job["status"] != "completed" or not job["cleaned_filename"]:
        abort(404, description="File not found")

    cleaned_path = os.path.join(config.CLEANED_FOLDER, job["cleaned_filename"])
    if not os.path.exists(cleaned_path):
        abort(404, description="File no longer available")

    ext = core.get_extension(job["cleaned_filename"])
    download_name = _build_download_name(job["original_name"], ext)

    return send_from_directory(
        config.CLEANED_FOLDER,
        job["cleaned_filename"],
        as_attachment=True,
        download_name=download_name,
    )


@app.route("/status/<job_id>")
def status(job_id):
    job = logger.get_job(config.DB_PATH, job_id)
    if not job:
        abort(404, description="Job not found")

    return jsonify(_job_to_status_payload(job))


@app.route("/history")
def history():
    jobs = logger.get_history(config.DB_PATH, limit=50)
    result = []
    for job in jobs:
        stripped = json.loads(job["stripped_fields"])
        result.append(
            {
                "job_id": job["job_id"],
                "original_name": job["original_name"],
                "file_type": job["file_type"],
                "status": job["status"],
                "stripped_count": len(stripped),
                "timestamp": job["timestamp"],
            }
        )
    return jsonify(result)


@app.route("/job/<job_id>", methods=["DELETE"])
def delete_job(job_id):
    job = logger.get_job(config.DB_PATH, job_id)
    if not job:
        abort(404, description="Job not found")

    if job["cleaned_filename"]:
        _safe_remove(os.path.join(config.CLEANED_FOLDER, job["cleaned_filename"]))

    ext = core.get_extension(job["original_name"])
    if ext:
        _safe_remove(os.path.join(config.UPLOAD_FOLDER, f"{job_id}_input.{ext}"))

    logger.delete_job(config.DB_PATH, job_id)

    return jsonify({"status": "deleted", "job_id": job_id})


@app.errorhandler(404)
def handle_not_found(err):
    return jsonify({"error": err.description or "Not found"}), 404


@app.errorhandler(413)
def handle_too_large(err):
    max_mb = config.MAX_FILE_SIZE // (1024 * 1024)
    return jsonify({"error": f"File too large. Maximum size is {max_mb}MB"}), 413


@app.errorhandler(415)
def handle_unsupported(err):
    return jsonify({"error": err.description or "Unsupported file type"}), 415


@app.errorhandler(500)
def handle_server_error(err):
    return jsonify({"error": "Internal server error"}), 500


def _cleanup_loop():
    """Background janitor: delete files older than AUTO_DELETE_AFTER_SECONDS."""
    while True:
        now = time.time()
        for folder in (config.UPLOAD_FOLDER, config.CLEANED_FOLDER):
            try:
                entries = os.listdir(folder)
            except OSError:
                continue
            for name in entries:
                path = os.path.join(folder, name)
                try:
                    if os.path.isfile(path) and now - os.path.getmtime(path) > config.AUTO_DELETE_AFTER_SECONDS:
                        os.remove(path)
                except OSError:
                    pass
        time.sleep(config.CLEANUP_INTERVAL_SECONDS)


def _start_cleanup_thread():
    thread = threading.Thread(target=_cleanup_loop, daemon=True)
    thread.start()


_start_cleanup_thread()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
