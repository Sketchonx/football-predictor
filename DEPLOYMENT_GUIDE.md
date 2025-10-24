# 🚀 Guide de déploiement du Dashboard

## Option 1 : Streamlit Cloud (Recommandé - GRATUIT) ⭐

### Avantages
- ✅ **100% Gratuit** pour les projets publics
- ✅ Hébergement optimisé pour Streamlit
- ✅ URL permanente (ex: `https://football-predictor.streamlit.app`)
- ✅ SSL/HTTPS automatique
- ✅ Mise à jour automatique à chaque push GitHub
- ✅ Parfait pour épingler dans Telegram

### 📋 Étapes de déploiement

#### 1. Préparer le repository GitHub

```bash
# Pousser tout le code sur GitHub
git add .
git commit -m "feat: Prepare for Streamlit Cloud deployment"
git push origin main
```

#### 2. Créer un compte Streamlit Cloud

1. Aller sur **https://share.streamlit.io**
2. Se connecter avec GitHub
3. Autoriser Streamlit à accéder à vos repositories

#### 3. Déployer l'application

1. Cliquer sur **"New app"**
2. Sélectionner :
   - **Repository** : `Sketchonx/football-predictor`
   - **Branch** : `main`
   - **Main file path** : `dashboard.py`
3. Cliquer sur **"Deploy"**

#### 4. Configurer les secrets

Dans Streamlit Cloud :
1. Aller dans **Settings** > **Secrets**
2. Ajouter vos variables d'environnement :

```toml
# Copier le contenu de votre fichier .env ici
GEMINI_API_KEY = "AIzaSyDZH2Y8Nf2MnfSgPX18nyB_CFhy0qLi97E"
TELEGRAM_BOT_TOKEN = "8457457360:AAFKbEbcn_jOvpy1EFI8bDNaUZYNXG5MA9c"
TELEGRAM_CHAT_ID = "-1003121682985"
API_FOOTBALL_KEY = "a58fd503fdf1c6c4ed042d552732abf6"
TIMEZONE = "Europe/Brussels"
MIN_CONFIDENCE = "75"
MIN_ODDS = "1.50"
MAX_ODDS = "4.00"
MAX_PREDICTIONS = "8"
```

3. Sauvegarder

#### 5. Obtenir l'URL

Une fois déployé, vous obtiendrez une URL du type :
```
https://football-predictor.streamlit.app
```

#### 6. Épingler dans Telegram

1. Ouvrir votre groupe Telegram
2. Envoyer le lien du dashboard
3. Cliquer sur le message > **Pin message**

✅ **C'est fait !** Votre dashboard est maintenant accessible 24/7 !

---

## Option 2 : Railway (Alternatif - GRATUIT avec limites)

### Avantages
- ✅ 500 heures gratuites/mois
- ✅ Déploiement automatique depuis GitHub
- ✅ SSL inclus

### Étapes

1. Créer un compte sur **https://railway.app**
2. Connecter GitHub
3. Créer un nouveau projet depuis `football-predictor`
4. Railway détectera automatiquement Streamlit
5. Ajouter les variables d'environnement
6. Déployer

---

## Option 3 : Heroku (Payant - $7/mois minimum)

### Configuration requise

Créer un `Procfile` :

```bash
web: streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0
```

Créer un `setup.sh` :

```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

### Déploiement

```bash
heroku create football-predictor
git push heroku main
heroku config:set GEMINI_API_KEY="..."
heroku config:set TELEGRAM_BOT_TOKEN="..."
```

---

## Option 4 : VPS/Serveur personnel (Pour les avancés)

### Configuration

1. Installer Python 3.9+ sur le serveur
2. Cloner le repository
3. Installer les dépendances
4. Lancer avec `streamlit run dashboard.py --server.port=8501`
5. Configurer Nginx comme reverse proxy
6. Ajouter SSL avec Let's Encrypt

---

## 🔐 Sécurité

### Streamlit Cloud
- Les secrets sont chiffrés
- Accès HTTPS uniquement
- Pas d'authentification par défaut (dashboard public)

### Ajouter une authentification (optionnel)

Pour protéger le dashboard, ajouter au début de `dashboard.py` :

```python
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == "votre_mot_de_passe":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Mot de passe", type="password",
                     on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Mot de passe", type="password",
                     on_change=password_entered, key="password")
        st.error("😕 Mot de passe incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Reste du code dashboard...
```

---

## 📱 Intégration Telegram

### Créer un bouton dans les messages quotidiens

Modifier `telegram_sender.py` pour ajouter un bouton :

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Dans send_message()
keyboard = [[InlineKeyboardButton("📊 Voir le Dashboard",
             url="https://football-predictor.streamlit.app")]]
reply_markup = InlineKeyboardMarkup(keyboard)

await self.bot.send_message(
    chat_id=self.config.TELEGRAM_CHAT_ID,
    text=message,
    parse_mode='Markdown',
    reply_markup=reply_markup
)
```

---

## 🔄 Mises à jour automatiques

Avec Streamlit Cloud, chaque `git push` sur GitHub déclenche automatiquement un redéploiement du dashboard.

```bash
# Faire des modifications
git add .
git commit -m "Update dashboard"
git push origin main

# Streamlit Cloud se met à jour automatiquement (1-2 minutes)
```

---

## 🛠️ Dépannage

### Le dashboard ne démarre pas

1. Vérifier les logs dans Streamlit Cloud (Settings > Logs)
2. Vérifier que tous les secrets sont configurés
3. Vérifier que `requirements.txt` est à jour

### Erreur "Module not found"

Ajouter la dépendance manquante dans `requirements.txt` :

```bash
git add requirements.txt
git commit -m "Add missing dependency"
git push origin main
```

### Dashboard lent

- Streamlit Cloud : Gratuit mais limité en ressources
- Solution : Passer à Railway ou VPS pour plus de puissance

---

## 💰 Coûts estimés

| Solution | Coût | Limites |
|----------|------|---------|
| **Streamlit Cloud** | **Gratuit** | 1 app, ressources limitées |
| **Railway** | Gratuit | 500h/mois, puis $5-10/mois |
| **Heroku** | $7/mois | Dyno Eco |
| **VPS (DigitalOcean)** | $5/mois | 1GB RAM |

---

## ✅ Checklist finale

Avant de déployer :

- [ ] Code poussé sur GitHub
- [ ] `.env` dans `.gitignore`
- [ ] `requirements.txt` à jour
- [ ] `.streamlit/config.toml` créé
- [ ] Compte Streamlit Cloud créé
- [ ] Secrets configurés
- [ ] Dashboard testé en local
- [ ] URL épinglée dans Telegram

---

**🎉 Votre dashboard sera accessible 24/7 à l'adresse :**
```
https://football-predictor.streamlit.app
```

(Le nom exact dépendra de votre déploiement)
