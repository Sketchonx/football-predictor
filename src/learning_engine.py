import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class LearningEngine:
    def __init__(self):
        self.predictions_dir = Path('data/predictions')
        self.results_dir = Path('data/results')
        self.stats_dir = Path('data/stats')
        
        # Créer dossiers
        for dir in [self.predictions_dir, self.results_dir, self.stats_dir]:
            dir.mkdir(parents=True, exist_ok=True)
    
    def save_predictions(self, analysis_result, date):
        """Sauvegarde les prédictions du jour"""
        filepath = self.predictions_dir / f"{date}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        print(f"✅ Prédictions sauvegardées: {filepath}")

        # Ajouter automatiquement les pronostics en statut "pending" dans performance_history.json
        self._register_predictions_as_pending(analysis_result, date)
    
    def fetch_results(self, date):
        """Récupère les résultats réels (à implémenter avec scraping)"""
        # TODO: Scraper résultats depuis FlashScore ou API
        # Pour l'instant, retourne structure vide
        return {}
    
    def compare_predictions(self, date):
        """Compare prédictions vs résultats réels"""
        pred_file = self.predictions_dir / f"{date}.json"
        
        if not pred_file.exists():
            print(f"❌ Pas de prédictions pour {date}")
            return None
        
        with open(pred_file, 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        results = self.fetch_results(date)
        
        comparison = {
            'date': date,
            'predictions': predictions,
            'results': results,
            'accuracy': self._calculate_accuracy(predictions, results)
        }
        
        # Sauvegarder
        result_file = self.results_dir / f"{date}_verified.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        
        return comparison
    
    def _calculate_accuracy(self, predictions, results):
        """Calcule le taux de réussite"""
        if not results:
            return None
        
        # TODO: Implémenter logique de comparaison
        return {
            'win_rate': 0,
            'total': 0,
            'wins': 0,
            'losses': 0
        }
    
    def get_learning_stats(self):
        """Récupère statistiques pour ajuster le prompt"""
        stats_file = self.stats_dir / 'global_stats.json'
        
        if not stats_file.exists():
            return {
                'win_rate': 0,
                'total_predictions': 0,
                'common_errors': []
            }
        
        with open(stats_file, 'r') as f:
            return json.load(f)
    
    def update_stats(self, comparison):
        """Met à jour les statistiques globales"""
        stats = self.get_learning_stats()

        # TODO: Mise à jour intelligente basée sur les résultats

        stats_file = self.stats_dir / 'global_stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    def _register_predictions_as_pending(self, analysis_result, date):
        """Enregistre les nouveaux pronostics comme 'pending' dans performance_history.json"""
        performance_file = Path('data/performance_history.json')

        # Charger l'historique existant
        if performance_file.exists():
            with open(performance_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []

        # IDs existants
        existing_ids = {entry['prediction_id'] for entry in history}

        # Ajouter les nouveaux pronostics en pending
        recommendations = analysis_result.get('recommendations', [])
        new_entries = 0

        for idx, rec in enumerate(recommendations):
            prediction_id = f"{date}_{idx}"

            # Ajouter seulement si pas déjà présent
            if prediction_id not in existing_ids:
                history.append({
                    'prediction_id': prediction_id,
                    'result': 'pending',
                    'actual_score': None,
                    'recorded_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                new_entries += 1

        # Sauvegarder
        if new_entries > 0:
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            print(f"✅ {new_entries} pronostics enregistrés comme 'pending' dans performance_history.json")