import requests
import os
from io import BytesIO
from PIL import Image

API_URL = "http://127.0.0.1:8000/api"

def create_dummy_image():
    img = Image.new('RGB', (224, 224), color = (73, 109, 137))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_api():
    print("Testing /api/upload ...")
    session = requests.Session()
    files = [
        ('files', ('test1.jpg', create_dummy_image(), 'image/jpeg')),
        ('files', ('test2.jpg', create_dummy_image(), 'image/jpeg')),
    ]
    
    response = session.post(f"{API_URL}/upload", files=files)
    if response.status_code == 200:
        print("UPLOAD SUCCESS")
        print(response.json())
    else:
        print(f"UPLOAD FAILED: {response.status_code}")
        print(response.text)
        return
        
    print("\nTesting /api/download-report ...")
    report_res = session.get(f"{API_URL}/download-report")
    if report_res.status_code == 200:
        print(f"REPORT DOWNLOAD SUCCESS: {len(report_res.content)} bytes received")
        with open("test_report.xlsx", "wb") as f:
            f.write(report_res.content)
    else:
        print(f"REPORT DOWNLOAD FAILED: {report_res.status_code}")
        print(report_res.text)

if __name__ == '__main__':
    test_api()
