import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import pytz
import os
from config import Config

class MatchScraper:
    def __init__(self):
        self.config = Config()
        self.tz = pytz.timezone(self.config.TIMEZONE)
        
    def get_today_matches(self):
        """Récupère les matchs du jour depuis plusieurs sources"""
        matches = []
        
        # Source 1: FlashScore (via requests)
        matches.extend(self._scrape_flashscore())
        
        # Source 2: API-Football gratuite (limitée)
        matches.extend(self._scrape_api_football_free())
        
        # Filtrer par compétitions incluses
        filtered_matches = self._filter_matches(matches)
        
        return filtered_matches
    
    def _scrape_flashscore(self):
        """Scrape FlashScore pour matchs du jour"""
        try:
            today = datetime.now(self.tz).strftime('%Y-%m-%d')
            url = f"https://www.flashscore.com/football/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'lxml')
            
            matches = []
            # Parser le HTML (structure simplifiée)
            for match_div in soup.find_all('div', class_='event__match'):
                try:
                    home = match_div.find('div', class_='event__participant--home').text.strip()
                    away = match_div.find('div', class_='event__participant--away').text.strip()
                    competition = match_div.find('span', class_='event__title').text.strip()
                    time = match_div.find('div', class_='event__time').text.strip()
                    
                    matches.append({
                        'home': home,
                        'away': away,
                        'competition': competition,
                        'time': time,
                        'date': today,
                        'source': 'flashscore'
                    })
                except:
                    continue
            
            return matches
        except Exception as e:
            print(f"Erreur FlashScore: {e}")
            return []
    
    def _scrape_api_football_free(self):
        """Alternative : API-Football gratuite (100 req/jour)"""
        try:
            # NOTE: Nécessite une clé API gratuite de api-football.com
            # 100 requêtes/jour gratuites
            today = datetime.now(self.tz).strftime('%Y-%m-%d')
            
            # Remplacer par votre clé API gratuite si disponible
            api_key = os.getenv('API_FOOTBALL_KEY', None)
            if not api_key:
                return []
            
            url = "https://v3.football.api-sports.io/fixtures"
            headers = {'x-apisports-key': api_key}
            params = {'date': today}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            
            matches = []
            for fixture in data.get('response', []):
                matches.append({
                    'home': fixture['teams']['home']['name'],
                    'away': fixture['teams']['away']['name'],
                    'competition': fixture['league']['name'],
                    'time': fixture['fixture']['date'],
                    'date': today,
                    'source': 'api-football'
                })
            
            return matches
        except Exception as e:
            print(f"Erreur API-Football: {e}")
            return []
    
    def _filter_matches(self, matches):
        """Filtre les matchs selon compétitions et critères"""
        filtered = []
        
        for match in matches:
            competition = match.get('competition', '')
            
            # Exclure mots-clés interdits
            if any(keyword.lower() in competition.lower() 
                   for keyword in self.config.EXCLUDED_KEYWORDS):
                continue
            
            # Inclure uniquement compétitions européennes
            # Pour simplifier, on garde tous les matchs européens
            # (filtrage plus fin dans l'analyse IA)
            filtered.append(match)
        
        return filtered
    
    def format_matches_for_prompt(self, matches):
        """Formate les matchs pour le prompt"""
        if not matches:
            return "Aucun match disponible aujourd'hui."
        
        formatted = "MATCHS DU JOUR:\n\n"
        for i, match in enumerate(matches, 1):
            formatted += f"{i}. {match['home']} vs {match['away']}\n"
            formatted += f"   Compétition: {match['competition']}\n"
            formatted += f"   Heure: {match['time']}\n\n"
        
        return formatted

# Test
if __name__ == "__main__":
    scraper = MatchScraper()
    matches = scraper.get_today_matches()
    print(f"Matchs trouvés: {len(matches)}")
    print(scraper.format_matches_for_prompt(matches[:5]))