import os
import sqlite3
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

from werkzeug.utils import secure_filename

from blockchain import generate_file_hash
from qrcode_generator import generate_qr_code

from database import (
    create_tables,
    insert_certificate,
    get_certificate_by_id,
    get_all_certificates,
    verify_blockchain_integrity,
    search_certificates,
    delete_certificate
)


app = Flask(__name__)

app.secret_key = "certificate_secret_key"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
QRCODE_FOLDER = os.path.join(BASE_DIR, "qrcodes")

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["QRCODE_FOLDER"] = QRCODE_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QRCODE_FOLDER, exist_ok=True)

create_tables()


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == "admin" and password == "admin123":
            session["admin"] = username
            return redirect(url_for("dashboard"))

        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


@app.route("/upload", methods=["GET", "POST"])
def upload_certificate():
    if "admin" not in session:
        return redirect(url_for("login"))

    message = None
    error = None

    if request.method == "POST":
        certificate_id = request.form.get(
            "certificate_id", ""
        ).strip()

        student_name = request.form.get(
            "student_name", ""
        ).strip()

        register_number = request.form.get(
            "register_number", ""
        ).strip()

        course = request.form.get(
            "course", ""
        ).strip()

        institution = request.form.get(
            "institution", ""
        ).strip()

        issue_date = request.form.get(
            "issue_date", ""
        ).strip()

        certificate_file = request.files.get(
            "certificate_file"
        )

        if not all(
            [
                certificate_id,
                student_name,
                register_number,
                course,
                institution,
                issue_date
            ]
        ):
            error = "Please complete all certificate details."

        elif (
            certificate_file is None
            or certificate_file.filename == ""
        ):
            error = "Please select a certificate file."

        elif not allowed_file(certificate_file.filename):
            error = (
                "Only PDF, PNG, JPG and JPEG files are allowed."
            )

        else:
            safe_filename = secure_filename(
                certificate_file.filename
            )

            stored_filename = (
                f"{certificate_id}_{safe_filename}"
            )

            file_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                stored_filename
            )

            qr_filename = None

            try:
                certificate_file.save(file_path)

                certificate_hash = generate_file_hash(
                    file_path
                )

                qr_filename = generate_qr_code(
                    certificate_id
                )

                insert_certificate(
                    certificate_id,
                    student_name,
                    register_number,
                    course,
                    institution,
                    issue_date,
                    stored_filename,
                    qr_filename,
                    certificate_hash
                )

                message = (
                    "Certificate issued and stored successfully."
                )

            except sqlite3.IntegrityError:
                if os.path.exists(file_path):
                    os.remove(file_path)

                if qr_filename:
                    qr_path = os.path.join(
                        app.config["QRCODE_FOLDER"],
                        qr_filename
                    )

                    if os.path.exists(qr_path):
                        os.remove(qr_path)

                error = "Certificate ID already exists."

            except Exception as exc:
                if os.path.exists(file_path):
                    os.remove(file_path)

                if qr_filename:
                    qr_path = os.path.join(
                        app.config["QRCODE_FOLDER"],
                        qr_filename
                    )

                    if os.path.exists(qr_path):
                        os.remove(qr_path)

                error = f"Unable to issue certificate: {exc}"

    return render_template(
        "upload.html",
        message=message,
        error=error
    )


@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        certificate_id = request.form.get(
            "certificate_id", ""
        ).strip()

        uploaded_file = request.files.get(
            "certificate_file"
        )

        if not certificate_id:
            return render_template(
                "result.html",
                status="error",
                message="Please enter a certificate ID."
            )

        certificate = get_certificate_by_id(
            certificate_id
        )

        if certificate is None:
            return render_template(
                "result.html",
                status="invalid",
                message="Certificate record not found."
            )

        if (
            uploaded_file is None
            or uploaded_file.filename == ""
        ):
            return render_template(
                "result.html",
                status="error",
                message="Please upload a certificate file."
            )

        if not allowed_file(uploaded_file.filename):
            return render_template(
                "result.html",
                status="error",
                message=(
                    "Only PDF, PNG, JPG and JPEG "
                    "files are allowed."
                )
            )

        safe_filename = secure_filename(
            uploaded_file.filename
        )

        unique_name = (
            f"temporary_{uuid.uuid4().hex}_{safe_filename}"
        )

        temporary_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            unique_name
        )

        try:
            uploaded_file.save(temporary_path)

            uploaded_hash = generate_file_hash(
                temporary_path
            )

        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

        if uploaded_hash == certificate["certificate_hash"]:
            return render_template(
                "result.html",
                status="valid",
                message="Certificate verified successfully.",
                certificate=certificate
            )

        return render_template(
            "result.html",
            status="invalid",
            message=(
                "Certificate is modified, fake or "
                "does not match the stored record."
            )
        )

    certificate_id = request.args.get("id", "")

    return render_template(
        "verify.html",
        certificate_id=certificate_id
    )


@app.route("/blockchain")
def blockchain_records():
    if "admin" not in session:
        return redirect(url_for("login"))

    certificates = get_all_certificates()
    chain_valid = verify_blockchain_integrity()

    return render_template(
        "blockchain.html",
        certificates=certificates,
        chain_valid=chain_valid
    )


@app.route("/certificates")

def certificate_list():

    if "admin" not in session:

        return redirect(url_for("login"))

    search=request.args.get("search","")

    if search:

        certificates=search_certificates(search)

    else:

        certificates=get_all_certificates()

    return render_template(

    "certificates.html",

    certificates=certificates,

    search=search

    )


@app.route("/delete/<certificate_id>", methods=["POST"])
def delete_certificate_record(certificate_id):

    if "admin" not in session:
        return redirect(url_for("login"))

    certificate = get_certificate_by_id(certificate_id)

    if certificate:

        # Delete uploaded certificate
        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            certificate["file_name"]
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete QR code image
        qr_path = os.path.join(
            app.config["QRCODE_FOLDER"],
            certificate["qr_code"]
        )

        if os.path.exists(qr_path):
            os.remove(qr_path)

        # Delete database record
        delete_certificate(certificate_id)

    return redirect(url_for("certificate_list"))


@app.route("/qrcode/<path:filename>")
def get_qrcode(filename):
    return send_from_directory(
        app.config["QRCODE_FOLDER"],
        filename
    )
@app.route("/download/<certificate_id>")
def download_certificate(certificate_id):

    certificate = get_certificate_by_id(certificate_id)

    if certificate is None:
        return "Certificate not found"

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        certificate["file_name"],
        as_attachment=True
    )

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)