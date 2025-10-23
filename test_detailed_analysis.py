#!/usr/bin/env python3
"""
Test du système avec une analyse ultra-détaillée
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from telegram_sender import TelegramSender
from datetime import datetime

print("🧪 TEST ANALYSE ULTRA-DÉTAILLÉE")
print("=" * 60)
print()

# Exemple d'analyse détaillée réaliste
detailed_analysis = {
    "analysis_date": datetime.now().strftime('%Y-%m-%d'),
    "total_analyzed": 47,
    "total_retained": 2,
    
    "recommendations": [
        {
            "match": "PSG vs Bayern Munich",
            "competition": "Champions League - Phase de groupes",
            "kickoff": "21h00",
            
            "detailed_analysis": {
                "recent_form": {
                    "home_team": {
                        "last_5_matches": "4V-1N-0D, 14 buts pour, 3 contre",
                        "home_record": "À domicile: 3V-0N, 10 buts pour, 1 contre sur 3 derniers",
                        "trend": "Forme exceptionnelle en nette progression",
                        "details": "Victoires: 4-0 vs Nice, 3-0 vs Lens, 2-1 vs Monaco, 1-0 vs Marseille. Nul: 1-1 vs Milan"
                    },
                    "away_team": {
                        "last_5_matches": "2V-2N-1D, 8 buts pour, 6 contre",
                        "away_record": "À l'extérieur: 1V-1N-1D, 3 buts pour, 4 contre",
                        "trend": "Forme instable, difficulté en déplacement européen",
                        "details": "Défaite 2-1 vs Dortmund (ext), Nul 1-1 vs Inter (ext), Victoire 2-0 vs Cologne (dom)"
                    }
                },
                
                "head_to_head": {
                    "last_5": "PSG 3V, 1N, Bayern 1V",
                    "at_home": "PSG invaincu à domicile sur 3 derniers (2V-1N)",
                    "details": "3-0 PSG (2024, Paris), 2-1 PSG (2023, Paris), 1-1 (2023, Munich), 0-2 Bayern (2022, Paris), 3-1 PSG (2021, Paris)",
                    "trends": "Domination PSG au Parc des Princes. Moyenne 2.8 buts/match. Bayern n'a plus gagné à Paris depuis 2022."
                },
                
                "injuries_suspensions": {
                    "home_team": {
                        "absent": ["Kimpembe (défenseur, blessure longue durée, remplacé par Skriniar)"],
                        "impact": "Impact minime: Skriniar performant cette saison (7 matchs, 0 but encaissé). Rotation habituelle."
                    },
                    "away_team": {
                        "absent": [
                            "Manuel Neuer (gardien titulaire, blessure épaule - remplacé par Ulreich)",
                            "Thomas Müller (milieu offensif, 12 buts/8 passes cette saison - créateur principal)",
                            "Joshua Kimmich (milieu défensif, suspendu - organisateur de jeu)"
                        ],
                        "impact": "Impact MAJEUR: Absence du gardien #1 (Ulreich moins fiable, -15% parades). Müller absent = perte créativité offensive principale. Kimmich suspendu = milieu déséquilibré, moins de relance propre. Niveau global estimé -25%."
                    }
                },
                
                "tactical_analysis": {
                    "home_style": "4-3-3 ultra-offensif, possession 68%, pressing haut coordonné. Triangulations rapides dans dernier tiers. Exploite largeur avec Dembélé/Barcola. Mbappé en pointe, mouvement constant.",
                    "away_style": "4-2-3-1 flexible, pressing haut mais ligne défensive haute (risque). Jeu direct via Müller (absent!), transitions rapides. Vulnérabilité sur ballons longs et contre-attaques rapides.",
                    "key_matchup": "CRITIQUE: Vitesse PSG (Mbappé 35.3 km/h, Dembélé 35.1 km/h) vs ligne haute Bayern SANS Kimmich pour récupérer. Bayern joue haut = espace dans le dos. Avantage PSG énorme.",
                    "predicted_approach": "PSG va exploiter profondeur systématiquement. Bayern forcé de reculer sans Müller/Kimmich pour équilibrer. PSG domine possession et chances."
                },
                
                "schedule_fatigue": {
                    "home_team": "Dernier match il y a 5 jours (2-0 vs Lens). Rotation de 4 joueurs effectuée. Titulaires reposés, fraîcheur maximale. Aucun déplacement international récent.",
                    "away_team": "3 matchs en 8 jours: victoire Bundesliga il y a 3j (épuisant, 0-0 puis 2-1), déplacement en Champions il y a 6j. Rotation limitée (effectif court). Fatigue accumulée estimée élevée.",
                    "advantage": "Avantage physique et mental net pour PSG. Bayern arrive diminuée physiquement et avec blessés."
                },
                
                "context_stakes": {
                    "home_situation": "PSG 2e du groupe avec 9 points (3V). Doit gagner pour assurer qualification directe et éviter barrages. Pression forte mais motivation au maximum. Prestige européen en jeu après échec saison passée.",
                    "away_situation": "Bayern 1er avec 12 points (4V), déjà qualifié en 1/8. 1ère place pas décisive (différence faible pour tirage). Motivation relative, peut se permettre défaite. Entraîneur pourrait tourner effectif.",
                    "psychological": "PSG affamé de revanche et qualification. Supporters attendent victoire référence. Bayern joue 'libre', sans pression excessive. Avantage mental PSG.",
                    "overall": "Tous les facteurs psychologiques favorisent PSG: enjeu, motivation, revanche, supporters."
                },
                
                "home_advantage": {
                    "home_record_season": "PSG au Parc: 11 matchs, 9V-2N-0D, 31 buts pour, 8 contre. Forteresse absolue cette saison. 0 défaite à domicile toutes compétitions.",
                    "away_record_opponent": "Bayern en déplacement européen: 3V-1N-2D. Résultats mitigés (défaites Dortmund, Manchester City). Vulnérable hors d'Allemagne.",
                    "atmosphere": "Stade plein garanti (47929 places). Ambiance électrique attendue, Parc des Princes réputé hostile. Intimidation pour Bayern sans Neuer/Müller (leaders).",
                    "weather": "Temps clair prévu, 12°C, pas d'impact météo.",
                    "advantage_score": "9.5/10 - Avantage domicile quasi-maximum. PSG invaincu + Bayern fragile extérieur + ambiance."
                },
                
                "odds_value": {
                    "bet_odds": 2.05,
                    "implied_probability": "48.8%",
                    "estimated_real_probability": "58-63%",
                    "value_analysis": "VALUE BET FORT: Bookmakers sous-estiment PSG. Cote devrait être ~1.70. Edge de +9.2 à 14.2%. Marché influencé par réputation Bayern, mais contexte actuel ignoré (absents, fatigue).",
                    "odds_movement": "Cote baisse progressivement: 2.20 il y a 3j → 2.10 hier → 2.05 maintenant. 'Smart money' mise sur PSG. Correction en cours mais value persiste."
                },
                
                "key_factors_summary": [
                    "Forme écrasante PSG (9V-2N-0D domicile) vs Bayern instable extérieur (3V-1N-2D en Europe)",
                    "3 absences MAJEURES Bayern (Neuer, Müller, Kimmich) = -25% niveau estimé. PSG effectif complet",
                    "Fatigue physique Bayern (3 matchs/8j) vs PSG reposé (5j repos, rotation)",
                    "Enjeu décisif PSG (qualification) vs Bayern déjà qualifié (motivation moindre)",
                    "Avantage tactique: vitesse PSG vs ligne haute Bayern sans Kimmich = recette gagnante",
                    "Historique favorable: PSG invaincu domicile vs Bayern depuis 2 ans (2V-1N)",
                    "Value bet identifiée: cote 2.05 pour probabilité réelle 58-63% = +10% edge"
                ]
            },
            
            "conclusion": "Tous les indicateurs convergent massivement vers une victoire PSG. La convergence de facteurs est rare: forme exceptionnelle domicile (invaincu), adversaire affaibli (3 titulaires absents dont gardien et 2 cadres), fatigue adverse (3 matchs/8j), enjeu crucial vs motivation relative, avantage tactique évident (vitesse vs ligne haute), et cote offrant value (+10% edge). Historique confirme (PSG invaincu vs Bayern à domicile récemment). Risque principal: Bayern reste équipe de classe mondiale capable exploit, mais probabilités largement en faveur PSG. Confiance très élevée.",
            
            "bet_type": "1X2",
            "prediction": "1 (Victoire PSG)",
            "odds": 2.05,
            "confidence": 78,
            "risk_level": "Medium",
            
            "alternative_bets": [
                {
                    "type": "PSG -1 Handicap Européen",
                    "odds": 3.20,
                    "reasoning": "Si PSG gagne, probable par 2+ buts (défense Bayern affaiblie). Risque plus élevé mais cote attractive."
                },
                {
                    "type": "Over 2.5 buts",
                    "odds": 1.75,
                    "reasoning": "Attaque PSG prolifique, défense Bayern diminuée. Matchs PSG-Bayern souvent > 3 buts."
                }
            ]
        }
    ],
    
    "matches_excluded": {
        "count": 45,
        "examples": [
            {
                "match": "Real Madrid vs Shakhtar",
                "reason": "Cote Real 1.18 trop faible, gain insuffisant malgré victoire quasi-certaine"
            },
            {
                "match": "Man City vs Young Boys",
                "reason": "City déjà qualifié, risque forte rotation. Incertitude composition >60%"
            },
            {
                "match": "Benfica vs Salzburg",
                "reason": "Match équilibré, aucun avantage net détectable. Confiance <70%"
            }
        ]
    },
    
    "combined_bet": {
        "matches": ["PSG vs Bayern (1)", "Arsenal vs Inter (Over 2.5)"],
        "total_odds": 3.59,
        "confidence": 68,
        "detailed_reasoning": "PSG: probabilité 78% basée sur convergence facteurs. Arsenal-Inter: probabilité 73% (deux attaques top, défenses moyennes). Corrélation faible (ligues différentes, pas d'impact mutuel). Probabilité combinée: 78% × 73% = 57%. Cote combinée 3.59 implique 28% probabilité. Edge énorme: +29% vs marché. Risque Medium-High car combiné, mais value exceptionnelle.",
        "risk_level": "Medium-High"
    }
}

print("📝 Données de test détaillées créées")
print(f"   • 1 pronostic ultra-détaillé")
print(f"   • Toutes les sections d'analyse présentes")
print()

# Tester l'envoi
print("📤 Envoi sur Telegram...")
sender = TelegramSender()
success = sender.send_sync(detailed_analysis)

if success:
    print()
    print("=" * 60)
    print("✅ SUCCÈS ! Vérifiez votre Telegram")
    print("=" * 60)
    print()
    print("Vous devriez recevoir un message TRÈS détaillé avec:")
    print("  ✅ Forme récente complète")
    print("  ✅ Confrontations directes")
    print("  ✅ Blessures & impact")
    print("  ✅ Analyse tactique")
    print("  ✅ Calendrier & fatigue")
    print("  ✅ Contexte & enjeu")
    print("  ✅ Avantage domicile")
    print("  ✅ Analyse des cotes")
    print("  ✅ Facteurs clés")
    print("  ✅ Conclusion argumentée")
else:
    print("❌ Erreur envoi")