import qrcode
import qrcode.image.svg

def makeqr(title):
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    qr.add_data(title)
    qr.make(fit=True)
    img = qr.make_image(attrib={'class': 'qrcodeclass'})
    return img.to_string(encoding='unicode')