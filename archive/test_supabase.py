# test_supabase.py
from flask import Flask, jsonify
import os
from google.cloud import secretmanager
import requests

app = Flask(__name__)

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

@app.route('/test', methods=['GET'])
def test_supabase():
    try:
        supabase_url = get_secret("supabase-url")
        supabase_key = get_secret("supabase-key")
        
        # Log for debugging (will appear in Cloud Logs)
        print(f"URL repr: {repr(supabase_url)}")
        print(f"URL length: {len(supabase_url)}")

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        response = requests.get(
            f"{supabase_url}/rest/v1/asta_properties",
            headers=headers,
            params={"select": "id", "limit": "1"},
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "url_length": len(supabase_url),
                "url_repr": repr(supabase_url),
                "sample": response.json()[:1]
            })
        else:
            return jsonify({
                "status": "error",
                "code": response.status_code,
                "message": response.text
            }), 500
            
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))