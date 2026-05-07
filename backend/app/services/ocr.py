import cv2
import numpy as np
import pytesseract
from PIL import Image
import io

def preprocess_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    np_img = np.array(image)
    processed = cv2.threshold(np_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return processed

def extract_text_from_image(image_bytes):
    processed_img = preprocess_image(image_bytes)
    return pytesseract.image_to_string(processed_img)
