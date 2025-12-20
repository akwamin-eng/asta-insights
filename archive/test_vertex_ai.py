# test_vertex_ai.py
import vertexai
from vertexai.generative_models import GenerativeModel

# Initialize Vertex AI for your project and region
PROJECT_ID = "certain-voyager-403707"
REGION = "us-central1"
print(f"Initializing Vertex AI for project '{PROJECT_ID}' in region '{REGION}'...")
vertexai.init(project=PROJECT_ID, location=REGION)

# Use the automatic alias for Gemini 1.0 Pro
MODEL_NAME = "gemini-1.0-pro"
print(f"Loading model using alias: '{MODEL_NAME}'...")
try:
    model = GenerativeModel(MODEL_NAME)
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    exit(1)

# Simple test prompt
prompt = "What is the capital of France?"

print(f"\nSending prompt to {MODEL_NAME}: '{prompt}'")
try:
    response = model.generate_content(prompt)
    print("✅ Request successful.")
    print(f"🤖 Model Response: {response.text.strip()}")
except Exception as e:
    print(f"❌ Request failed: {e}")
    # Print full traceback for detailed debugging if needed
    # import traceback
    # traceback.print_exc()

print("\n--- Test Complete ---")