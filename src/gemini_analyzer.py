import google.generativeai as genai
import json
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
    
    def analyze_matches(self, matches_formatted, stats=None):
        """Analyse les matchs avec Gemini"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Charger statistiques d'apprentissage
        learning_context = ""
        if stats:
            learning_context = f"\n## APPRENTISSAGE\nTaux réussite: {stats.get('win_rate', 0)}%\nErreurs courantes: {stats.get('common_errors', [])}\n"
        
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