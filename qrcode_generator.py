import qrcode
import os


def generate_qr_code(certificate_id):

    os.makedirs("qrcodes", exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )

    verification_url = f"http://127.0.0.1:5000/verify?id={certificate_id}"

    qr.add_data(verification_url)

    qr.make(fit=True)

    image = qr.make_image(fill_color="black",
                          back_color="white")

    filename = f"{certificate_id}.png"

    save_path = os.path.join("qrcodes", filename)

    image.save(save_path)

    return filename