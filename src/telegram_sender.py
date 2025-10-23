from telegram import Bot
import asyncio
from config import Config
import json

class TelegramSender:
    def __init__(self):
        self.config = Config()
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
    
    def format_message(self, analysis_result):
        """Formate l'analyse en message Telegram"""
        if not analysis_result or not analysis_result.get('recommendations'):
            return "❌ Aucun pronostic intéressant aujourd'hui."
        
        date = analysis_result.get('analysis_date', 'N/A')
        recs = analysis_result['recommendations']
        
        message = f"⚽ **PRONOSTICS FOOTBALL - {date}**\n"
        message += f"📊 {len(recs)} pronostic(s) sélectionné(s)\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, rec in enumerate(recs, 1):
            message += f"**{i}. {rec['match']}**\n"
            message += f"🏆 {rec['competition']} | ⏰ {rec['kickoff']}\n\n"
            message += f"📝 {rec['analysis']}\n\n"
            message += f"🎯 **Pari**: {rec['prediction']}\n"
            message += f"💰 **Cote**: {rec['odds']}\n"
            message += f"✅ **Confiance**: {rec['confidence']}%\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Pari combiné
        if analysis_result.get('combined_bet'):
            combo = analysis_result['combined_bet']
            message += "🔥 **COMBINÉ SUGGÉRÉ**\n"
            message += f"Matchs: {', '.join(combo['matches'])}\n"
            message += f"Cote totale: {combo['total_odds']}\n"
            message += f"Confiance: {combo['confidence']}%\n"
            message += f"Raisonnement: {combo['reasoning']}\n"
        
        return message
    
    async def send_message(self, message):
        """Envoie le message sur Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            print("✅ Message envoyé sur Telegram")
            return True
        except Exception as e:
            print(f"❌ Erreur envoi Telegram: {e}")
            return False
    
    def send_sync(self, analysis_result):
        """Version synchrone pour GitHub Actions"""
        message = self.format_message(analysis_result)
        return asyncio.run(self.send_message(message))

# Test
if __name__ == "__main__":
    sender = TelegramSender()
    test_result = {
        "analysis_date": "2025-10-23",
        "recommendations": [{
            "match": "PSG vs Bayern",
            "competition": "Champions League",
            "kickoff": "21h00",
            "analysis": "PSG en grande forme, Bayern affaibli par blessures.",
            "prediction": "1 (Victoire PSG)",
            "odds": 2.10,
            "confidence": 78
        }]
    }
    sender.send_sync(test_result)