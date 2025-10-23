import sys
sys.path.insert(0, 'src')
from performance_tracker import PerformanceTracker
from telegram_sender import TelegramSender
from datetime import datetime, timedelta
from config import Config

class WeeklyReportGenerator:
    def __init__(self):
        self.tracker = PerformanceTracker()
        self.telegram = TelegramSender()
        self.config = Config()

    def get_last_week_predictions(self):
        """Récupère les pronostics de la semaine dernière"""
        all_predictions = self.tracker.get_all_predictions()

        # Date d'il y a 7 jours
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')

        # Filtrer les prédictions de la semaine
        week_predictions = [
            p for p in all_predictions
            if week_ago <= p['date'] <= today
        ]

        return week_predictions

    def calculate_weekly_stats(self, predictions):
        """Calcule les stats de la semaine"""
        if not predictions:
            return None

        completed = [p for p in predictions if p['result'] in ['win', 'loss']]
        wins = [p for p in completed if p['result'] == 'win']
        losses = [p for p in completed if p['result'] == 'loss']
        pending = [p for p in predictions if p['result'] not in ['win', 'loss']]

        # Stats par type de pari
        by_type = {}
        for pred in completed:
            bet_type = pred['bet_type']
            if bet_type not in by_type:
                by_type[bet_type] = {'wins': 0, 'total': 0}
            by_type[bet_type]['total'] += 1
            if pred['result'] == 'win':
                by_type[bet_type]['wins'] += 1

        # Stats par compétition
        by_competition = {}
        for pred in completed:
            comp = pred['competition']
            if comp not in by_competition:
                by_competition[comp] = {'wins': 0, 'total': 0}
            by_competition[comp]['total'] += 1
            if pred['result'] == 'win':
                by_competition[comp]['wins'] += 1

        # Meilleur pari (plus haute cote gagnée)
        best_bet = max(wins, key=lambda x: x['odds']) if wins else None

        # Série actuelle (victoires/défaites consécutives)
        if completed:
            completed_sorted = sorted(completed, key=lambda x: x['date'])
            current_streak = 0
            last_result = None
            for pred in reversed(completed_sorted):
                if pred['result'] == last_result or last_result is None:
                    current_streak += 1
                    last_result = pred['result']
                else:
                    break
            streak_type = last_result if last_result else None
        else:
            current_streak = 0
            streak_type = None

        return {
            'total_predictions': len(predictions),
            'completed': len(completed),
            'wins': len(wins),
            'losses': len(losses),
            'pending': len(pending),
            'win_rate': (len(wins) / len(completed) * 100) if completed else 0,
            'avg_odds': sum([p['odds'] for p in predictions]) / len(predictions),
            'avg_confidence': sum([p['confidence'] for p in predictions]) / len(predictions),
            'by_type': by_type,
            'by_competition': by_competition,
            'best_bet': best_bet,
            'current_streak': current_streak,
            'streak_type': streak_type
        }

    def format_report(self, stats):
        """Formate le rapport en texte pour Telegram"""
        if not stats:
            return "📊 *RAPPORT HEBDOMADAIRE*\n\n❌ Aucun pronostic cette semaine."

        # Émoji selon performance
        if stats['win_rate'] >= 70:
            performance_emoji = "🔥"
        elif stats['win_rate'] >= 60:
            performance_emoji = "✅"
        elif stats['win_rate'] >= 50:
            performance_emoji = "📊"
        else:
            performance_emoji = "⚠️"

        # Date de la semaine
        week_start = (datetime.now() - timedelta(days=7)).strftime('%d/%m')
        week_end = datetime.now().strftime('%d/%m/%Y')

        report = f"""📊 *RAPPORT HEBDOMADAIRE* 📊
Période: {week_start} - {week_end}

━━━━━━━━━━━━━━━━━━━━━━

{performance_emoji} *PERFORMANCE GLOBALE*

✅ *Taux de réussite:* {stats['win_rate']:.1f}%
   └ {stats['wins']} victoires / {stats['losses']} défaites

📈 *Total pronostics:* {stats['total_predictions']}
   └ {stats['completed']} terminés | {stats['pending']} en attente

💎 *Cote moyenne:* {stats['avg_odds']:.2f}
⭐ *Confiance moyenne:* {stats['avg_confidence']:.0f}%"""

        # Série actuelle
        if stats['current_streak'] > 1:
            streak_emoji = "🔥" if stats['streak_type'] == 'win' else "❄️"
            streak_text = "victoires" if stats['streak_type'] == 'win' else "défaites"
            report += f"\n{streak_emoji} *Série en cours:* {stats['current_streak']} {streak_text} consécutives"

        report += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n📊 *PAR TYPE DE PARI*\n"

        # Stats par type
        for bet_type, data in sorted(stats['by_type'].items(), key=lambda x: x[1]['wins'], reverse=True):
            win_rate_type = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            emoji = "🎯" if win_rate_type >= 60 else "⚪"
            report += f"\n{emoji} *{bet_type}*: {data['wins']}/{data['total']} ({win_rate_type:.0f}%)"

        # Stats par compétition (top 3)
        if stats['by_competition']:
            report += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n🏆 *PAR COMPÉTITION*\n"
            sorted_comps = sorted(stats['by_competition'].items(), key=lambda x: x[1]['total'], reverse=True)[:3]
            for comp, data in sorted_comps:
                win_rate_comp = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
                emoji = "🎯" if win_rate_comp >= 60 else "⚪"
                comp_short = comp[:30] + "..." if len(comp) > 30 else comp
                report += f"\n{emoji} *{comp_short}*: {data['wins']}/{data['total']} ({win_rate_comp:.0f}%)"

        # Meilleur pari
        if stats['best_bet']:
            report += f"""

━━━━━━━━━━━━━━━━━━━━━━

🏆 *MEILLEUR PARI DE LA SEMAINE*
{stats['best_bet']['match']}
💰 Cote: {stats['best_bet']['odds']:.2f}
🎲 Type: {stats['best_bet']['bet_type']}
🏅 Compétition: {stats['best_bet']['competition'][:30]}
📅 Date: {stats['best_bet']['date']}
"""

        # Conseils selon performance
        report += "\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if stats['win_rate'] >= 70:
            report += "🔥 *Excellente semaine !* Performance exceptionnelle, continue ainsi !"
        elif stats['win_rate'] >= 60:
            report += "✅ *Bonne performance !* Taux de réussite solide, reste discipliné."
        elif stats['win_rate'] >= 50:
            report += "📊 *Performance correcte.* Au-dessus de 50%, mais peut mieux faire !"
        else:
            report += "⚠️ *Semaine difficile.* Patience et analyse des erreurs nécessaires."

        report += f"\n\n_Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}_ 🤖"

        return report

    def generate_and_send(self):
        """Génère et envoie le rapport hebdomadaire"""
        print("📊 Génération du rapport hebdomadaire...")

        # Récupérer les prédictions de la semaine
        predictions = self.get_last_week_predictions()
        print(f"   📈 {len(predictions)} pronostics cette semaine")

        # Calculer les stats
        stats = self.calculate_weekly_stats(predictions)

        # Formater le rapport
        report = self.format_report(stats)

        # Envoyer sur Telegram
        print("📤 Envoi du rapport sur Telegram...")
        import asyncio
        success = asyncio.run(self.telegram.send_message(report))

        if success:
            print("✅ Rapport hebdomadaire envoyé avec succès!")
        else:
            print("❌ Erreur lors de l'envoi du rapport")

        return success


if __name__ == "__main__":
    # Test
    generator = WeeklyReportGenerator()
    generator.generate_and_send()
