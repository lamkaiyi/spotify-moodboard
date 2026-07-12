import os
import requests
from jinja2 import Environment, FileSystemLoader

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

def fetch_spotify_data(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Recent Tracks
    recent_res = requests.get('https://api.spotify.com/v1/me/player/recently-played?limit=10', headers=headers)
    recent_res.raise_for_status()
    recent_data = recent_res.json()
    
    recent_tracks = []
    for item in recent_data.get('items', []):
        track = item['track']
        recent_tracks.append({
            'name': track['name'],
            'artist': ', '.join([a['name'] for a in track['artists']]),
            'album': track['album']['name'],
            'image_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'link': track['external_urls'].get('spotify', '')
        })

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
    pl_res = requests.get('https://api.spotify.com/v1/me/playlists?limit=10', headers=headers)
    pl_res.raise_for_status()
    pl_data = pl_res.json()
    
    playlists = []
    for pl in pl_data.get('items', []):
        if not pl:
            continue
        playlists.append({
            'name': pl['name'],
            'owner': pl['owner']['display_name'],
            'album': '',
            'image_url': pl['images'][0]['url'] if pl.get('images') else '',
            'link': pl['external_urls'].get('spotify', '')
        })
        
    return {
        'recent_tracks': recent_tracks,
        'top_tracks': top_tracks,
        'playlists': playlists
    }

def get_dummy_data():
    return {
        'recent_tracks': [
            {'name': 'Dummy Track 1', 'artist': 'Artist A', 'album': 'Album A', 'image_url': 'https://via.placeholder.com/150/1db954/ffffff?text=Track+1', 'link': '#'},
            {'name': 'Dummy Track 2', 'artist': 'Artist B', 'album': 'Album B', 'image_url': 'https://via.placeholder.com/150/1db954/ffffff?text=Track+2', 'link': '#'}
        ],
        'top_tracks': [
            {'name': 'Top Dummy 1', 'artist': 'Artist B', 'album': 'Album B', 'image_url': 'https://via.placeholder.com/150/ff4d4d/ffffff?text=Top+1', 'link': '#'}
        ],
        'playlists': [
            {'name': 'Dummy Playlist', 'owner': 'User C', 'album': '', 'image_url': 'https://via.placeholder.com/150/4d79ff/ffffff?text=Playlist+1', 'link': '#'}
        ]
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
