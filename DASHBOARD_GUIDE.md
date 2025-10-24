# 📊 Guide du Dashboard

## 🚀 Lancer le dashboard

```bash
# Option 1 : Script automatique
./run_dashboard.sh

# Option 2 : Commande directe
streamlit run dashboard.py
```

Le dashboard sera accessible sur **http://localhost:8501**

## 📈 Métriques affichées

Le dashboard affiche **uniquement des statistiques de performance** (pas de notion de bankroll) :

### Vue d'ensemble
- **Taux de réussite** : Pourcentage de pronostics gagnants
- **Total pronostics** : Nombre total avec nombre terminés
- **Victoires / Défaites** : Nombre de wins vs losses
- **Cote moyenne** : Moyenne des cotes avec confiance moyenne

### Graphiques
1. **Performance par type de pari** : Barres groupées (Victoires vs Défaites)
2. **Performance par compétition** : Top 5 des compétitions
3. **Évolution dans le temps** : Courbe du taux de réussite

### Tableau historique
- Liste complète des pronostics
- Codes couleur : ✅ Gagné | ❌ Perdu | ⏳ En attente
- Détails : Date, Match, Compétition, Type, Cote, Confiance

## ✏️ Enregistrer les résultats

### Méthode 1 : Via le dashboard
1. Ouvrir le dashboard
2. Dérouler "✏️ Enregistrer un résultat"
3. Sélectionner le pronostic
4. Choisir "win" ou "loss"
5. Ajouter le score (optionnel)
6. Cliquer "💾 Enregistrer"

### Méthode 2 : Via Python

```python
from src.performance_tracker import PerformanceTracker

tracker = PerformanceTracker()

# Enregistrer un résultat
tracker.record_result(
    prediction_id="2025-10-23_0",  # Format: date_index
    result="win",  # ou "loss"
    actual_score="2-1"  # optionnel
)
```

### Méthode 3 : Via script

```bash
python3 << EOF
import sys
sys.path.insert(0, 'src')
from performance_tracker import PerformanceTracker

tracker = PerformanceTracker()
tracker.record_result("2025-10-23_0", "win", "2-1")
print("✅ Résultat enregistré!")
EOF
```

## 🔄 Actualiser le dashboard

Le dashboard se met à jour automatiquement quand vous enregistrez un nouveau résultat. Si besoin de forcer l'actualisation :

1. Dans le dashboard, cliquer sur le menu hamburger (☰) en haut à droite
2. Cliquer sur "Rerun"

Ou appuyer sur **`R`** dans le dashboard.

## 📁 Fichiers de données

- **Prédictions** : `data/predictions/YYYY-MM-DD.json`
- **Résultats** : `data/performance_history.json`

## 🛠️ Dépannage

### Le dashboard ne se lance pas

```bash
# Réinstaller les dépendances
pip3 install -r requirements.txt

# Relancer
streamlit run dashboard.py
```

### Erreur "Module not found"

```bash
# S'assurer d'être dans le bon répertoire
cd /Users/thibaultvanrome/Applications/football-predictor

# Vérifier Python
python3 --version  # Doit être >= 3.9
```

### Les graphiques ne s'affichent pas

```bash
# Mettre à jour Plotly
pip3 install --upgrade plotly streamlit

# Vider le cache
streamlit cache clear
```

### Aucune donnée affichée

1. Vérifier que des prédictions existent : `ls data/predictions/`
2. Vérifier le tracker : `python3 src/performance_tracker.py`
3. Enregistrer au moins un résultat

## 📊 Exemple de workflow quotidien

1. **Matin** : Le système génère automatiquement les pronostics
2. **Soir** : Les matchs sont terminés
3. **Enregistrement** :
   ```bash
   # Ouvrir le dashboard
   streamlit run dashboard.py

   # Ou enregistrer via script
   python3 -c "
   import sys
   sys.path.insert(0, 'src')
   from performance_tracker import PerformanceTracker
   tracker = PerformanceTracker()
   tracker.record_result('2025-10-23_0', 'win', '2-1')
   "
   ```
4. **Consultation** : Vérifier les stats dans le dashboard

## 🎨 Personnalisation

Le dashboard utilise un thème sombre par défaut. Pour changer :

1. Créer `.streamlit/config.toml` :
```toml
[theme]
primaryColor = "#00d4aa"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#1e2130"
textColor = "#ffffff"
```

2. Relancer le dashboard

## 📱 Accès distant

Pour accéder au dashboard depuis un autre appareil :

```bash
streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
```

Puis accéder via : `http://[VOTRE_IP]:8501`

## 🔐 Sécurité

⚠️ **Important** : Le dashboard n'a pas d'authentification par défaut.

Pour protéger :
1. Utiliser un VPN
2. Ou déployer avec authentification (Streamlit Cloud)
3. Ou utiliser un reverse proxy avec auth (nginx)

---

**💡 Astuce** : Le dashboard se met à jour automatiquement toutes les 10 minutes. Pour un rafraîchissement instantané après avoir enregistré un résultat, appuyez sur `R`.
