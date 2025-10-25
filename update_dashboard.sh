#!/bin/bash
# Script pour forcer l'actualisation du dashboard Streamlit

echo "🔄 Actualisation du dashboard..."

# Commit et push des données
git add data/performance_history.json data/predictions/*.json data/error_analysis.json data/learnings.json 2>/dev/null

if git diff --staged --quiet; then
  echo "ℹ️ Aucune modification à pousser"
else
  git commit -m "📊 Mise à jour dashboard - $(date +'%Y-%m-%d %H:%M')"
  git push origin main
  echo "✅ Dashboard actualisé ! Streamlit Cloud se rafraîchira dans 1-2 minutes"
fi
