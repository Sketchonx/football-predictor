# 🔧 Dépannage Streamlit Cloud

## ❗ Error: installer returned a non-zero exit code

### Cause
Problème d'installation des dépendances Python.

### Solutions

#### 1. Vérifier requirements.txt

Utiliser des versions **fixes** (pas `>=`) :

```txt
google-generativeai==0.8.2
python-telegram-bot==20.7
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
python-dotenv==1.0.0
pytz==2023.3
streamlit==1.29.0
plotly==5.18.0
pandas==2.1.4
```

#### 2. Ajouter packages.txt

Créer `packages.txt` à la racine :

```txt
libxml2-dev
libxslt-dev
```

#### 3. Vérifier Python version

Streamlit Cloud utilise **Python 3.9** par défaut.

Pour forcer une version, créer `.python-version` :

```txt
3.11
```

#### 4. Pousser les corrections

```bash
git add requirements.txt packages.txt
git commit -m "fix: Update dependencies for Streamlit Cloud"
git push origin main
```

Streamlit Cloud redémarrera automatiquement le déploiement.

---

## 🚫 Module not found errors

### Erreur: "ModuleNotFoundError: No module named 'src'"

Le dashboard importe `from src.performance_tracker import ...`

**Solution :** Modifier `dashboard.py` pour ajouter le chemin :

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

### Erreur: "No module named 'config'"

**Solution :** S'assurer que le chemin est correct dans les imports.

---

## 🔐 Secrets not configured

### Erreur: KeyError ou None values

**Cause :** Les secrets ne sont pas configurés dans Streamlit Cloud.

**Solution :**

1. Aller sur l'app dans Streamlit Cloud
2. Cliquer sur **Settings** (⚙️)
3. Cliquer sur **Secrets**
4. Copier tout le contenu de votre `.env` :

```toml
GEMINI_API_KEY = "votre_clé"
TELEGRAM_BOT_TOKEN = "votre_token"
TELEGRAM_CHAT_ID = "votre_chat_id"
API_FOOTBALL_KEY = "votre_clé"
TIMEZONE = "Europe/Brussels"
MIN_CONFIDENCE = "75"
MIN_ODDS = "1.50"
MAX_ODDS = "4.00"
MAX_PREDICTIONS = "8"
```

5. Cliquer **Save**
6. Redémarrer l'app

---

## 📁 File not found errors

### Erreur: "FileNotFoundError: data/predictions/"

**Cause :** Les dossiers `data/` n'existent pas sur Streamlit Cloud.

**Solution 1 :** Créer les dossiers avec `.gitkeep`

```bash
mkdir -p data/predictions
touch data/predictions/.gitkeep
touch data/.gitkeep
git add data/
git commit -m "Add data directories"
git push origin main
```

**Solution 2 :** Modifier le code pour créer les dossiers automatiquement

Dans `performance_tracker.py` :

```python
def ensure_data_dirs(self):
    os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
    os.makedirs(self.predictions_dir, exist_ok=True)
```

---

## 🐌 App is slow or crashes

### Cause
Streamlit Cloud gratuit a des ressources limitées.

### Solutions

1. **Optimiser le chargement des données**

```python
@st.cache_data(ttl=300)  # Cache 5 minutes
def load_predictions():
    tracker = PerformanceTracker()
    return tracker.get_all_predictions()
```

2. **Limiter l'historique affiché**

```python
# Au lieu de tous les pronostics
recent_predictions = predictions[:50]  # Seulement les 50 derniers
```

3. **Passer à Railway ou VPS** si trop lent

---

## 🔄 App doesn't update after push

### Solution

1. Aller sur l'app dans Streamlit Cloud
2. Menu hamburger (☰) > **Reboot app**
3. Ou attendre 2-3 minutes (mise à jour automatique)

---

## 🎨 Theme not applied

### Cause
Le fichier `.streamlit/config.toml` n'est pas committé.

### Solution

Vérifier le `.gitignore` :

```bash
# Ne PAS ignorer config.toml
# .streamlit/config.toml  <-- Commenté ou supprimé

# Ignorer SEULEMENT secrets.toml
.streamlit/secrets.toml
```

Puis :

```bash
git add .streamlit/config.toml
git commit -m "Add Streamlit theme config"
git push origin main
```

---

## 📊 No data displayed

### Cause
Pas de prédictions ou résultats dans les fichiers JSON.

### Solution

1. **Vérifier que les fichiers existent** :

```bash
ls data/predictions/
ls data/performance_history.json
```

2. **Créer des données de test** localement puis pousser :

```bash
python3 src/main.py  # Générer des prédictions
python3 src/auto_update_results.py  # Mettre à jour les résultats
git add data/
git commit -m "Add test data"
git push origin main
```

---

## 🔧 Quick fixes checklist

Avant de redéployer, vérifier :

- [ ] `requirements.txt` utilise des versions fixes
- [ ] `packages.txt` existe (si erreur lxml)
- [ ] `.streamlit/config.toml` est committé
- [ ] Secrets configurés dans Streamlit Cloud
- [ ] Dossiers `data/` existent avec `.gitkeep`
- [ ] Code testé localement : `streamlit run dashboard.py`

---

## 📞 Support

Si le problème persiste :

1. **Logs Streamlit Cloud** : Settings > Logs
2. **Tester localement** : `streamlit run dashboard.py`
3. **GitHub Issues** : Vérifier les erreurs similaires

---

## ✅ Déploiement réussi

Quand tout fonctionne, vous verrez :

```
✅ App is live at: https://football-predictor.streamlit.app
```

Le dashboard sera accessible 24/7 ! 🎉
