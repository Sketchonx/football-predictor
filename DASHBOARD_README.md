# 📊 Dashboard Football Predictor

## Actualisation du dashboard

### 🔄 Automatique
Le dashboard Streamlit Cloud se met à jour automatiquement quand les données changent sur GitHub :

- **11h00 UTC (13h Belgique)** : Après l'analyse quotidienne
- **23h00 UTC (01h Belgique)** : Après la mise à jour des résultats

**Délai :** 1-2 minutes après le push GitHub

### 🖱️ Manuelle (depuis le dashboard)
1. Ouvrez le dashboard Streamlit
2. Cliquez sur **"🔄 Refresh"** en haut à droite
3. Ou appuyez sur **"R"** au clavier

### ⚡ Manuelle (depuis votre machine locale)
Si vous voulez forcer la mise à jour immédiatement :

```bash
./update_dashboard.sh
```

Cela pousse les dernières données vers GitHub, et Streamlit Cloud se rafraîchira dans 1-2 minutes.

## Données affichées

- **Total pronostics** : Nombre total de paris effectués
- **Taux de réussite** : Pourcentage de paris gagnants (uniquement sur paris terminés)
- **Pending ⏳** : Matchs en attente de résultat (affichés avec badge orange)
- **Victoires ✅** : Paris gagnants (badge vert)
- **Défaites ❌** : Paris perdus (badge rouge)

## Onglets

### 📊 Performance
- Vue d'ensemble des statistiques
- Graphiques d'évolution
- Stats par type de pari (1X2, BTTS, Over/Under, etc.)
- Stats par compétition (Premier League, La Liga, etc.)

### 🔍 Analyses d'erreurs
- Catégories d'erreurs (absences joueurs, forme récente, etc.)
- Apprentissages clés
- Exemples de paris perdus analysés
