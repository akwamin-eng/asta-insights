import requests
import json

# Configuration
# We will test against your LOCAL server first (run `uvicorn api.main:app` in another terminal)
API_URL = "http://127.0.0.1:8000/whatsapp/webhook"

def test_text_message():
    """Simulates a user sending a text message."""
    print("\n--- �� Testing Text Message ---")
    payload = {
        "From": "whatsapp:+1234567890",  # Fake User
        "Body": "Hello Asta, do you have any houses in Oyibi?",
        "NumMedia": "0"
    }
    
    try:
        # Send as form data (Twilio format)
        response = requests.post(API_URL, data=payload)
        print(f"✅ Status Code: {response.status_code}")
        print(f"📩 Response XML: {response.text[:200]}...") # Show first 200 chars
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("💡 Hint: Is your local server running?")

def test_image_message():
    """Simulates a user sending an image (via URL)."""
    print("\n--- 🧪 Testing Image Message ---")
    payload = {
        "From": "whatsapp:+1234567890",
        "Body": "",
        "NumMedia": "1",
        "MediaUrl0": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Building92.jpg/800px-Building92.jpg",
        "MediaContentType0": "image/jpeg"
    }
    
    try:
        response = requests.post(API_URL, data=payload)
        print(f"✅ Status Code: {response.status_code}")
        if response.status_code == 200:
            print("📸 Image processed successfully (mock).")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    print("🤖 Asta Phase 3: WhatsApp Simulator")
    user_input = input("Test (1) Text or (2) Image? [1/2]: ")
    
    if user_input == "1":
        test_text_message()
    elif user_input == "2":
        test_image_message()
    else:
        print("Invalid choice.")
