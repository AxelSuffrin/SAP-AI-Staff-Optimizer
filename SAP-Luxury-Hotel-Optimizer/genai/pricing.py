import random
from datetime import datetime, timedelta

class PricingEngine:
    """
    Simulates a predictive pricing engine that would typically be 
    implemented using SAP's AI technologies for hotel room pricing optimization.
    """
    
    def __init__(self, bookings, competitors, events):
        self.bookings = bookings
        self.competitors = competitors
        self.events = events
        
    def get_hotel_bookings(self, hotel_id):
        """Get all bookings for a specific hotel."""
        return [b for b in self.bookings if b["hotel_id"] == hotel_id]
    
    def get_competitor_price(self, hotel_id):
        """Get competitor price for a specific hotel."""
        competitor = next((c for c in self.competitors if c["hotel_id"] == hotel_id), None)
        return competitor["competitor_price"] if competitor else None
    
    def get_nearby_events(self, location, date=None):
        """Get events near a specific location and optionally on a specific date."""
        nearby_events = [e for e in self.events if e["location"] == location]
        if date:
            nearby_events = [e for e in nearby_events if e["date"] == date]
        return nearby_events
    
    def calculate_season_factor(self, date_str=None):
        """Calculate season factor based on current date."""
        if not date_str:
            date = datetime.now()
        else:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
        # Summer months get higher rates
        if date.month in [6, 7, 8]:
            return random.uniform(1.15, 1.3)
        # Winter holidays also get higher rates
        elif date.month == 12 and date.day >= 15:
            return random.uniform(1.2, 1.35)
        # Spring and fall are shoulder seasons
        elif date.month in [4, 5, 9, 10]:
            return random.uniform(1.0, 1.15)
        # Winter (non-holiday) gets lower rates
        else:
            return random.uniform(0.85, 1.0)
    
    def calculate_demand_factor(self, hotel_bookings):
        """Calculate demand factor based on current bookings."""
        if not hotel_bookings:
            return 1.0
            
        # Simple demand calculation - more bookings = higher factor
        avg_bookings = sum(b["bookings"] for b in hotel_bookings) / len(hotel_bookings)
        
        # Scale to a factor between 0.8 and 1.5
        return 0.8 + min(avg_bookings / 50, 0.7)
    
    def calculate_event_factor(self, nearby_events):
        """Calculate event factor based on local events."""
        if not nearby_events:
            return 1.0
            
        # Sum up the expected attendance
        total_attendance = sum(e["expected_attendance"] for e in nearby_events)
        
        # Scale to a factor between 1.0 and 1.5
        return 1.0 + min(total_attendance / 10000, 0.5)
    
    def calculate_competitor_factor(self, hotel_id, base_price):
        """Calculate competitor factor based on nearby hotel rates."""
        competitor_price = self.get_competitor_price(hotel_id)
        
        if not competitor_price:
            return 1.0
            
        # Calculate the ratio of competitor price to our base price
        ratio = competitor_price / base_price
        
        # If competitors are more expensive, we can raise prices
        # If competitors are cheaper, we might need to lower prices
        if ratio > 1.1:
            return random.uniform(1.05, 1.15)
        elif ratio < 0.9:
            return random.uniform(0.9, 0.98)
        else:
            return random.uniform(0.95, 1.05)
    
    def calculate_price(self, hotel_id, hotel_rating=4.0, date_str=None):
        """Calculate optimized dynamic price for a hotel room."""
        # Get relevant data
        hotel_bookings = self.get_hotel_bookings(hotel_id)
        
        # Calculate base price based on hotel rating
        base_price = 100 + (hotel_rating * 40)
        
        # Calculate pricing factors
        season_factor = self.calculate_season_factor(date_str)
        demand_factor = self.calculate_demand_factor(hotel_bookings)
        
        # Get hotel location from a booking (assuming all bookings have same location)
        hotel_location = None
        if hotel_bookings:
            hotel_data = next((h for h in self.bookings if h["hotel_id"] == hotel_id), None)
            if hotel_data:
                # This is a simplification - in real data we'd have location in the hotel object
                hotel_location = "Sample Location"
        
        # Calculate event and competitor factors
        event_factor = 1.0
        if hotel_location:
            nearby_events = self.get_nearby_events(hotel_location, date_str)
            event_factor = self.calculate_event_factor(nearby_events)
            
        competitor_factor = self.calculate_competitor_factor(hotel_id, base_price)
        
        # Calculate luxury factor based on hotel rating
        luxury_factor = 1.0 + (hotel_rating - 3.0) * 0.15
        
        # Calculate final price
        dynamic_price = base_price * season_factor * demand_factor * event_factor * competitor_factor * luxury_factor
        
        # Create pricing factors object
        pricing_factors = {
            "season_factor": round(season_factor, 2),
            "demand_factor": round(demand_factor, 2),
            "event_factor": round(event_factor, 2),
            "competitor_factor": round(competitor_factor, 2),
            "luxury_factor": round(luxury_factor, 2)
        }
        
        return round(dynamic_price, 2), pricing_factors
    
    def generate_price_forecast(self, hotel_id, hotel_rating=4.0, days=7):
        """Generate price forecast for the next X days."""
        forecast = []
        today = datetime.now()
        
        for i in range(days):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # Add some randomness for each day
            variation = random.uniform(0.95, 1.05)
            
            price, factors = self.calculate_price(hotel_id, hotel_rating, date_str)
            price = price * variation
            
            forecast.append({
                "date": date_str,
                "price": round(price, 2),
                "factors": factors
            })
            
        return forecast
