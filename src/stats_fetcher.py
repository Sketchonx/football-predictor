"""
Module pour récupérer des statistiques RÉELLES via API-Football.
Fournit des données factuelles à jour au lieu de laisser Gemini inventer.
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class StatsFetcher:
    """Récupère les statistiques réelles via API-Football."""

    def __init__(self):
        self.api_key = os.getenv('API_FOOTBALL_KEY')
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {'x-apisports-key': self.api_key}

    def get_team_stats(self, team_id: int, league_id: int, season: int = 2025) -> Dict:
        """
        Récupère les statistiques d'une équipe pour la saison en cours.

        Returns:
            Dict avec forme récente, stats domicile/extérieur, buts marqués/encaissés
        """
        try:
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': team_id,
                'league': league_id,
                'season': season
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()

            if data.get('response'):
                stats = data['response']
                return {
                    'form': stats.get('form', 'N/A'),
                    'goals_for_home': stats['goals']['for']['total']['home'],
                    'goals_for_away': stats['goals']['for']['total']['away'],
                    'goals_against_home': stats['goals']['against']['total']['home'],
                    'goals_against_away': stats['goals']['against']['total']['away'],
                    'wins_home': stats['fixtures']['wins']['home'],
                    'wins_away': stats['fixtures']['wins']['away'],
                    'draws_home': stats['fixtures']['draws']['home'],
                    'draws_away': stats['fixtures']['draws']['away'],
                    'loses_home': stats['fixtures']['loses']['home'],
                    'loses_away': stats['fixtures']['loses']['away']
                }
            return {}
        except Exception as e:
            print(f"Erreur récupération stats équipe {team_id}: {e}")
            return {}

    def get_h2h(self, team1_id: int, team2_id: int, last: int = 5) -> List[Dict]:
        """
        Récupère les dernières confrontations directes entre 2 équipes.

        Returns:
            Liste des derniers matchs H2H avec scores et dates
        """
        try:
            url = f"{self.base_url}/fixtures/headtohead"
            params = {
                'h2h': f"{team1_id}-{team2_id}",
                'last': last
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()

            h2h_matches = []
            for fixture in data.get('response', [])[:last]:
                h2h_matches.append({
                    'date': fixture['fixture']['date'][:10],
                    'home_team': fixture['teams']['home']['name'],
                    'away_team': fixture['teams']['away']['name'],
                    'score': f"{fixture['goals']['home']}-{fixture['goals']['away']}",
                    'winner': fixture['teams']['home']['name'] if fixture['teams']['home']['winner'] else
                             (fixture['teams']['away']['name'] if fixture['teams']['away']['winner'] else 'Nul')
                })

            return h2h_matches
        except Exception as e:
            print(f"Erreur récupération H2H: {e}")
            return []

    def get_team_form(self, team_id: int, last_matches: int = 5) -> List[Dict]:
        """
        Récupère les derniers matchs d'une équipe (forme récente RÉELLE).

        Returns:
            Liste des derniers matchs avec résultats réels
        """
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'last': last_matches
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()

            recent_matches = []
            for fixture in data.get('response', [])[:last_matches]:
                teams = fixture['teams']
                goals = fixture['goals']
                is_home = teams['home']['id'] == team_id

                recent_matches.append({
                    'date': fixture['fixture']['date'][:10],
                    'opponent': teams['away']['name'] if is_home else teams['home']['name'],
                    'location': 'Domicile' if is_home else 'Extérieur',
                    'score': f"{goals['home']}-{goals['away']}",
                    'result': 'V' if (is_home and teams['home']['winner']) or (not is_home and teams['away']['winner']) else
                             ('N' if goals['home'] == goals['away'] else 'D'),
                    'competition': fixture['league']['name']
                })

            return recent_matches
        except Exception as e:
            print(f"Erreur récupération forme équipe {team_id}: {e}")
            return []

    def get_team_injuries(self, team_id: int) -> List[Dict]:
        """
        Récupère les blessures/suspensions actuelles d'une équipe.

        Returns:
            Liste des joueurs absents avec raison
        """
        try:
            url = f"{self.base_url}/injuries"
            params = {'team': team_id}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()

            injuries = []
            for injury in data.get('response', []):
                injuries.append({
                    'player': injury['player']['name'],
                    'type': injury['player']['type'],  # Blessure ou Suspension
                    'reason': injury['player']['reason']
                })

            return injuries
        except Exception as e:
            print(f"Erreur récupération blessures équipe {team_id}: {e}")
            return []

    def get_match_data(self, fixture_id: int) -> Dict:
        """
        Récupère toutes les données d'un match spécifique.

        Returns:
            Dict avec stats complètes du match
        """
        try:
            url = f"{self.base_url}/fixtures"
            params = {'id': fixture_id}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()

            if data.get('response'):
                fixture = data['response'][0]
                return {
                    'home_team_id': fixture['teams']['home']['id'],
                    'away_team_id': fixture['teams']['away']['id'],
                    'home_team': fixture['teams']['home']['name'],
                    'away_team': fixture['teams']['away']['name'],
                    'league_id': fixture['league']['id'],
                    'league_name': fixture['league']['name'],
                    'date': fixture['fixture']['date'],
                    'status': fixture['fixture']['status']['long']
                }
            return {}
        except Exception as e:
            print(f"Erreur récupération match {fixture_id}: {e}")
            return {}

    def build_real_context(self, home_team_id: int, away_team_id: int, league_id: int) -> str:
        """
        Construit un contexte factuel complet pour un match.
        Ce contexte sera injecté dans le prompt Gemini avec des VRAIES données.

        Returns:
            Texte formaté avec toutes les stats réelles
        """
        context = "### DONNÉES RÉELLES ET VÉRIFIÉES\n\n"

        # Stats équipe domicile
        home_stats = self.get_team_stats(home_team_id, league_id)
        if home_stats:
            context += f"**Équipe Domicile - Statistiques saison:**\n"
            context += f"- Domicile: {home_stats['wins_home']}V-{home_stats['draws_home']}N-{home_stats['loses_home']}D\n"
            context += f"- Buts marqués domicile: {home_stats['goals_for_home']}\n"
            context += f"- Buts encaissés domicile: {home_stats['goals_against_home']}\n"
            context += f"- Forme générale: {home_stats['form']}\n\n"

        # Stats équipe extérieur
        away_stats = self.get_team_stats(away_team_id, league_id)
        if away_stats:
            context += f"**Équipe Extérieur - Statistiques saison:**\n"
            context += f"- Extérieur: {away_stats['wins_away']}V-{away_stats['draws_away']}N-{away_stats['loses_away']}D\n"
            context += f"- Buts marqués extérieur: {away_stats['goals_for_away']}\n"
            context += f"- Buts encaissés extérieur: {away_stats['goals_against_away']}\n"
            context += f"- Forme générale: {away_stats['form']}\n\n"

        # Forme récente domicile
        home_form = self.get_team_form(home_team_id, 5)
        if home_form:
            context += f"**Équipe Domicile - 5 derniers matchs (RÉELS):**\n"
            for match in home_form:
                context += f"- {match['date']}: vs {match['opponent']} ({match['location']}) - {match['score']} ({match['result']}) [{match['competition']}]\n"
            context += "\n"

        # Forme récente extérieur
        away_form = self.get_team_form(away_team_id, 5)
        if away_form:
            context += f"**Équipe Extérieur - 5 derniers matchs (RÉELS):**\n"
            for match in away_form:
                context += f"- {match['date']}: vs {match['opponent']} ({match['location']}) - {match['score']} ({match['result']}) [{match['competition']}]\n"
            context += "\n"

        # H2H
        h2h = self.get_h2h(home_team_id, away_team_id, 5)
        if h2h:
            context += f"**Confrontations directes - 5 derniers matchs (RÉELS):**\n"
            for match in h2h:
                context += f"- {match['date']}: {match['home_team']} vs {match['away_team']} - {match['score']} (Vainqueur: {match['winner']})\n"
            context += "\n"

        # Blessures domicile
        home_injuries = self.get_team_injuries(home_team_id)
        if home_injuries:
            context += f"**Équipe Domicile - Absents (RÉELS):**\n"
            for injury in home_injuries:
                context += f"- {injury['player']}: {injury['type']} ({injury['reason']})\n"
            context += "\n"

        # Blessures extérieur
        away_injuries = self.get_team_injuries(away_team_id)
        if away_injuries:
            context += f"**Équipe Extérieur - Absents (RÉELS):**\n"
            for injury in away_injuries:
                context += f"- {injury['player']}: {injury['type']} ({injury['reason']})\n"
            context += "\n"

        context += "**IMPORTANT:** Toutes ces données sont RÉELLES et VÉRIFIÉES via API-Football. Utilise-les pour ton analyse au lieu de ta mémoire.\n"

        return context


if __name__ == '__main__':
    # Test
    fetcher = StatsFetcher()

    # Exemple: Paris SG (id=85) vs Marseille (id=81) en Ligue 1 (id=61)
    print("Test récupération données réelles...")
    context = fetcher.build_real_context(85, 81, 61)
    print(context)
