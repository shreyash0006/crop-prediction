from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import joblib
import numpy as np
import os
import json
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from models.prediction_models import PredictionModels
from database import (
    init_db, get_user_by_email, get_user_by_id, create_user,
    save_prediction, get_user_predictions, save_forum_post, get_forum_posts,
    get_user_forum_posts, save_marketplace_listing, get_marketplace_listings,
    get_user_listings, get_all_users, get_user_stats, delete_user,
    get_recent_predictions, delete_forum_post, delete_marketplace_listing
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'agri-predict-local-secret')
app.config['JSON_SORT_KEYS'] = False

# Initialize database
init_db()

# Initialize prediction models
try:
    prediction_models = PredictionModels()
    models_loaded = True
except Exception as e:
    print(f"Error loading models: {e}")
    models_loaded = False


# --- Auth Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page.', 'danger')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def normalize_crop_name(crop):
    if not crop:
        return 'Maize'
    crop_name = str(crop).strip().lower().replace('_', ' ')
    crop_name = crop_name.replace(' paddy', '').replace(',', '').replace('(', '').replace(')', '')
    return crop_name.title()


# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')

        if role not in ('farmer', 'user'):
            role = 'user'

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        success = create_user(username, email, password_hash, role, full_name, phone, location)
        if success:
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        flash('Username or email already exists.', 'danger')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# --- Dashboard Routes ---
@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'farmer':
        return redirect(url_for('farmer_dashboard_view'))
    return redirect(url_for('user_dashboard_view'))


@app.route('/admin')
@role_required('admin')
def admin_dashboard():
    stats = get_user_stats()
    users = get_all_users()
    recent_preds = get_recent_predictions(10)
    forum = get_forum_posts(20)
    listings = get_marketplace_listings(20)
    return render_template('admin_dashboard.html',
                           stats=stats, users=users,
                           recent_predictions=recent_preds,
                           forum_posts=forum,
                           marketplace_listings=listings)


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@role_required('admin')
def admin_delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('Cannot delete your own account.', 'danger')
    else:
        delete_user(user_id)
        flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete-post/<int:post_id>', methods=['POST'])
@role_required('admin')
def admin_delete_post(post_id):
    delete_forum_post(post_id)
    flash('Post deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete-listing/<int:listing_id>', methods=['POST'])
@role_required('admin')
def admin_delete_listing(listing_id):
    delete_marketplace_listing(listing_id)
    flash('Listing deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/farmer-dashboard')
@role_required('farmer')
def farmer_dashboard_view():
    uid = session['user_id']
    predictions = get_user_predictions(uid)
    listings = get_user_listings(uid)
    forum_posts = get_user_forum_posts(uid)
    return render_template('farmer_dashboard.html',
                           predictions=predictions,
                           listings=listings,
                           forum_posts=forum_posts)


@app.route('/user-dashboard')
@role_required('user')
def user_dashboard_view():
    uid = session['user_id']
    predictions = get_user_predictions(uid)
    return render_template('user_dashboard.html', predictions=predictions)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/yield-prediction')
def yield_prediction():
    return render_template('yield_prediction.html')


@app.route('/disease-prediction')
def disease_prediction():
    return render_template('disease_prediction.html')


@app.route('/fertilizer-recommendation')
def fertilizer_recommendation():
    return render_template('fertilizer_recommendation.html')


@app.route('/weather-prediction')
def weather_prediction():
    return render_template('weather_prediction.html')


# API Routes for predictions
@app.route('/api/predict-yield', methods=['POST'])
def api_predict_yield():
    try:
        data = request.get_json(silent=True) or {}
        rainfall = safe_float(data.get('rainfall'), 800)
        pesticide = safe_float(data.get('pesticide'), 120)
        temperature = safe_float(data.get('temperature'), 25)
        crop = data.get('crop', 'Maize')

        if models_loaded and prediction_models.yield_model is not None:
            yield_pred = prediction_models.predict_yield(rainfall, pesticide, temperature)
            if yield_pred is None:
                yield_pred = round((rainfall * 0.12) + (temperature * 8) - (pesticide * 0.06), 2)
        else:
            rain_factor = min(max(rainfall / 1000, 0.45), 1.6)
            pest_factor = min(max(pesticide / 200, 0.5), 1.25)
            temp_factor = max(0.55, 1 - abs(temperature - 25) / 25)
            yield_pred = round(30000 * rain_factor * pest_factor * temp_factor, 2)

        message = f'Predicted yield for {crop}: {yield_pred} hg/ha'

        if session.get('user_id'):
            save_prediction(
                session['user_id'], 'Yield Prediction',
                json.dumps({'rainfall': rainfall, 'pesticide': pesticide, 'temperature': temperature, 'crop': crop}),
                message
            )

        return jsonify({'success': True, 'prediction': yield_pred, 'crop': crop, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/predict-disease', methods=['POST'])
def api_predict_disease():
    try:
        data = request.get_json(silent=True) or {}
        rainfall = safe_float(data.get('rainfall'), 800)
        temperature = safe_float(data.get('temperature'), 27)
        humidity = safe_float(data.get('humidity'), 70)
        pesticide = safe_float(data.get('pesticide'), 100)

        if models_loaded and prediction_models.disease_model is not None:
            disease_risk = prediction_models.predict_disease_risk(rainfall, temperature, pesticide)
            if disease_risk is None:
                disease_risk = 'Medium'
        else:
            risk_score = 0
            if rainfall > 1000:
                risk_score += 2
            elif rainfall > 500:
                risk_score += 1
            if 15 <= temperature <= 25:
                risk_score += 2
            if humidity > 80:
                risk_score += 1
            if pesticide < 100:
                risk_score += 1
            disease_risk = 'High' if risk_score >= 4 else 'Medium' if risk_score >= 2 else 'Low'

        recommendations = {
            'High': 'Apply fungicide, improve drainage, reduce plant density',
            'Medium': 'Monitor crops closely, ensure proper ventilation',
            'Low': 'Continue regular monitoring, maintain good practices'
        }

        message = f'Disease risk level: {disease_risk}'
        if session.get('user_id'):
            save_prediction(
                session['user_id'], 'Disease Prediction',
                json.dumps({'rainfall': rainfall, 'temperature': temperature, 'humidity': humidity}),
                message
            )

        return jsonify({
            'success': True,
            'risk_level': disease_risk,
            'recommendation': recommendations.get(disease_risk, 'Monitor regularly'),
            'message': message
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/recommend-fertilizer', methods=['POST'])
def api_recommend_fertilizer():
    try:
        data = request.get_json(silent=True) or {}
        crop = data.get('crop', 'Maize')
        rainfall = safe_float(data.get('rainfall'), 800)
        soil_type = str(data.get('soil_type', 'loamy')).lower()
        field_size = safe_float(data.get('field_size', 1.0), 1.0)
        growth_stage = str(data.get('growth_stage', 'vegetative')).lower()

        if models_loaded and prediction_models.fertilizer_recommender is not None:
            try:
                recommendation = prediction_models.recommend_fertilizer(crop, rainfall)
                if recommendation:
                    if session.get('user_id'):
                        save_prediction(
                            session['user_id'], 'Fertilizer Recommendation',
                            json.dumps({'crop': crop, 'rainfall': rainfall, 'soil_type': soil_type}),
                            recommendation.get('recommendation', f"Fertilizer recommendation for {crop}")
                        )
                    return jsonify({
                        'success': True,
                        'fertilizer': recommendation,
                        'field_size': field_size,
                        'message': 'Fertilizer recommendation generated successfully'
                    })
            except Exception as model_error:
                print(f"Model error: {model_error}")

        recommendation = generate_fallback_fertilizer_recommendation(crop, rainfall, soil_type, growth_stage, field_size)

        if session.get('user_id'):
            save_prediction(
                session['user_id'], 'Fertilizer Recommendation',
                json.dumps({'crop': crop, 'rainfall': rainfall, 'soil_type': soil_type}),
                recommendation.get('recommendation', f"Fertilizer recommendation for {crop}")
            )

        return jsonify({
            'success': True,
            'fertilizer': recommendation,
            'field_size': field_size,
            'message': 'Fertilizer recommendation generated successfully (estimated values)',
            'note': 'Recommendations based on field-tested agronomic rules'
        })

    except Exception as e:
        print(f"Fertilizer recommendation error: {e}")
        return jsonify({'success': False, 'error': f'Unable to generate recommendation: {str(e)}'})


def generate_fallback_fertilizer_recommendation(crop, rainfall, soil_type, growth_stage, field_size):
    """Generate a deterministic, agronomically sound fertilizer recommendation."""
    crop_profile = {
        'Maize': {'N': 120, 'P': 60, 'K': 40},
        'Rice': {'N': 100, 'P': 50, 'K': 50},
        'Potatoes': {'N': 150, 'P': 80, 'K': 120},
        'Soybeans': {'N': 20, 'P': 40, 'K': 60},
        'Wheat': {'N': 120, 'P': 40, 'K': 30},
        'Sorghum': {'N': 80, 'P': 40, 'K': 40},
        'Cotton': {'N': 120, 'P': 60, 'K': 60},
        'Sugarcane': {'N': 200, 'P': 80, 'K': 100},
        'Tomatoes': {'N': 150, 'P': 100, 'K': 150},
        'Groundnut': {'N': 25, 'P': 40, 'K': 45},
        'Onion': {'N': 90, 'P': 50, 'K': 70},
        'Chili': {'N': 110, 'P': 60, 'K': 80},
    }

    crop_key = normalize_crop_name(crop)
    matched_crop = next((name for name in crop_profile if crop_key.lower() in name.lower() or name.lower() in crop_key.lower()), 'Maize')
    base = crop_profile.get(matched_crop, crop_profile['Maize'])

    rainfall = max(0.0, rainfall)
    soil_factors = {
        'clay': {'N': 0.95, 'P': 1.10, 'K': 0.90},
        'sandy': {'N': 1.15, 'P': 1.20, 'K': 1.10},
        'loamy': {'N': 1.00, 'P': 1.00, 'K': 1.00},
        'black': {'N': 0.95, 'P': 0.90, 'K': 1.05},
        'red': {'N': 1.05, 'P': 1.10, 'K': 1.00},
        'alluvial': {'N': 1.00, 'P': 1.05, 'K': 1.00},
        'silt': {'N': 0.98, 'P': 1.05, 'K': 0.98},
    }
    soil_factor = soil_factors.get(soil_type, {'N': 1.0, 'P': 1.0, 'K': 1.0})

    if rainfall < 400:
        rain_factor = {'N': 1.20, 'P': 1.10, 'K': 1.10}
        rainfall_note = 'Low rainfall: increased nutrient demand to maintain productivity.'
    elif rainfall > 1500:
        rain_factor = {'N': 0.80, 'P': 0.85, 'K': 1.15}
        rainfall_note = 'High rainfall: reduce N and P slightly; maintain potassium for crop resilience.'
    else:
        rain_factor = {'N': 1.00, 'P': 1.00, 'K': 1.00}
        rainfall_note = 'Normal rainfall: standard nutrient application.'

    stage_factors = {
        'pre-sowing': {'N': 0.35, 'P': 0.5, 'K': 0.35},
        'sowing': {'N': 0.50, 'P': 0.60, 'K': 0.45},
        'vegetative': {'N': 1.20, 'P': 0.85, 'K': 0.90},
        'flowering': {'N': 0.70, 'P': 1.20, 'K': 1.10},
        'maturity': {'N': 0.25, 'P': 0.30, 'K': 0.80},
        'early_growth': {'N': 1.10, 'P': 0.90, 'K': 0.90},
    }
    stage_factor = stage_factors.get(growth_stage, {'N': 1.0, 'P': 1.0, 'K': 1.0})

    final_n = max(10, round(base['N'] * rain_factor['N'] * soil_factor['N'] * stage_factor['N']))
    final_p = max(5, round(base['P'] * rain_factor['P'] * soil_factor['P'] * stage_factor['P']))
    final_k = max(5, round(base['K'] * rain_factor['K'] * soil_factor['K'] * stage_factor['K']))

    field_size = max(0.1, field_size)
    total_n = round(final_n * field_size, 1)
    total_p = round(final_p * field_size, 1)
    total_k = round(final_k * field_size, 1)

    return {
        'matched_crop': matched_crop,
        'nitrogen_kg_ha': final_n,
        'phosphorus_kg_ha': final_p,
        'potassium_kg_ha': final_k,
        'total_nitrogen_kg': total_n,
        'total_phosphorus_kg': total_p,
        'total_potassium_kg': total_k,
        'recommendation': f'Apply {final_n}kg/ha N, {final_p}kg/ha P, {final_k}kg/ha K for {matched_crop}',
        'rainfall_factor': rainfall_note,
        'soil_type': soil_type.title(),
        'growth_stage': growth_stage.replace('_', ' ').title(),
        'application_schedule': generate_application_schedule(growth_stage, final_n, final_p, final_k),
        'fertilizer_types': generate_fertilizer_types(final_n, final_p, final_k, matched_crop),
        'cost_estimate': calculate_fertilizer_cost(final_n, final_p, final_k, field_size)
    }


def generate_application_schedule(growth_stage, n, p, k):
    schedules = {
        'pre-sowing': {
            'basal': {'N': max(10, round(n * 0.6)), 'P': max(10, round(p * 0.7)), 'K': max(10, round(k * 0.6))},
            'schedule': 'Apply the full basal dose before sowing and incorporate into the soil.'
        },
        'sowing': {
            'basal': {'N': max(10, round(n * 0.5)), 'P': max(10, round(p * 0.7)), 'K': max(10, round(k * 0.5))},
            'top_dress_1': {'N': max(10, round(n * 0.5)), 'K': max(10, round(k * 0.5))},
            'schedule': 'Apply 50% of nitrogen and potassium at sowing; top dress the remainder after 3-4 weeks.'
        },
        'vegetative': {
            'basal': {'N': max(10, round(n * 0.4)), 'P': max(10, round(p * 0.8)), 'K': max(10, round(k * 0.4))},
            'top_dress_1': {'N': max(10, round(n * 0.4)), 'K': max(10, round(k * 0.4))},
            'top_dress_2': {'N': max(10, round(n * 0.2)), 'K': max(10, round(k * 0.2))},
            'schedule': 'Use split nitrogen applications during vegetative growth; keep phosphorus basal.'
        },
        'flowering': {
            'current': {'N': max(10, round(n * 0.3)), 'P': max(10, round(p * 0.7)), 'K': max(10, round(k * 0.6))},
            'next': {'N': max(10, round(n * 0.2)), 'P': max(10, round(p * 0.3)), 'K': max(10, round(k * 0.4))},
            'schedule': 'Prioritize phosphorus and potassium during flowering to improve fruit set and quality.'
        },
        'maturity': {
            'current': {'N': max(10, round(n * 0.15)), 'P': max(10, round(p * 0.2)), 'K': max(10, round(k * 0.5))},
            'schedule': 'Minimal nitrogen; maintain potassium to protect grain filling and crop quality.'
        }
    }
    return schedules.get(growth_stage, schedules['vegetative'])


def generate_fertilizer_types(n, p, k, matched_crop):
    nitrogen_sources = ['Urea (46% N)', 'Ammonium Sulphate (21% N)', 'Urea + DAP blend']
    phosphorus_sources = ['DAP (46% P2O5)', 'SSP (16% P2O5)', 'TSP (46% P2O5)']
    potassium_sources = ['MOP (60% K2O)', 'SOP (50% K2O)', 'Potash blend']

    return [
        {'nutrient': 'Nitrogen', 'recommended_source': nitrogen_sources[0], 'quantity_needed': f'{max(10, round(n / 0.46, 1))} kg/ha'},
        {'nutrient': 'Phosphorus', 'recommended_source': phosphorus_sources[0], 'quantity_needed': f'{max(10, round(p / 0.46, 1))} kg/ha'},
        {'nutrient': 'Potassium', 'recommended_source': potassium_sources[0], 'quantity_needed': f'{max(10, round(k / 0.60, 1))} kg/ha'}
    ]


def calculate_fertilizer_cost(n, p, k, field_size):
    n_cost = 30
    p_cost = 60
    k_cost = 35
    total_cost = (n * n_cost + p * p_cost + k * k_cost) * field_size
    return {
        'per_hectare': round(n * n_cost + p * p_cost + k * k_cost, 2),
        'total_field': round(total_cost, 2),
        'currency': 'INR',
        'breakdown': {
            'nitrogen_cost': round(n * n_cost * field_size, 2),
            'phosphorus_cost': round(p * p_cost * field_size, 2),
            'potassium_cost': round(k * k_cost * field_size, 2)
        }
    }


@app.route('/api/predict-weather', methods=['POST'])
def api_predict_weather():
    try:
        data = request.get_json(silent=True) or {}
        year = int(data.get('year', 2025))
        location = data.get('location', 'General')

        if models_loaded and prediction_models.weather_model is not None:
            rainfall_pred = prediction_models.predict_weather(year)
            if rainfall_pred is None:
                rainfall_pred = 800 + (year - 2020) * 8
        else:
            rainfall_pred = 800 + (year - 2020) * 8

        if rainfall_pred < 400:
            weather_advice = 'Low rainfall expected. Consider drought-resistant crops and irrigation planning.'
        elif rainfall_pred > 1500:
            weather_advice = 'High rainfall expected. Ensure proper drainage and flood management.'
        else:
            weather_advice = 'Normal rainfall expected. Good conditions for most crops.'

        message = f'Weather prediction for {year}: {rainfall_pred}mm rainfall'
        if session.get('user_id'):
            save_prediction(
                session['user_id'], 'Weather Prediction',
                json.dumps({'year': year, 'location': location}),
                message
            )

        return jsonify({
            'success': True,
            'year': year,
            'location': location,
            'predicted_rainfall': rainfall_pred,
            'advice': weather_advice,
            'message': message
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/crop-recommendation')
def crop_recommendation():
    return render_template('crop_recommendation.html')


@app.route('/api/recommend-crop', methods=['POST'])
def api_recommend_crop():
    try:
        data = request.get_json(silent=True) or {}
        rainfall = safe_float(data.get('rainfall'), 800)
        temperature = safe_float(data.get('temperature'), 27)
        humidity = safe_float(data.get('humidity'), 70)
        soil_type = str(data.get('soil_type', 'loamy')).lower()
        ph_level = safe_float(data.get('ph_level'), 6.8)
        season = str(data.get('season', 'kharif')).lower()
        farm_size = safe_float(data.get('farm_size', 1.0), 1.0)
        water_availability = str(data.get('water_availability', 'moderate')).lower()
        experience_level = str(data.get('experience_level', 'intermediate')).lower()
        market_preference = str(data.get('market_preference', 'food_grain')).lower()

        recommendations = generate_crop_recommendations(
            rainfall, temperature, humidity, soil_type, ph_level,
            season, farm_size, water_availability, experience_level, market_preference
        )

        top_crop = recommendations[0]['crop_name'] if recommendations else 'N/A'
        if session.get('user_id'):
            save_prediction(
                session['user_id'], 'Crop Recommendation',
                json.dumps({'rainfall': rainfall, 'temperature': temperature, 'soil_type': soil_type, 'season': season}),
                f'Top recommendation: {top_crop}'
            )

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'message': 'Crop recommendations generated successfully',
            'parameters_used': {
                'rainfall': rainfall,
                'temperature': temperature,
                'humidity': humidity,
                'soil_type': soil_type,
                'season': season
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def generate_crop_recommendations(rainfall, temperature, humidity, soil_type, ph_level, season, farm_size,
                                 water_availability, experience_level, market_preference):
    crop_database = {
        'Rice': {
            'rainfall': (1000, 2500), 'temperature': (20, 35), 'humidity': (70, 95),
            'soil_types': ['clay', 'loamy', 'alluvial'], 'ph_range': (5.5, 7.0),
            'water_need': 'high', 'season': ['kharif', 'rabi'], 'experience': ['beginner', 'intermediate', 'advanced'],
            'market_type': 'food_grain', 'yield_potential': 'high', 'investment': 'medium', 'duration': '120-150 days', 'profit_margin': 'medium'
        },
        'Wheat': {
            'rainfall': (300, 1000), 'temperature': (15, 25), 'humidity': (50, 70),
            'soil_types': ['loamy', 'clay', 'black'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['rabi'], 'experience': ['beginner', 'intermediate', 'advanced'],
            'market_type': 'food_grain', 'yield_potential': 'high', 'investment': 'medium', 'duration': '120-140 days', 'profit_margin': 'medium'
        },
        'Maize': {
            'rainfall': (500, 1200), 'temperature': (18, 32), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (5.5, 7.0),
            'water_need': 'medium', 'season': ['kharif', 'rabi', 'zaid'], 'experience': ['beginner', 'intermediate', 'advanced'],
            'market_type': 'food_grain', 'yield_potential': 'high', 'investment': 'medium', 'duration': '90-120 days', 'profit_margin': 'high'
        },
        'Cotton': {
            'rainfall': (500, 1200), 'temperature': (21, 35), 'humidity': (60, 85),
            'soil_types': ['black', 'alluvial', 'red'], 'ph_range': (6.0, 8.0),
            'water_need': 'medium', 'season': ['kharif'], 'experience': ['intermediate', 'advanced'],
            'market_type': 'cash_crop', 'yield_potential': 'high', 'investment': 'high', 'duration': '180-200 days', 'profit_margin': 'very_high'
        },
        'Sugarcane': {
            'rainfall': (1000, 2000), 'temperature': (20, 35), 'humidity': (70, 90),
            'soil_types': ['loamy', 'clay', 'alluvial'], 'ph_range': (6.0, 7.5),
            'water_need': 'very_high', 'season': ['annual'], 'experience': ['intermediate', 'advanced'],
            'market_type': 'cash_crop', 'yield_potential': 'very_high', 'investment': 'very_high', 'duration': '12-18 months', 'profit_margin': 'high'
        },
        'Soybeans': {
            'rainfall': (400, 800), 'temperature': (20, 30), 'humidity': (60, 80),
            'soil_types': ['loamy', 'black', 'red'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['kharif'], 'experience': ['beginner', 'intermediate'],
            'market_type': 'oilseed', 'yield_potential': 'medium', 'investment': 'low', 'duration': '90-110 days', 'profit_margin': 'medium'
        },
        'Groundnut': {
            'rainfall': (500, 1000), 'temperature': (20, 30), 'humidity': (65, 85),
            'soil_types': ['sandy', 'red', 'black'], 'ph_range': (6.0, 7.0),
            'water_need': 'medium', 'season': ['kharif', 'rabi'], 'experience': ['beginner', 'intermediate'],
            'market_type': 'oilseed', 'yield_potential': 'medium', 'investment': 'medium', 'duration': '100-120 days', 'profit_margin': 'medium'
        },
        'Tomato': {
            'rainfall': (400, 800), 'temperature': (18, 27), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (6.0, 7.0),
            'water_need': 'high', 'season': ['rabi', 'zaid'], 'experience': ['intermediate', 'advanced'],
            'market_type': 'vegetable', 'yield_potential': 'high', 'investment': 'high', 'duration': '90-120 days', 'profit_margin': 'very_high'
        },
        'Potato': {
            'rainfall': (400, 700), 'temperature': (15, 25), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (5.5, 6.5),
            'water_need': 'medium', 'season': ['rabi'], 'experience': ['intermediate', 'advanced'],
            'market_type': 'vegetable', 'yield_potential': 'high', 'investment': 'high', 'duration': '90-120 days', 'profit_margin': 'high'
        },
        'Onion': {
            'rainfall': (300, 600), 'temperature': (15, 25), 'humidity': (60, 70),
            'soil_types': ['loamy', 'sandy', 'alluvial'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['rabi', 'kharif'], 'experience': ['intermediate', 'advanced'],
            'market_type': 'vegetable', 'yield_potential': 'medium', 'investment': 'medium', 'duration': '120-150 days', 'profit_margin': 'high'
        },
        'Sunflower': {
            'rainfall': (400, 800), 'temperature': (20, 30), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['kharif', 'rabi'], 'experience': ['beginner', 'intermediate'],
            'market_type': 'oilseed', 'yield_potential': 'medium', 'investment': 'low', 'duration': '90-110 days', 'profit_margin': 'medium'
        },
        'Chili': {
            'rainfall': (600, 1200), 'temperature': (20, 30), 'humidity': (70, 85),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (6.0, 7.0),
            'water_need': 'medium', 'season': ['kharif', 'rabi'], 'experience': ['intermediate', 'advanced'],
            'market_type': 'spice', 'yield_potential': 'high', 'investment': 'medium', 'duration': '150-180 days', 'profit_margin': 'very_high'
        }
    }

    crop_scores = []
    for crop, requirements in crop_database.items():
        score = 0
        details = []

        rain_min, rain_max = requirements['rainfall']
        if rain_min <= rainfall <= rain_max:
            score += 20
            details.append(f'Rainfall suitable ({rain_min}-{rain_max} mm)')
        else:
            score += max(0, 20 - abs(rainfall - ((rain_min + rain_max) / 2)) / 100)
            details.append(f'Rainfall near optimum ({rain_min}-{rain_max} mm)')

        temp_min, temp_max = requirements['temperature']
        if temp_min <= temperature <= temp_max:
            score += 20
            details.append(f'Temperature suitable ({temp_min}-{temp_max}°C)')
        else:
            score += max(0, 20 - abs(temperature - ((temp_min + temp_max) / 2)) / 3)
            details.append(f'Temperature close to crop requirement ({temp_min}-{temp_max}°C)')

        if soil_type in requirements['soil_types']:
            score += 15
            details.append(f'Soil matches {soil_type} requirement')
        else:
            score += 8
            details.append(f'Soil is moderately suitable; {requirements["soil_types"][0]} preferred')

        ph_min, ph_max = requirements['ph_range']
        if ph_min <= ph_level <= ph_max:
            score += 10
            details.append(f'pH is suitable ({ph_min}-{ph_max})')
        else:
            score += max(0, 5 - abs(ph_level - ((ph_min + ph_max) / 2)))
            details.append(f'Adjust pH toward {ph_min}-{ph_max}')

        if season in requirements['season'] or 'annual' in requirements['season']:
            score += 10
            details.append(f'Season matches {season}')
        else:
            score += 5
            details.append(f'Best season: {', '.join(requirements['season'])}')

        if experience_level in requirements['experience']:
            score += 10
            details.append(f'Experience requirement suitable')
        else:
            score += 6
            details.append(f'Requires {requirements["experience"][-1]} level expertise')

        water_compatibility = {'low': ['low', 'medium'], 'medium': ['low', 'medium', 'high'], 'high': ['medium', 'high', 'very_high'], 'very_high': ['high', 'very_high']}
        if requirements['water_need'] in water_compatibility.get(water_availability, []):
            score += 10
            details.append('Water availability is compatible')
        else:
            score += 5
            details.append(f'Water requirement: {requirements["water_need"]}')

        if requirements['market_type'] == market_preference or market_preference == 'mixed':
            score += 5
            details.append('Matches market preference')
        else:
            score += 3
            details.append(f'Market type: {requirements["market_type"].replace("_", " ").title()}')

        score_percentage = round(min(100, max(0, score)), 1)
        if score_percentage >= 80:
            recommendation_level = 'Highly Recommended'
            level_class = 'success'
        elif score_percentage >= 65:
            recommendation_level = 'Recommended'
            level_class = 'primary'
        elif score_percentage >= 50:
            recommendation_level = 'Moderately Suitable'
            level_class = 'warning'
        else:
            recommendation_level = 'Not Recommended'
            level_class = 'danger'

        crop_scores.append({
            'crop_name': crop,
            'suitability_score': score_percentage,
            'recommendation_level': recommendation_level,
            'level_class': level_class,
            'details': details,
            'estimated_yield': calculate_estimated_yield(crop, score_percentage, farm_size),
            'investment_needed': calculate_investment(crop, farm_size),
            'profit_potential': requirements['profit_margin'],
            'duration': requirements['duration'],
            'special_notes': generate_special_notes(crop, rainfall, temperature, soil_type),
            'market_type': requirements['market_type'].replace('_', ' ').title(),
            'water_requirement': requirements['water_need'].title(),
        })

    return sorted(crop_scores, key=lambda item: item['suitability_score'], reverse=True)[:8]


def calculate_estimated_yield(crop, score_percentage, farm_size):
    base_yields = {
        'Rice': 4000, 'Wheat': 3500, 'Maize': 5000, 'Cotton': 2000,
        'Sugarcane': 80000, 'Soybeans': 2500, 'Groundnut': 2000,
        'Tomato': 40000, 'Potato': 25000, 'Onion': 30000,
        'Sunflower': 1800, 'Chili': 3000
    }

    base_yield = base_yields.get(crop, 3000)
    factor = score_percentage / 100
    estimated_yield_per_ha = round(base_yield * factor * 1.05)
    total_yield = round(estimated_yield_per_ha * max(0.1, farm_size), 1)

    return {
        'per_hectare': estimated_yield_per_ha,
        'total_farm': total_yield,
        'unit': 'kg' if crop not in ('Sugarcane',) else 'tons'
    }


def calculate_investment(crop, farm_size):
    investment_per_ha = {
        'Rice': 30000, 'Wheat': 25000, 'Maize': 20000, 'Cotton': 37000,
        'Sugarcane': 100000, 'Soybeans': 15000, 'Groundnut': 22000,
        'Tomato': 50000, 'Potato': 42000, 'Onion': 30000,
        'Sunflower': 12500, 'Chili': 25000
    }

    per_ha = investment_per_ha.get(crop, 20000)
    return {'per_hectare': per_ha, 'total_farm': round(per_ha * max(0.1, farm_size), 2), 'currency': 'INR'}


def generate_special_notes(crop, rainfall, temperature, soil_type):
    notes = {
        'Rice': ['Ensure proper water management.', 'Use efficient irrigation scheduling.'],
        'Wheat': ['Apply nitrogen in split doses.', 'Monitor for rust and lodging.'],
        'Maize': ['Maintain spacing for even nutrient uptake.', 'Good option for intercropping.'],
        'Cotton': ['Watch for insect pressure.', 'Ensure timely crop protection.'],
        'Sugarcane': ['Long-duration crop; plan for irrigation.', 'Higher nutrient demand.'],
        'Soybeans': ['Good rotation crop.', 'Use inoculation for better nodulation.'],
        'Tomato': ['Stake and prune for disease reduction.', 'Monitor irrigation carefully.'],
        'Potato': ['Plan suitable storage.', 'Maintain moisture evenly.'],
        'Onion': ['Watch for bulb size uniformity.', 'Use steady irrigation during bulbing.'],
        'Chili': ['High-value crop with strong market demand.', 'Use good drainage.']
    }
    result = notes.get(crop, ['Follow local agronomic best practices.'])
    if rainfall > 1500:
        result.append('High rainfall: provide drainage and avoid waterlogging.')
    elif rainfall < 400:
        result.append('Low rainfall: supplement irrigation.')
    if temperature > 35:
        result.append('High temperature: protect against heat stress.')
    elif temperature < 15:
        result.append('Cool conditions: use frost protection when needed.')
    return result


@app.route('/farmer-connect')
def farmer_connect():
    return render_template('farmer_connect.html')


@app.route('/farmer-connect/forum')
def farmer_forum():
    return render_template('farmer_forum.html')


@app.route('/farmer-connect/experts')
def expert_advice():
    return render_template('expert_advice.html')


@app.route('/farmer-connect/marketplace')
def farmer_marketplace():
    return render_template('farmer_marketplace.html')


@app.route('/api/post-question', methods=['POST'])
def api_post_question():
    try:
        data = request.get_json(silent=True) or {}
        question_data = {
            'id': generate_question_id(),
            'farmer_name': data.get('farmer_name', 'Farmer'),
            'location': data.get('location', 'Unknown'),
            'crop_type': data.get('crop_type', 'General'),
            'category': data.get('category', 'General'),
            'question': data.get('question', 'No question provided'),
            'timestamp': get_current_timestamp(),
            'responses': [],
            'helpful_count': 0,
            'status': 'open'
        }

        if session.get('user_id'):
            save_forum_post(session['user_id'], data.get('question', '')[:100], data.get('question', ''), data.get('category', 'General'), data.get('crop_type', 'General'))

        return jsonify({
            'success': True,
            'question_id': question_data['id'],
            'message': 'Your question has been posted successfully!',
            'estimated_response_time': '2-4 hours'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/get-forum-posts')
def api_get_forum_posts():
    db_posts = get_forum_posts(50)
    real_posts = []
    for p in db_posts:
        real_posts.append({
            'id': f'DB{p["id"]}',
            'farmer_name': p['full_name'],
            'location': p['location'] or 'Unknown',
            'crop_type': p['crop_type'],
            'category': p['category'],
            'question': p['content'],
            'timestamp': p['created_at'],
            'responses': 0,
            'helpful_count': 0,
            'status': 'open'
        })

    all_posts = real_posts + generate_mock_forum_posts()
    return jsonify({'success': True, 'posts': all_posts, 'total_posts': len(all_posts)})


@app.route('/api/connect-farmers', methods=['POST'])
def api_connect_farmers():
    try:
        data = request.get_json(silent=True) or {}
        location = data.get('location', 'Local Region')
        crop_interest = data.get('crop_interest', 'All')
        nearby_farmers = generate_nearby_farmers(location, crop_interest)
        return jsonify({'success': True, 'farmers': nearby_farmers, 'message': f'Found {len(nearby_farmers)} farmers in your area'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/submit-listing', methods=['POST'])
def api_submit_listing():
    try:
        data = request.get_json(silent=True) or {}
        listing = {
            'id': generate_listing_id(),
            'farmer_name': data.get('farmer_name', 'Farmer'),
            'contact': data.get('contact', 'Not Provided'),
            'location': data.get('location', 'Unknown'),
            'listing_type': data.get('listing_type', 'sell'),
            'item_name': data.get('item_name', 'Crop'),
            'quantity': data.get('quantity', '1'),
            'price': data.get('price', 'Negotiable'),
            'description': data.get('description', ''),
            'timestamp': get_current_timestamp(),
            'status': 'active'
        }

        if session.get('user_id'):
            save_marketplace_listing(
                session['user_id'],
                data.get('item_name', 'Crop'),
                data.get('quantity', '1'),
                data.get('price', 'Negotiable'),
                data.get('description', ''),
                data.get('listing_type', 'sell'),
                data.get('location', '')
            )

        return jsonify({'success': True, 'listing_id': listing['id'], 'message': 'Your listing has been posted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def generate_question_id():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_listing_id():
    import random, string
    return 'LST' + ''.join(random.choices(string.digits, k=6))


def get_current_timestamp():
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def generate_mock_forum_posts():
    from datetime import datetime, timedelta
    return [
        {
            'id': 'Q001',
            'farmer_name': 'Rajesh Kumar',
            'location': 'Punjab',
            'crop_type': 'Wheat',
            'category': 'Disease Management',
            'question': 'My wheat crop is showing yellow rust symptoms. What immediate action should I take?',
            'timestamp': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'responses': 3,
            'helpful_count': 12,
            'status': 'answered'
        },
        {
            'id': 'Q002',
            'farmer_name': 'Priya Sharma',
            'location': 'Maharashtra',
            'crop_type': 'Cotton',
            'category': 'Pest Control',
            'question': 'How to control bollworm attack in cotton without using excessive pesticides?',
            'timestamp': (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
            'responses': 7,
            'helpful_count': 25,
            'status': 'answered'
        },
        {
            'id': 'Q003',
            'farmer_name': 'Suresh Patel',
            'location': 'Gujarat',
            'crop_type': 'Groundnut',
            'category': 'Soil Management',
            'question': 'Best organic fertilizers for groundnut cultivation in sandy soil?',
            'timestamp': (datetime.now() - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
            'responses': 5,
            'helpful_count': 18,
            'status': 'answered'
        },
        {
            'id': 'Q004',
            'farmer_name': 'Lakshmi Devi',
            'location': 'Andhra Pradesh',
            'crop_type': 'Rice',
            'category': 'Water Management',
            'question': 'How to implement drip irrigation system for paddy cultivation?',
            'timestamp': (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
            'responses': 1,
            'helpful_count': 3,
            'status': 'open'
        },
        {
            'id': 'Q005',
            'farmer_name': 'Ramesh Reddy',
            'location': 'Karnataka',
            'crop_type': 'Tomato',
            'category': 'Market Information',
            'question': 'Current market rates for tomatoes in Bangalore wholesale market?',
            'timestamp': (datetime.now() - timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S'),
            'responses': 0,
            'helpful_count': 1,
            'status': 'open'
        }
    ]


def generate_nearby_farmers(location, crop_interest):
    import random
    farmers = [
        {'name': 'Amit Singh', 'location': location, 'crops': ['Wheat', 'Mustard', 'Barley'], 'experience': '15 years', 'specialization': 'Organic farming', 'contact': '+91 98xxx-xxxxx', 'rating': 4.8, 'distance': f'{random.randint(2, 15)} km'},
        {'name': 'Sunita Devi', 'location': location, 'crops': ['Rice', 'Vegetables', 'Pulses'], 'experience': '12 years', 'specialization': 'Sustainable agriculture', 'contact': '+91 97xxx-xxxxx', 'rating': 4.6, 'distance': f'{random.randint(5, 20)} km'},
        {'name': 'Kiran Patil', 'location': location, 'crops': ['Cotton', 'Soybean', 'Maize'], 'experience': '20 years', 'specialization': 'Precision farming', 'contact': '+91 96xxx-xxxxx', 'rating': 4.9, 'distance': f'{random.randint(8, 25)} km'},
        {'name': 'Deepak Yadav', 'location': location, 'crops': ['Sugarcane', 'Wheat', 'Potato'], 'experience': '18 years', 'specialization': 'Water management', 'contact': '+91 95xxx-xxxxx', 'rating': 4.7, 'distance': f'{random.randint(3, 12)} km'}
    ]
    if crop_interest != 'All':
        farmers = [f for f in farmers if crop_interest in f['crops']]
    return random.sample(farmers, min(len(farmers), 6))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)
