import os
import urllib.parse
import requests
import webbrowser
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID') or input("Enter your Spotify Client ID: ").strip()
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET') or input("Enter your Spotify Client Secret: ").strip()

# We use example.com because it is a static site that won't strip our query parameters (like Google did!)
REDIRECT_URI = 'https://example.com/callback'
SCOPES = 'user-read-recently-played user-top-read playlist-read-private'

def get_refresh_token():
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES
    })
    
    print("\n" + "*"*80)
    print("STEP 1: We are opening Spotify in your browser.")
    print("STEP 2: Click 'Agree'.")
    print("STEP 3: You will be redirected to example.com.")
    print("STEP 4: Copy the ENTIRE URL from the address bar (it will look like https://example.com/callback?code=...)")
    print("*"*80 + "\n")
    
    webbrowser.open(auth_url)
    
    redirected_url = input("Paste the full example.com URL here: ").strip()
    
    try:
        query = urllib.parse.urlparse(redirected_url).query
        params = urllib.parse.parse_qs(query)
        code = params['code'][0]
    except Exception as e:
        print("\nError extracting the code. Make sure the URL has '?code=...' in it.")
        return

    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    res = requests.post(token_url, data=data)
    res_data = res.json()
    
    if 'refresh_token' in res_data:
        print("\n" + "="*70)
        print("SUCCESS! YOUR REFRESH TOKEN IS:")
        print(res_data['refresh_token'])
        print("="*70 + "\n")
    else:
        print("\nFailed to get token:", res_data)

if __name__ == "__main__":
    get_refresh_token()
