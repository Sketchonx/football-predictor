# Ajouter un bouton Dashboard dans les messages Telegram

Pour ajouter un bouton cliquable vers le dashboard dans chaque message quotidien :

## Modifier telegram_sender.py

Ajouter l'import au début du fichier :

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
```

Dans la méthode `send_message()`, avant le `await self.bot.send_message()` :

```python
# Créer un bouton vers le dashboard
keyboard = [[
    InlineKeyboardButton("📊 Voir le Dashboard",
                        url="https://football-predictor.streamlit.app")
]]
reply_markup = InlineKeyboardMarkup(keyboard)
```

Puis ajouter `reply_markup=reply_markup` dans l'appel `send_message` :

```python
await self.bot.send_message(
    chat_id=self.config.TELEGRAM_CHAT_ID,
    text=message,
    parse_mode='Markdown',
    reply_markup=reply_markup  # <-- Ajouter cette ligne
)
```

## Résultat

Chaque message quotidien aura maintenant un bouton cliquable "📊 Voir le Dashboard" qui ouvrira directement votre dashboard hébergé !

**Remarque :** Remplacez l'URL par votre URL réelle après déploiement sur Streamlit Cloud.
