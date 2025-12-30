# import cv2
# import easyocr
# import re
#
#
# class PlateReader:
#     def __init__(self):
#         # Initialize EasyOCR for English. valid_ids helps filter garbage text.
#         print("⏳ Loading OCR Model... (This might take a moment)")
#         self.reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have CUDA
#
#     def read_plate(self, frame, x1, y1, x2, y2):
#         """
#         Crops the vehicle area and attempts to read the text.
#         """
#         # 1. Crop the vehicle from the frame
#         # Adding a small margin can help OCR
#         h, w, _ = frame.shape
#         crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
#
#         # 2. Convert to grayscale for better OCR
#         gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
#
#         # 3. Read Text
#         results = self.reader.readtext(gray)
#
#         # 4. Process results to find the best match
#         detected_text = ""
#         for (bbox, text, prob) in results:
#             # Filter: Keep only alphanumeric, remove spaces
#             clean_text = re.sub(r'[^A-Za-z0-9]', '', text).upper()
#
#             # Heuristic: License plates usually have 4+ characters
#             if len(clean_text) > 4 and prob > 0.4:
#                 detected_text = clean_text
#                 break  # Return the first strong match
#
#         return detected_text
import cv2
import requests
import json


class PlateReader:
    def __init__(self):
        # 🔑 PASTE YOUR TOKEN BELOW
        self.api_key = "a718f7b21b6c4fe431ecee5551b4643556fc142c"

        self.api_url = 'https://api.platerecognizer.com/v1/plate-reader/'
        self.regions = ['in']  # 'in' = India. Change to 'us', 'eu', etc. if needed.
        print("☁️ Cloud OCR Ready. (Requires Internet)")

    def read_plate(self, frame, x1, y1, x2, y2):
        """
        Sends the cropped vehicle image to the Cloud API for recognition.
        """
        h, w, _ = frame.shape

        # 1. Crop the vehicle image
        # Adding a small margin helps the AI see the context
        crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

        # 2. Save it locally temporarily (API requires a file)
        temp_filename = "temp_plate.jpg"
        cv2.imwrite(temp_filename, crop)

        detected_plate = None

        try:
            # 3. Send to Cloud API
            with open(temp_filename, 'rb') as fp:
                response = requests.post(
                    self.api_url,
                    data=dict(regions=self.regions),
                    files=dict(upload=fp),
                    headers={'Authorization': f'Token {self.api_key}'}
                )

            # 4. Parse Response
            data = response.json()

            # Check if any plate was found
            if 'results' in data and len(data['results']) > 0:
                # Get the top result
                plate_data = data['results'][0]
                detected_plate = plate_data['plate'].upper()  # e.g. "DL8CAF5030"
                confidence = plate_data['score']

                print(f"✅ Cloud OCR: {detected_plate} (Conf: {confidence})")
            else:
                print("❌ Cloud OCR: No plate text found.")

        except Exception as e:
            print(f"⚠️ API Error: {e}")
            # Common error: No internet, or Invalid Token

        return detected_plate