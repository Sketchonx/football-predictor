# 🚀 Correction et Redéploiement - Commandes Rapides

## ❗ Vous avez une erreur "installer returned a non-zero exit code" ?

Suivez ces étapes pour corriger :

## 📋 Étape 1 : Vérifier les fichiers modifiés

```bash
ls -la requirements.txt packages.txt .streamlit/config.toml
```

Vous devriez voir :
- ✅ `requirements.txt` (versions fixes)
- ✅ `packages.txt` (dépendances système)
- ✅ `.streamlit/config.toml` (configuration)

## 📋 Étape 2 : Vérifier le contenu

### requirements.txt
```bash
cat requirements.txt
```

Doit contenir des versions **fixes** (pas de `>=`) :
```
google-generativeai==0.8.2
streamlit==1.29.0
...
```

### packages.txt
```bash
cat packages.txt
```

Doit contenir :
```
libxml2-dev
libxslt-dev
```

## 📋 Étape 3 : Pousser les corrections sur GitHub

```bash
# Ajouter tous les fichiers modifiés
git add requirements.txt packages.txt .streamlit/config.toml data/

# Créer un commit
git commit -m "fix: Update dependencies for Streamlit Cloud compatibility"

# Pousser sur GitHub
git push origin main
```

## 📋 Étape 4 : Streamlit Cloud va redéployer automatiquement

1. Aller sur https://share.streamlit.io
2. Ouvrir votre app
3. Regarder les logs (Settings > Logs)
4. Attendre 2-3 minutes

## ✅ Si ça fonctionne :

Vous verrez :
```
✅ App is live at: https://football-predictor.streamlit.app
```

## ❌ Si ça ne fonctionne toujours pas :

### Vérifier les secrets

1. Dans Streamlit Cloud > Settings > Secrets
2. Ajouter :

```toml
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
4. Reboot app

### Vérifier les logs

Dans Streamlit Cloud : Settings > Logs

Recherchez :
- ❌ `ModuleNotFoundError` → Vérifier imports
- ❌ `FileNotFoundError` → Vérifier dossiers data/
- ❌ `KeyError` → Vérifier secrets

## 🔄 Forcer un redéploiement

Dans Streamlit Cloud :
1. Menu hamburger (☰)
2. **Reboot app**

Ou créer un commit vide :
```bash
git commit --allow-empty -m "trigger: Force Streamlit Cloud redeploy"
git push origin main
```

## 📞 Besoin d'aide ?

Consultez : [STREAMLIT_TROUBLESHOOTING.md](STREAMLIT_TROUBLESHOOTING.md)

---

## 🎉 Une fois déployé avec succès :

### Obtenir l'URL

Votre dashboard sera accessible à :
```
https://football-predictor.streamlit.app
```
(Le nom exact peut varier)

### Épingler dans Telegram

1. Ouvrir le groupe Telegram
2. Envoyer : `📊 Dashboard: https://football-predictor.streamlit.app`
3. Cliquer sur le message > Pin message

### Ajouter un bouton (optionnel)

Voir : [add_dashboard_button.md](add_dashboard_button.md)

---

## ✅ Checklist finale

Avant de déployer, vérifier :

- [x] `requirements.txt` avec versions fixes
- [x] `packages.txt` créé
- [x] `.streamlit/config.toml` committé
- [x] Dossiers `data/` avec `.gitkeep`
- [x] Code testé localement
- [ ] Secrets configurés dans Streamlit Cloud
- [ ] App déployée avec succès
- [ ] URL épinglée dans Telegram

🚀 **Bonne chance !**
