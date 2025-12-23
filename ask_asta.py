import requests
import time
import sys
import json

# --- CONFIGURATION ---
# Connects to your live API backend
API_URL = "https://asta-insights.onrender.com" 
# Use "http://127.0.0.1:8000" if testing locally before pushing

def type_writer(text, speed=0.015):
    """Effect to make text look like it's being generated live"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    print("\n")

def print_header():
    # Clear screen (works on Mac/Linux/Windows usually)
    print("\033c", end="")
    print("\033[96m" + "="*60)
    print("   🧠 ASTA INTELLIGENCE HUB (DEMO MODE)")
    print(f"   📡 Connecting to: {API_URL}")
    print("="*60 + "\033[0m")
    print("Type 'exit' to quit.\n")

def main():
    print_header()
    
    # 1. Health Check (Ping the API)
    try:
        print("\033[90m[System] Handshaking with Neural Core...\033[0m")
        start = time.time()
        requests.get(API_URL) # Wake up the server if sleeping
        ping = (time.time() - start) * 1000
        print(f"\033[92m[System] Online ({int(ping)}ms). Asta is listening.\033[0m\n")
    except Exception as e:
        print(f"\033[91m[Error] Could not reach API. Is it deployed? ({str(e)})\033[0m")
        return

    # 2. Chat Loop
    while True:
        try:
            # Get User Input
            user_input = input("\033[1mYou:\033[0m ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("\033[90mDisconnecting session...\033[0m")
                break
            
            if not user_input.strip():
                continue
            
            # Show "Thinking" animation
            sys.stdout.write("\033[93mAsta is analyzing live market data...\033[0m")
            sys.stdout.flush()
            
            # Call the /agent/chat Endpoint
            start_time = time.time()
            try:
                response = requests.post(
                    f"{API_URL}/agent/chat", 
                    json={"query": user_input},
                    timeout=30
                )
                
                # Clear the "Thinking..." line
                sys.stdout.write(f"\r\033[K") 
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "No response text.")
                    
                    # Print Header
                    duration = time.time() - start_time
                    print(f"\033[95mAsta ({duration:.1f}s):\033[0m")
                    
                    # Stream the text
                    type_writer(reply)
                else:
                    print(f"\033[91m[API Error] {response.status_code}: {response.text}\033[0m")

            except requests.exceptions.ConnectionError:
                print(f"\r\033[K\033[91m[Network Error] Could not connect to Asta.\033[0m")
                
        except KeyboardInterrupt:
            print("\n\033[90mSession terminated.\033[0m")
            break
        except Exception as e:
            print(f"\n\033[91m[System Error] {str(e)}\033[0m")

if __name__ == "__main__":
    main()
