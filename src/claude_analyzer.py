"""
Analyseur utilisant Claude (Anthropic) au lieu de Gemini.
Claude est plus rigoureux, moins sujet aux hallucinations, et meilleur pour suivre des instructions complexes.
"""

import anthropic
import json
import os
from datetime import datetime
from config import Config


class ClaudeAnalyzer:
    """Analyse les matchs de football avec Claude API."""

    def __init__(self):
        self.config = Config()
        self.api_key = os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY manquante dans .env")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        # Utiliser Claude 3.5 Sonnet - meilleur rapport qualité/prix/performance
        self.model = "claude-3-5-sonnet-20241022"

    def load_prompt_template(self):
        """Charge le prompt depuis le fichier."""
        try:
            with open('prompts/base_prompt.txt', 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return self._get_default_prompt()

    def _get_default_prompt(self):
        """Prompt par défaut si fichier non trouvé."""
        return """Analyse ces matchs de football et fournis des pronostics VALUE BET.

RÈGLES:
- Cotes minimum: 1.70
- Focus sur où le marché se TROMPE
- Pas de paris évidents
- 3-5 pronostics de QUALITÉ maximum
- Combiné OBLIGATOIRE

Réponds en JSON valide."""

    def analyze_matches(self, matches_formatted, stats=None):
        """Analyse les matchs avec Claude."""
        today = datetime.now().strftime('%Y-%m-%d')

        prompt_template = self.load_prompt_template()
        prompt = prompt_template.format(
            date=today,
            version="2.0-Claude",
            max_predictions=self.config.MAX_PREDICTIONS,
            min_confidence=self.config.MIN_CONFIDENCE,
            min_odds=self.config.MIN_ODDS,
            max_odds=self.config.MAX_ODDS,
            matches_list=matches_formatted
        )

        # Système de retry pour Claude
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"🤖 Analyse avec Claude (tentative {attempt + 1}/{max_retries})...")

                # Appel API Claude avec streaming désactivé
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=8000,  # Claude peut générer de longues analyses
                    temperature=0.3,  # Raisonnement rigoureux et cohérent
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                # Extraire le texte de la réponse
                result_text = message.content[0].text.strip()

                # Nettoyer markdown si présent
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0].strip()
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0].strip()

                # Nettoyer les caractères invisibles
                result_text = result_text.replace('\u200b', '').replace('\ufeff', '')

                # Trouver le premier { et le dernier }
                start = result_text.find('{')
                end = result_text.rfind('}')

                if start != -1 and end != -1:
                    result_text = result_text[start:end+1]

                # Parser JSON
                result = json.loads(result_text)

                # Limiter au nombre maximum de prédictions
                if 'recommendations' in result and len(result['recommendations']) > self.config.MAX_PREDICTIONS:
                    result['recommendations'] = result['recommendations'][:self.config.MAX_PREDICTIONS]
                    result['total_retained'] = len(result['recommendations'])

                print(f"✅ Analyse Claude réussie ({len(result.get('recommendations', []))} pronostics)")
                return result

            except json.JSONDecodeError as e:
                print(f"⚠️ Tentative {attempt + 1}/{max_retries} - Erreur parsing JSON: {e}")
                if attempt < max_retries - 1:
                    print("🔄 Nouvelle tentative avec Claude...")
                    continue
                else:
                    print(f"❌ Échec après {max_retries} tentatives")
                    print(f"Réponse brute: {result_text[:500] if 'result_text' in locals() else 'N/A'}")
                    return None

            except anthropic.APIError as e:
                print(f"❌ Erreur API Claude: {e}")
                if attempt < max_retries - 1:
                    print("🔄 Nouvelle tentative...")
                    continue
                return None

            except Exception as e:
                print(f"❌ Erreur inattendue: {e}")
                return None

        return None


# Test
if __name__ == "__main__":
    try:
        analyzer = ClaudeAnalyzer()
        test_matches = """
MATCHS DU JOUR:

1. AC Milan vs Pisa
   Serie A | 18:45

2. Real Sociedad vs Sevilla
   La Liga | 19:00
"""
        result = analyzer.analyze_matches(test_matches)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"❌ {e}")
        print("Ajoutez ANTHROPIC_API_KEY dans votre fichier .env")
