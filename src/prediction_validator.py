#!/usr/bin/env python3
"""
Validateur de prédictions pour corriger automatiquement les erreurs
notamment les inversions Home/Away
"""

import json
import difflib
from typing import Dict, List, Any


class PredictionValidator:
    """Valide et corrige les prédictions générées par Claude"""

    def __init__(self, original_matches: List[Dict]):
        """
        Args:
            original_matches: Liste des matchs originaux de l'API avec home/away corrects
        """
        self.original_matches = original_matches
        # Créer un index pour accès rapide
        self.matches_index = {}
        for match in original_matches:
            key = self._normalize_team_name(match['home']) + "_" + self._normalize_team_name(match['away'])
            self.matches_index[key] = match

    def _normalize_team_name(self, team_name: str) -> str:
        """Normalise un nom d'équipe pour comparaison"""
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
        name = re.sub(r'\s*\d+\s*', '', name)

        return name.strip()

    def _find_match(self, match_string: str) -> Dict:
        """
        Trouve le match original correspondant à partir d'une string "Team A vs Team B"

        Returns:
            Dict avec 'home', 'away', 'is_inverted'
        """
        # Parser le string du match
        if ' vs ' in match_string:
            parts = match_string.split(' vs ')
        elif ' - ' in match_string:
            parts = match_string.split(' - ')
        else:
            # Format non reconnu, impossible de valider
            return None

        if len(parts) != 2:
            return None

        team1 = parts[0].strip()
        team2 = parts[1].strip()

        team1_norm = self._normalize_team_name(team1)
        team2_norm = self._normalize_team_name(team2)

        # Chercher dans l'ordre normal
        key_normal = team1_norm + "_" + team2_norm
        if key_normal in self.matches_index:
            return {
                'home': self.matches_index[key_normal]['home'],
                'away': self.matches_index[key_normal]['away'],
                'is_inverted': False,
                'original_match': self.matches_index[key_normal]
            }

        # Chercher dans l'ordre inversé
        key_inverted = team2_norm + "_" + team1_norm
        if key_inverted in self.matches_index:
            return {
                'home': self.matches_index[key_inverted]['home'],
                'away': self.matches_index[key_inverted]['away'],
                'is_inverted': True,
                'original_match': self.matches_index[key_inverted]
            }

        # Pas trouvé avec matching exact, essayer fuzzy matching
        for match in self.original_matches:
            home_norm = self._normalize_team_name(match['home'])
            away_norm = self._normalize_team_name(match['away'])

            # Calculer similarité
            sim1_home = difflib.SequenceMatcher(None, team1_norm, home_norm).ratio()
            sim1_away = difflib.SequenceMatcher(None, team2_norm, away_norm).ratio()
            sim2_home = difflib.SequenceMatcher(None, team1_norm, away_norm).ratio()
            sim2_away = difflib.SequenceMatcher(None, team2_norm, home_norm).ratio()

            # Ordre normal
            if sim1_home > 0.8 and sim1_away > 0.8:
                return {
                    'home': match['home'],
                    'away': match['away'],
                    'is_inverted': False,
                    'original_match': match
                }

            # Ordre inversé
            if sim2_home > 0.8 and sim2_away > 0.8:
                return {
                    'home': match['home'],
                    'away': match['away'],
                    'is_inverted': True,
                    'original_match': match
                }

        return None

    def validate_and_fix_predictions(self, predictions: Dict, min_odds: float = 2.00) -> Dict:
        """
        Valide les prédictions et corrige automatiquement les inversions Home/Away
        Filtre également les cotes trop basses

        Args:
            predictions: Dictionnaire JSON des prédictions de Claude
            min_odds: Cote minimale acceptée (défaut: 2.00)

        Returns:
            Dictionnaire JSON corrigé avec métadonnées de validation
        """
        corrections_made = []
        rejected_low_odds = []

        if 'recommendations' not in predictions:
            return predictions

        # Filtrer les recommandations avec cotes trop basses AVANT tout traitement
        valid_recommendations = []

        for i, rec in enumerate(predictions['recommendations']):
            odds = rec.get('odds', 0)

            # Rejeter si cote trop basse
            if odds < min_odds:
                rejected_low_odds.append({
                    'match': rec.get('match', 'Unknown'),
                    'odds': odds,
                    'reason': f'Cote {odds} < minimum {min_odds}'
                })
                corrections_made.append({
                    'match': rec.get('match', 'Unknown'),
                    'issue': 'ODDS_TOO_LOW',
                    'action': f'REJECTED: Cote {odds} < {min_odds} (minimum requis)'
                })
                continue  # Skip cette recommandation

            valid_recommendations.append(rec)

        # Remplacer les recommandations par celles validées
        predictions['recommendations'] = valid_recommendations
        predictions['total_retained'] = len(valid_recommendations)

        # Traiter les inversions Home/Away sur les recommandations restantes
        for i, rec in enumerate(predictions['recommendations']):
            match_string = rec.get('match', '')

            # Trouver le match original
            match_info = self._find_match(match_string)

            if match_info is None:
                corrections_made.append({
                    'match': match_string,
                    'issue': 'MATCH_NOT_FOUND',
                    'action': 'WARNING - Match non trouvé dans les données API'
                })
                continue

            # Si inversion détectée
            if match_info['is_inverted']:
                old_match_string = match_string
                new_match_string = f"{match_info['home']} vs {match_info['away']}"

                # Corriger le string du match
                predictions['recommendations'][i]['match'] = new_match_string

                # Corriger le detailed_analysis si présent
                if 'detailed_analysis' in rec:
                    analysis = rec['detailed_analysis']

                    # Inverser home_team et away_team dans toutes les sections
                    sections_to_swap = [
                        'recent_form',
                        'injuries_suspensions',
                        'schedule_fatigue'
                    ]

                    for section in sections_to_swap:
                        if section in analysis and isinstance(analysis[section], dict):
                            if 'home_team' in analysis[section] and 'away_team' in analysis[section]:
                                # Swap home_team et away_team
                                temp = analysis[section]['home_team']
                                analysis[section]['home_team'] = analysis[section]['away_team']
                                analysis[section]['away_team'] = temp

                corrections_made.append({
                    'match': old_match_string,
                    'issue': 'HOME_AWAY_INVERTED',
                    'action': f'CORRECTED: {old_match_string} → {new_match_string}',
                    'corrected_match': new_match_string
                })

        # Ajouter métadonnées de validation
        predictions['validation'] = {
            'validated': True,
            'corrections_count': len(corrections_made),
            'corrections': corrections_made,
            'rejected_low_odds_count': len(rejected_low_odds),
            'rejected_low_odds': rejected_low_odds
        }

        return predictions

    def generate_validation_report(self, predictions: Dict) -> str:
        """Génère un rapport de validation lisible"""
        if 'validation' not in predictions:
            return "❌ Prédictions non validées"

        validation = predictions['validation']

        report = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += "📋 RAPPORT DE VALIDATION\n"
        report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if validation['corrections_count'] == 0:
            report += "✅ Aucune correction nécessaire\n"
            report += "✅ Toutes les prédictions sont correctes\n"
        else:
            report += f"⚠️  {validation['corrections_count']} correction(s) effectuée(s)\n\n"

            for i, correction in enumerate(validation['corrections'], 1):
                report += f"{i}. {correction['issue']}\n"
                report += f"   Match: {correction['match']}\n"
                report += f"   Action: {correction['action']}\n\n"

        return report
