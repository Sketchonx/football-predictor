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
        """
        Enrichit les données d'un match avec stats API-Football (SMART)

        STRATÉGIE INTELLIGENTE:
        - ALWAYS AVAILABLE: Forme récente, H2H, blessures, stats saison, classement, top scorers/assists
        - MATCH-TIME ONLY: Lineups, odds, stats match, events (seulement <2h avant match)

        Cette approche évite les requêtes inutiles et garantit des données RÉELLES.
        """
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

            # Calculer le temps avant le match
            match_time_str = match.get('time', '')
            time_until_match = None
            try:
                from dateutil import parser
                import pytz
                match_datetime = parser.parse(match_time_str)
                now = datetime.now(pytz.UTC)
                time_until_match = (match_datetime - now).total_seconds() / 3600  # heures
            except:
                time_until_match = 999  # Si erreur, supposer match loin

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

            # 6. PRÉDICTIONS API-FOOTBALL (pour comparaison avec nos analyses) - TOUJOURS DISPONIBLE
            url_predictions = f"https://v3.football.api-sports.io/predictions"
            params_predictions = {'fixture': fixture_id}
            resp_predictions = requests.get(url_predictions, headers=headers, params=params_predictions, timeout=10)
            if resp_predictions.status_code == 200:
                predictions_data = resp_predictions.json().get('response', [])
                if predictions_data and len(predictions_data) > 0:  # Vérifier que les données existent
                    match['api_predictions'] = predictions_data
                else:
                    match['api_predictions'] = []

            # ═══════════════════════════════════════════════════════════════
            # DONNÉES "MATCH-TIME ONLY" - SEULEMENT si match dans <2 heures
            # ═══════════════════════════════════════════════════════════════

            if time_until_match is not None and time_until_match < 2:
                print(f"   ⏰ Match dans {time_until_match:.1f}h - Récupération données temps réel...")

                # 8. COTES EN TEMPS RÉEL (disponible ~2h avant)
                url_odds = f"https://v3.football.api-sports.io/odds"
                params_odds = {'fixture': fixture_id}
                resp_odds = requests.get(url_odds, headers=headers, params=params_odds, timeout=10)
                if resp_odds.status_code == 200:
                    odds_data = resp_odds.json().get('response', [])
                    if odds_data and len(odds_data) > 0:
                        match['odds'] = odds_data

                # 9. COMPOSITIONS D'ÉQUIPE CONFIRMÉES (disponible ~1-2h avant)
                url_lineups = f"https://v3.football.api-sports.io/fixtures/lineups"
                params_lineups = {'fixture': fixture_id}
                resp_lineups = requests.get(url_lineups, headers=headers, params=params_lineups, timeout=10)
                if resp_lineups.status_code == 200:
                    lineups_data = resp_lineups.json().get('response', [])
                    if lineups_data and len(lineups_data) > 0:
                        match['lineups'] = lineups_data

                # 10. ÉVÉNEMENTS DU MATCH (seulement si match en cours ou terminé)
                url_events = f"https://v3.football.api-sports.io/fixtures/events"
                params_events = {'fixture': fixture_id}
                resp_events = requests.get(url_events, headers=headers, params=params_events, timeout=10)
                if resp_events.status_code == 200:
                    events_data = resp_events.json().get('response', [])
                    if events_data and len(events_data) > 0:
                        match['match_events'] = events_data

                # 11. STATISTIQUES DÉTAILLÉES DU MATCH (seulement si match en cours/terminé)
                url_match_stats = f"https://v3.football.api-sports.io/fixtures/statistics"
                params_match_stats = {'fixture': fixture_id}
                resp_match_stats = requests.get(url_match_stats, headers=headers, params=params_match_stats, timeout=10)
                if resp_match_stats.status_code == 200:
                    stats_data = resp_match_stats.json().get('response', [])
                    if stats_data and len(stats_data) > 0:
                        match['match_statistics'] = stats_data
            else:
                print(f"   ⏳ Match dans {time_until_match:.1f}h - Données temps réel non encore disponibles")

            # 11. TOP BUTEURS DE LA LIGUE (cache par ligue pour économiser requêtes)
            if league_id and not hasattr(self, f'_topscorers_cache_{league_id}'):
                url_topscorers = f"https://v3.football.api-sports.io/players/topscorers"
                params_topscorers = {'league': league_id, 'season': season}
                resp_topscorers = requests.get(url_topscorers, headers=headers, params=params_topscorers, timeout=10)
                if resp_topscorers.status_code == 200:
                    setattr(self, f'_topscorers_cache_{league_id}', resp_topscorers.json().get('response', []))
            match['league_topscorers'] = getattr(self, f'_topscorers_cache_{league_id}', [])

            # 12. TOP PASSEURS DE LA LIGUE (cache par ligue)
            if league_id and not hasattr(self, f'_topassists_cache_{league_id}'):
                url_topassists = f"https://v3.football.api-sports.io/players/topassists"
                params_topassists = {'league': league_id, 'season': season}
                resp_topassists = requests.get(url_topassists, headers=headers, params=params_topassists, timeout=10)
                if resp_topassists.status_code == 200:
                    setattr(self, f'_topassists_cache_{league_id}', resp_topassists.json().get('response', []))
            match['league_topassists'] = getattr(self, f'_topassists_cache_{league_id}', [])

            # 13. JOUEURS ÉCARTÉS LONG TERME (sidelined)
            if team_home_id:
                url_sidelined_home = f"https://v3.football.api-sports.io/sidelined"
                params_sidelined_home = {'team': team_home_id}
                resp_sidelined_home = requests.get(url_sidelined_home, headers=headers, params=params_sidelined_home, timeout=10)
                if resp_sidelined_home.status_code == 200:
                    match['home_sidelined'] = resp_sidelined_home.json().get('response', [])

            if team_away_id:
                url_sidelined_away = f"https://v3.football.api-sports.io/sidelined"
                params_sidelined_away = {'team': team_away_id}
                resp_sidelined_away = requests.get(url_sidelined_away, headers=headers, params=params_sidelined_away, timeout=10)
                if resp_sidelined_away.status_code == 200:
                    match['away_sidelined'] = resp_sidelined_away.json().get('response', [])

            # 14. INFO ENTRAÎNEURS (récent, tactiques)
            if team_home_id:
                url_coach_home = f"https://v3.football.api-sports.io/coachs"
                params_coach_home = {'team': team_home_id}
                resp_coach_home = requests.get(url_coach_home, headers=headers, params=params_coach_home, timeout=10)
                if resp_coach_home.status_code == 200:
                    match['home_coach'] = resp_coach_home.json().get('response', [])

            if team_away_id:
                url_coach_away = f"https://v3.football.api-sports.io/coachs"
                params_coach_away = {'team': team_away_id}
                resp_coach_away = requests.get(url_coach_away, headers=headers, params=params_coach_away, timeout=10)
                if resp_coach_away.status_code == 200:
                    match['away_coach'] = resp_coach_away.json().get('response', [])

            # 15. TRANSFERTS RÉCENTS (nouveaux joueurs, adaptations)
            if team_home_id:
                url_transfers_home = f"https://v3.football.api-sports.io/transfers"
                params_transfers_home = {'team': team_home_id}
                resp_transfers_home = requests.get(url_transfers_home, headers=headers, params=params_transfers_home, timeout=10)
                if resp_transfers_home.status_code == 200:
                    match['home_transfers'] = resp_transfers_home.json().get('response', [])[:10]  # 10 derniers transferts

            if team_away_id:
                url_transfers_away = f"https://v3.football.api-sports.io/transfers"
                params_transfers_away = {'team': team_away_id}
                resp_transfers_away = requests.get(url_transfers_away, headers=headers, params=params_transfers_away, timeout=10)
                if resp_transfers_away.status_code == 200:
                    match['away_transfers'] = resp_transfers_away.json().get('response', [])[:10]

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
            if match.get('odds') and len(match['odds']) > 0:
                formatted += "┌─ 💰 COTES EN TEMPS RÉEL (marchés principaux) ─────────┐\n"
                try:
                    for odds_data in match['odds'][:3]:  # Top 3 bookmakers
                        if not isinstance(odds_data, dict):
                            continue
                        bm_name = odds_data.get('bookmaker', {}).get('name', 'Unknown')
                        bets = odds_data.get('bets', [])

                        for bet in bets:
                            bet_name = bet.get('name', '')
                            values = bet.get('values', [])

                            if bet_name == 'Match Winner':
                                formatted += f"│ [{bm_name}] 1X2:\n"
                                for value in values:
                                    formatted += f"│   - {value.get('value', 'N/A')}: {value.get('odd', 'N/A')}\n"
                            elif bet_name == 'Goals Over/Under':
                                formatted += f"│ [{bm_name}] Over/Under:\n"
                                for value in values[:4]:
                                    formatted += f"│   - {value.get('value', 'N/A')}: {value.get('odd', 'N/A')}\n"
                            elif bet_name == 'Both Teams Score':
                                formatted += f"│ [{bm_name}] BTTS:\n"
                                for value in values:
                                    formatted += f"│   - {value.get('value', 'N/A')}: {value.get('odd', 'N/A')}\n"
                    formatted += "└────────────────────────────────────────────────────────┘\n\n"
                except Exception as e:
                    formatted += "│ ⚠️ Erreur parsing cotes - données non disponibles\n"
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

            # 8. COMPOSITIONS D'ÉQUIPE & SYSTÈMES TACTIQUES
            if match.get('lineups'):
                formatted += "┌─ ⚽ COMPOSITIONS & TACTIQUES ──────────────────────────┐\n"
                for lineup in match['lineups']:
                    team_name = lineup.get('team', {}).get('name', 'N/A')
                    formation = lineup.get('formation', 'N/A')
                    coach_name = lineup.get('coach', {}).get('name', 'N/A')

                    emoji = "🏠" if team_name == match['home'] else "✈️"
                    formatted += f"│ {emoji} {team_name}: Formation {formation}\n"
                    formatted += f"│    Entraîneur: {coach_name}\n"

                    # Afficher les 11 titulaires
                    startXI = lineup.get('startXI', [])
                    if startXI:
                        formatted += f"│    Titulaires: "
                        players_list = [p.get('player', {}).get('name', 'N/A') for p in startXI[:11]]
                        formatted += f"{', '.join(players_list[:5])}...\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 9. TOP BUTEURS DE LA LIGUE (menaces offensives)
            if match.get('league_topscorers'):
                formatted += "┌─ ⚽ TOP 10 BUTEURS DE LA LIGUE ────────────────────────┐\n"
                home_team = match['home']
                away_team = match['away']

                for idx, scorer in enumerate(match['league_topscorers'][:10], 1):
                    player_name = scorer.get('player', {}).get('name', 'N/A')
                    team_name = scorer.get('statistics', [{}])[0].get('team', {}).get('name', 'N/A')
                    goals = scorer.get('statistics', [{}])[0].get('goals', {}).get('total', 0)

                    marker = ""
                    if team_name == home_team:
                        marker = "🏠 "
                    elif team_name == away_team:
                        marker = "✈️ "

                    formatted += f"│ {idx:2}. {marker}{player_name} ({team_name}): {goals} buts\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 10. TOP PASSEURS DE LA LIGUE (créativité offensive)
            if match.get('league_topassists'):
                formatted += "┌─ 🎯 TOP 10 PASSEURS DE LA LIGUE ──────────────────────┐\n"
                home_team = match['home']
                away_team = match['away']

                for idx, assister in enumerate(match['league_topassists'][:10], 1):
                    player_name = assister.get('player', {}).get('name', 'N/A')
                    team_name = assister.get('statistics', [{}])[0].get('team', {}).get('name', 'N/A')
                    assists = assister.get('statistics', [{}])[0].get('goals', {}).get('assists', 0)

                    marker = ""
                    if team_name == home_team:
                        marker = "🏠 "
                    elif team_name == away_team:
                        marker = "✈️ "

                    formatted += f"│ {idx:2}. {marker}{player_name} ({team_name}): {assists} passes\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 11. JOUEURS ÉCARTÉS LONG TERME (sidelined)
            if match.get('home_sidelined'):
                formatted += "┌─ 🚑 JOUEURS ÉCARTÉS LONG TERME DOMICILE ──────────────┐\n"
                if len(match['home_sidelined']) == 0:
                    formatted += "│ ✅ Aucun joueur écarté long terme\n"
                else:
                    for sideline in match['home_sidelined'][:5]:
                        player = sideline.get('player', {}).get('name', 'N/A')
                        reason = sideline.get('type', 'N/A')
                        start_date = sideline.get('start', 'N/A')[:10] if sideline.get('start') else 'N/A'
                        formatted += f"│ ⚠️ {player}: {reason} (depuis {start_date})\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            if match.get('away_sidelined'):
                formatted += "┌─ 🚑 JOUEURS ÉCARTÉS LONG TERME EXTÉRIEUR ─────────────┐\n"
                if len(match['away_sidelined']) == 0:
                    formatted += "│ ✅ Aucun joueur écarté long terme\n"
                else:
                    for sideline in match['away_sidelined'][:5]:
                        player = sideline.get('player', {}).get('name', 'N/A')
                        reason = sideline.get('type', 'N/A')
                        start_date = sideline.get('start', 'N/A')[:10] if sideline.get('start') else 'N/A'
                        formatted += f"│ ⚠️ {player}: {reason} (depuis {start_date})\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 12. INFO ENTRAÎNEURS (expérience, arrivée récente)
            if match.get('home_coach'):
                formatted += "┌─ 👔 ENTRAÎNEUR DOMICILE ───────────────────────────────┐\n"
                coach = match['home_coach'][0] if match['home_coach'] else {}
                if coach:
                    coach_name = coach.get('name', 'N/A')
                    coach_age = coach.get('age', 'N/A')
                    nationality = coach.get('nationality', 'N/A')
                    formatted += f"│ Nom: {coach_name} ({nationality}, {coach_age} ans)\n"

                    career = coach.get('career', [])
                    if career:
                        current_team = career[-1]
                        start_date = current_team.get('start', 'N/A')[:10] if current_team.get('start') else 'N/A'
                        formatted += f"│ En poste depuis: {start_date}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            if match.get('away_coach'):
                formatted += "┌─ 👔 ENTRAÎNEUR EXTÉRIEUR ──────────────────────────────┐\n"
                coach = match['away_coach'][0] if match['away_coach'] else {}
                if coach:
                    coach_name = coach.get('name', 'N/A')
                    coach_age = coach.get('age', 'N/A')
                    nationality = coach.get('nationality', 'N/A')
                    formatted += f"│ Nom: {coach_name} ({nationality}, {coach_age} ans)\n"

                    career = coach.get('career', [])
                    if career:
                        current_team = career[-1]
                        start_date = current_team.get('start', 'N/A')[:10] if current_team.get('start') else 'N/A'
                        formatted += f"│ En poste depuis: {start_date}\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            # 13. TRANSFERTS RÉCENTS (nouveaux joueurs, adaptation)
            if match.get('home_transfers'):
                formatted += "┌─ 🔄 TRANSFERTS RÉCENTS DOMICILE (derniers) ───────────┐\n"
                if len(match['home_transfers']) == 0:
                    formatted += "│ ℹ️ Aucun transfert récent\n"
                else:
                    for transfer in match['home_transfers'][:5]:
                        player_name = transfer.get('player', {}).get('name', 'N/A')
                        transfer_type = transfer.get('transfers', [{}])[0].get('type', 'N/A')
                        from_team = transfer.get('transfers', [{}])[0].get('teams', {}).get('out', {}).get('name', 'N/A')
                        to_team = transfer.get('transfers', [{}])[0].get('teams', {}).get('in', {}).get('name', 'N/A')
                        date = transfer.get('transfers', [{}])[0].get('date', 'N/A')[:10] if transfer.get('transfers', [{}])[0].get('date') else 'N/A'

                        if to_team == match['home']:
                            formatted += f"│ ⬇️ {player_name}: {from_team} → {to_team} ({transfer_type}, {date})\n"
                        elif from_team == match['home']:
                            formatted += f"│ ⬆️ {player_name}: {from_team} → {to_team} ({transfer_type}, {date})\n"
                formatted += "└────────────────────────────────────────────────────────┘\n\n"

            if match.get('away_transfers'):
                formatted += "┌─ 🔄 TRANSFERTS RÉCENTS EXTÉRIEUR (derniers) ──────────┐\n"
                if len(match['away_transfers']) == 0:
                    formatted += "│ ℹ️ Aucun transfert récent\n"
                else:
                    for transfer in match['away_transfers'][:5]:
                        player_name = transfer.get('player', {}).get('name', 'N/A')
                        transfer_type = transfer.get('transfers', [{}])[0].get('type', 'N/A')
                        from_team = transfer.get('transfers', [{}])[0].get('teams', {}).get('out', {}).get('name', 'N/A')
                        to_team = transfer.get('transfers', [{}])[0].get('teams', {}).get('in', {}).get('name', 'N/A')
                        date = transfer.get('transfers', [{}])[0].get('date', 'N/A')[:10] if transfer.get('transfers', [{}])[0].get('date') else 'N/A'

                        if to_team == match['away']:
                            formatted += f"│ ⬇️ {player_name}: {from_team} → {to_team} ({transfer_type}, {date})\n"
                        elif from_team == match['away']:
                            formatted += f"│ ⬆️ {player_name}: {from_team} → {to_team} ({transfer_type}, {date})\n"
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