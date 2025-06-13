import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from distance_calculator import calculate_distance
import pandas as pd

def map_preference_to_value(pref):
    pref_map = {'Low': 0.33, 'Medium': 0.66, 'High': 1.0}
    return pref_map.get(pref, 0.33)  # Default to Low if invalid

def compute_service_match(user_service, hospital_services):
    if pd.isna(hospital_services) or pd.isna(user_service):
        return 0.0
    user_service = user_service.lower().strip()
    hospital_services = hospital_services.lower().strip()
    if user_service in hospital_services:
        return 1.0
    elif any(word in hospital_services for word in user_service.split()):
        return 0.5
    return 0.0

def map_cost_rating(cost_rating):
    if pd.isna(cost_rating):
        return 1.0
    cost_map = {'Low': 1.0, 'Medium': 2.0, 'High': 3.0, 'Premium': 3.0}
    return cost_map.get(cost_rating.strip().capitalize(), 1.0)

def setup_fuzzy_system():
    cost = ctrl.Antecedent(np.arange(1, 3.1, 0.1), 'cost')
    quality = ctrl.Antecedent(np.arange(3, 5.1, 0.1), 'quality')
    user_rating = ctrl.Antecedent(np.arange(1, 5.1, 0.1), 'user_rating')
    service_match = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'service_match')
    user_cost_pref = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'user_cost_pref')
    user_quality_pref = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'user_quality_pref')
    proximity = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'proximity')
    recommendation = ctrl.Consequent(np.arange(0, 1.1, 0.1), 'recommendation')

    cost['low'] = fuzz.trapmf(cost.universe, [1, 1, 1.2, 1.8])
    cost['medium'] = fuzz.trapmf(cost.universe, [1.2, 1.8, 2.2, 2.8])
    cost['high'] = fuzz.trapmf(cost.universe, [2.2, 2.8, 3, 3])

    quality['low'] = fuzz.trapmf(quality.universe, [3, 3, 3.4, 3.8])
    quality['medium'] = fuzz.trapmf(quality.universe, [3.4, 3.8, 4.2, 4.6])
    quality['high'] = fuzz.trapmf(quality.universe, [4.2, 4.6, 5, 5])

    user_rating['low'] = fuzz.trapmf(user_rating.universe, [1, 1, 2, 3])
    user_rating['medium'] = fuzz.trapmf(user_rating.universe, [2, 3, 3.5, 4])
    user_rating['high'] = fuzz.trapmf(user_rating.universe, [3.5, 4, 5, 5])

    service_match['low'] = fuzz.trapmf(service_match.universe, [0, 0, 0.3, 0.6])
    service_match['high'] = fuzz.trapmf(service_match.universe, [0.4, 0.7, 1, 1])

    user_cost_pref['low'] = fuzz.trapmf(user_cost_pref.universe, [0, 0, 0.2, 0.4])
    user_cost_pref['medium'] = fuzz.trapmf(user_cost_pref.universe, [0.3, 0.5, 0.7, 0.9])
    user_cost_pref['high'] = fuzz.trapmf(user_cost_pref.universe, [0.6, 0.8, 1, 1])

    user_quality_pref['low'] = fuzz.trapmf(user_quality_pref.universe, [0, 0, 0.2, 0.4])
    user_quality_pref['medium'] = fuzz.trapmf(user_quality_pref.universe, [0.3, 0.5, 0.7, 0.9])
    user_quality_pref['high'] = fuzz.trapmf(user_quality_pref.universe, [0.6, 0.8, 1, 1])

    proximity['far'] = fuzz.trapmf(proximity.universe, [0, 0, 0.2, 0.4])
    proximity['medium'] = fuzz.trapmf(proximity.universe, [0.3, 0.4, 0.6, 0.7])
    proximity['near'] = fuzz.trapmf(proximity.universe, [0.6, 0.7, 0.9, 1])
    proximity['very_near'] = fuzz.trapmf(proximity.universe, [0.8, 0.9, 1, 1])

    recommendation['low'] = fuzz.trapmf(recommendation.universe, [0, 0, 0.3, 0.5])
    recommendation['medium'] = fuzz.trapmf(recommendation.universe, [0.4, 0.5, 0.6, 0.7])
    recommendation['high'] = fuzz.trapmf(recommendation.universe, [0.6, 0.7, 1, 1])

    rules = [
        ctrl.Rule(
            service_match['high'] & proximity['very_near'] & quality['high'] & user_rating['high'] &
            ((cost['low'] & user_cost_pref['low']) | (cost['medium'] & user_cost_pref['medium']) | (cost['high'] & user_cost_pref['high'])) &
            user_quality_pref['high'],
            recommendation['high']
        ),
        ctrl.Rule(
            service_match['high'] & proximity['near'] & quality['high'] & user_rating['medium'] &
            ((cost['low'] & user_cost_pref['low']) | (cost['medium'] & user_cost_pref['medium'])) &
            user_quality_pref['high'],
            recommendation['high']
        ),
        ctrl.Rule(
            service_match['high'] & proximity['medium'] & (quality['medium'] | quality['high']) & user_rating['medium'] &
            ((cost['low'] & user_cost_pref['low']) | (cost['medium'] & user_cost_pref['medium'])),
            recommendation['medium']
        ),
        ctrl.Rule(
            service_match['high'] & proximity['near'] & quality['medium'] & user_rating['medium'] &
            user_quality_pref['medium'],
            recommendation['medium']
        ),
        ctrl.Rule(
            service_match['low'] | proximity['far'] | (quality['low'] & user_quality_pref['high']),
            recommendation['low']
        ),
        ctrl.Rule(
            (cost['high'] & user_cost_pref['low']) | (cost['medium'] & user_cost_pref['low']),
            recommendation['low']
        ),
        ctrl.Rule(
            service_match['high'] & proximity['very_near'] & quality['medium'] & user_rating['high'] &
            user_quality_pref['medium'] & (cost['low'] | cost['medium']),
            recommendation['high']
        ),
        ctrl.Rule(
            service_match['low'] & proximity['very_near'] & quality['high'] & user_rating['high'] &
            user_quality_pref['high'] & cost['low'] & user_cost_pref['low'],
            recommendation['medium']
        )
    ]

    hospital_ctrl = ctrl.ControlSystem(rules)
    return ctrl.ControlSystemSimulation(hospital_ctrl)

def compute_recommendation_score(row, user_service, user_cost_pref, user_quality_pref, user_coords, fuzzy_system):
    try:
        service_score = compute_service_match(user_service, row['Services'])
        cost_value = map_cost_rating(row['Cost Level'])
        quality_value = float(row['Quality Score']) if pd.notna(row['Quality Score']) else 3.1
        user_rating_value = float(row['User Rating']) if pd.notna(row['User Rating']) else 3.0
        proximity_score, _ = calculate_distance(user_coords, row.get('Coordinates'))

        fuzzy_system.input['cost'] = cost_value
        fuzzy_system.input['quality'] = quality_value
        fuzzy_system.input['user_rating'] = user_rating_value
        fuzzy_system.input['service_match'] = service_score
        fuzzy_system.input['user_cost_pref'] = user_cost_pref
        fuzzy_system.input['user_quality_pref'] = user_quality_pref
        fuzzy_system.input['proximity'] = proximity_score

        fuzzy_system.compute()
        return fuzzy_system.output.get('recommendation', 0.0)
    except Exception as e:
        print(f"Error processing {row['Name']}: {e}")
        return 0.0