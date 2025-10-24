# ⚽ Football Predictor

Système d'analyse et de prédiction de matchs de football utilisant l'IA Gemini, avec dashboard de suivi des performances.

## 🚀 Fonctionnalités

- **Analyse IA** : Analyse approfondie des matchs avec Gemini 2.5 Flash
- **Filtrage intelligent** : Uniquement championnats européens majeurs + compétitions UEFA
- **Types de paris variés** : 1X2, Over/Under, BTTS, Handicap
- **Envoi automatique** : Notifications Telegram quotidiennes
- **Dashboard professionnel** : Suivi des performances en temps réel
- **GitHub Actions** : Automatisation quotidienne

## 📦 Installation

```bash
# Cloner le repository
git clone https://github.com/Sketchonx/football-predictor.git
cd football-predictor

# Installer les dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

Créez un fichier `.env` à la racine :

```env
# API Keys
GEMINI_API_KEY=votre_cle_gemini
TELEGRAM_BOT_TOKEN=votre_token_telegram
TELEGRAM_CHAT_ID=votre_chat_id
API_FOOTBALL_KEY=votre_cle_api_football

# Configuration
TIMEZONE=Europe/Brussels
MIN_CONFIDENCE=75
MIN_ODDS=1.50
MAX_ODDS=4.00
MAX_PREDICTIONS=8
```

## 🎯 Utilisation

### Analyse quotidienne

```bash
python3 src/main.py
```

Cette commande :
1. Récupère les matchs du jour depuis API-Football
2. Filtre selon les championnats configurés
3. Analyse avec Gemini AI
4. Sauvegarde les prédictions dans `data/predictions/`
5. Envoie un message sur Telegram

### Dashboard

```bash
streamlit run dashboard.py
```

Le dashboard sera accessible sur `http://localhost:8501`

**Fonctionnalités du dashboard :**
- 📊 Vue d'ensemble (taux de réussite, ROI, profits)
- 📈 Performance par type de pari
- 🏆 Performance par compétition
- 📅 Évolution dans le temps
- 📋 Historique des pronostics
- ✏️ Enregistrement des résultats

### Rapport hebdomadaire

Un rapport de performance est envoyé automatiquement **tous les lundis à 9h UTC** sur Telegram avec :
- 📊 Taux de réussite de la semaine écoulée
- ✅ Nombre de victoires/défaites
- 📈 Performance par type de pari
- 🏆 Performance par compétition (Top 3)
- 💎 Cote et confiance moyennes
- 🔥 Série en cours (victoires/défaites consécutives)
- 🏅 Meilleur pari de la semaine

Pour générer manuellement un rapport :
```bash
python3 src/weekly_report.py
```

## 📁 Structure du projet

```
football-predictor/
├── src/
│   ├── main.py              # Script principal
│   ├── match_scraper.py     # Récupération des matchs
│   ├── gemini_analyzer.py   # Analyse IA
│   ├── telegram_sender.py   # Envoi Telegram
│   ├── performance_tracker.py # Suivi des performances
│   └── config.py            # Configuration
├── prompts/
│   └── base_prompt.txt      # Prompt détaillé pour Gemini
├── data/
│   ├── predictions/         # Fichiers JSON des prédictions
│   └── performance_history.json # Historique des résultats
├── dashboard.py             # Dashboard Streamlit
├── requirements.txt         # Dépendances Python
└── .github/workflows/
    └── daily_analysis.yml   # Workflow GitHub Actions
```

## 🏆 Championnats analysés

### Compétitions UEFA
- UEFA Champions League
- UEFA Europa League
- UEFA Europa Conference League

### Championnats nationaux
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Angleterre)
- 🇪🇸 La Liga (Espagne)
- 🇮🇹 Serie A (Italie)
- 🇩🇪 Bundesliga (Allemagne)
- 🇫🇷 Ligue 1 (France)
- 🇧🇪 Jupiler Pro League (Belgique)

## 📊 Types de paris

Le système propose différents types de paris selon le contexte :

- **1X2** : Victoire/Nul/Défaite (40%)
- **Over/Under 2.5 buts** : Matchs à buts (30%)
- **BTTS** : Both Teams To Score (20%)
- **Handicap** : Pour gros favoris (10%)

## 🤖 Automatisation

### Analyse quotidienne
Le workflow s'exécute automatiquement tous les jours à **11h UTC** (12h Belgique) :
1. Récupère les matchs du jour
2. Analyse avec Gemini
3. Envoie les pronostics sur Telegram
4. Sauvegarde dans le repository

### Mise à jour automatique des résultats 🆕
Le workflow s'exécute automatiquement tous les jours à **23h UTC** (00h Belgique) :
1. Récupère les scores finaux via API-Football
2. Détermine automatiquement si les pronostics sont gagnants/perdants
3. Met à jour la base de données
4. Commit les résultats sur GitHub

**Plus besoin de saisir manuellement les résultats !** ✨

### Rapport hebdomadaire
Le workflow s'exécute tous les **lundis à 9h UTC** :
1. Analyse les performances de la semaine écoulée
2. Envoie le rapport sur Telegram

## 📱 Enregistrer les résultats (Manuel - Optionnel)

⚡ **Les résultats sont maintenant mis à jour automatiquement tous les soirs à 23h UTC !**

Si vous voulez mettre à jour manuellement avant :

### Automatiquement (Recommandé)
```bash
python3 src/auto_update_results.py
```

### Via le dashboard

1. Ouvrir `http://localhost:8501`
2. Dérouler la section "✏️ Enregistrer un résultat"
3. Sélectionner le pronostic
4. Choisir le résultat (win/loss)
5. Enregistrer

### Via Python

```python
from src.performance_tracker import PerformanceTracker

tracker = PerformanceTracker()
tracker.record_result(
    prediction_id="2025-10-23_0",
    result="win",  # ou "loss"
    actual_score="2-1"  # optionnel
)
```

## 📈 Métriques du dashboard

- **Taux de réussite** : % de pronostics gagnants
- **ROI** : Retour sur investissement (%)
- **Profit/Perte** : Gains en euros (base 10€/pari)
- **Performance par type** : Statistiques par type de pari
- **Performance par compétition** : Statistiques par championnat
- **Évolution** : Graphique de progression

## 🔧 Personnalisation

### Modifier les championnats

Éditez `src/config.py` :

```python
INCLUDED_LEAGUE_IDS = [
    2,    # UEFA Champions League
    39,   # Premier League
    # Ajouter d'autres IDs...
]
```

### Modifier le prompt

Éditez `prompts/base_prompt.txt` pour ajuster :
- Les critères d'analyse
- La profondeur des analyses
- Les types de paris favorisés
- Le format de sortie

### Modifier les seuils

Dans `.env` :
- `MIN_CONFIDENCE=75` : Confiance minimale (%)
- `MIN_ODDS=1.50` : Cote minimale
- `MAX_ODDS=4.00` : Cote maximale
- `MAX_PREDICTIONS=8` : Nombre max de pronostics/jour

## 🐛 Dépannage

### Erreur API-Football
- Vérifiez votre clé API
- Vérifiez la limite (100 requêtes/jour en gratuit)

### Erreur Gemini
- Vérifiez votre clé API Gemini
- Vérifiez les quotas

### Dashboard ne s'affiche pas
```bash
pip install --upgrade streamlit plotly pandas
streamlit run dashboard.py
```

## 📝 Licence

MIT License

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

---

**⚽ Bonne chance avec vos pronostics ! 🍀**
