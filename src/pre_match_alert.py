#!/usr/bin/env python3
"""
Module d'alerte pré-match - Détecte les changements critiques
Vérifie les compositions confirmées vs prédictions initiales
Envoie une alerte Telegram si changements importants (joueurs clés, tactique)
"""

import sys
sys.path.insert(0, 'src')
import json
import os
import requests
from datetime import datetime, timedelta
import pytz
from telegram_sender import TelegramSender
from config import Config

class PreMatchAlertSystem:
    def __init__(self):
        self.config = Config()
        self.api_key = os.getenv('API_FOOTBALL_KEY')
        self.telegram = TelegramSender()
        self.tz = pytz.timezone(self.config.TIMEZONE)

    def load_today_predictions(self):
        """Charge les prédictions du jour"""
        today = datetime.now(self.tz).strftime('%Y-%m-%d')
        pred_file = f'data/predictions/{today}.json'

        if not os.path.exists(pred_file):
            print(f"❌ Aucune prédiction pour {today}")
            return None

        with open(pred_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_match_lineup(self, fixture_id):
        """Récupère la composition d'un match via API-Football"""
        if not self.api_key:
            return None

        try:
            url = "https://v3.football.api-sports.io/fixtures/lineups"
            headers = {'x-apisports-key': self.api_key}
            params = {'fixture': fixture_id}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()

            if data.get('response'):
                return data['response']
            return None

        except Exception as e:
            print(f"❌ Erreur API lineups: {e}")
            return None

    def find_fixture_id(self, match_name, match_date):
        """Trouve le fixture_id d'un match"""
        if not self.api_key:
            return None

        try:
            url = "https://v3.football.api-sports.io/fixtures"
            headers = {'x-apisports-key': self.api_key}
            params = {
                'date': match_date,
                'timezone': self.config.TIMEZONE
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()

            # Parser le nom du match
            teams = match_name.split(' vs ')
            if len(teams) != 2:
                return None

            home_pred, away_pred = teams[0].strip(), teams[1].strip()

            # Chercher le match correspondant
            for fixture in data.get('response', []):
                home_api = fixture['teams']['home']['name']
                away_api = fixture['teams']['away']['name']

                # Matching souple
                if (home_pred.lower() in home_api.lower() or home_api.lower() in home_pred.lower()) and \
                   (away_pred.lower() in away_api.lower() or away_api.lower() in away_pred.lower()):
                    return fixture['fixture']['id']

            return None

        except Exception as e:
            print(f"❌ Erreur recherche fixture: {e}")
            return None

    def extract_key_players(self, lineup_data):
        """Extrait les joueurs clés d'une composition"""
        key_players = []

        if not lineup_data:
            return key_players

        for team in lineup_data:
            team_name = team.get('team', {}).get('name', '')
            formation = team.get('formation', '')

            # Joueurs titulaires
            starters = team.get('startXI', [])
            for player_info in starters:
                player = player_info.get('player', {})
                key_players.append({
                    'team': team_name,
                    'name': player.get('name', ''),
                    'number': player.get('number', ''),
                    'pos': player.get('pos', ''),
                    'status': 'starter'
                })

        return key_players

    def detect_critical_changes(self, prediction, lineup_data):
        """Détecte les changements critiques entre prédiction et composition réelle"""
        changes = []

        if not lineup_data:
            return changes

        # Extraire les absences mentionnées dans la prédiction
        injuries_home = prediction.get('detailed_analysis', {}).get('injuries_suspensions', {}).get('home_team', {}).get('absent', [])
        injuries_away = prediction.get('detailed_analysis', {}).get('injuries_suspensions', {}).get('away_team', {}).get('absent', [])

        # Joueurs clés de la composition réelle
        real_players = self.extract_key_players(lineup_data)

        # Détecter joueurs blessés qui finalement jouent
        for injury in injuries_home + injuries_away:
            player_name = injury.split('(')[0].strip() if '(' in injury else injury.strip()

            # Chercher si ce joueur est finalement titulaire
            for real_player in real_players:
                if player_name.lower() in real_player['name'].lower() or \
                   real_player['name'].lower() in player_name.lower():
                    changes.append({
                        'type': 'RETOUR_SURPRISE',
                        'player': real_player['name'],
                        'team': real_player['team'],
                        'details': f"⚠️ {real_player['name']} annoncé blessé mais TITULAIRE !"
                    })

        # Détecter changements tactiques majeurs
        for team_lineup in lineup_data:
            team_name = team_lineup.get('team', {}).get('name', '')
            formation = team_lineup.get('formation', '')

            if formation:
                changes.append({
                    'type': 'FORMATION',
                    'team': team_name,
                    'formation': formation,
                    'details': f"📋 {team_name} joue en {formation}"
                })

        return changes

    def check_matches_for_alerts(self):
        """Vérifie tous les matchs du jour pour détecter des changements"""
        predictions = self.load_today_predictions()

        if not predictions:
            return

        print("🔍 Vérification des changements pré-match...")

        today = datetime.now(self.tz).strftime('%Y-%m-%d')
        alerts = []

        for rec in predictions.get('recommendations', []):
            match_name = rec['match']
            kickoff = rec['kickoff']

            print(f"\n📊 Analyse: {match_name} ({kickoff})")

            # Trouver le fixture_id
            fixture_id = self.find_fixture_id(match_name, today)

            if not fixture_id:
                print(f"   ⏭️  Fixture non trouvé")
                continue

            # Récupérer la composition
            lineup_data = self.get_match_lineup(fixture_id)

            if not lineup_data:
                print(f"   ⏳ Composition pas encore disponible")
                continue

            # Détecter changements
            changes = self.detect_critical_changes(rec, lineup_data)

            if changes:
                critical_changes = [c for c in changes if c['type'] == 'RETOUR_SURPRISE']

                if critical_changes:
                    alerts.append({
                        'match': match_name,
                        'kickoff': kickoff,
                        'changes': critical_changes,
                        'prediction': rec['prediction'],
                        'confidence': rec['confidence']
                    })
                    print(f"   ⚠️  {len(critical_changes)} changement(s) critique(s) détecté(s)")
                else:
                    print(f"   ✅ Composition conforme aux attentes")

        # Envoyer alertes Telegram si changements critiques
        if alerts:
            self.send_telegram_alert(alerts)
        else:
            print("\n✅ Aucun changement critique détecté")

    def send_telegram_alert(self, alerts):
        """Envoie une alerte Telegram pour changements critiques"""
        message = "🚨 **ALERTE PRÉ-MATCH - CHANGEMENTS DÉTECTÉS**\n\n"

        for alert in alerts:
            message += f"⚽ **{alert['match']}** ({alert['kickoff']})\n"
            message += f"📊 Prédiction initiale: {alert['prediction']} ({alert['confidence']}% confiance)\n\n"

            for change in alert['changes']:
                message += f"{change['details']}\n"

            message += f"\n💡 **Impact possible:** Ce changement peut affecter l'analyse initiale.\n"
            message += f"Réévaluez votre pari en tenant compte de cette information.\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━━\n\n"

        message += f"🤖 Alerte automatique - {datetime.now(self.tz).strftime('%H:%M')}\n"

        print(f"\n📤 Envoi alerte Telegram...")
        success = self.telegram.send_message(message)

        if success:
            print("✅ Alerte envoyée avec succès")
        else:
            print("❌ Échec envoi alerte")

def main():
    print("🚀 Démarrage système d'alerte pré-match...")

    alerter = PreMatchAlertSystem()
    alerter.check_matches_for_alerts()

    print("\n✅ Vérification terminée")

if __name__ == '__main__':
    main()
