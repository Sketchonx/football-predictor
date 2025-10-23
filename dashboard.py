import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.insert(0, 'src')
from performance_tracker import PerformanceTracker

# Configuration de la page
st.set_page_config(
    page_title="Football Predictor Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un design moderne
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2e3241;
    }
    .stMetric label {
        color: #8b92a7 !important;
        font-size: 14px !important;
    }
    .stMetric .metric-value {
        color: #ffffff !important;
        font-size: 32px !important;
        font-weight: bold !important;
    }
    h1 {
        color: #00d4aa;
        font-weight: 800;
    }
    h2, h3 {
        color: #ffffff;
    }
    .win-badge {
        background-color: #00d4aa;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .loss-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .pending-badge {
        background-color: #ffa500;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation
tracker = PerformanceTracker()

# Header
st.markdown("# ⚽ Football Predictor Dashboard")
st.markdown("---")

# Sidebar - Filtres
st.sidebar.header("🔍 Filtres")
date_range = st.sidebar.date_input(
    "Période",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

# Charger les données
predictions = tracker.get_all_predictions()
stats = tracker.calculate_statistics()
stats_by_type = tracker.get_statistics_by_type()
stats_by_comp = tracker.get_statistics_by_competition()

# Section 1: Métriques principales
st.markdown("## 📊 Vue d'ensemble")

col1, col2, col3, col4 = st.columns(4)

with col1:
    win_rate_delta = None
    if stats['completed'] > 0:
        win_rate_delta = f"{stats['win_rate']:.1f}%"
    st.metric(
        label="Taux de réussite",
        value=f"{stats['win_rate']:.1f}%",
        delta=win_rate_delta if stats['completed'] >= 10 else None
    )

with col2:
    roi_color = "normal" if stats['roi'] >= 0 else "inverse"
    st.metric(
        label="ROI",
        value=f"{stats['roi']:.1f}%",
        delta=f"€{stats['profit']:.2f}" if stats['completed'] > 0 else None,
        delta_color=roi_color
    )

with col3:
    st.metric(
        label="Pronostics gagnants",
        value=f"{stats['total_wins']}/{stats['completed']}",
        delta=f"{stats['pending']} en attente"
    )

with col4:
    st.metric(
        label="Cote moyenne",
        value=f"{stats['avg_odds']:.2f}",
        delta=f"Confiance: {stats['avg_confidence']:.0f}%"
    )

st.markdown("---")

# Section 2: Graphiques
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Performance par type de pari")

    if stats_by_type:
        df_types = pd.DataFrame([
            {
                'Type': bet_type,
                'Victoires': data['wins'],
                'Défaites': data['losses'],
                'Taux de réussite': data['win_rate']
            }
            for bet_type, data in stats_by_type.items()
        ])

        # Graphique en barres
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Victoires',
            x=df_types['Type'],
            y=df_types['Victoires'],
            marker_color='#00d4aa'
        ))
        fig.add_trace(go.Bar(
            name='Défaites',
            x=df_types['Type'],
            y=df_types['Défaites'],
            marker_color='#ff4b4b'
        ))

        fig.update_layout(
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#2e3241'),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible pour ce graphique")

with col2:
    st.markdown("### 🏆 Performance par compétition")

    if stats_by_comp:
        # Prendre les top 5 compétitions
        sorted_comps = sorted(stats_by_comp.items(), key=lambda x: x[1]['total'], reverse=True)[:5]

        df_comps = pd.DataFrame([
            {
                'Compétition': comp[:20] + '...' if len(comp) > 20 else comp,
                'Taux de réussite': data['win_rate'],
                'Total': data['total']
            }
            for comp, data in sorted_comps
        ])

        # Graphique à barres horizontales
        fig = px.bar(
            df_comps,
            y='Compétition',
            x='Taux de réussite',
            orientation='h',
            color='Taux de réussite',
            color_continuous_scale=['#ff4b4b', '#ffa500', '#00d4aa'],
            text='Total'
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(showgrid=True, gridcolor='#2e3241'),
            yaxis=dict(showgrid=False),
            height=400,
            coloraxis_showscale=False
        )

        fig.update_traces(texttemplate='%{text} paris', textposition='outside')

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible pour ce graphique")

st.markdown("---")

# Section 3: Évolution dans le temps
st.markdown("### 📅 Évolution des performances")

if predictions:
    # Créer un DataFrame avec l'évolution
    completed_predictions = [p for p in predictions if p['result'] in ['win', 'loss']]

    if completed_predictions:
        df_timeline = pd.DataFrame(completed_predictions)
        df_timeline['date'] = pd.to_datetime(df_timeline['date'])
        df_timeline = df_timeline.sort_values('date')

        # Calcul du win rate cumulé
        df_timeline['cumulative_wins'] = (df_timeline['result'] == 'win').cumsum()
        df_timeline['cumulative_total'] = range(1, len(df_timeline) + 1)
        df_timeline['cumulative_win_rate'] = (df_timeline['cumulative_wins'] / df_timeline['cumulative_total']) * 100

        # Graphique d'évolution
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_timeline['date'],
            y=df_timeline['cumulative_win_rate'],
            mode='lines+markers',
            name='Taux de réussite',
            line=dict(color='#00d4aa', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 170, 0.1)'
        ))

        # Ligne de référence à 50%
        fig.add_hline(y=50, line_dash="dash", line_color="white", opacity=0.3)

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(showgrid=True, gridcolor='#2e3241'),
            yaxis=dict(showgrid=True, gridcolor='#2e3241', title='Taux de réussite (%)'),
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enregistrez des résultats pour voir l'évolution")
else:
    st.info("Aucun pronostic disponible")

st.markdown("---")

# Section 4: Tableau des derniers pronostics
st.markdown("### 📋 Derniers pronostics")

if predictions:
    # Prendre les 20 derniers
    recent_predictions = predictions[:20]

    # Créer le DataFrame
    df_predictions = pd.DataFrame([
        {
            'Date': p['date'],
            'Match': p['match'],
            'Compétition': p['competition'][:25] + '...' if len(p['competition']) > 25 else p['competition'],
            'Type': p['bet_type'],
            'Pronostic': p['prediction'][:30] + '...' if len(p['prediction']) > 30 else p['prediction'],
            'Cote': f"{p['odds']:.2f}",
            'Confiance': f"{p['confidence']}%",
            'Résultat': '✅ Gagné' if p['result'] == 'win' else ('❌ Perdu' if p['result'] == 'loss' else '⏳ En attente')
        }
        for p in recent_predictions
    ])

    # Fonction pour colorer les résultats
    def color_result(val):
        if '✅' in str(val):
            return 'background-color: rgba(0, 212, 170, 0.2)'
        elif '❌' in str(val):
            return 'background-color: rgba(255, 75, 75, 0.2)'
        elif '⏳' in str(val):
            return 'background-color: rgba(255, 165, 0, 0.2)'
        return ''

    # Afficher le tableau stylisé
    st.dataframe(
        df_predictions.style.applymap(color_result, subset=['Résultat']),
        use_container_width=True,
        height=600
    )
else:
    st.info("Aucun pronostic disponible")

# Section 5: Interface de saisie des résultats
st.markdown("---")
st.markdown("### ✏️ Enregistrer un résultat")

with st.expander("Cliquez pour enregistrer le résultat d'un pronostic"):
    pending_predictions = [p for p in predictions if not p['result'] or p['result'] not in ['win', 'loss']]

    if pending_predictions:
        selected_pred = st.selectbox(
            "Sélectionner un pronostic",
            options=range(len(pending_predictions)),
            format_func=lambda x: f"{pending_predictions[x]['date']} - {pending_predictions[x]['match']} ({pending_predictions[x]['bet_type']})"
        )

        col1, col2 = st.columns(2)

        with col1:
            result = st.radio("Résultat", ['win', 'loss'])

        with col2:
            actual_score = st.text_input("Score réel (optionnel)", placeholder="Ex: 2-1")

        if st.button("💾 Enregistrer"):
            pred_id = pending_predictions[selected_pred]['id']
            tracker.record_result(pred_id, result, actual_score)
            st.success("✅ Résultat enregistré avec succès!")
            st.rerun()
    else:
        st.info("Aucun pronostic en attente")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #8b92a7; padding: 20px;'>
    <p>⚽ Football Predictor Dashboard | Propulsé par Streamlit & Gemini AI</p>
</div>
""", unsafe_allow_html=True)
