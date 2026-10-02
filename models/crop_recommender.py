"""
Advanced Crop Recommender Engine
Uses intelligent scoring based on agronomic requirements and environmental conditions.
"""

import json
from typing import Dict, List, Tuple, Any

class CropRecommender:
    """
    Intelligent crop recommendation engine based on agronomic science.
    Provides recommendations tailored to specific environmental and economic conditions.
    """

    def __init__(self):
        self.crop_profiles = self._initialize_crop_profiles()
        self.region_preferences = self._initialize_region_preferences()

    def _initialize_crop_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Detailed crop requirement profiles based on agronomic science.
        Each crop has strict ranges and penalty calculations for deviations.
        """
        return {
            'Rice': {
                'rainfall': {'optimal': (1200, 1500), 'acceptable': (1000, 2000), 'threshold': 800},
                'temperature': {'optimal': (24, 28), 'acceptable': (20, 32), 'threshold': 15},
                'humidity': {'optimal': (80, 95), 'acceptable': (70, 100), 'threshold': 60},
                'soil_types': {'clay': 0.95, 'loamy': 0.85, 'alluvial': 0.99, 'black': 0.70, 'sandy': 0.40, 'red': 0.60},
                'ph_range': {'optimal': (6.0, 6.8), 'acceptable': (5.5, 7.0)},
                'seasons': {'kharif': 0.95, 'rabi': 0.60, 'summer': 0.30},
                'water_need': 'high',
                'base_yield': 5000,
                'capital_investment': 35000,
                'market_type': 'staple',
                'minimum_rainfall': 800,
                'min_area': 0.2,
            },
            'Wheat': {
                'rainfall': {'optimal': (400, 600), 'acceptable': (300, 1000), 'threshold': 250},
                'temperature': {'optimal': (15, 22), 'acceptable': (13, 25), 'threshold': 10},
                'humidity': {'optimal': (45, 65), 'acceptable': (40, 75), 'threshold': 35},
                'soil_types': {'loamy': 0.95, 'clay': 0.90, 'black': 0.85, 'alluvial': 0.75, 'red': 0.60, 'sandy': 0.45},
                'ph_range': {'optimal': (6.5, 7.5), 'acceptable': (6.0, 8.0)},
                'seasons': {'rabi': 0.95, 'kharif': 0.20},
                'water_need': 'medium',
                'base_yield': 3500,
                'capital_investment': 28000,
                'market_type': 'staple',
                'minimum_rainfall': 250,
                'min_area': 0.5,
            },
            'Maize': {
                'rainfall': {'optimal': (600, 1000), 'acceptable': (500, 1200), 'threshold': 400},
                'temperature': {'optimal': (21, 27), 'acceptable': (18, 32), 'threshold': 15},
                'humidity': {'optimal': (65, 80), 'acceptable': (60, 85), 'threshold': 50},
                'soil_types': {'loamy': 0.95, 'sandy': 0.80, 'red': 0.85, 'black': 0.70, 'clay': 0.65, 'alluvial': 0.80},
                'ph_range': {'optimal': (6.0, 7.0), 'acceptable': (5.5, 7.5)},
                'seasons': {'kharif': 0.90, 'rabi': 0.70, 'zaid': 0.60},
                'water_need': 'medium',
                'base_yield': 5500,
                'capital_investment': 22000,
                'market_type': 'staple',
                'minimum_rainfall': 400,
                'min_area': 0.25,
            },
            'Millets': {
                'rainfall': {'optimal': (300, 600), 'acceptable': (250, 800), 'threshold': 200},
                'temperature': {'optimal': (25, 35), 'acceptable': (20, 40), 'threshold': 18},
                'humidity': {'optimal': (50, 70), 'acceptable': (40, 80), 'threshold': 35},
                'soil_types': {'sandy': 0.95, 'red': 0.90, 'black': 0.60, 'loamy': 0.70, 'clay': 0.45, 'alluvial': 0.50},
                'ph_range': {'optimal': (6.0, 8.0), 'acceptable': (5.5, 8.5)},
                'seasons': {'kharif': 0.95, 'rabi': 0.50},
                'water_need': 'low',
                'base_yield': 1800,
                'capital_investment': 10000,
                'market_type': 'specialty_grain',
                'minimum_rainfall': 200,
                'min_area': 0.1,
            },
            'Cotton': {
                'rainfall': {'optimal': (700, 1100), 'acceptable': (500, 1500), 'threshold': 400},
                'temperature': {'optimal': (22, 30), 'acceptable': (20, 35), 'threshold': 15},
                'humidity': {'optimal': (60, 80), 'acceptable': (50, 85), 'threshold': 40},
                'soil_types': {'black': 0.95, 'alluvial': 0.90, 'red': 0.85, 'loamy': 0.75, 'clay': 0.70, 'sandy': 0.50},
                'ph_range': {'optimal': (6.0, 8.0), 'acceptable': (5.5, 8.5)},
                'seasons': {'kharif': 0.95, 'rabi': 0.30},
                'water_need': 'high',
                'base_yield': 2000,
                'capital_investment': 45000,
                'market_type': 'cash_crop',
                'minimum_rainfall': 400,
                'min_area': 0.5,
            },
            'Sugarcane': {
                'rainfall': {'optimal': (1200, 1800), 'acceptable': (1000, 2500), 'threshold': 900},
                'temperature': {'optimal': (20, 30), 'acceptable': (18, 35), 'threshold': 15},
                'humidity': {'optimal': (75, 90), 'acceptable': (70, 95), 'threshold': 60},
                'soil_types': {'loamy': 0.95, 'clay': 0.90, 'alluvial': 0.95, 'black': 0.85, 'red': 0.70, 'sandy': 0.50},
                'ph_range': {'optimal': (6.0, 8.5), 'acceptable': (5.5, 9.0)},
                'seasons': {'annual': 0.95},
                'water_need': 'very_high',
                'base_yield': 75000,
                'capital_investment': 120000,
                'market_type': 'cash_crop',
                'minimum_rainfall': 900,
                'min_area': 1.0,
            },
            'Soybeans': {
                'rainfall': {'optimal': (450, 700), 'acceptable': (400, 800), 'threshold': 350},
                'temperature': {'optimal': (22, 28), 'acceptable': (20, 30), 'threshold': 18},
                'humidity': {'optimal': (60, 75), 'acceptable': (50, 80), 'threshold': 45},
                'soil_types': {'loamy': 0.95, 'black': 0.90, 'red': 0.85, 'clay': 0.75, 'alluvial': 0.70, 'sandy': 0.55},
                'ph_range': {'optimal': (6.0, 7.5), 'acceptable': (5.5, 8.0)},
                'seasons': {'kharif': 0.95, 'summer': 0.60},
                'water_need': 'medium',
                'base_yield': 2800,
                'capital_investment': 16000,
                'market_type': 'oilseed',
                'minimum_rainfall': 350,
                'min_area': 0.2,
            },
            'Groundnut': {
                'rainfall': {'optimal': (500, 800), 'acceptable': (400, 1000), 'threshold': 300},
                'temperature': {'optimal': (25, 30), 'acceptable': (22, 32), 'threshold': 20},
                'humidity': {'optimal': (60, 80), 'acceptable': (50, 85), 'threshold': 40},
                'soil_types': {'sandy': 0.95, 'red': 0.90, 'loamy': 0.85, 'black': 0.60, 'clay': 0.50, 'alluvial': 0.70},
                'ph_range': {'optimal': (5.8, 7.0), 'acceptable': (5.5, 7.5)},
                'seasons': {'kharif': 0.95, 'rabi': 0.70},
                'water_need': 'medium',
                'base_yield': 2200,
                'capital_investment': 18000,
                'market_type': 'oilseed',
                'minimum_rainfall': 300,
                'min_area': 0.2,
            },
            'Chickpea': {
                'rainfall': {'optimal': (300, 500), 'acceptable': (250, 700), 'threshold': 200},
                'temperature': {'optimal': (15, 22), 'acceptable': (10, 25), 'threshold': 8},
                'humidity': {'optimal': (45, 60), 'acceptable': (40, 70), 'threshold': 35},
                'soil_types': {'loamy': 0.95, 'black': 0.90, 'clay': 0.85, 'red': 0.75, 'alluvial': 0.80, 'sandy': 0.50},
                'ph_range': {'optimal': (6.0, 8.0), 'acceptable': (5.8, 8.5)},
                'seasons': {'rabi': 0.95, 'summer': 0.40},
                'water_need': 'low',
                'base_yield': 2000,
                'capital_investment': 12000,
                'market_type': 'pulse',
                'minimum_rainfall': 200,
                'min_area': 0.1,
            },
            'Potato': {
                'rainfall': {'optimal': (450, 650), 'acceptable': (400, 750), 'threshold': 350},
                'temperature': {'optimal': (15, 22), 'acceptable': (13, 24), 'threshold': 10},
                'humidity': {'optimal': (60, 80), 'acceptable': (55, 85), 'threshold': 50},
                'soil_types': {'loamy': 0.95, 'sandy': 0.90, 'red': 0.85, 'alluvial': 0.80, 'black': 0.70, 'clay': 0.60},
                'ph_range': {'optimal': (5.5, 6.8), 'acceptable': (5.0, 7.5)},
                'seasons': {'rabi': 0.95, 'winter': 0.90},
                'water_need': 'medium',
                'base_yield': 20000,
                'capital_investment': 38000,
                'market_type': 'vegetable',
                'minimum_rainfall': 350,
                'min_area': 0.1,
            },
            'Tomato': {
                'rainfall': {'optimal': (500, 800), 'acceptable': (400, 900), 'threshold': 300},
                'temperature': {'optimal': (20, 28), 'acceptable': (18, 30), 'threshold': 15},
                'humidity': {'optimal': (65, 80), 'acceptable': (60, 85), 'threshold': 50},
                'soil_types': {'loamy': 0.95, 'sandy': 0.90, 'red': 0.85, 'alluvial': 0.80, 'black': 0.65, 'clay': 0.60},
                'ph_range': {'optimal': (6.0, 7.0), 'acceptable': (5.8, 7.5)},
                'seasons': {'rabi': 0.95, 'summer': 0.70},
                'water_need': 'high',
                'base_yield': 35000,
                'capital_investment': 55000,
                'market_type': 'vegetable',
                'minimum_rainfall': 300,
                'min_area': 0.1,
            },
            'Onion': {
                'rainfall': {'optimal': (350, 550), 'acceptable': (300, 650), 'threshold': 250},
                'temperature': {'optimal': (15, 25), 'acceptable': (12, 27), 'threshold': 10},
                'humidity': {'optimal': (55, 70), 'acceptable': (50, 75), 'threshold': 40},
                'soil_types': {'loamy': 0.95, 'sandy': 0.90, 'alluvial': 0.90, 'red': 0.75, 'black': 0.70, 'clay': 0.65},
                'ph_range': {'optimal': (6.0, 7.0), 'acceptable': (5.8, 7.5)},
                'seasons': {'rabi': 0.95, 'summer': 0.60},
                'water_need': 'medium',
                'base_yield': 30000,
                'capital_investment': 28000,
                'market_type': 'vegetable',
                'minimum_rainfall': 250,
                'min_area': 0.05,
            },
            'Chili': {
                'rainfall': {'optimal': (750, 1200), 'acceptable': (600, 1500), 'threshold': 500},
                'temperature': {'optimal': (22, 28), 'acceptable': (20, 30), 'threshold': 18},
                'humidity': {'optimal': (70, 85), 'acceptable': (65, 90), 'threshold': 55},
                'soil_types': {'loamy': 0.95, 'sandy': 0.85, 'red': 0.90, 'alluvial': 0.80, 'black': 0.70, 'clay': 0.65},
                'ph_range': {'optimal': (6.0, 7.0), 'acceptable': (5.8, 7.5)},
                'seasons': {'kharif': 0.95, 'rabi': 0.80},
                'water_need': 'high',
                'base_yield': 3500,
                'capital_investment': 30000,
                'market_type': 'spice_cash_crop',
                'minimum_rainfall': 500,
                'min_area': 0.1,
            },
            'Sunflower': {
                'rainfall': {'optimal': (500, 800), 'acceptable': (400, 900), 'threshold': 350},
                'temperature': {'optimal': (22, 28), 'acceptable': (20, 32), 'threshold': 18},
                'humidity': {'optimal': (60, 75), 'acceptable': (50, 80), 'threshold': 45},
                'soil_types': {'loamy': 0.95, 'sandy': 0.90, 'red': 0.85, 'black': 0.70, 'clay': 0.65, 'alluvial': 0.75},
                'ph_range': {'optimal': (6.0, 7.5), 'acceptable': (5.8, 8.0)},
                'seasons': {'kharif': 0.90, 'rabi': 0.80},
                'water_need': 'medium',
                'base_yield': 1900,
                'capital_investment': 13000,
                'market_type': 'oilseed',
                'minimum_rainfall': 350,
                'min_area': 0.2,
            },
        }

    def _initialize_region_preferences(self) -> Dict[str, List[str]]:
        """Region-specific crop preferences based on local markets and climate."""
        return {
            'punjab': ['Wheat', 'Rice', 'Cotton', 'Maize'],
            'maharashtra': ['Cotton', 'Sugarcane', 'Chili', 'Tomato'],
            'karnataka': ['Sugarcane', 'Millets', 'Chickpea', 'Sunflower'],
            'madhya_pradesh': ['Wheat', 'Maize', 'Soybeans', 'Chickpea'],
            'uttar_pradesh': ['Rice', 'Wheat', 'Sugarcane', 'Potato'],
            'maharashtra': ['Cotton', 'Sugarcane', 'Tomato', 'Onion'],
            'tamil_nadu': ['Rice', 'Sugarcane', 'Coconut', 'Groundnut'],
            'andhra_pradesh': ['Rice', 'Sugarcane', 'Groundnut', 'Cotton'],
            'telangana': ['Rice', 'Cotton', 'Millets', 'Groundnut'],
            'rajasthan': ['Wheat', 'Millets', 'Groundnut', 'Mustard'],
            'gujarath': ['Cotton', 'Groundnut', 'Millets', 'Sunflower'],
        }

    def recommend_crops(self, rainfall: float, temperature: float, humidity: float,
                       soil_type: str, ph_level: float, season: str,
                       farm_size: float, water_availability: str,
                       experience_level: str, market_preference: str,
                       region: str = 'general') -> List[Dict[str, Any]]:
        """
        Generate crop recommendations based on comprehensive agronomic scoring.
        
        Args:
            rainfall: Annual rainfall in mm
            temperature: Average temperature in °C
            humidity: Relative humidity in %
            soil_type: Type of soil (loamy, clay, sandy, red, black, alluvial)
            ph_level: Soil pH
            season: Growing season (kharif, rabi, zaid, summer, annual)
            farm_size: Farm size in hectares
            water_availability: Water availability level (low, medium, high, very_high)
            experience_level: Farmer experience (beginner, intermediate, advanced)
            market_preference: Market type preference (staple, cash_crop, vegetable, spice, oilseed)
            region: Geographic region for local preference weighting
        
        Returns:
            List of recommended crops with detailed scoring and analysis
        """
        recommendations = []
        region_preferred = self.region_preferences.get(region.lower(), [])

        for crop_name, profile in self.crop_profiles.items():
            # Skip crops with insufficient farm size
            if farm_size < profile.get('min_area', 0.1):
                continue

            # Check minimum rainfall threshold
            if rainfall < profile.get('minimum_rainfall', 0) * 0.8:
                continue

            score, details = self._calculate_crop_score(
                crop_name, profile, rainfall, temperature, humidity,
                soil_type, ph_level, season, water_availability,
                experience_level, market_preference, region_preferred
            )

            if score > 0:
                recommendations.append({
                    'crop_name': crop_name,
                    'suitability_score': round(score, 1),
                    'details': details,
                    'estimated_yield': self._estimate_yield(crop_name, profile, score),
                    'capital_investment': profile['capital_investment'],
                    'market_type': profile['market_type'],
                    'min_rainfall': profile['minimum_rainfall'],
                    'water_requirement': profile['water_need'],
                })

        # Sort by score
        recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
        return recommendations[:10]  # Return top 10

    def _calculate_crop_score(self, crop_name: str, profile: Dict, rainfall: float,
                             temperature: float, humidity: float, soil_type: str,
                             ph_level: float, season: str, water_availability: str,
                             experience_level: str, market_preference: str,
                             region_preferred: List[str]) -> Tuple[float, List[str]]:
        """
        Calculate comprehensive suitability score for a crop.
        Uses weighted scoring with heavy penalties for critical mismatches.
        """
        score = 0.0
        max_score = 100.0
        details = []
        weights = {
            'rainfall': 0.25,
            'temperature': 0.20,
            'soil': 0.15,
            'humidity': 0.12,
            'ph': 0.10,
            'season': 0.10,
            'water': 0.05,
            'market': 0.03,
        }

        # RAINFALL SCORE (Most Critical)
        rainfall_score = self._score_rainfall(rainfall, profile, details)
        score += rainfall_score * weights['rainfall'] * 100

        # TEMPERATURE SCORE
        temp_score = self._score_temperature(temperature, profile, details)
        score += temp_score * weights['temperature'] * 100

        # SOIL SCORE
        soil_score = self._score_soil(soil_type, profile, details)
        score += soil_score * weights['soil'] * 100

        # HUMIDITY SCORE
        humidity_score = self._score_humidity(humidity, profile, details)
        score += humidity_score * weights['humidity'] * 100

        # pH SCORE
        ph_score = self._score_ph(ph_level, profile, details)
        score += ph_score * weights['ph'] * 100

        # SEASON SCORE
        season_score = self._score_season(season, profile, details)
        score += season_score * weights['season'] * 100

        # WATER AVAILABILITY SCORE
        water_score = self._score_water(water_availability, profile, details)
        score += water_score * weights['water'] * 100

        # MARKET PREFERENCE SCORE
        market_score = self._score_market(market_preference, profile, details)
        score += market_score * weights['market'] * 100

        # REGIONAL PREFERENCE BONUS
        if crop_name in region_preferred:
            score += 3
            details.append(f"Regional preference: {crop_name} is well-suited to your area")

        # Normalize final score
        final_score = min(100.0, max(0.0, score))
        return final_score, details

    def _score_rainfall(self, rainfall: float, profile: Dict, details: List[str]) -> float:
        optimal_min, optimal_max = profile['rainfall']['optimal']
        acceptable_min, acceptable_max = profile['rainfall']['acceptable']

        if optimal_min <= rainfall <= optimal_max:
            details.append(f"Rainfall is optimal ({optimal_min}-{optimal_max} mm)")
            return 1.0
        elif acceptable_min <= rainfall <= acceptable_max:
            deviation = min(optimal_min - rainfall, rainfall - optimal_max)
            penalty = abs(deviation) / max(abs(optimal_min - acceptable_min), abs(acceptable_max - optimal_max))
            score = 1.0 - (penalty * 0.3)
            details.append(f"Rainfall is acceptable but not optimal ({rainfall} mm vs {optimal_min}-{optimal_max} mm optimal)")
            return score
        else:
            # Outside acceptable range - heavy penalty
            if rainfall < acceptable_min:
                deficit = acceptable_min - rainfall
                penalty = min(1.0, deficit / acceptable_min)
            else:
                excess = rainfall - acceptable_max
                penalty = min(1.0, excess / acceptable_max)
            score = max(0.0, 1.0 - (penalty * 0.8))
            details.append(f"Rainfall ({rainfall} mm) is outside acceptable range ({acceptable_min}-{acceptable_max} mm)")
            return score

    def _score_temperature(self, temperature: float, profile: Dict, details: List[str]) -> float:
        optimal_min, optimal_max = profile['temperature']['optimal']
        acceptable_min, acceptable_max = profile['temperature']['acceptable']

        if optimal_min <= temperature <= optimal_max:
            details.append(f"Temperature is optimal ({optimal_min}-{optimal_max}°C)")
            return 1.0
        elif acceptable_min <= temperature <= acceptable_max:
            deviation = min(optimal_min - temperature, temperature - optimal_max)
            penalty = abs(deviation) / max(abs(optimal_min - acceptable_min), abs(acceptable_max - optimal_max))
            score = 1.0 - (penalty * 0.35)
            details.append(f"Temperature is acceptable but not optimal ({temperature}°C vs {optimal_min}-{optimal_max}°C optimal)")
            return score
        else:
            if temperature < acceptable_min:
                deficit = acceptable_min - temperature
                penalty = min(1.0, deficit / (acceptable_min - 0))
            else:
                excess = temperature - acceptable_max
                penalty = min(1.0, excess / (50 - acceptable_max))
            score = max(0.1, 1.0 - (penalty * 0.75))
            details.append(f"Temperature ({temperature}°C) is marginal for this crop")
            return score

    def _score_soil(self, soil_type: str, profile: Dict, details: List[str]) -> float:
        soil_type = soil_type.lower()
        soil_weights = profile['soil_types']
        
        if soil_type in soil_weights:
            score = soil_weights[soil_type]
            best_soil = max(soil_weights, key=soil_weights.get)
            if soil_type == best_soil:
                details.append(f"Soil type ({soil_type}) is ideal for this crop")
            else:
                details.append(f"Soil type ({soil_type}) is suitable; {best_soil} would be better")
            return score
        else:
            # Unknown soil type - use average
            avg_score = sum(soil_weights.values()) / len(soil_weights)
            details.append(f"Soil type is moderately suitable (exact compatibility unknown)")
            return avg_score * 0.7

    def _score_humidity(self, humidity: float, profile: Dict, details: List[str]) -> float:
        optimal_min, optimal_max = profile['humidity']['optimal']
        acceptable_min, acceptable_max = profile['humidity']['acceptable']

        if optimal_min <= humidity <= optimal_max:
            details.append(f"Humidity is optimal ({optimal_min}-{optimal_max}%)")
            return 1.0
        elif acceptable_min <= humidity <= acceptable_max:
            score = 0.85
            details.append(f"Humidity is acceptable ({humidity}%)")
            return score
        else:
            score = 0.5
            details.append(f"Humidity ({humidity}%) is marginal")
            return score

    def _score_ph(self, ph_level: float, profile: Dict, details: List[str]) -> float:
        optimal_min, optimal_max = profile['ph_range']['optimal']
        acceptable_min, acceptable_max = profile['ph_range']['acceptable']

        if optimal_min <= ph_level <= optimal_max:
            details.append(f"Soil pH ({ph_level}) is optimal")
            return 1.0
        elif acceptable_min <= ph_level <= acceptable_max:
            score = 0.80
            details.append(f"Soil pH ({ph_level}) is acceptable; consider adjustment")
            return score
        else:
            score = 0.4
            details.append(f"Soil pH ({ph_level}) requires amendment")
            return score

    def _score_season(self, season: str, profile: Dict, details: List[str]) -> float:
        seasons = profile['seasons']
        season_lower = season.lower()
        
        if season_lower in seasons:
            score = seasons[season_lower]
            details.append(f"Season ({season}) is suitable for this crop")
            return score
        else:
            avg_season_score = sum(seasons.values()) / len(seasons)
            details.append(f"Season may be suboptimal")
            return avg_season_score * 0.6

    def _score_water(self, water_availability: str, profile: Dict, details: List[str]) -> float:
        water_need = profile['water_need'].lower()
        water_avail = water_availability.lower()
        
        compatibility_matrix = {
            'low': {'low': 1.0, 'medium': 0.6, 'high': 0.2, 'very_high': 0.1},
            'medium': {'low': 0.8, 'medium': 1.0, 'high': 0.9, 'very_high': 0.7},
            'high': {'low': 0.3, 'medium': 0.8, 'high': 1.0, 'very_high': 0.95},
            'very_high': {'low': 0.1, 'medium': 0.6, 'high': 0.95, 'very_high': 1.0},
        }
        
        score = compatibility_matrix.get(water_need, {}).get(water_avail, 0.5)
        details.append(f"Water availability ({water_avail}) is compatible with crop needs")
        return score

    def _score_market(self, market_preference: str, profile: Dict, details: List[str]) -> float:
        market_pref = market_preference.lower()
        crop_market = profile['market_type'].lower()
        
        if market_pref == 'mixed' or market_pref == 'all':
            return 1.0
        elif market_pref in crop_market or crop_market in market_pref:
            return 1.0
        else:
            return 0.5

    def _estimate_yield(self, crop_name: str, profile: Dict, score: float) -> Dict[str, Any]:
        """Estimate yield based on suitability score."""
        base_yield = profile['base_yield']
        factor = (score / 100.0) * 1.1  # Allow up to 110% under perfect conditions
        estimated_yield = round(base_yield * factor, 0)
        return {'per_hectare': estimated_yield, 'unit': 'kg'}
