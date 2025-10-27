#!/usr/bin/env python3
"""
Module de mise à jour automatique des résultats
Récupère les scores via API-Football et met à jour les pronostics
"""

import sys
sys.path.insert(0, 'src')
import requests
import os
from datetime import datetime
from performance_tracker import PerformanceTracker
from config import Config

class AutoResultUpdater:
    def __init__(self):
        self.tracker = PerformanceTracker()
        self.config = Config()
        self.api_key = os.getenv('API_FOOTBALL_KEY')

    def normalize_team_name(self, team_name):
        """
        Normalise les noms d'équipes pour améliorer le matching
        Supprime suffixes communs, articles, et caractères spéciaux
        """
        name = team_name.lower().strip()

        # Supprimer suffixes courants
        suffixes = [' kv', ' fc', ' sc', ' sv', ' ac', ' as', ' bv', ' cf', ' afc', ' ssc']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Supprimer préfixes courants
        prefixes = ['fc ', 'sc ', 'sv ', 'ac ', 'as ', 'bv ', 'cf ', 'afc ', 'ssc ']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]

        # Supprimer numéros (ex: "05" dans "FSV Mainz 05")
        import re
        name = re.sub(r'\s*\d+\s*$', '', name)

        return name.strip()

    def teams_match(self, pred_team, api_team):
        """
        Vérifie si deux noms d'équipes correspondent
        Utilise plusieurs stratégies pour gérer les variations de noms
        """
        pred_norm = self.normalize_team_name(pred_team)
        api_norm = self.normalize_team_name(api_team)

        # Matching exact après normalisation
        if pred_norm == api_norm:
            return True

        # Matching si l'un contient l'autre (après normalisation)
        if pred_norm in api_norm or api_norm in pred_norm:
            return True

        # Matching par mots clés principaux (au moins 2 mots en commun)
        pred_words = set(pred_norm.split())
        api_words = set(api_norm.split())
        common_words = pred_words & api_words

        if len(common_words) >= 2:
            return True

        # Matching si un seul mot mais significatif (plus de 4 lettres)
        if len(common_words) == 1:
            word = list(common_words)[0]
            if len(word) > 4:
                return True

        return False

    def get_match_result(self, home_team, away_team, match_date):
        """Récupère le résultat d'un match via API-Football"""
        if not self.api_key:
            print("⚠️  API_FOOTBALL_KEY non configurée")
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

            if data.get('response'):
                for fixture in data['response']:
                    home = fixture['teams']['home']['name']
                    away = fixture['teams']['away']['name']

                    # Vérifier si c'est le bon match (avec matching amélioré)
                    # Tester les 2 ordres possibles car les prédictions peuvent avoir Home/Away inversé
                    match_found = False
                    is_inverted = False

                    # Ordre normal
                    if self.teams_match(home_team, home) and self.teams_match(away_team, away):
                        match_found = True
                        is_inverted = False
                    # Ordre inversé (bug dans les prédictions)
                    elif self.teams_match(home_team, away) and self.teams_match(away_team, home):
                        match_found = True
                        is_inverted = True
                        print(f"   ⚠️  INVERSION DÉTECTÉE: Home/Away corrigé automatiquement")

                    if match_found:
                        status = fixture['fixture']['status']['short']

                        # Match terminé ?
                        if status in ['FT', 'AET', 'PEN']:
                            home_goals = fixture['goals']['home']
                            away_goals = fixture['goals']['away']

                            return {
                                'home_team': home,
                                'away_team': away,
                                'home_goals': home_goals,
                                'away_goals': away_goals,
                                'status': status,
                                'score': f"{home_goals}-{away_goals}",
                                'was_inverted': is_inverted  # Signaler si inversion corrigée
                            }

            return None

        except Exception as e:
            print(f"❌ Erreur API-Football: {e}")
            return None

    def check_prediction_result(self, prediction, match_result):
        """
        Vérifie si le pronostic est gagné ou perdu selon le résultat
        """
        if not match_result:
            return None

        home_goals = match_result['home_goals']
        away_goals = match_result['away_goals']
        bet_type = prediction['bet_type']
        pred_text = prediction['prediction'].lower()

        # 1X2
        if bet_type == "1X2":
            if "1" in pred_text or "victoire" in pred_text and prediction['match'].split(' vs ')[0] in pred_text:
                return 'win' if home_goals > away_goals else 'loss'
            elif "2" in pred_text or "victoire" in pred_text and prediction['match'].split(' vs ')[1] in pred_text:
                return 'win' if away_goals > home_goals else 'loss'
            elif "x" in pred_text.lower() or "nul" in pred_text:
                return 'win' if home_goals == away_goals else 'loss'

        # Handicap
        elif "handicap" in bet_type.lower():
            if "-1.5" in bet_type or "-1.5" in pred_text:
                # Vérifier qui doit gagner avec handicap
                if "1" in pred_text or prediction['match'].split(' vs ')[0] in pred_text:
                    return 'win' if (home_goals - away_goals) >= 2 else 'loss'
                else:
                    return 'win' if (away_goals - home_goals) >= 2 else 'loss'

        # Over/Under 2.5
        elif "over" in bet_type.lower() or "under" in bet_type.lower():
            total_goals = home_goals + away_goals
            if "over" in pred_text.lower():
                return 'win' if total_goals > 2.5 else 'loss'
            elif "under" in pred_text.lower():
                return 'win' if total_goals < 2.5 else 'loss'

        # BTTS (Both Teams To Score)
        elif "btts" in bet_type.lower():
            both_scored = home_goals > 0 and away_goals > 0
            if "yes" in pred_text.lower():
                return 'win' if both_scored else 'loss'
            else:
                return 'win' if not both_scored else 'loss'

        return None

    def update_pending_predictions(self):
        """Met à jour tous les pronostics en attente"""
        print("🔄 Mise à jour automatique des résultats...\n")

        predictions = self.tracker.get_all_predictions()
        pending = [p for p in predictions if p['result'] not in ['win', 'loss']]

        if not pending:
            print("✅ Aucun pronostic en attente!")
            return

        print(f"📋 {len(pending)} pronostics à vérifier\n")

        updated = 0
        not_finished = 0
        errors = 0

        for pred in pending:
            print(f"🔍 Vérification: {pred['match']}")

            # Extraire les équipes
            teams = pred['match'].split(' vs ')
            if len(teams) != 2:
                print(f"   ⚠️  Format de match invalide")
                errors += 1
                continue

            home_team = teams[0].strip()
            away_team = teams[1].strip()

            # Récupérer le résultat
            match_result = self.get_match_result(home_team, away_team, pred['date'])

            if not match_result:
                print(f"   ⏳ Match non terminé ou non trouvé")
                not_finished += 1
                continue

            # Vérifier le pronostic
            result = self.check_prediction_result(pred, match_result)

            if result:
                # Enregistrer le résultat
                self.tracker.record_result(
                    pred['id'],
                    result,
                    match_result['score']
                )

                emoji = "✅" if result == 'win' else "❌"
                print(f"   {emoji} {result.upper()} - Score: {match_result['score']}")
                updated += 1
            else:
                print(f"   ⚠️  Impossible de déterminer le résultat")
                errors += 1

        # Résumé
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DE LA MISE À JOUR")
        print("="*60)
        print(f"✅ Mis à jour: {updated}")
        print(f"⏳ Non terminés: {not_finished}")
        print(f"⚠️  Erreurs: {errors}")

        if updated > 0:
            print("\n📈 STATISTIQUES MISES À JOUR:")
            stats = self.tracker.calculate_statistics()
            print(f"   Taux de réussite: {stats['win_rate']:.1f}%")
            print(f"   Pronostics: {stats['total_wins']}/{stats['completed']}")
            print(f"   En attente: {stats['pending']}")

        return updated


if __name__ == "__main__":
    updater = AutoResultUpdater()
    updater.update_pending_predictions()
