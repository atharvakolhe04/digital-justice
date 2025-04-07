import qrcode
import os
from io import BytesIO
from PIL import Image
from flask import url_for

def generate_document_qr(verification_code, save_path=None):
    """
    Generate QR code for document verification
    
    Args:
        verification_code (str): Unique verification code for the document
        save_path (str, optional): Path to save the QR code image. If None, returns the image as BytesIO
        
    Returns:
        BytesIO or str: BytesIO object containing the QR code image or path where the image was saved
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Add verification URL to QR code
    # Use absolute URL with configurable base for mobile scanning
    base_url = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
    verification_url = f"{base_url}/verify-document/{verification_code}"
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    if save_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # Save the image
        img.save(save_path)
        return save_path
    else:
        # Return the image as BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

def generate_fine_qr(challan_number, save_path=None):
    """
    Generate QR code for fine/challan verification and payment
    
    Args:
        challan_number (str): Unique challan number
        save_path (str, optional): Path to save the QR code image. If None, returns the image as BytesIO
        
    Returns:
        BytesIO or str: BytesIO object containing the QR code image or path where the image was saved
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Add payment URL to QR code
    # Use absolute URL with configurable base for mobile scanning
    base_url = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
    payment_url = f"{base_url}/pay-fine/{challan_number}"
    qr.add_data(payment_url)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    if save_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # Save the image
        img.save(save_path)
        return save_path
    else:
        # Return the image as BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io
