from PIL import Image, ImageDraw, ImageFont
import os

def create_digital_signature(output_path):
    # Create a white background image
    img = Image.new('RGB', (200, 100), 'white')
    draw = ImageDraw.Draw(img)
    
    # Load a font (you might need to adjust the path based on your system)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Draw the signature
    draw.text((10, 10), "Digital Signature", fill="black", font=font)
    draw.text((10, 40), "Government of India", fill="black", font=font)
    
    # Save the image
    img.save(output_path)

if __name__ == "__main__":
    signature_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'digital-signature.png')
    create_digital_signature(signature_path)
