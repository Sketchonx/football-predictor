#!/usr/bin/env python3
"""
Script de ré-analyse des matchs avec alerte Telegram en cas de changement
Utilisé pour envoyer des mises à jour aux utilisateurs quand l'analyse change
"""

import json
import os
import sys
from datetime import datetime
from telegram import Bot
import asyncio
from config import Config
from match_scraper import MatchScraper
from claude_analyzer import ClaudeAnalyzer

class ReanalysisAlertSender:
    def __init__(self):
        self.config = Config()
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)

    async def send_reanalysis_alert(self, old_analysis, new_analysis):
        """
        Envoie une alerte Telegram indiquant les changements détectés
        """
        date = new_analysis.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))

        # Construire le message d'alerte
        message = "🚨 **ALERTE - RÉ-ANALYSE EFFECTUÉE** 🚨\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += f"📅 Date: {date}\n"
        message += f"⏰ Heure: {datetime.now().strftime('%H:%M')}\n\n"

        message += "⚠️ **CHANGEMENTS DÉTECTÉS DANS L'ANALYSE**\n"
        message += "Des nouvelles informations (compositions, blessures, etc.) ont été détectées.\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"

        # Comparer les recommandations
        old_recs = old_analysis.get('recommendations', [])
        new_recs = new_analysis.get('recommendations', [])

        # Cas 1: Ancien pari existait, maintenant rejeté
        if len(old_recs) > 0 and len(new_recs) == 0:
            old_rec = old_recs[0]
            message += "❌ **PARI ANNULÉ**\n\n"
            message += f"⚽ **{old_rec['match']}**\n"
            message += f"⏰ Coup d'envoi: {old_rec['kickoff']}\n\n"

            message += "📊 **Analyse initiale (ce matin):**\n"
            message += f"✅ {old_rec['prediction']}\n"
            message += f"💰 Cote: {old_rec['odds']}\n"
            message += f"📈 Confiance: {old_rec['confidence']}%\n"
            message += f"🎯 Type: {old_rec['bet_type']}\n\n"

            message += "🔄 **Nouvelle analyse (maintenant):**\n"
            message += f"❌ PARI REJETÉ\n\n"

            # Raison de l'exclusion
            excluded = new_analysis.get('matches_excluded', {}).get('examples', [])
            if excluded:
                message += f"**Raison:**\n{excluded[0].get('reason', 'Match trop incertain')}\n\n"

            message += "💡 **Recommandation:**\n"
            message += "⛔ Ne pariez PAS sur ce match.\n\n"

        # Cas 2: Pas de pari avant, maintenant recommandé
        elif len(old_recs) == 0 and len(new_recs) > 0:
            new_rec = new_recs[0]
            message += "✅ **NOUVEAU PARI RECOMMANDÉ**\n\n"
            message += f"⚽ **{new_rec['match']}**\n"
            message += f"⏰ Coup d'envoi: {new_rec['kickoff']}\n\n"

            message += "📊 **Analyse initiale:**\n"
            message += "❌ Aucun pari recommandé\n\n"

            message += "🔄 **Nouvelle analyse avec données actualisées:**\n"
            message += f"✅ **{new_rec['prediction']}**\n"
            message += f"💰 Cote: {new_rec['odds']}\n"
            message += f"📈 Confiance: {new_rec['confidence']}%\n"
            message += f"🎯 Type: {new_rec['bet_type']}\n"
            message += f"⚠️ Risque: {new_rec['risk_level']}\n\n"

            message += f"**📝 Conclusion:**\n{new_rec.get('conclusion', 'N/A')[:300]}...\n\n"

        # Cas 3: Pari existait, maintenant changé
        elif len(old_recs) > 0 and len(new_recs) > 0:
            old_rec = old_recs[0]
            new_rec = new_recs[0]

            message += "🔄 **PARI MODIFIÉ**\n\n"
            message += f"⚽ **{new_rec['match']}**\n"
            message += f"⏰ Coup d'envoi: {new_rec['kickoff']}\n\n"

            message += "📊 **Analyse initiale (ce matin):**\n"
            message += f"• {old_rec['prediction']}\n"
            message += f"• Cote: {old_rec['odds']}\n"
            message += f"• Confiance: {old_rec['confidence']}%\n"
            message += f"• Type: {old_rec['bet_type']}\n\n"

            message += "🔄 **Nouvelle analyse (maintenant):**\n"
            message += f"• **{new_rec['prediction']}**\n"
            message += f"• Cote: {new_rec['odds']}\n"
            message += f"• Confiance: {new_rec['confidence']}%\n"
            message += f"• Type: {new_rec['bet_type']}\n"
            message += f"• Risque: {new_rec['risk_level']}\n\n"

            message += f"**📝 Nouvelle conclusion:**\n{new_rec.get('conclusion', 'N/A')[:300]}...\n\n"

        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += "ℹ️ Cette alerte est envoyée automatiquement lorsque des changements importants sont détectés (compositions confirmées, retours de blessure, etc.)\n\n"
        message += "🤖 Ré-analyse automatique\n"
        message += "🤖 Propulsé par Claude Sonnet 4.5\n"

        # Envoyer le message
        try:
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            print(f"❌ Erreur envoi Telegram: {e}")
            return False

    def send_reanalysis_alert_sync(self, old_analysis, new_analysis):
        """Version synchrone pour compatibilité"""
        return asyncio.run(self.send_reanalysis_alert(old_analysis, new_analysis))


def main():
    """
    Exécute une ré-analyse et envoie une alerte si changements détectés
    """
    print("🔄 Démarrage ré-analyse...")

    # Charger l'ancienne analyse (si existe)
    today = datetime.now().strftime('%Y-%m-%d')
    old_prediction_file = f'data/predictions/{today}.json'

    old_analysis = None
    if os.path.exists(old_prediction_file):
        with open(old_prediction_file, 'r', encoding='utf-8') as f:
            old_analysis = json.load(f)
        print(f"✅ Ancienne analyse chargée: {len(old_analysis.get('recommendations', []))} recommandation(s)")
    else:
        print("⚠️  Pas d'analyse précédente trouvée")

    # Lancer nouvelle analyse
    print("🤖 Lancement nouvelle analyse avec Claude...")
    scraper = MatchScraper()
    analyzer = ClaudeAnalyzer()

    # Récupérer les matchs
    matches = scraper.get_today_matches()
    print(f"✅ {len(matches)} match(s) trouvé(s)")

    if len(matches) == 0:
        print("❌ Aucun match disponible, arrêt.")
        sys.exit(0)

    # Analyser avec Claude
    new_analysis = analyzer.analyze_matches(matches)

    # Sauvegarder la nouvelle analyse
    with open(old_prediction_file, 'w', encoding='utf-8') as f:
        json.dump(new_analysis, f, indent=2, ensure_ascii=False)
    print(f"✅ Nouvelle analyse sauvegardée: {len(new_analysis.get('recommendations', []))} recommandation(s)")

    # Vérifier s'il y a des changements
    if old_analysis is None:
        print("ℹ️  Première analyse du jour, pas de comparaison possible")
        sys.exit(0)

    old_recs = old_analysis.get('recommendations', [])
    new_recs = new_analysis.get('recommendations', [])

    # Détecter changements
    has_changes = False

    if len(old_recs) != len(new_recs):
        has_changes = True
        print(f"🔄 Changement détecté: {len(old_recs)} → {len(new_recs)} recommandations")
    elif len(old_recs) > 0 and len(new_recs) > 0:
        # Comparer les prédictions
        old_pred = old_recs[0].get('prediction', '')
        new_pred = new_recs[0].get('prediction', '')

        if old_pred != new_pred:
            has_changes = True
            print(f"🔄 Changement détecté: '{old_pred}' → '{new_pred}'")

    # Envoyer alerte si changements
    if has_changes:
        print("📤 Envoi alerte Telegram...")
        sender = ReanalysisAlertSender()
        success = sender.send_reanalysis_alert_sync(old_analysis, new_analysis)

        if success:
            print("✅ Alerte envoyée avec succès")
        else:
            print("❌ Échec envoi alerte")
    else:
        print("ℹ️  Pas de changement détecté, pas d'alerte envoyée")


if __name__ == '__main__':
    main()
