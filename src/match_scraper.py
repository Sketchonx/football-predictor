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
        """Enrichit les données d'un match avec stats API-Football (EXHAUSTIF)"""
        try:
            api_key = os.getenv('API_FOOTBALL_KEY', None)
            if not api_key or match.get('source') != 'api-football':
                return match

            headers = {'x-apisports-key': api_key}
            fixture_id = match.get('fixture_id')
            league_id = match.get('league_id')
            season = datetime.now().year

            if not fixture_id:
                return match

            team_home_id = match.get('team_home_id')
            team_away_id = match.get('team_away_id')

            # 1. FORME RÉCENTE (10 derniers matchs au lieu de 5 pour plus de contexte)
            if team_home_id:
                url_home = f"https://v3.football.api-sports.io/fixtures"
                params_home = {'team': team_home_id, 'last': 10}
                resp_home = requests.get(url_home, headers=headers, params=params_home, timeout=10)
                if resp_home.status_code == 200:
                    match['home_recent_form'] = resp_home.json().get('response', [])

            if team_away_id:
                url_away = f"https://v3.football.api-sports.io/fixtures"
                params_away = {'team': team_away_id, 'last': 10}
                resp_away = requests.get(url_away, headers=headers, params=params_away, timeout=10)
                if resp_away.status_code == 200:
                    match['away_recent_form'] = resp_away.json().get('response', [])

            # 2. CONFRONTATIONS DIRECTES (10 derniers H2H pour historique complet)
            if team_home_id and team_away_id:
                url_h2h = f"https://v3.football.api-sports.io/fixtures/headtohead"
                params_h2h = {'h2h': f"{team_home_id}-{team_away_id}", 'last': 10}
                resp_h2h = requests.get(url_h2h, headers=headers, params=params_h2h, timeout=10)
                if resp_h2h.status_code == 200:
                    match['head_to_head'] = resp_h2h.json().get('response', [])

            # 3. BLESSURES ET SUSPENSIONS (données actuelles)
            if team_home_id:
                url_injuries_home = f"https://v3.football.api-sports.io/injuries"
                params_injuries_home = {'team': team_home_id, 'season': season}
                resp_injuries_home = requests.get(url_injuries_home, headers=headers, params=params_injuries_home, timeout=10)
                if resp_injuries_home.status_code == 200:
                    match['home_injuries'] = resp_injuries_home.json().get('response', [])

            if team_away_id:
                url_injuries_away = f"https://v3.football.api-sports.io/injuries"
                params_injuries_away = {'team': team_away_id, 'season': season}
                resp_injuries_away = requests.get(url_injuries_away, headers=headers, params=params_injuries_away, timeout=10)
                if resp_injuries_away.status_code == 200:
                    match['away_injuries'] = resp_injuries_away.json().get('response', [])

            # 4. STATISTIQUES D'ÉQUIPE SAISON (forme domicile/extérieur, moyenne buts, etc.)
            if team_home_id and league_id:
                url_stats_home = f"https://v3.football.api-sports.io/teams/statistics"
                params_stats_home = {'team': team_home_id, 'league': league_id, 'season': season}
                resp_stats_home = requests.get(url_stats_home, headers=headers, params=params_stats_home, timeout=10)
                if resp_stats_home.status_code == 200:
                    match['home_season_stats'] = resp_stats_home.json().get('response', {})

            if team_away_id and league_id:
                url_stats_away = f"https://v3.football.api-sports.io/teams/statistics"
                params_stats_away = {'team': team_away_id, 'league': league_id, 'season': season}
                resp_stats_away = requests.get(url_stats_away, headers=headers, params=params_stats_away, timeout=10)
                if resp_stats_away.status_code == 200:
                    match['away_season_stats'] = resp_stats_away.json().get('response', {})

            # 5. CLASSEMENT DE LA LIGUE (position, points, écart)
            if league_id:
                url_standings = f"https://v3.football.api-sports.io/standings"
                params_standings = {'league': league_id, 'season': season}
                resp_standings = requests.get(url_standings, headers=headers, params=params_standings, timeout=10)
                if resp_standings.status_code == 200:
                    match['league_standings'] = resp_standings.json().get('response', [])

            # 6. COTES EN TEMPS RÉEL (CRUCIAL pour value bets)
            url_odds = f"https://v3.football.api-sports.io/odds"
            params_odds = {'fixture': fixture_id}
            resp_odds = requests.get(url_odds, headers=headers, params=params_odds, timeout=10)
            if resp_odds.status_code == 200:
                match['odds'] = resp_odds.json().get('response', [])

            # 7. PRÉDICTIONS API-FOOTBALL (pour comparaison avec nos analyses)
            url_predictions = f"https://v3.football.api-sports.io/predictions"
            params_predictions = {'fixture': fixture_id}
            resp_predictions = requests.get(url_predictions, headers=headers, params=params_predictions, timeout=10)
            if resp_predictions.status_code == 200:
                match['api_predictions'] = resp_predictions.json().get('response', [])

            return match

        except Exception as e:
            print(f"⚠️ Erreur enrichissement match {match.get('home')} vs {match.get('away')}: {e}")
            return match

    def format_matches_for_prompt(self, matches):
        """Formate les matchs pour le prompt avec TOUTES les données enrichies"""
        if not matches:
            return "Aucun match disponible aujourd'hui."

        formatted = "═══════════════════════════════════════════════════════\n"
        formatted += "MATCHS DU JOUR - DONNÉES EXHAUSTIVES API-FOOTBALL\n"
        formatted += "═══════════════════════════════════════════════════════\n\n"

        for i, match in enumerate(matches, 1):
            formatted += f"\n{'█' * 60}\n"
            formatted += f"MATCH #{i}: {match['home']} vs {match['away']}\n"
            formatted += f"{'█' * 60}\n\n"
            formatted += f"📍 Compétition: {match['competition']}\n"
            formatted += f"⏰ Coup d'envoi: {match['time']}\n\n"

            # 1. CLASSEMENT & POSITION
            if match.get('league_standings'):
                formatted += "┌─ 📊 CLASSEMENT ACTUEL ─────────────────────────────────┐\n"
                standings = match['league_standings'][0]['league']['standings'][0] if match['league_standings'] else []
                home_team_name = match['home']
                away_team_name = match['away']

                for team in standings:
                    if team['team']['name'] == home_team_name:
                        formatted += f"│ 🏠 {home_team_name}: {team['rank']}e place - {team['points']} pts\n"
                        formatted += f"│    Bilan: {team['all']['win']}V-{team['all']['draw']}N-{team['all']['lose']}D\n"
                        formatted += f"│    Buts: {team['all']['goals']['for']} pour, {team['all']['goals']['against']} contre (diff: {team['goalsDiff']})\n"
                        formatted += f"│    Domicile: {team['home']['win']}V-{team['home']['draw']}N-{team['home']['lose']}D\n"
                    elif team['team']['name'] == away_team_name:
                        formatted += f"│ ✈️  {away_team_name}: {team['rank']}e place - {team['points']} pts\n"
                        formatted += f"│    Bilan: {team['all']['win']}V-{team['all']['draw']}N-{team['all']['lose']}D\n"
                        formatted += f"│    Buts: {team['all']['goals']['for']} pour, {team['all']['goals']['against']} contre (diff: {team['goalsDiff']})\n"
                        formatted += f"│    Extérieur: {team['away']['win']}V-{team['away']['draw']}N-{team['away']['lose']}D\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 2. STATISTIQUES SAISON COMPLÈTES
            if match.get('home_season_stats'):
                stats_home = match['home_season_stats']
                formatted += "┌─ 📈 STATS SAISON ÉQUIPE DOMICILE ──────────────────────┐\n"
                if stats_home.get('fixtures'):
                    formatted += f"│ Matchs joués: {stats_home['fixtures']['played']['total']}\n"
                    formatted += f"│ Victoires: {stats_home['fixtures']['wins']['total']} ({stats_home['fixtures']['wins']['home']} domicile)\n"
                    formatted += f"│ Nuls: {stats_home['fixtures']['draws']['total']}\n"
                    formatted += f"│ Défaites: {stats_home['fixtures']['loses']['total']}\n"
                if stats_home.get('goals'):
                    formatted += f"│ Buts marqués: {stats_home['goals']['for']['total']['total']} (moy: {stats_home['goals']['for']['average']['total']})\n"
                    formatted += f"│ Buts encaissés: {stats_home['goals']['against']['total']['total']} (moy: {stats_home['goals']['against']['average']['total']})\n"
                if stats_home.get('biggest'):
                    formatted += f"│ Plus grande victoire: {stats_home['biggest']['wins']['home']}\n"
                    formatted += f"│ Plus lourde défaite: {stats_home['biggest']['loses']['home']}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            if match.get('away_season_stats'):
                stats_away = match['away_season_stats']
                formatted += "┌─ 📈 STATS SAISON ÉQUIPE EXTÉRIEURE ────────────────────┐\n"
                if stats_away.get('fixtures'):
                    formatted += f"│ Matchs joués: {stats_away['fixtures']['played']['total']}\n"
                    formatted += f"│ Victoires: {stats_away['fixtures']['wins']['total']} ({stats_away['fixtures']['wins']['away']} extérieur)\n"
                    formatted += f"│ Nuls: {stats_away['fixtures']['draws']['total']}\n"
                    formatted += f"│ Défaites: {stats_away['fixtures']['loses']['total']}\n"
                if stats_away.get('goals'):
                    formatted += f"│ Buts marqués: {stats_away['goals']['for']['total']['total']} (moy: {stats_away['goals']['for']['average']['total']})\n"
                    formatted += f"│ Buts encaissés: {stats_away['goals']['against']['total']['total']} (moy: {stats_away['goals']['against']['average']['total']})\n"
                if stats_away.get('biggest'):
                    formatted += f"│ Plus grande victoire: {stats_away['biggest']['wins']['away']}\n"
                    formatted += f"│ Plus lourde défaite: {stats_away['biggest']['loses']['away']}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 3. FORME RÉCENTE (10 derniers matchs)
            if match.get('home_recent_form'):
                formatted += "┌─ 🔥 FORME RÉCENTE DOMICILE (10 derniers) ─────────────┐\n"
                for idx, game in enumerate(match['home_recent_form'][:10], 1):
                    home_team = game['teams']['home']['name']
                    away_team = game['teams']['away']['name']
                    score_home = game['goals']['home']
                    score_away = game['goals']['away']
                    date_game = game['fixture']['date'][:10]
                    result = "V" if (home_team == match['home'] and score_home > score_away) or (away_team == match['home'] and score_away > score_home) else ("N" if score_home == score_away else "D")
                    formatted += f"│ {idx:2}. [{result}] {date_game}: {home_team} {score_home}-{score_away} {away_team}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            if match.get('away_recent_form'):
                formatted += "┌─ 🔥 FORME RÉCENTE EXTÉRIEUR (10 derniers) ────────────┐\n"
                for idx, game in enumerate(match['away_recent_form'][:10], 1):
                    home_team = game['teams']['home']['name']
                    away_team = game['teams']['away']['name']
                    score_home = game['goals']['home']
                    score_away = game['goals']['away']
                    date_game = game['fixture']['date'][:10]
                    result = "V" if (home_team == match['away'] and score_home > score_away) or (away_team == match['away'] and score_away > score_home) else ("N" if score_home == score_away else "D")
                    formatted += f"│ {idx:2}. [{result}] {date_game}: {home_team} {score_home}-{score_away} {away_team}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 4. CONFRONTATIONS DIRECTES
            if match.get('head_to_head'):
                formatted += "┌─ 🔄 CONFRONTATIONS DIRECTES (10 derniers H2H) ────────┐\n"
                for idx, game in enumerate(match['head_to_head'][:10], 1):
                    home_team = game['teams']['home']['name']
                    away_team = game['teams']['away']['name']
                    score_home = game['goals']['home']
                    score_away = game['goals']['away']
                    date_game = game['fixture']['date'][:10]
                    formatted += f"│ {idx:2}. {date_game}: {home_team} {score_home}-{score_away} {away_team}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 5. BLESSURES ET SUSPENSIONS
            if match.get('home_injuries'):
                formatted += "┌─ 🏥 BLESSURES/SUSPENSIONS DOMICILE ───────────────────┐\n"
                if len(match['home_injuries']) == 0:
                    formatted += "│ ✅ Aucune blessure signalée\n"
                else:
                    for injury in match['home_injuries'][:10]:
                        player = injury['player']['name']
                        reason = injury['player']['reason']
                        formatted += f"│ ❌ {player}: {reason}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            if match.get('away_injuries'):
                formatted += "┌─ 🏥 BLESSURES/SUSPENSIONS EXTÉRIEUR ──────────────────┐\n"
                if len(match['away_injuries']) == 0:
                    formatted += "│ ✅ Aucune blessure signalée\n"
                else:
                    for injury in match['away_injuries'][:10]:
                        player = injury['player']['name']
                        reason = injury['player']['reason']
                        formatted += f"│ ❌ {player}: {reason}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 6. COTES EN TEMPS RÉEL
            if match.get('odds'):
                formatted += "┌─ 💰 COTES EN TEMPS RÉEL (marchés principaux) ─────────┐\n"
                for bookmaker in match['odds'][:3]:  # Top 3 bookmakers
                    bm_name = bookmaker['bookmaker']['name']
                    for bet in bookmaker['bets']:
                        if bet['name'] == 'Match Winner':
                            formatted += f"│ [{bm_name}] 1X2:\n"
                            for value in bet['values']:
                                formatted += f"│   - {value['value']}: {value['odd']}\n"
                        elif bet['name'] == 'Goals Over/Under':
                            formatted += f"│ [{bm_name}] Over/Under:\n"
                            for value in bet['values'][:4]:
                                formatted += f"│   - {value['value']}: {value['odd']}\n"
                        elif bet['name'] == 'Both Teams Score':
                            formatted += f"│ [{bm_name}] BTTS:\n"
                            for value in bet['values']:
                                formatted += f"│   - {value['value']}: {value['odd']}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 7. PRÉDICTIONS API-FOOTBALL (référence)
            if match.get('api_predictions'):
                pred = match['api_predictions'][0] if match['api_predictions'] else {}
                if pred:
                    formatted += "┌─ 🤖 PRÉDICTION API-FOOTBALL (référence) ──────────────┐\n"
                    if pred.get('predictions'):
                        formatted += f"│ Gagnant probable: {pred['predictions'].get('winner', {}).get('name', 'N/A')}\n"
                        formatted += f"│ Conseil: {pred['predictions'].get('advice', 'N/A')}\n"
                    if pred.get('comparison'):
                        comp = pred['comparison']
                        formatted += f"│ Forme: {comp.get('form', {}).get('home', 'N/A')} vs {comp.get('form', {}).get('away', 'N/A')}\n"
                        formatted += f"│ Att: {comp.get('att', {}).get('home', 'N/A')} vs {comp.get('att', {}).get('away', 'N/A')}\n"
                        formatted += f"│ Def: {comp.get('def', {}).get('home', 'N/A')} vs {comp.get('def', {}).get('away', 'N/A')}\n"
                    formatted += "│ ⚠️ IMPORTANT: Ces prédictions sont INDICATIVES, tu dois faire ta propre analyse\n"
                    formatted += "└────────────────────────────────────────────────────────┘\n\n"

            formatted += "\n" + "═" * 60 + "\n\n"

        formatted += "\n🎯 INSTRUCTION: Analyse TOUTES ces données réelles pour identifier les VALUE BETS.\n"
        formatted += "Les cotes fournies sont RÉELLES et EN TEMPS RÉEL.\n"
        formatted += "NE PAS inventer de données - TOUT est fourni ci-dessus.\n\n"

        return formatted

# Test
if __name__ == "__main__":
    scraper = MatchScraper()
    matches = scraper.get_today_matches()
    print(f"Matchs trouvés: {len(matches)}")
    print(scraper.format_matches_for_prompt(matches[:5]))