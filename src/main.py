#!/usr/bin/env python3
import sys
from datetime import datetime
from match_scraper import MatchScraper
from gemini_analyzer import GeminiAnalyzer
from telegram_sender import TelegramSender
from learning_engine import LearningEngine

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
    
    # 3. Analyse avec Gemini
    print("🤖 Analyse IA en cours...")
    analyzer = GeminiAnalyzer()
    result = analyzer.analyze_matches(matches_formatted, stats)
    
    if not result:
        print("❌ Erreur analyse")
        return
    
    print(f"✅ Analyse terminée: {len(result.get('recommendations', []))} pronostics")
    
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