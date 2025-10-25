from telegram import Bot
import asyncio
from config import Config
import json

class TelegramSender:
    def __init__(self):
        self.config = Config()
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
    
    def format_detailed_message(self, analysis_result):
        """Formate l'analyse détaillée en message Telegram"""
        if not analysis_result or not analysis_result.get('recommendations'):
            return "❌ Aucun pronostic intéressant aujourd'hui après analyse approfondie."
        
        date = analysis_result.get('analysis_date', 'N/A')
        recs = analysis_result['recommendations']
        total_analyzed = analysis_result.get('total_analyzed', 0)
        
        # En-tête
        message = f"⚽ **ANALYSES APPROFONDIES - {date}**\n"
        message += f"━━━━━━━━━━━━━━━━━━━━\n"
        message += f"📊 {total_analyzed} matchs analysés\n"
        message += f"✅ {len(recs)} pronostic(s) retenu(s)\n"
        message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Chaque pronostic détaillé
        for i, rec in enumerate(recs, 1):
            message += f"**═══ PRONOSTIC #{i} ═══**\n\n"
            message += f"🏆 **{rec['match']}**\n"
            message += f"📍 {rec['competition']} | ⏰ {rec['kickoff']}\n\n"
            
            # Analyse détaillée
            details = rec.get('detailed_analysis', {})
            
            # 1. FORME RÉCENTE
            if 'recent_form' in details:
                message += "**📈 FORME RÉCENTE**\n"
                
                home = details['recent_form'].get('home_team', {})
                if home:
                    message += f"🏠 *Domicile:* {home.get('last_5_matches', 'N/A')}\n"
                    message += f"   └ {home.get('trend', '')}\n"
                    if home.get('details'):
                        message += f"   └ {home['details'][:100]}...\n"
                
                away = details['recent_form'].get('away_team', {})
                if away:
                    message += f"✈️ *Extérieur:* {away.get('last_5_matches', 'N/A')}\n"
                    message += f"   └ {away.get('trend', '')}\n"
                    if away.get('details'):
                        message += f"   └ {away['details'][:100]}...\n"
                
                message += "\n"
            
            # 2. CONFRONTATIONS DIRECTES
            if 'head_to_head' in details:
                h2h = details['head_to_head']
                message += "**🔄 CONFRONTATIONS DIRECTES**\n"
                message += f"Bilan: {h2h.get('last_5', 'N/A')}\n"
                if h2h.get('details'):
                    message += f"Détails: {h2h['details'][:120]}...\n"
                message += "\n"
            
            # 3. BLESSURES & SUSPENSIONS
            if 'injuries_suspensions' in details:
                inj = details['injuries_suspensions']
                message += "**🏥 BLESSURES & SUSPENSIONS**\n"
                
                if inj.get('home_team'):
                    home_inj = inj['home_team']
                    if home_inj.get('absent'):
                        message += f"🏠 Absents: {', '.join(home_inj['absent'][:3])}\n"
                    message += f"   └ Impact: {home_inj.get('impact', 'N/A')[:80]}...\n"
                
                if inj.get('away_team'):
                    away_inj = inj['away_team']
                    if away_inj.get('absent'):
                        message += f"✈️ Absents: {', '.join(away_inj['absent'][:3])}\n"
                    message += f"   └ Impact: {away_inj.get('impact', 'N/A')[:80]}...\n"
                
                message += "\n"
            
            # 4. TACTIQUE
            if 'tactical_analysis' in details:
                tact = details['tactical_analysis']
                message += "**⚙️ ANALYSE TACTIQUE**\n"
                if tact.get('home_style'):
                    message += f"🏠 {tact['home_style'][:90]}...\n"
                if tact.get('away_style'):
                    message += f"✈️ {tact['away_style'][:90]}...\n"
                if tact.get('key_matchup'):
                    message += f"🔑 Duel clé: {tact['key_matchup'][:100]}...\n"
                message += "\n"
            
            # 5. CALENDRIER & FATIGUE
            if 'schedule_fatigue' in details:
                sched = details['schedule_fatigue']
                message += "**🔋 CALENDRIER & FATIGUE**\n"
                if sched.get('home_team'):
                    message += f"🏠 {sched['home_team']}\n"
                if sched.get('away_team'):
                    message += f"✈️ {sched['away_team']}\n"
                if sched.get('advantage'):
                    message += f"⚖️ {sched['advantage']}\n"
                message += "\n"
            
            # 6. CONTEXTE & ENJEU
            if 'context_stakes' in details:
                ctx = details['context_stakes']
                message += "**🎯 CONTEXTE & ENJEU**\n"
                if ctx.get('home_situation'):
                    message += f"🏠 {ctx['home_situation'][:100]}...\n"
                if ctx.get('away_situation'):
                    message += f"✈️ {ctx['away_situation'][:100]}...\n"
                if ctx.get('psychological'):
                    message += f"🧠 {ctx['psychological'][:100]}...\n"
                message += "\n"
            
            # 7. AVANTAGE DOMICILE
            if 'home_advantage' in details:
                home_adv = details['home_advantage']
                message += "**🏟️ AVANTAGE DOMICILE**\n"
                if home_adv.get('home_record_season'):
                    message += f"📊 {home_adv['home_record_season']}\n"
                if home_adv.get('advantage_score'):
                    message += f"⭐ Score: {home_adv['advantage_score']}\n"
                message += "\n"
            
            # 8. COTES & VALUE
            if 'odds_value' in details:
                odds_val = details['odds_value']
                message += "**💰 ANALYSE DES COTES**\n"
                message += f"Cote: {odds_val.get('bet_odds', 'N/A')}\n"
                message += f"Proba implicite: {odds_val.get('implied_probability', 'N/A')}\n"
                message += f"Proba estimée: {odds_val.get('estimated_real_probability', 'N/A')}\n"
                message += f"Value: {odds_val.get('value_analysis', 'N/A')}\n"
                message += "\n"
            
            # 9. FACTEURS CLÉS
            if 'key_factors_summary' in details:
                message += "**🔑 FACTEURS CLÉS DÉCISIFS**\n"
                for j, factor in enumerate(details['key_factors_summary'][:5], 1):
                    message += f"{j}. {factor[:120]}...\n"
                message += "\n"
            
            # 10. CONCLUSION
            if rec.get('conclusion'):
                message += "**📝 CONCLUSION**\n"
                message += f"{rec['conclusion'][:300]}...\n\n"
            
            # 11. RECOMMANDATION FINALE
            message += "**🎯 RECOMMANDATION**\n"
            message += f"**Type:** {rec['bet_type']}\n"
            message += f"**Pari:** {rec['prediction']}\n"
            message += f"**Cote:** {rec['odds']}\n"
            message += f"**Confiance:** {rec['confidence']}%\n"
            message += f"**Risque:** {rec.get('risk_level', 'N/A')}\n"
            
            # Alternatives si disponibles
            if rec.get('alternative_bets'):
                message += "\n*Alternatives:*\n"
                for alt in rec['alternative_bets'][:2]:
                    message += f"• {alt['type']} @ {alt['odds']}\n"
            
            message += "\n" + "━"*30 + "\n\n"
        
        # Pari combiné
        if analysis_result.get('combined_bet'):
            combo = analysis_result['combined_bet']
            message += "**🔥 COMBINÉ SUGGÉRÉ**\n"
            message += f"Matchs: {', '.join(combo['matches'])}\n"
            message += f"Cote totale: {combo['total_odds']}\n"
            message += f"Confiance: {combo['confidence']}%\n"
            message += f"Risque: {combo.get('risk_level', 'N/A')}\n"
            
            if combo.get('detailed_reasoning'):
                message += f"\nRaisonnement:\n{combo['detailed_reasoning'][:200]}...\n"
            
            message += "\n"
        
        # Matchs exclus (échantillon)
        if analysis_result.get('matches_excluded'):
            excluded = analysis_result['matches_excluded']
            message += f"📋 **{excluded.get('count', 0)} matchs exclus**\n"
            
            if excluded.get('examples'):
                message += "Exemples:\n"
                for ex in excluded['examples'][:3]:
                    message += f"• {ex.get('match', 'N/A')}: {ex.get('reason', 'N/A')}\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━\n"
        message += "✅ Analyse terminée\n"
        message += f"🤖 Propulsé par Claude Sonnet 4.5\n"

        return message
    
    async def send_message(self, message):
        """Envoie le message sur Telegram"""
        try:
            # Telegram a une limite de 4096 caractères
            # Si trop long, diviser en plusieurs messages
            max_length = 4000
            
            if len(message) <= max_length:
                await self.bot.send_message(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    text=message,
                    parse_mode='Markdown'
                )
            else:
                # Diviser en plusieurs messages
                parts = []
                current_part = ""
                
                for line in message.split('\n'):
                    if len(current_part) + len(line) + 1 > max_length:
                        parts.append(current_part)
                        current_part = line + '\n'
                    else:
                        current_part += line + '\n'
                
                if current_part:
                    parts.append(current_part)
                
                # Envoyer chaque partie
                for i, part in enumerate(parts, 1):
                    await self.bot.send_message(
                        chat_id=self.config.TELEGRAM_CHAT_ID,
                        text=f"**[Partie {i}/{len(parts)}]**\n\n{part}",
                        parse_mode='Markdown'
                    )
                    await asyncio.sleep(1)  # Pause entre messages
            
            print("✅ Message(s) envoyé(s) sur Telegram")
            return True
        except Exception as e:
            print(f"❌ Erreur envoi Telegram: {e}")
            return False
    
    def send_sync(self, analysis_result):
        """Version synchrone"""
        message = self.format_detailed_message(analysis_result)
        return asyncio.run(self.send_message(message))

# Compatibilité avec l'ancienne fonction
    def format_message(self, analysis_result):
        """Alias pour compatibilité"""
        return self.format_detailed_message(analysis_result)