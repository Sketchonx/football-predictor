import json
import os
from datetime import datetime
from typing import Dict, List
import glob

class PerformanceTracker:
    def __init__(self, predictions_dir='data/predictions', results_file='data/performance_history.json'):
        self.predictions_dir = predictions_dir
        self.results_file = results_file
        self.ensure_data_dirs()

    def ensure_data_dirs(self):
        """Créer les dossiers nécessaires"""
        os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
        os.makedirs(self.predictions_dir, exist_ok=True)

    def load_performance_history(self) -> List[Dict]:
        """Charge l'historique des performances"""
        if not os.path.exists(self.results_file):
            return []

        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_performance_history(self, history: List[Dict]):
        """Sauvegarde l'historique des performances"""
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(history, indent=2, ensure_ascii=False, fp=f)

    def record_result(self, prediction_id: str, result: str, actual_score: str = None):
        """
        Enregistre le résultat d'un pronostic

        Args:
            prediction_id: ID du pronostic (format: date_match_index)
            result: 'win', 'loss', 'pending'
            actual_score: Score réel du match (optionnel)
        """
        history = self.load_performance_history()

        # Chercher si le pronostic existe déjà
        for entry in history:
            if entry.get('prediction_id') == prediction_id:
                entry['result'] = result
                entry['actual_score'] = actual_score
                entry['updated_at'] = datetime.now().isoformat()
                self.save_performance_history(history)
                return

        # Sinon, ajouter une nouvelle entrée
        history.append({
            'prediction_id': prediction_id,
            'result': result,
            'actual_score': actual_score,
            'recorded_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })

        self.save_performance_history(history)

    def get_all_predictions(self) -> List[Dict]:
        """Récupère tous les pronostics depuis les fichiers JSON"""
        predictions = []

        # Parcourir tous les fichiers de prédictions
        prediction_files = glob.glob(f"{self.predictions_dir}/*.json")

        for file_path in sorted(prediction_files, reverse=True):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                date = data.get('analysis_date', os.path.basename(file_path).replace('.json', ''))

                for idx, rec in enumerate(data.get('recommendations', [])):
                    prediction_id = f"{date}_{idx}"

                    predictions.append({
                        'id': prediction_id,
                        'date': date,
                        'match': rec.get('match'),
                        'competition': rec.get('competition'),
                        'bet_type': rec.get('bet_type'),
                        'prediction': rec.get('prediction'),
                        'odds': rec.get('odds'),
                        'confidence': rec.get('confidence'),
                        'risk_level': rec.get('risk_level', 'Medium'),
                        'result': None,  # Sera mis à jour depuis performance_history.json
                        'actual_score': None
                    })
            except Exception as e:
                print(f"Erreur lecture {file_path}: {e}")
                continue

        # Enrichir avec les résultats
        history = self.load_performance_history()
        history_dict = {h['prediction_id']: h for h in history}

        for pred in predictions:
            if pred['id'] in history_dict:
                pred['result'] = history_dict[pred['id']].get('result')
                pred['actual_score'] = history_dict[pred['id']].get('actual_score')

        return predictions

    def calculate_statistics(self) -> Dict:
        """Calcule les statistiques globales"""
        predictions = self.get_all_predictions()

        if not predictions:
            return {
                'total_predictions': 0,
                'completed': 0,
                'win_rate': 0,
                'total_wins': 0,
                'total_losses': 0,
                'pending': 0,
                'avg_odds': 0,
                'avg_confidence': 0
            }

        completed = [p for p in predictions if p['result'] in ['win', 'loss']]
        wins = [p for p in completed if p['result'] == 'win']
        losses = [p for p in completed if p['result'] == 'loss']
        pending = [p for p in predictions if p['result'] not in ['win', 'loss']]

        return {
            'total_predictions': len(predictions),
            'completed': len(completed),
            'win_rate': (len(wins) / len(completed) * 100) if completed else 0,
            'total_wins': len(wins),
            'total_losses': len(losses),
            'pending': len(pending),
            'avg_odds': sum([p['odds'] for p in predictions]) / len(predictions),
            'avg_confidence': sum([p['confidence'] for p in predictions]) / len(predictions),
        }

    def get_statistics_by_type(self) -> Dict:
        """Statistiques par type de pari"""
        predictions = self.get_all_predictions()
        completed = [p for p in predictions if p['result'] in ['win', 'loss']]

        by_type = {}

        for pred in completed:
            bet_type = pred['bet_type']
            if bet_type not in by_type:
                by_type[bet_type] = {'wins': 0, 'losses': 0, 'total': 0}

            by_type[bet_type]['total'] += 1
            if pred['result'] == 'win':
                by_type[bet_type]['wins'] += 1
            else:
                by_type[bet_type]['losses'] += 1

        # Calculer le taux de réussite
        for bet_type in by_type:
            total = by_type[bet_type]['total']
            wins = by_type[bet_type]['wins']
            by_type[bet_type]['win_rate'] = (wins / total * 100) if total > 0 else 0

        return by_type

    def get_statistics_by_competition(self) -> Dict:
        """Statistiques par compétition"""
        predictions = self.get_all_predictions()
        completed = [p for p in predictions if p['result'] in ['win', 'loss']]

        by_comp = {}

        for pred in completed:
            comp = pred['competition']
            if comp not in by_comp:
                by_comp[comp] = {'wins': 0, 'losses': 0, 'total': 0}

            by_comp[comp]['total'] += 1
            if pred['result'] == 'win':
                by_comp[comp]['wins'] += 1
            else:
                by_comp[comp]['losses'] += 1

        # Calculer le taux de réussite
        for comp in by_comp:
            total = by_comp[comp]['total']
            wins = by_comp[comp]['wins']
            by_comp[comp]['win_rate'] = (wins / total * 100) if total > 0 else 0

        return by_comp


if __name__ == "__main__":
    # Test
    tracker = PerformanceTracker()
    stats = tracker.calculate_statistics()
    print(json.dumps(stats, indent=2))
