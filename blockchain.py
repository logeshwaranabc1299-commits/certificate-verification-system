import hashlib
import json


def generate_file_hash(file_path):
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as certificate_file:
        while True:
            file_data = certificate_file.read(4096)

            if not file_data:
                break

            sha256_hash.update(file_data)

    return sha256_hash.hexdigest()


def generate_block_hash(
    certificate_id,
    student_name,
    register_number,
    course,
    institution,
    issue_date,
    certificate_hash,
    previous_hash,
    timestamp
):
    block_data = {
        "certificate_id": certificate_id,
        "student_name": student_name,
        "register_number": register_number,
        "course": course,
        "institution": institution,
        "issue_date": issue_date,
        "certificate_hash": certificate_hash,
        "previous_hash": previous_hash,
        "timestamp": timestamp
    }

    block_string = json.dumps(
        block_data,
        sort_keys=True
    ).encode()

    return hashlib.sha256(block_string).hexdigest()