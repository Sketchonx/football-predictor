import os
from dotenv import load_dotenv

load_dotenv()

class Config:
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
    
    # Compétitions
    INCLUDED_COMPETITIONS = [
        'Champions League', 'Europa League', 'Conference League',
        'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
        'Championship', 'Liga Portugal', 'Eredivisie', 'Belgian Pro League',
        'World Cup Qualification', 'Euro Qualification'
    ]
    
    EXCLUDED_KEYWORDS = ['Friendly', 'Amical', 'U21', 'U19', 'Youth']