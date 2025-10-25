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

        # Enrichir avec stats supplémentaires (forme, H2H, blessures)
        print("📊 Enrichissement des matchs avec données contextuelles...")
        enriched_matches = []
        for match in filtered_matches:
            enriched_match = self._enrich_match_data(match)
            enriched_matches.append(enriched_match)

        return enriched_matches
    
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
                match_data = {
                    'home': fixture['teams']['home']['name'],
                    'away': fixture['teams']['away']['name'],
                    'competition': fixture['league']['name'],
                    'league_id': fixture['league']['id'],
                    'country': fixture['league']['country'],
                    'time': fixture['fixture']['date'],
                    'date': today,
                    'source': 'api-football',
                    'fixture_id': fixture['fixture']['id'],
                    'team_home_id': fixture['teams']['home']['id'],
                    'team_away_id': fixture['teams']['away']['id']
                }
                matches.append(match_data)

            return matches
        except Exception as e:
            print(f"Erreur API-Football: {e}")
            return []
    
    def _filter_matches(self, matches):
        """Filtre les matchs selon compétitions et critères"""
        filtered = []

        for match in matches:
            competition = match.get('competition', '')
            league_id = match.get('league_id')

            # Exclure mots-clés interdits
            if any(keyword.lower() in competition.lower()
                   for keyword in self.config.EXCLUDED_KEYWORDS):
                continue

            # Filtrer par ID de ligue si disponible (plus précis)
            if league_id and league_id in self.config.INCLUDED_LEAGUE_IDS:
                filtered.append(match)
            # Sinon filtrer par nom de compétition (pour FlashScore)
            elif not league_id and any(included.lower() in competition.lower()
                   for included in self.config.INCLUDED_COMPETITIONS):
                # Vérifier le pays pour éviter les faux positifs
                country = match.get('country', '')
                # Accepter uniquement si pays européen ou vide
                if not country or country in ['England', 'Spain', 'Italy', 'Germany', 'France', 'Belgium', 'World', 'Europe']:
                    filtered.append(match)

        return filtered
    
    def _enrich_match_data(self, match):
        """Enrichit les données d'un match avec stats API-Football"""
        try:
            api_key = os.getenv('API_FOOTBALL_KEY', None)
            if not api_key or match.get('source') != 'api-football':
                return match

            headers = {'x-apisports-key': api_key}
            fixture_id = match.get('fixture_id')

            if not fixture_id:
                return match

            # Récupérer les statistiques d'équipe (forme récente)
            team_home_id = match.get('team_home_id')
            team_away_id = match.get('team_away_id')

            # Forme récente équipe domicile (5 derniers matchs)
            if team_home_id:
                url_home = f"https://v3.football.api-sports.io/fixtures"
                params_home = {'team': team_home_id, 'last': 5}
                resp_home = requests.get(url_home, headers=headers, params=params_home, timeout=10)
                if resp_home.status_code == 200:
                    match['home_recent_form'] = resp_home.json().get('response', [])

            # Forme récente équipe extérieure
            if team_away_id:
                url_away = f"https://v3.football.api-sports.io/fixtures"
                params_away = {'team': team_away_id, 'last': 5}
                resp_away = requests.get(url_away, headers=headers, params=params_away, timeout=10)
                if resp_away.status_code == 200:
                    match['away_recent_form'] = resp_away.json().get('response', [])

            # Confrontations directes (H2H)
            if team_home_id and team_away_id:
                url_h2h = f"https://v3.football.api-sports.io/fixtures/headtohead"
                params_h2h = {'h2h': f"{team_home_id}-{team_away_id}"}
                resp_h2h = requests.get(url_h2h, headers=headers, params=params_h2h, timeout=10)
                if resp_h2h.status_code == 200:
                    match['head_to_head'] = resp_h2h.json().get('response', [])[:5]  # 5 derniers

            # Blessures et suspensions
            if team_home_id:
                url_injuries_home = f"https://v3.football.api-sports.io/injuries"
                params_injuries_home = {'team': team_home_id, 'fixture': fixture_id}
                resp_injuries_home = requests.get(url_injuries_home, headers=headers, params=params_injuries_home, timeout=10)
                if resp_injuries_home.status_code == 200:
                    match['home_injuries'] = resp_injuries_home.json().get('response', [])

            if team_away_id:
                url_injuries_away = f"https://v3.football.api-sports.io/injuries"
                params_injuries_away = {'team': team_away_id, 'fixture': fixture_id}
                resp_injuries_away = requests.get(url_injuries_away, headers=headers, params=params_injuries_away, timeout=10)
                if resp_injuries_away.status_code == 200:
                    match['away_injuries'] = resp_injuries_away.json().get('response', [])

            return match

        except Exception as e:
            print(f"⚠️ Erreur enrichissement match {match.get('home')} vs {match.get('away')}: {e}")
            return match

    def format_matches_for_prompt(self, matches):
        """Formate les matchs pour le prompt avec données enrichies"""
        if not matches:
            return "Aucun match disponible aujourd'hui."

        formatted = "MATCHS DU JOUR AVEC DONNÉES CONTEXTUELLES:\n\n"
        for i, match in enumerate(matches, 1):
            formatted += f"═══ MATCH #{i} ═══\n"
            formatted += f"🏆 {match['home']} vs {match['away']}\n"
            formatted += f"📍 Compétition: {match['competition']}\n"
            formatted += f"⏰ Heure: {match['time']}\n\n"

            # Forme récente équipe domicile
            if match.get('home_recent_form'):
                formatted += "📊 FORME RÉCENTE DOMICILE (5 derniers matchs):\n"
                for game in match['home_recent_form'][:5]:
                    home_team = game['teams']['home']['name']
                    away_team = game['teams']['away']['name']
                    score_home = game['goals']['home']
                    score_away = game['goals']['away']
                    date_game = game['fixture']['date'][:10]
                    formatted += f"  • {date_game}: {home_team} {score_home}-{score_away} {away_team}\n"
                formatted += "\n"

            # Forme récente équipe extérieure
            if match.get('away_recent_form'):
                formatted += "📊 FORME RÉCENTE EXTÉRIEUR (5 derniers matchs):\n"
                for game in match['away_recent_form'][:5]:
                    home_team = game['teams']['home']['name']
                    away_team = game['teams']['away']['name']
                    score_home = game['goals']['home']
                    score_away = game['goals']['away']
                    date_game = game['fixture']['date'][:10]
                    formatted += f"  • {date_game}: {home_team} {score_home}-{score_away} {away_team}\n"
                formatted += "\n"

            # Confrontations directes
            if match.get('head_to_head'):
                formatted += "🔄 CONFRONTATIONS DIRECTES (5 derniers H2H):\n"
                for game in match['head_to_head'][:5]:
                    home_team = game['teams']['home']['name']
                    away_team = game['teams']['away']['name']
                    score_home = game['goals']['home']
                    score_away = game['goals']['away']
                    date_game = game['fixture']['date'][:10]
                    formatted += f"  • {date_game}: {home_team} {score_home}-{score_away} {away_team}\n"
                formatted += "\n"

            # Blessures équipe domicile
            if match.get('home_injuries'):
                formatted += "🏥 BLESSURES/SUSPENSIONS DOMICILE:\n"
                for injury in match['home_injuries'][:5]:
                    player = injury['player']['name']
                    reason = injury['player']['reason']
                    formatted += f"  • {player}: {reason}\n"
                formatted += "\n"

            # Blessures équipe extérieure
            if match.get('away_injuries'):
                formatted += "🏥 BLESSURES/SUSPENSIONS EXTÉRIEUR:\n"
                for injury in match['away_injuries'][:5]:
                    player = injury['player']['name']
                    reason = injury['player']['reason']
                    formatted += f"  • {player}: {reason}\n"
                formatted += "\n"

            formatted += "─" * 50 + "\n\n"

        return formatted

# Test
if __name__ == "__main__":
    scraper = MatchScraper()
    matches = scraper.get_today_matches()
    print(f"Matchs trouvés: {len(matches)}")
    print(scraper.format_matches_for_prompt(matches[:5]))