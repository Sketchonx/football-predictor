import google.generativeai as genai
import json
import os
from datetime import datetime
from config import Config

class GeminiAnalyzer:
    def __init__(self):
        self.config = Config()
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def load_prompt_template(self):
        """Charge le prompt depuis le fichier"""
        try:
            with open('prompts/base_prompt.txt', 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return self._get_default_prompt()
    
    def _get_default_prompt(self):
        """Prompt par défaut optimisé"""
        return """# ANALYSEUR FOOTBALL PROFESSIONNEL

Date: {date}
Version: {version}

## MISSION
Analyser matchs européens avec probabilité gain ≥75%, cote 1.50-4.00.

## COMPÉTITIONS
✅ Ligues européennes, Champions/Europa/Conference League, Qualifications Mondial/Euro
❌ Amicaux, Hors Europe

## MÉTHODOLOGIE
1. Forme récente (10 matchs): buts, xG, possession
2. Effectif: blessures, suspensions, fatigue (calendrier 7j)
3. H2H: 5 derniers matchs
4. Contexte: enjeu (titre/maintien/qualification)
5. Tactique: systèmes, compositions probables

## CRITÈRES ÉLIMINATION
- Incertitude composition >50%
- Cote favorite <1.40 (trop sûr)
- Enjeu faible

## TYPES PARIS
1X2, Over/Under 2.5, BTTS, Handicap, Corners (si pertinent)

## OUTPUT (JSON strict)
{{
  "analysis_date": "{date}",
  "total_analyzed": X,
  "recommendations": [
    {{
      "match": "Équipe A vs Équipe B",
      "competition": "...",
      "kickoff": "20h45",
      "analysis": "Synthèse 3-4 phrases max, facteurs décisifs uniquement",
      "critical_factors": ["Facteur 1", "Facteur 2"],
      "bet_type": "1X2 / OU / BTTS / Handicap",
      "prediction": "1 (Victoire A) / 2 / X / Over 2.5 / etc",
      "odds": 1.85,
      "confidence": 78
    }}
  ],
  "combined_bet": {{
    "matches": ["Match 1", "Match 2"],
    "total_odds": 3.15,
    "confidence": 72,
    "reasoning": "1 phrase justification"
  }}
}}

## RÈGLES
- Max {max_predictions} pronostics
- Confiance minimum {min_confidence}%
- Cotes {min_odds}-{max_odds}
- Envoyer si ≥1 match pertinent
- Pas de répétition
- Analyse = preuve de réflexion

{matches_list}

RÉPONDS UNIQUEMENT EN JSON VALIDE. PAS DE MARKDOWN, PAS DE TEXTE HORS JSON."""
    
    def _load_learnings(self):
        """Charge les apprentissages des erreurs passées."""
        learnings_file = os.path.join(self.config.DATA_DIR, 'learnings.json')

        if not os.path.exists(learnings_file):
            return ""

        try:
            with open(learnings_file, 'r', encoding='utf-8') as f:
                learnings = json.load(f)

            if learnings['total_errors_analyzed'] == 0:
                return ""

            # Construire le contexte d'apprentissage
            context = "\n\n## ⚠️ APPRENTISSAGES DES ERREURS PASSÉES\n\n"
            context += f"**{learnings['total_errors_analyzed']} erreurs analysées** - Applique ces conclusions pour éviter les mêmes erreurs.\n\n"

            # Top 3 catégories d'erreurs
            if learnings['categories']:
                sorted_categories = sorted(
                    learnings['categories'].items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:3]

                context += "### Principales causes d'erreurs:\n"
                for category, data in sorted_categories:
                    context += f"- **{category.replace('_', ' ').title()}** ({data['count']} fois)\n"
                    # Ajouter un exemple de conclusion
                    if data['examples']:
                        context += f"  → Exemple: {data['examples'][-1]['conclusion']}\n"

            # Dernières conclusions actionnables
            if learnings.get('key_learnings'):
                context += "\n### ⚡ Règles à appliquer MAINTENANT:\n"
                for learning in learnings['key_learnings'][-5:]:
                    context += f"- {learning['conclusion']}\n"

            context += "\n**IMPORTANT**: Vérifie systématiquement ces points avant chaque pronostic.\n\n"

            return context

        except Exception as e:
            print(f"⚠️ Erreur chargement apprentissages: {e}")
            return ""

    def analyze_matches(self, matches_formatted, stats=None):
        """Analyse les matchs avec Gemini"""
        today = datetime.now().strftime('%Y-%m-%d')

        # Charger les apprentissages des erreurs passées
        learning_context = self._load_learnings()

        prompt_template = self.load_prompt_template()
        prompt = prompt_template.format(
            date=today,
            version="1.0",
            max_predictions=self.config.MAX_PREDICTIONS,
            min_confidence=self.config.MIN_CONFIDENCE,
            min_odds=self.config.MIN_ODDS,
            max_odds=self.config.MAX_ODDS,
            matches_list=matches_formatted
        ) + learning_context
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Nettoyer markdown si présent
            result_text = result_text.replace('```json', '').replace('```', '').strip()

            # Parser JSON
            result = json.loads(result_text)

            # Limiter au nombre maximum de prédictions configuré
            if 'recommendations' in result and len(result['recommendations']) > self.config.MAX_PREDICTIONS:
                result['recommendations'] = result['recommendations'][:self.config.MAX_PREDICTIONS]
                result['total_retained'] = len(result['recommendations'])

            return result
        
        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON: {e}")
            print(f"Réponse brute: {response.text[:500]}")
            return None
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return None

# Test
if __name__ == "__main__":
    analyzer = GeminiAnalyzer()
    test_matches = "1. PSG vs Bayern\n   Champions League\n   21h00"
    result = analyzer.analyze_matches(test_matches)
    print(json.dumps(result, indent=2, ensure_ascii=False))