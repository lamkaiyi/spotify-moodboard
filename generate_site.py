import os
import requests
import json
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REFRESH_TOKEN = os.environ.get('SPOTIFY_REFRESH_TOKEN')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')

def get_access_token():
    auth_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': SPOTIFY_REFRESH_TOKEN,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(auth_url, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def calculate_mood_from_genres(artist_ids, access_token):
    if not artist_ids:
        return {"dominant": "Unknown", "colors": ["#000", "#000"], "percentages": {}, "max_percentage": 0}
    
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        res = requests.get(f'https://api.spotify.com/v1/artists?ids={",".join(artist_ids)}', headers=headers, timeout=10)
        if res.status_code != 200:
            return {"dominant": "Unknown", "colors": ["#000", "#000"], "percentages": {}, "max_percentage": 0}
        
        artists = res.json().get('artists', [])
    except Exception as e:
        print(f"Error fetching artists: {e}")
        return {"dominant": "Unknown", "colors": ["#000", "#000"], "percentages": {}, "max_percentage": 0}

    mood_counts = {"Happy": 0, "Chill": 0, "Sad": 0, "Angry": 0}
    
    # Keyword matching for genres
    keywords = {
        "Happy": ['pop', 'dance', 'party', 'disco', 'funk', 'house', 'upbeat', 'edm', 'latin', 'reggaeton', 'k-pop'],
        "Chill": ['acoustic', 'lo-fi', 'jazz', 'ambient', 'chill', 'soul', 'r&b', 'indie', 'folk', 'classical'],
        "Sad": ['sad', 'melancholy', 'emo', 'blues', 'heartbreak', 'goth'],
        "Angry": ['metal', 'rock', 'punk', 'hardcore', 'rap', 'hip hop', 'drill', 'grime', 'trap']
    }
    
    for a in artists:
        if not a: continue
        genres = a.get('genres', [])
        matched = False
        for g in genres:
            g_lower = g.lower()
            for mood, words in keywords.items():
                if any(w in g_lower for w in words):
                    mood_counts[mood] += 1
                    matched = True
                    break
            if matched:
                break
        
        if not matched and genres:
            # Fallback for unmatched genres
            mood_counts["Chill"] += 1

    total = sum(mood_counts.values())
    if total == 0:
        return {"dominant": "Unknown", "colors": ["#000", "#000"], "percentages": {}, "max_percentage": 0}
        
    dominant = max(mood_counts, key=mood_counts.get)
    percentages = {k: int((v/total)*100) for k, v in mood_counts.items()}
    
    colors = {
        "Happy": ["#FFB703", "#FB8500"],
        "Chill": ["#8ECAE6", "#219EBC"],
        "Sad": ["#023047", "#001020"],
        "Angry": ["#D90429", "#8D0801"]
    }
    
    return {
        "dominant": dominant,
        "colors": colors.get(dominant, ["#1db954", "#121212"]),
        "percentages": percentages,
        "max_percentage": percentages.get(dominant, 0)
    }

def fetch_spotify_data(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Fetch Current User Profile to get user ID
    user_res = requests.get('https://api.spotify.com/v1/me', headers=headers)
    user_res.raise_for_status()
    user_id = user_res.json().get('id')
    
    # Recent Tracks
    recent_res = requests.get('https://api.spotify.com/v1/me/player/recently-played?limit=20', headers=headers)
    recent_res.raise_for_status()
    recent_data = recent_res.json()
    
    recent_tracks = []
    recent_artist_ids = []
    for item in recent_data.get('items', []):
        track = item['track']
        recent_tracks.append({
            'name': track['name'],
            'artist': ', '.join([a['name'] for a in track['artists']]),
            'album': track['album']['name'],
            'image_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'link': track['external_urls'].get('spotify', '')
        })
        if track['artists']:
            recent_artist_ids.append(track['artists'][0]['id'])
    
    recent_artist_ids = list(set(recent_artist_ids))[:50]

    # Top Tracks
    top_res = requests.get('https://api.spotify.com/v1/me/top/tracks?limit=10', headers=headers)
    top_res.raise_for_status()
    top_data = top_res.json()
    
    top_tracks = []
    for track in top_data.get('items', []):
        top_tracks.append({
            'name': track['name'],
            'artist': ', '.join([a['name'] for a in track['artists']]),
            'album': track['album']['name'],
            'image_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'link': track['external_urls'].get('spotify', '')
        })

    # Playlists
    pl_res = requests.get('https://api.spotify.com/v1/me/playlists?limit=50', headers=headers)
    pl_res.raise_for_status()
    pl_data = pl_res.json()
    
    THIRD_PARTY_KEYWORDS = ['shazam', 'soundhound']
    
    playlists = []
    for pl in pl_data.get('items', []):
        if not pl: continue
        if pl['owner'].get('id') != user_id: continue
            
        pl_name_lower = pl['name'].lower()
        is_third_party = any(keyword in pl_name_lower for keyword in THIRD_PARTY_KEYWORDS)
                
        playlists.append({
            'id': pl['id'],
            'name': pl['name'],
            'owner': pl['owner']['display_name'],
            'album': '',
            'image_url': pl['images'][0]['url'] if pl.get('images') else '',
            'link': pl['external_urls'].get('spotify', ''),
            'is_third_party': is_third_party
        })
        
        if len(playlists) >= 10: break

    # Pre-calculate Moods using Spotify Artist Genres
    mood_data = {}
    
    if recent_artist_ids:
        print(f"  Fetching mood for {len(recent_artist_ids)} recent artists via Spotify Genres...")
        mood_data['recent'] = calculate_mood_from_genres(recent_artist_ids, access_token)
    else:
        mood_data['recent'] = {"dominant": "Unknown", "colors": ["#000", "#000"], "percentages": {}, "max_percentage": 0}

    return {
        'recent_tracks': recent_tracks[:10],
        'top_tracks': top_tracks,
        'playlists': playlists,
        'mood_data_json': json.dumps(mood_data)
    }

def get_dummy_data():
    mood_data = {
        'recent': {"dominant": "Happy", "colors": ["#FFB703", "#FB8500"], "percentages": {"Happy": 60, "Chill": 20, "Sad": 10, "Angry": 10}, "max_percentage": 60}
    }
    return {
        'recent_tracks': [
            {'name': 'Dummy Track 1', 'artist': 'Artist A', 'album': 'Album A', 'image_url': 'https://via.placeholder.com/150/1db954/ffffff?text=Track+1', 'link': '#'}
        ],
        'top_tracks': [
            {'name': 'Top Dummy 1', 'artist': 'Artist B', 'album': 'Album B', 'image_url': 'https://via.placeholder.com/150/ff4d4d/ffffff?text=Top+1', 'link': '#'}
        ],
        'playlists': [
            {'id': 'dummy_pl_1', 'name': 'Late Night Sadness', 'owner': 'User C', 'image_url': 'https://via.placeholder.com/150/4d79ff/ffffff?text=Playlist+1', 'link': '#'},
            {'id': 'dummy_pl_2', 'name': 'Morning Coffee Chill', 'owner': 'User C', 'image_url': 'https://via.placeholder.com/150/4d79ff/ffffff?text=Playlist+2', 'link': '#'}
        ],
        'mood_data_json': json.dumps(mood_data)
    }

def main():
    if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and SPOTIFY_REFRESH_TOKEN:
        try:
            print("Fetching real Spotify data...")
            token = get_access_token()
            data = fetch_spotify_data(token)
        except Exception as e:
            print(f"Error fetching data: {e}. Falling back to dummy data.")
            data = get_dummy_data()
    else:
        print("Spotify credentials missing. Using dummy data.")
        data = get_dummy_data()
        
    template_dir = 'templates'
    template_file = 'index.template.html'
    
    # Render template
    jinja_env = Environment(loader=FileSystemLoader(template_dir))
    template = jinja_env.get_template(template_file)
    html_out = template.render(**data)
        
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_out)
    print("Successfully generated index.html")

if __name__ == '__main__':
    main()
