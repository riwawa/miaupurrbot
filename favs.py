import json
import os

FAV_FILE = "favorites.json"

def load_favorites():
    # Se o arquivo não existe OU está vazio, retorna dict vazio
    if not os.path.exists(FAV_FILE) or os.stat(FAV_FILE).st_size == 0:
        return {}

    try:
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        # Se o arquivo estiver corrompido, também começa limpo
        return {}

def save_favorites(data):
    with open(FAV_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_favorite(user_id, gif_url):
    data = load_favorites()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = []
    if gif_url not in data[user_id]:
        data[user_id].append(gif_url)
        save_favorites(data)

def get_user_favorites(user_id):
    data = load_favorites()
    return data.get(str(user_id), [])
