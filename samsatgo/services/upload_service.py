from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename


def allowed_image(filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_uploaded_image(file_storage, folder_name):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image(file_storage.filename):
        raise ValueError("Format file harus PNG, JPG, JPEG, atau WEBP.")

    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    target_dir = upload_root / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[-1].lower()
    filename = f"{uuid4().hex}.{extension}"
    file_path = target_dir / filename
    file_storage.save(file_path)

    return f"uploads/{folder_name}/{filename}"

