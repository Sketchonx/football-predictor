#!/usr/bin/env python3
"""
Script interactif pour enregistrer les résultats des pronostics
"""

import sys
sys.path.insert(0, 'src')
from performance_tracker import PerformanceTracker

def main():
    tracker = PerformanceTracker()
    predictions = tracker.get_all_predictions()

    # Filtrer les prédictions en attente
    pending = [p for p in predictions if p['result'] not in ['win', 'loss']]

    if not pending:
        print("✅ Aucun pronostic en attente!")
        print(f"📊 Stats actuelles:")
        stats = tracker.calculate_statistics()
        print(f"   Taux de réussite: {stats['win_rate']:.1f}%")
        print(f"   Pronostics: {stats['total_wins']}/{stats['completed']}")
        return

    print(f"📋 {len(pending)} pronostics en attente\n")
    print("=" * 70)

    for i, pred in enumerate(pending, 1):
        print(f"\n🎯 PRONOSTIC #{i}/{len(pending)}")
        print(f"   Match: {pred['match']}")
        print(f"   Compétition: {pred['competition']}")
        print(f"   Date: {pred['date']}")
        print(f"   Type: {pred['bet_type']}")
        print(f"   Prédiction: {pred['prediction']}")
        print(f"   Cote: {pred['odds']}")
        print(f"   Confiance: {pred['confidence']}%")
        print("-" * 70)

        # Demander le résultat
        while True:
            choice = input("\n   Résultat? (w=win, l=loss, s=skip, q=quit): ").lower().strip()

            if choice == 'q':
                print("\n👋 Arrêt de la mise à jour")
                return
            elif choice == 's':
                print("   ⏭️  Ignoré")
                break
            elif choice in ['w', 'l']:
                result = 'win' if choice == 'w' else 'loss'

                # Demander le score (optionnel)
                score = input("   Score réel (optionnel, Enter pour ignorer): ").strip()
                score = score if score else None

                # Enregistrer
                tracker.record_result(pred['id'], result, score)

                emoji = "✅" if result == 'win' else "❌"
                print(f"   {emoji} Enregistré: {result.upper()}" + (f" ({score})" if score else ""))
                break
            else:
                print("   ⚠️  Choix invalide. Utilisez w/l/s/q")

    # Afficher le résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ MIS À JOUR")
    print("=" * 70)
    stats = tracker.calculate_statistics()
    print(f"✅ Taux de réussite: {stats['win_rate']:.1f}%")
    print(f"📈 Pronostics: {stats['total_wins']} victoires / {stats['total_losses']} défaites")
    print(f"⏳ En attente: {stats['pending']}")
    print(f"💎 Cote moyenne: {stats['avg_odds']:.2f}")
    print(f"⭐ Confiance moyenne: {stats['avg_confidence']:.0f}%")

    print("\n🚀 Pour voir le dashboard: streamlit run dashboard.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interruption par l'utilisateur")
        sys.exit(0)
