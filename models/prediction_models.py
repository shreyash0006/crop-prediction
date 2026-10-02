import joblib
import numpy as np
import os
from models.crop_recommender import CropRecommender

class PredictionModels:
    def __init__(self):
        self.models_dir = 'models/'
        self.yield_model = None
        self.disease_model = None
        self.weather_model = None
        self.fertilizer_recommender = None
        self.crop_recommender = CropRecommender()  # Use new recommender
        self.load_models()
    
    def load_models(self):
        """Load all trained models"""
        try:
            if os.path.exists(f'{self.models_dir}yield_prediction_model.pkl'):
                self.yield_model = joblib.load(f'{self.models_dir}yield_prediction_model.pkl')
                self.yield_scaler = joblib.load(f'{self.models_dir}yield_scaler.pkl')
            
            if os.path.exists(f'{self.models_dir}disease_prediction_model.pkl'):
                self.disease_model = joblib.load(f'{self.models_dir}disease_prediction_model.pkl')
                self.disease_scaler = joblib.load(f'{self.models_dir}disease_scaler.pkl')
                self.disease_encoder = joblib.load(f'{self.models_dir}disease_encoder.pkl')
            
            if os.path.exists(f'{self.models_dir}weather_model.pkl'):
                self.weather_model = joblib.load(f'{self.models_dir}weather_model.pkl')
                
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def predict_yield(self, rainfall, pesticide, temperature):
        """Predict crop yield"""
        if self.yield_model and self.yield_scaler:
            try:
                input_data = np.array([[rainfall, pesticide, temperature]])
                input_scaled = self.yield_scaler.transform(input_data)
                prediction = self.yield_model.predict(input_scaled)[0]
                return round(prediction, 2)
            except:
                return None
        return None
    
    def predict_disease_risk(self, rainfall, temperature, pesticide):
        """Predict disease risk"""
        if self.disease_model and self.disease_scaler and self.disease_encoder:
            try:
                input_data = np.array([[rainfall, temperature, pesticide]])
                input_scaled = self.disease_scaler.transform(input_data)
                prediction = self.disease_model.predict(input_scaled)[0]
                risk_level = self.disease_encoder.inverse_transform([prediction])[0]
                return risk_level
            except:
                return None
        return None
    
    def recommend_crops(self, rainfall, temperature, humidity, soil_type, ph_level,
                       season, farm_size, water_availability, experience_level,
                       market_preference, region='general'):
        """Get crop recommendations using the new engine"""
        return self.crop_recommender.recommend_crops(
            rainfall, temperature, humidity, soil_type, ph_level, season,
            farm_size, water_availability, experience_level, market_preference, region
        )
    
    def predict_weather(self, year):
        """Predict weather patterns"""
        if self.weather_model:
            try:
                prediction = self.weather_model.predict(np.array([[year]]))[0]
                return round(prediction, 1)
            except:
                return None
        return None
