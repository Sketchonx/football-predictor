import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Répertoires
    DATA_DIR = 'data'
    PREDICTIONS_DIR = os.path.join('data', 'predictions')

    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    # Paramètres Analyse
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Brussels')
    MIN_CONFIDENCE = int(os.getenv('MIN_CONFIDENCE', 75))
    MIN_ODDS = float(os.getenv('MIN_ODDS', 1.50))
    MAX_ODDS = float(os.getenv('MAX_ODDS', 4.00))
    MAX_PREDICTIONS = int(os.getenv('MAX_PREDICTIONS', 8))
    
    # IDs des ligues à inclure (API-Football)
    INCLUDED_LEAGUE_IDS = [
        # Compétitions UEFA
        2,    # UEFA Champions League
        3,    # UEFA Europa League
        848,  # UEFA Europa Conference League
        # Top 5 championnats européens
        39,   # Premier League (Angleterre)
        140,  # La Liga (Espagne)
        135,  # Serie A (Italie)
        78,   # Bundesliga (Allemagne)
        61,   # Ligue 1 (France)
        # Belgique
        144,  # Jupiler Pro League (Belgique)
    ]

    # Compétitions (noms pour filtrage texte si pas d'ID)
    INCLUDED_COMPETITIONS = [
        # Compétitions UEFA
        'Champions League', 'UEFA Champions League',
        'Europa League', 'UEFA Europa League',
        'Conference League', 'UEFA Europa Conference League',
        # Top 5 championnats européens
        'Premier League',
        'La Liga', 'LaLiga',
        'Serie A',
        'Bundesliga',
        'Ligue 1',
        # Belgique
        'Belgian Pro League', 'Jupiler Pro League', 'First Division A'
    ]
    
    EXCLUDED_KEYWORDS = ['Friendly', 'Amical', 'U21', 'U19', 'Youth']