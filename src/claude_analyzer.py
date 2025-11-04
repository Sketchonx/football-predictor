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
        # Utiliser Claude Sonnet 4.5 (le meilleur modèle actuel - mai 2025)
        self.model = "claude-sonnet-4-20250514"

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

        # Intégrer les apprentissages des erreurs passées
        learnings_summary = self._get_learnings()

        prompt = prompt_template.format(
            date=today,
            version="2.0-Claude",
            max_predictions=self.config.MAX_PREDICTIONS,
            min_confidence=self.config.MIN_CONFIDENCE,
            min_odds=self.config.MIN_ODDS,
            max_odds=self.config.MAX_ODDS,
            matches_list=matches_formatted
        )

        # DEBUG: Sauvegarder le prompt pour vérification
        try:
            with open(f'data/debug_prompt_{today}.txt', 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"🐛 DEBUG: Prompt sauvegardé dans data/debug_prompt_{today}.txt ({len(prompt)} caractères)")
        except Exception as e:
            print(f"⚠️ Impossible de sauvegarder debug prompt: {e}")

        # Ajouter les apprentissages si disponibles
        if learnings_summary:
            prompt = prompt + "\n\n" + learnings_summary

        # Système de retry pour Claude avec backoff exponentiel
        max_retries = 5  # Augmenté de 2 à 5 pour gérer les surcharges
        import time

        for attempt in range(max_retries):
            try:
                print(f"🤖 Analyse avec Claude (tentative {attempt + 1}/{max_retries})...")

                # Appel API Claude avec streaming activé pour longues requêtes
                result_text = ""
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=32000,  # AUGMENTÉ: permet des analyses beaucoup plus détaillées sans troncature
                    temperature=0.3,  # Raisonnement rigoureux et cohérent
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                ) as stream:
                    for text in stream.text_stream:
                        result_text += text

                result_text = result_text.strip()

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
                    # Attendre avant de retry (backoff exponentiel)
                    wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
                    print(f"⏳ Attente {wait_time}s avant nouvelle tentative...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Échec après {max_retries} tentatives")
                    print(f"Réponse brute: {result_text[:500] if 'result_text' in locals() else 'N/A'}")
                    return None

            except anthropic.APIError as e:
                error_str = str(e)
                print(f"❌ Erreur API Claude: {e}")

                # Si c'est une erreur de surcharge (529) ou rate limit (429), attendre plus longtemps
                if '529' in error_str or 'overloaded' in error_str.lower():
                    if attempt < max_retries - 1:
                        # Attendre plus longtemps pour les surcharges (backoff exponentiel agressif)
                        wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s, 40s, 80s
                        print(f"⏳ Serveurs Claude surchargés. Attente {wait_time}s avant nouvelle tentative...")
                        time.sleep(wait_time)
                        continue
                elif '429' in error_str:
                    if attempt < max_retries - 1:
                        # Rate limit - attendre encore plus longtemps
                        wait_time = 10 * (2 ** attempt)  # 10s, 20s, 40s, 80s, 160s
                        print(f"⏳ Rate limit atteint. Attente {wait_time}s avant nouvelle tentative...")
                        time.sleep(wait_time)
                        continue
                else:
                    # Autre erreur API - retry avec délai normal
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"⏳ Attente {wait_time}s avant nouvelle tentative...")
                        time.sleep(wait_time)
                        continue

                print(f"❌ Échec après {max_retries} tentatives")
                return None

            except Exception as e:
                print(f"❌ Erreur inattendue: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ Attente {wait_time}s avant nouvelle tentative...")
                    time.sleep(wait_time)
                    continue
                return None

        return None

    def _get_learnings(self):
        """Récupère les apprentissages des erreurs passées."""
        try:
            learnings_file = os.path.join('data', 'learnings.json')
            if not os.path.exists(learnings_file):
                return ""

            with open(learnings_file, 'r', encoding='utf-8') as f:
                learnings = json.load(f)

            if learnings.get('total_errors_analyzed', 0) == 0:
                return ""

            summary = "\n\n---\n\n## 🎓 APPRENTISSAGES DES ERREURS PASSÉES\n\n"
            summary += f"**{learnings['total_errors_analyzed']} erreurs analysées précédemment.**\n\n"

            # Top catégories d'erreurs
            if learnings.get('categories'):
                sorted_categories = sorted(
                    learnings['categories'].items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:3]

                summary += "**⚠️ Principales causes d'erreurs à éviter :**\n"
                for category, data in sorted_categories:
                    summary += f"- **{category}** : {data['count']} fois\n"

            # Conclusions récentes à appliquer
            if learnings.get('key_learnings'):
                summary += "\n**💡 Règles apprises (à IMPÉRATIVEMENT appliquer) :**\n"
                for learning in learnings['key_learnings'][-5:]:
                    summary += f"- {learning['conclusion']}\n"

            summary += "\n**→ Prends en compte ces apprentissages dans ton analyse actuelle.**\n"

            return summary

        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des apprentissages: {e}")
            return ""


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
