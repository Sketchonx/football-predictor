#!/bin/bash

# Football Predictor Dashboard Launcher
# Ce script lance le dashboard Streamlit

echo "🚀 Démarrage du Football Predictor Dashboard..."
echo ""

# Vérifier si streamlit est installé
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit n'est pas installé"
    echo "📦 Installation des dépendances..."
    pip3 install -r requirements.txt
fi

# Lancer le dashboard
echo "✅ Lancement du dashboard..."
echo "📊 Le dashboard sera accessible sur http://localhost:8501"
echo ""
streamlit run dashboard.py
