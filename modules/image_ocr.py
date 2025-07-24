# core/input_handlers/image_ocr.py

from PIL import Image
import pytesseract
import os

# Optional: Set path to tesseract executable if not in PATH (Windows users)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path, lang='eng'):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return ""
    
if __name__ == "__main__":
    input_file = "image.png"
    output = extract_text_from_image(input_file)
    # print("Detected Language:", output["language_code"])
    print("Transcription:", output)
