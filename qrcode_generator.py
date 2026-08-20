import qrcode
import os


def generate_qr_code(admin_id, certificate_id):

    base_dir = os.path.abspath(
        os.path.dirname(__file__)
    )

    qr_folder = os.path.join(
        base_dir,
        "qrcodes"
    )

    os.makedirs(qr_folder, exist_ok=True)

    verification_url = (
        "https://certificate-verification-system-1-i3al.onrender.com"
        f"/certificate/{admin_id}/{certificate_id}"
    )

    print("QR URL:", verification_url)

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )

    qr.add_data(verification_url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    filename = f"{admin_id}_{certificate_id}.png"

    save_path = os.path.join(
        qr_folder,
        filename
    )

    image.save(save_path)

    return filename