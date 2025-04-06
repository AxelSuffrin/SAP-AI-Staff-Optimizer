from flask import Flask, render_template, request, jsonify
import json
import os
import random
from datetime import datetime, timedelta
from mock.sap_mock import SAPMockGenerator
from genai.pricing import PricingEngine
from genai.staffing import StaffingEngine

app = Flask(__name__)

# Initialize and generate mock data if it doesn't exist or is empty
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

# Check if hotels.json exists AND has data
hotels_file = os.path.join(data_dir, 'hotels.json')
hotels_empty = True

if os.path.exists(hotels_file) and os.path.getsize(hotels_file) > 2:
    # File exists and has more content than just "[]"
    with open(hotels_file) as f:
        hotels_data = json.load(f)
        if hotels_data and len(hotels_data) > 0:
            hotels_empty = False

# Generate data if needed
if hotels_empty:
    print("Generating mock hotel data...")
    generator = SAPMockGenerator()
    generator.generate_hotels(300)  # Generate 300 hotel properties
    generator.generate_bookings()
    generator.generate_events()
    generator.generate_competitors()
    generator.export_to_json(data_dir)
    print("Mock data generation complete!")

# Load mock data
try:
    with open(os.path.join(data_dir, 'hotels.json')) as f:
        hotels = json.load(f)
except Exception as e:
    print(f"Error loading hotels.json: {e}")
    hotels = []

try:
    with open(os.path.join(data_dir, 'bookings.json')) as f:
        bookings = json.load(f)
except Exception as e:
    print(f"Error loading bookings.json: {e}")
    bookings = []

try:
    with open(os.path.join(data_dir, 'events.json')) as f:
        events = json.load(f)
except Exception as e:
    print(f"Error loading events.json: {e}")
    events = []

try:
    with open(os.path.join(data_dir, 'competitors.json')) as f:
        competitors = json.load(f)
except Exception as e:
    print(f"Error loading competitors.json: {e}")
    competitors = []

# Fix location matching - ensure some hotels have the same locations as events
if hotels and events:
    # Get unique event locations
    event_locations = set(event['location'] for event in events)
    
    # Assign some event locations to hotels to ensure matches
    for i, location in enumerate(event_locations):
        if i < len(hotels):
            hotels[i]['location'] = location
    
    # Save updated hotels data
    with open(os.path.join(data_dir, 'hotels.json'), 'w') as f:
        json.dump(hotels, f, indent=2)
    
    print(f"Updated {len(event_locations)} hotels to match event locations")

# Initialize engines
pricing_engine = PricingEngine(bookings, competitors, events)
staffing_engine = StaffingEngine(bookings, hotels, events)

@app.route('/')
def index():
    """Main dashboard page"""
    # Get counts for dashboard
    countries = set(hotel['country'] for hotel in hotels)
    total_rooms = sum(hotel['rooms'] for hotel in hotels)
    
    # Get sample hotels for display
    sample_hotels = random.sample(hotels, min(10, len(hotels)))
    
    return render_template('index.html', 
                          hotels=sample_hotels,
                          hotel_count=len(hotels),
                          country_count=len(countries),
                          total_rooms=total_rooms)

@app.route('/pricing')
def pricing_page():
    """Dynamic pricing optimization page"""
    # Get hotel_id from query param or use first hotel
    hotel_id = request.args.get('hotel_id', hotels[0]['hotel_id'] if hotels else None)
    
    # Get hotel details
    hotel = next((h for h in hotels if h['hotel_id'] == hotel_id), None)
    
    if not hotel:
        return "Hotel not found", 404
        
    return render_template('pricing.html', 
                          hotel=hotel,
                          hotels=hotels)

@app.route('/staffing')
def staffing_page():
    """Staffing optimization page"""
    # Get hotel_id from query param or use first hotel
    hotel_id = request.args.get('hotel_id', hotels[0]['hotel_id'] if hotels else None)
    
    # Get hotel details
    hotel = next((h for h in hotels if h['hotel_id'] == hotel_id), None)
    
    if not hotel:
        return "Hotel not found", 404
        
    return render_template('staffing.html', 
                          hotel=hotel,
                          hotels=hotels)

@app.route('/hotels-with-events')
def hotels_with_events():
    """Shows all hotels that have events in the next 7 days"""
    hotels_with_events = []
    
    for hotel in hotels:
        nearby_events = [e for e in events if e['location'] == hotel['location']]
        if nearby_events:
            # Count events in the next 7 days
            today = datetime.now()
            upcoming_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            upcoming_events = [e for e in nearby_events if e['date'] in upcoming_dates]
            
            if upcoming_events:
                hotels_with_events.append({
                    'hotel': hotel,
                    'event_count': len(upcoming_events),
                    'events': upcoming_events
                })
    
    return render_template('hotels_with_events.html', 
                          hotels_with_events=hotels_with_events)

@app.route('/api/pricing/<hotel_id>')
def get_pricing(hotel_id):
    """API endpoint to get dynamic pricing data"""
    # Find hotel details
    hotel = next((h for h in hotels if h['hotel_id'] == hotel_id), None)
    
    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404
    
    # Get hotel's booking data
    hotel_bookings = [b for b in bookings if b['hotel_id'] == hotel_id]
    
    # Get nearby events
    nearby_events = [e for e in events if e['location'] == hotel['location']]
    
    # Calculate pricing factors
    season_factor = random.uniform(0.9, 1.3)
    demand_factor = random.uniform(0.85, 1.4)
    event_factor = 1.2 if nearby_events else 1.0
    competitor_factor = random.uniform(0.9, 1.1)
    luxury_factor = 1.0 + (hotel['rating'] - 3.0) * 0.15
    
    # Calculate dynamic price
    base_price = round(100 + (hotel['rating'] * 40), 2)
    dynamic_price = round(base_price * season_factor * demand_factor * event_factor * competitor_factor * luxury_factor, 2)
    
    # Get next 7 days for forecast
    today = datetime.now()
    forecast_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    # Generate price forecast with slight variations
    price_forecast = []
    for date in forecast_dates:
        # Add some daily variation
        daily_factor = random.uniform(0.95, 1.05)
        # Check if event on this date
        date_event_factor = 1.25 if any(e['date'] == date for e in nearby_events) else 1.0
        
        price = round(dynamic_price * daily_factor * date_event_factor, 2)
        price_forecast.append({
            "date": date,
            "price": price,
            "has_event": date_event_factor > 1.0
        })
    
    response = {
        "hotel_id": hotel_id,
        "hotel_name": hotel['name'],
        "location": hotel['location'],
        "country": hotel['country'],
        "rating": hotel['rating'],
        "base_price": base_price,
        "dynamic_price": dynamic_price,
        "pricing_factors": {
            "season_factor": round(season_factor, 2),
            "demand_factor": round(demand_factor, 2),
            "event_factor": round(event_factor, 2),
            "competitor_factor": round(competitor_factor, 2),
            "luxury_factor": round(luxury_factor, 2)
        },
        "price_forecast": price_forecast,
        "nearby_events": [{"name": e["name"], "date": e["date"]} for e in nearby_events[:3]],
        "explanation": generate_pricing_explanation(hotel, season_factor, demand_factor, event_factor, competitor_factor)
    }
    
    return jsonify(response)

@app.route('/api/staffing/<hotel_id>')
def get_staffing(hotel_id):
    """API endpoint to get staffing recommendations"""
    # Find hotel details
    hotel = next((h for h in hotels if h['hotel_id'] == hotel_id), None)
    
    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404
    
    # Get forecast data from staffing engine
    staffing_data = staffing_engine.calculate_staffing(hotel_id)
    
    return jsonify(staffing_data)

@app.route('/debug/locations')
def debug_locations():
    """Debug endpoint to check location matching"""
    hotel_locations = set(hotel['location'] for hotel in hotels)
    event_locations = set(event['location'] for event in events)
    matching_locations = hotel_locations.intersection(event_locations)
    
    event_dates = set(event['date'] for event in events)
    current_date = datetime.now().strftime("%Y-%m-%d")
    upcoming_dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    return jsonify({
        'hotel_locations': list(hotel_locations),
        'event_locations': list(event_locations),
        'matching_locations': list(matching_locations),
        'event_dates': list(event_dates),
        'current_date': current_date,
        'upcoming_dates': upcoming_dates
    })

def generate_pricing_explanation(hotel, season_factor, demand_factor, event_factor, competitor_factor):
    """Generate human-readable explanation for pricing decisions"""
    explanation = f"The recommended rate for {hotel['name']} is based on several factors: "
    
    factors = []
    if season_factor > 1.1:
        factors.append("high season demand")
    elif season_factor < 0.95:
        factors.append("low season adjustments")
    
    if demand_factor > 1.1:
        factors.append("strong current booking trends")
    elif demand_factor < 0.95:
        factors.append("softer than usual demand")
    
    if event_factor > 1.0:
        factors.append("local events increasing demand")
    
    if competitor_factor > 1.05:
        factors.append("competitor hotels raising their rates")
    elif competitor_factor < 0.95:
        factors.append("competitive pressure from nearby properties")
    
    if not factors:
        explanation += "standard pricing aligned with market conditions."
    else:
        explanation += ", ".join(factors[:-1])
        if len(factors) > 1:
            explanation += f", and {factors[-1]}."
        else:
            explanation += f"{factors[0]}."
    
    return explanation

if __name__ == '__main__':
    app.run(debug=True)
