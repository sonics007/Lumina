import json
import os

CONFIG_FILE = 'groups_config.json'

def get_base_dir():
    return os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_config_path(username=None):
    base_dir = get_base_dir()
    if username:
        # User specific config
        user_dir = os.path.join(base_dir, 'configs', 'users')
        if not os.path.exists(user_dir):
            try:
                os.makedirs(user_dir, exist_ok=True)
            except: pass
        return os.path.join(user_dir, f'groups_{username}.json')
    return os.path.join(base_dir, CONFIG_FILE)

def load_config(username=None):
    path = get_config_path(username)
    
    # If checking for specific user and file doesn't exist, fallback to global
    if username and not os.path.exists(path):
        path = get_config_path(None)

    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_config(config, username=None):
    path = get_config_path(username)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_group_display_name(original_name, config=None):
    if not original_name:
        return "Uncategorized"
    if config is None:
        config = load_config()
    
    if original_name in config:
        return config[original_name].get('display_name', original_name)
    return original_name

def get_group_order(original_name, config=None, context='movie'):
    """
    Context: 'movie', 'series', 'live'.
    """
    if not original_name:
        return 9999
    if config is None:
        config = load_config()
        
    if original_name in config:
        # Try context specific order
        key = f'order_{context}'
        if key in config[original_name]:
            return config[original_name][key]
        # Fallback to global order
        return config[original_name].get('order', 9999)
    return 9999

def has_user_config(username):
    if not username: return False
    path = get_config_path(username)
    return os.path.exists(path)
