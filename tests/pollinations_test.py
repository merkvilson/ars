import requests

prompt = "a futuristic city under the ocean, cinematic lighting"
response = requests.get(f"https://image.pollinations.ai/prompt/{prompt}")

with open("city.jpg", "wb") as f:
    f.write(response.content)
