# 🔑 Configuration de l'API Claude (Anthropic)

## ⚠️ Important : Claude Pro ≠ API

- **Claude Pro (20$/mois)** : Accès à l'interface web **claude.ai**
- **Claude API** : Système séparé, **facturé à l'usage** (pay-as-you-go)

Même si vous avez Claude Pro, vous devez **créer un compte API séparé**.

---

## 📝 Étapes pour obtenir votre clé API

### 1. Créer un compte API Anthropic

1. Allez sur : **https://console.anthropic.com/**
2. Cliquez sur "Sign Up" (ou "Log In" si vous avez déjà un compte)
3. Utilisez votre email (peut être le même que Claude Pro)
4. Vérifiez votre email

### 2. Obtenir votre clé API

1. Une fois connecté, allez dans **"API Keys"** (menu de gauche)
2. Cliquez sur **"Create Key"**
3. Donnez un nom à la clé (ex: "Football Predictor")
4. **COPIEZ immédiatement la clé** (format: `sk-ant-api03-...`)
   - ⚠️ Elle ne sera affichée qu'une seule fois !

### 3. Ajouter la clé dans votre projet

Ouvrez le fichier `.env` et remplacez :

```env
ANTHROPIC_API_KEY=votre_cle_anthropic_ici
```

Par :

```env
ANTHROPIC_API_KEY=sk-ant-api03-VOTRE_VRAIE_CLE_ICI
```

### 4. Ajouter des crédits (si nécessaire)

Anthropic peut vous donner des **crédits gratuits** pour tester (5-10$).

Sinon, ajoutez une carte bancaire :
1. Allez dans **"Billing"**
2. Cliquez sur **"Add Payment Method"**
3. Ajoutez votre carte

---

## 💰 Tarification API Claude

### Claude 3.5 Sonnet (modèle utilisé)

- **Input** : $3 / million de tokens (~750 000 mots)
- **Output** : $15 / million de tokens

### Coût estimé pour ce projet

**Par analyse quotidienne** :
- Prompt + contexte : ~2 000 tokens input
- Réponse détaillée : ~3 000 tokens output
- **Coût par analyse : ~0.05€** (5 centimes)

**Par mois** (1 analyse/jour) :
- 30 analyses × 0.05€ = **~1.50€/mois**

C'est **négligeable** comparé à la valeur des analyses !

---

## ✅ Tester que ça fonctionne

Une fois la clé ajoutée dans `.env`, testez :

```bash
python3 src/claude_analyzer.py
```

Si vous voyez un message d'analyse, c'est bon ! ✅

---

## 🚀 Lancer l'analyse complète

```bash
python3 src/main.py
```

Vous recevrez une analyse **beaucoup plus fiable** avec Claude :
- ✅ Raisonnement rigoureux et méthodique
- ✅ Moins d'hallucinations/inventions
- ✅ Meilleur respect du prompt VALUE BET
- ✅ Analyses plus prudentes et nuancées

---

## 🔒 Sécurité

⚠️ **IMPORTANT** : Ne partagez JAMAIS votre clé API !

- Ne la commitez pas sur GitHub (le `.env` est déjà dans `.gitignore`)
- Ne la partagez avec personne
- Si compromise, régénérez-la immédiatement sur console.anthropic.com

---

## 📞 Support

Si vous avez des questions sur la facturation ou l'API :
- Support Anthropic : https://support.anthropic.com/
- Documentation API : https://docs.anthropic.com/

---

## 🎯 Résumé

1. ✅ Créer compte sur console.anthropic.com
2. ✅ Générer clé API
3. ✅ Copier dans `.env` → `ANTHROPIC_API_KEY=sk-ant-...`
4. ✅ Tester avec `python3 src/main.py`
5. 🎉 Profiter d'analyses de QUALITÉ !

**Coût : ~1.50€/mois pour 1 analyse/jour**
