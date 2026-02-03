from urllib.parse import urlparse

# Centrálna konfigurácia providerov
# Vygenerované zo súborov v v7_multi_provider/providers/

PROVIDERS = {
    # Auvexiug
    'auvexiug.com': {
        'referer': 'https://auvexiug.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },

    # Cavanhabg
    'cavanhabg.com': {
        'referer': 'https://cavanhabg.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },

    # FilmCDN / S2
    'filmcdn.top': {
        'referer': 'https://s2.filmcdn.top/',
        'extra_headers': {'Origin': 'https://s2.filmcdn.top', 'Accept-Encoding': 'identity'}
    },
    's2.filmcdn.top': {
        'referer': 'https://s2.filmcdn.top/',
        'extra_headers': {'Origin': 'https://s2.filmcdn.top', 'Accept-Encoding': 'identity'}
    },
    'cfglobalcdn.com': { # Často alias pre FilmCDN
         'referer': 'https://s2.filmcdn.top/',
         'extra_headers': {'Origin': 'https://s2.filmcdn.top'}
    },

    # Ghbrisk
    'ghbrisk.com': {
        'referer': 'https://ghbrisk.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },

    # Haxloppd (HGLink Mirror)
    'haxloppd.com': {
        'referer': 'https://film-adult.top/',
        'extra_headers': {'Accept': '*/*'}
    },
    'shavtape.com': {
        'referer': 'https://film-adult.top/',
        'extra_headers': {'Accept': '*/*'}
    },

    # HGLink
    'hglink.to': {
        'referer': 'https://film-adult.top/',
        'extra_headers': {'Accept': '*/*'}
    },

    # HLSWish
    'hlswish.com': {
        'referer': 'https://hlswish.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },
    'hlswish.org': {
        'referer': 'https://hlswish.org/',
         'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },

    # Movearnpre
    'movearnpre.com': {
        'referer': 'https://movearnpre.com/',
        'extra_headers': {'Origin': 'https://movearnpre.com', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate'}
    },

    # Streamtape (Pozor, Streamtape casto vyzaduje zlozitejsiu logiku nez len unpack)
    'streamtape.com': {
        'referer': 'https://streamtape.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate'}
    },

    # Swdyu
    'swdyu.com': {
        'referer': 'https://swdyu.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },
    
    # Voe.sx (Tiez casto zlozitejsie)
    'voe.sx': {
        'referer': 'https://voe.sx/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },

    # Yuguaab
    'yuguaab.com': {
        'referer': 'https://yuguaab.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },

    # Myvidplay / DoodStream
    'myvidplay.com': {
        'referer': 'https://myvidplay.com/',
        'extra_headers': {'Accept': '*/*', 'Accept-Encoding': 'identity'}
    },
    'dood.to': { 'referer': 'https://dood.to/' },
    'dood.so': { 'referer': 'https://dood.so/' },
    'doodstream.com': { 'referer': 'https://doodstream.com/' }
}

def get_provider_config(url):
    """
    Vráti konfiguráciu pre danú URL na základe domény.
    Priority:
    1. Exact match (netloc)
    2. Subdomain check (key in netloc)
    """
    try:
        domain = urlparse(url).netloc
        # 1. Exact match
        if domain in PROVIDERS: return PROVIDERS[domain]
        # 2. Subdomain match (iterujeme cez kluce)
        for key in PROVIDERS:
            if key in domain: return PROVIDERS[key]
    except:
        pass
    return {}
