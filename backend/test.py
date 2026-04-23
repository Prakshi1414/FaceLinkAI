import requests

url = "http://127.0.0.1:8000/register-face"

files = [
    ("files", ("img1.jpg", open("img1.jpg", "rb"), "image/jpeg")),
    ("files", ("img2.jpg", open("img2.jpg", "rb"), "image/jpeg")),
    ("files", ("img3.jpg", open("img3.jpg", "rb"), "image/jpeg")),
]

data = {
    "name": "prakshi"
}

response = requests.post(url, files=files, data=data)

print("Status Code:", response.status_code)
print("Response:", response.json())