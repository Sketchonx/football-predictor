#!/usr/bin/env python3
import sys
import os
from datetime import datetime
from match_scraper import MatchScraper
from claude_analyzer import ClaudeAnalyzer  # Remplacé Gemini par Claude
from telegram_sender import TelegramSender
from learning_engine import LearningEngine
from prediction_validator import PredictionValidator  # Validateur pour corriger inversions Home/Away
from config import Config

def main():
    print("🚀 Démarrage analyse football...")
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Récupération matchs
    print("📥 Récupération des matchs...")
    scraper = MatchScraper()
    matches = scraper.get_today_matches()
    print(f"✅ {len(matches)} matchs trouvés")

    if not matches:
        print("❌ Aucun match disponible, arrêt.")
        return


    matches_formatted = scraper.format_matches_for_prompt(matches)
    
    # 2. Récupération stats d'apprentissage
    learning = LearningEngine()
    stats = learning.get_learning_stats()
    
    # 3. Analyse avec Claude (Anthropic)
    print("🤖 Analyse avec Claude en cours...")
    analyzer = ClaudeAnalyzer()
    result = analyzer.analyze_matches(matches_formatted, stats)
    
    if not result:
        print("❌ Erreur analyse")
        return
    
    print(f"✅ Analyse terminée: {len(result.get('recommendations', []))} pronostics")

    # 3b. VALIDATION ET CORRECTION AUTOMATIQUE (Home/Away inversions + cotes trop basses)
    print("🔍 Validation et correction automatique...")
    config = Config()
    validator = PredictionValidator(matches)
    result = validator.validate_and_fix_predictions(result, min_odds=config.MIN_ODDS)

    # Afficher rapport de validation
    validation_report = validator.generate_validation_report(result)
    print(validation_report)

    print(f"✅ Après validation: {len(result.get('recommendations', []))} pronostics retenus")

    # 4. Sauvegarde prédictions
    learning.save_predictions(result, today)
    
    # 5. Envoi Telegram
    if result.get('recommendations'):
        print("📤 Envoi Telegram...")
        sender = TelegramSender()
        sender.send_sync(result)
    else:
        print("ℹ️ Aucun pronostic pertinent, pas d'envoi")

if __name__ == "__main__":
    main()