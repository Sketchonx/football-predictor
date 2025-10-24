"""
Analyse post-match pour identifier les erreurs et en tirer des conclusions.
Ce module analyse les pronostics perdus pour améliorer les futures prédictions.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai
from config import Config


class PostMatchAnalyzer:
    """Analyse les pronostics perdus pour identifier les causes d'erreur."""

    def __init__(self, config: Config = None):
        """
        Initialise l'analyseur post-match.

        Args:
            config: Configuration de l'application
        """
        self.config = config or Config()

        # Configuration Gemini pour l'analyse
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        self.analysis_file = os.path.join(self.config.DATA_DIR, 'error_analysis.json')
        self.learnings_file = os.path.join(self.config.DATA_DIR, 'learnings.json')

    def analyze_lost_predictions(self, predictions_file: str) -> List[Dict]:
        """
        Analyse tous les pronostics perdus d'un fichier.

        Args:
            predictions_file: Chemin vers le fichier de prédictions

        Returns:
            Liste des analyses d'erreurs
        """
        # Charger les prédictions
        with open(predictions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        analyses = []

        for pred in data.get('recommendations', []):
            # Analyser uniquement les pronostics perdus
            if pred.get('result') == 'lost' and not pred.get('analyzed', False):
                analysis = self._analyze_single_prediction(pred)
                if analysis:
                    analyses.append(analysis)
                    # Marquer comme analysé
                    pred['analyzed'] = True

        # Sauvegarder les prédictions mises à jour
        with open(predictions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Sauvegarder les analyses
        if analyses:
            self._save_analyses(analyses)
            self._update_learnings(analyses)

        return analyses

    def _analyze_single_prediction(self, prediction: Dict) -> Optional[Dict]:
        """
        Analyse un pronostic perdu pour identifier la cause d'erreur.

        Args:
            prediction: Données du pronostic perdu

        Returns:
            Analyse de l'erreur ou None
        """
        match_info = prediction.get('match', {})
        reasoning = prediction.get('reasoning', '')
        bet_type = prediction.get('bet_type', '')
        bet_choice = prediction.get('bet_choice', '')
        final_score = prediction.get('final_score', '')

        # Construire le prompt d'analyse
        prompt = f"""
Tu es un expert en analyse de paris sportifs. Analyse ce pronostic PERDU et identifie pourquoi la prédiction était incorrecte.

**MATCH:**
{match_info.get('home_team')} vs {match_info.get('away_team')}
Compétition: {match_info.get('league')}
Date: {match_info.get('date')}

**PRONOSTIC FAIT:**
Type: {bet_type}
Choix: {bet_choice}
Raisonnement: {reasoning}

**RÉSULTAT RÉEL:**
Score final: {final_score}
Statut: PERDU

**ANALYSE DEMANDÉE:**

1. **Cause principale de l'erreur** (1 phrase concise):
   - Mauvaise appréciation de quoi exactement?

2. **Facteurs manqués** (2-3 points):
   - Quels éléments n'ont pas été correctement évalués?
   - Impact d'absences? Forme récente? Contexte du match?

3. **Conclusion actionnable** (1 phrase):
   - Quelle règle/principe aurait dû être appliqué?

Réponds en JSON:
{{
  "main_cause": "...",
  "missed_factors": ["...", "...", "..."],
  "actionable_conclusion": "...",
  "error_category": "absence_joueur" | "forme_recente" | "contexte_match" | "statistiques_trompeuses" | "surestimation_favori" | "sous_estimation_outsider" | "autre"
}}
"""

        try:
            response = self.model.generate_content(prompt)
            analysis_text = response.text.strip()

            # Extraire le JSON de la réponse
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0].strip()

            analysis = json.loads(analysis_text)

            # Ajouter métadonnées
            analysis['match_id'] = prediction.get('match_id')
            analysis['match'] = match_info
            analysis['bet_type'] = bet_type
            analysis['bet_choice'] = bet_choice
            analysis['final_score'] = final_score
            analysis['analysis_date'] = datetime.now().isoformat()

            return analysis

        except Exception as e:
            print(f"❌ Erreur lors de l'analyse du match {match_info.get('home_team')} vs {match_info.get('away_team')}: {e}")
            return None

    def _save_analyses(self, analyses: List[Dict]):
        """Sauvegarde les analyses d'erreurs."""
        # Charger les analyses existantes
        existing_analyses = []
        if os.path.exists(self.analysis_file):
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                existing_analyses = json.load(f)

        # Ajouter les nouvelles analyses
        existing_analyses.extend(analyses)

        # Sauvegarder
        with open(self.analysis_file, 'w', encoding='utf-8') as f:
            json.dump(existing_analyses, f, ensure_ascii=False, indent=2)

        print(f"✅ {len(analyses)} analyses d'erreurs sauvegardées")

    def _update_learnings(self, analyses: List[Dict]):
        """
        Met à jour le fichier d'apprentissages avec les nouvelles conclusions.

        Args:
            analyses: Liste des analyses d'erreurs
        """
        # Charger les apprentissages existants
        learnings = {
            'last_updated': datetime.now().isoformat(),
            'total_errors_analyzed': 0,
            'categories': {},
            'key_learnings': []
        }

        if os.path.exists(self.learnings_file):
            with open(self.learnings_file, 'r', encoding='utf-8') as f:
                learnings = json.load(f)

        # Mettre à jour les statistiques
        learnings['total_errors_analyzed'] += len(analyses)
        learnings['last_updated'] = datetime.now().isoformat()

        # Compter par catégorie
        for analysis in analyses:
            category = analysis.get('error_category', 'autre')
            if category not in learnings['categories']:
                learnings['categories'][category] = {
                    'count': 0,
                    'examples': []
                }

            learnings['categories'][category]['count'] += 1
            learnings['categories'][category]['examples'].append({
                'match': f"{analysis['match']['home_team']} vs {analysis['match']['away_team']}",
                'conclusion': analysis['actionable_conclusion']
            })

            # Limiter à 5 exemples par catégorie
            if len(learnings['categories'][category]['examples']) > 5:
                learnings['categories'][category]['examples'] = learnings['categories'][category]['examples'][-5:]

        # Extraire les apprentissages clés
        for analysis in analyses:
            learning_entry = {
                'date': analysis['analysis_date'],
                'category': analysis['error_category'],
                'conclusion': analysis['actionable_conclusion']
            }
            learnings['key_learnings'].append(learning_entry)

        # Garder les 20 apprentissages les plus récents
        learnings['key_learnings'] = learnings['key_learnings'][-20:]

        # Sauvegarder
        with open(self.learnings_file, 'w', encoding='utf-8') as f:
            json.dump(learnings, f, ensure_ascii=False, indent=2)

        print(f"✅ Apprentissages mis à jour: {learnings['total_errors_analyzed']} erreurs analysées au total")

    def get_learnings_summary(self) -> str:
        """
        Récupère un résumé des apprentissages pour l'intégrer dans le prompt.

        Returns:
            Résumé des apprentissages en format texte
        """
        if not os.path.exists(self.learnings_file):
            return ""

        with open(self.learnings_file, 'r', encoding='utf-8') as f:
            learnings = json.load(f)

        if learnings['total_errors_analyzed'] == 0:
            return ""

        summary = "\n### APPRENTISSAGES DES ERREURS PASSÉES\n\n"
        summary += f"**{learnings['total_errors_analyzed']} erreurs analysées**\n\n"

        # Top 3 catégories d'erreurs
        sorted_categories = sorted(
            learnings['categories'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:3]

        summary += "**Principales causes d'erreurs:**\n"
        for category, data in sorted_categories:
            summary += f"- {category}: {data['count']} fois\n"

        # Derniers apprentissages clés
        summary += "\n**Conclusions récentes à appliquer:**\n"
        for learning in learnings['key_learnings'][-5:]:
            summary += f"- {learning['conclusion']}\n"

        return summary


def analyze_recent_predictions():
    """Fonction principale pour analyser les prédictions récentes."""
    analyzer = PostMatchAnalyzer()
    config = Config()

    predictions_dir = os.path.join(config.DATA_DIR, 'predictions')

    if not os.path.exists(predictions_dir):
        print("❌ Aucun répertoire de prédictions trouvé")
        return

    # Analyser tous les fichiers de prédictions
    prediction_files = [f for f in os.listdir(predictions_dir) if f.endswith('.json')]

    total_analyses = 0
    for filename in prediction_files:
        filepath = os.path.join(predictions_dir, filename)
        print(f"\n📊 Analyse de {filename}...")
        analyses = analyzer.analyze_lost_predictions(filepath)
        total_analyses += len(analyses)

    print(f"\n✅ Analyse terminée: {total_analyses} erreurs analysées au total")

    # Afficher le résumé des apprentissages
    summary = analyzer.get_learnings_summary()
    if summary:
        print("\n" + "="*60)
        print(summary)
        print("="*60)


if __name__ == '__main__':
    analyze_recent_predictions()
