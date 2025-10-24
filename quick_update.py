#!/usr/bin/env python3
"""
Script rapide pour enregistrer les résultats
Modifiez les résultats ci-dessous puis lancez le script
"""

import sys
sys.path.insert(0, 'src')
from performance_tracker import PerformanceTracker

# ====================================================
# MODIFIEZ ICI LES RÉSULTATS
# ====================================================

results = [
    # Format: ("prediction_id", "win" ou "loss", "score optionnel")

    # Match 1: Rapid Vienna vs Fiorentina (Victoire Fiorentina prédite)
    ("2025-10-23_5", "win", "1-2"),  # Changez "win" en "loss" si perdu

    # Match 2: AS Roma vs Plzen (Victoire Roma -1.5 prédite)
    ("2025-10-23_6", "win", "2-0"),  # Changez "win" en "loss" si perdu

    # Match 3: SC Freiburg vs Utrecht (BTTS Yes prédit)
    ("2025-10-23_7", "win", "2-1"),  # Changez "win" en "loss" si perdu
]

# ====================================================
# NE PAS MODIFIER EN DESSOUS
# ====================================================

def main():
    tracker = PerformanceTracker()

    print("🔄 Mise à jour des résultats...\n")

    for pred_id, result, score in results:
        tracker.record_result(pred_id, result, score)
        emoji = "✅" if result == "win" else "❌"
        print(f"{emoji} {pred_id}: {result.upper()} ({score})")

    print("\n📊 STATISTIQUES MISES À JOUR:")
    stats = tracker.calculate_statistics()
    print(f"   ✅ Taux de réussite: {stats['win_rate']:.1f}%")
    print(f"   📈 Pronostics: {stats['total_wins']} victoires / {stats['total_losses']} défaites")
    print(f"   ⏳ En attente: {stats['pending']}")
    print(f"   💎 Cote moyenne: {stats['avg_odds']:.2f}")

    print("\n✅ Mise à jour terminée!")
    print("🚀 Pour voir le dashboard: streamlit run dashboard.py")

if __name__ == "__main__":
    main()
