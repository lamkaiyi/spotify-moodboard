import os
import requests
import json
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REFRESH_TOKEN = os.environ.get('SPOTIFY_REFRESH_TOKEN')

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

def calculate_mood(track_features):
    if not track_features:
        return {"dominant": "Unknown", "colors": ["#000", "#000"], "percentages": {}}
    
    mood_counts = {"Happy": 0, "Chill": 0, "Sad": 0, "Angry": 0}
    for f in track_features:
        if not f: continue
        val = f.get('valence', 0.5)
        eng = f.get('energy', 0.5)
        if val >= 0.5 and eng >= 0.5:
            mood_counts["Happy"] += 1
        elif val >= 0.5 and eng < 0.5:
            mood_counts["Chill"] += 1
        elif val < 0.5 and eng < 0.5:
            mood_counts["Sad"] += 1
        else:
            mood_counts["Angry"] += 1
            
    total = sum(mood_counts.values())
    if total == 0:
        return {"dominant": "Unknown", "colors": ["#000", "#000"], "percentages": {}}
        
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
    recent_track_ids = []
    for item in recent_data.get('items', []):
        track = item['track']
        recent_tracks.append({
            'name': track['name'],
            'artist': ', '.join([a['name'] for a in track['artists']]),
            'album': track['album']['name'],
            'image_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'link': track['external_urls'].get('spotify', '')
        })
        recent_track_ids.append(track['id'])

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

    # Pre-calculate Moods
    mood_data = {}
    
    # 1. Recent Tracks Mood
    if recent_track_ids:
        # Spotify allows up to 100 IDs per request
        f_res = requests.get(f'https://api.spotify.com/v1/audio-features?ids={",".join(recent_track_ids[:100])}', headers=headers)
        if f_res.status_code == 200:
            mood_data['recent'] = calculate_mood(f_res.json().get('audio_features', []))
        else:
            mood_data['recent'] = calculate_mood([])
            
    # 2. Playlists Mood
    for pl in playlists:
        tracks_res = requests.get(f"https://api.spotify.com/v1/playlists/{pl['id']}/tracks?limit=30", headers=headers)
        if tracks_res.status_code == 200:
            t_data = tracks_res.json().get('items', [])
            t_ids = [t['track']['id'] for t in t_data if t.get('track') and t['track'].get('id')]
            if t_ids:
                pf_res = requests.get(f'https://api.spotify.com/v1/audio-features?ids={",".join(t_ids[:100])}', headers=headers)
                if pf_res.status_code == 200:
                    mood_data[pl['id']] = calculate_mood(pf_res.json().get('audio_features', []))
                    continue
        mood_data[pl['id']] = calculate_mood([])

    return {
        'recent_tracks': recent_tracks[:10],
        'top_tracks': top_tracks,
        'playlists': playlists,
        'mood_data_json': json.dumps(mood_data)
    }

def get_dummy_data():
    mood_data = {
        'recent': {"dominant": "Happy", "colors": ["#FFB703", "#FB8500"], "percentages": {"Happy": 60, "Chill": 20, "Sad": 10, "Angry": 10}, "max_percentage": 60},
        'dummy_pl_1': {"dominant": "Sad", "colors": ["#023047", "#001020"], "percentages": {"Happy": 10, "Chill": 30, "Sad": 50, "Angry": 10}, "max_percentage": 50},
        'dummy_pl_2': {"dominant": "Chill", "colors": ["#8ECAE6", "#219EBC"], "percentages": {"Happy": 20, "Chill": 70, "Sad": 10, "Angry": 0}, "max_percentage": 70}
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
