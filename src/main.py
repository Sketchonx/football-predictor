#!/usr/bin/env python3
import sys
import os
from datetime import datetime
from match_scraper import MatchScraper
from claude_analyzer import ClaudeAnalyzer  # Remplacé Gemini par Claude
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

    # Limiter à 10 matchs max pour éviter JSON trop long
    MAX_MATCHES_TO_ANALYZE = 10
    if len(matches) > MAX_MATCHES_TO_ANALYZE:
        print(f"⚠️ Limitation à {MAX_MATCHES_TO_ANALYZE} matchs (sur {len(matches)}) pour optimiser l'analyse")
        matches = matches[:MAX_MATCHES_TO_ANALYZE]

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