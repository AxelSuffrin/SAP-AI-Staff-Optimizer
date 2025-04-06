import random
from datetime import datetime, timedelta

class StaffingEngine:
    """
    Simulates an AI-powered staffing optimization engine that would
    typically be implemented using SAP's AI technologies.
    """
    
    def __init__(self, bookings, hotels, events):
        self.bookings = bookings
        self.hotels = hotels
        self.events = events
        
    def get_hotel_details(self, hotel_id):
        """Get details for a specific hotel."""
        return next((h for h in self.hotels if h["hotel_id"] == hotel_id), None)
        
    def get_hotel_bookings(self, hotel_id):
        """Get all bookings for a specific hotel."""
        return [b for b in self.bookings if b["hotel_id"] == hotel_id]
    
    def get_nearby_events(self, location, date=None):
        """Get events near a specific location and optionally on a specific date."""
        nearby_events = [e for e in self.events if e["location"] == location]
        if date:
            nearby_events = [e for e in nearby_events if e["date"] == date]
        return nearby_events
    
    def calculate_base_staffing(self, hotel):
        """Calculate base staffing needs based on hotel size."""
        if not hotel:
            return {
                "front_desk": 3,
                "housekeeping": 10,
                "concierge": 2,
                "restaurant": 6,
                "maintenance": 3
            }
            
        rooms = hotel["rooms"]
        
        # Base staffing calculation
        front_desk = max(2, round(rooms / 100) + 1)
        housekeeping = max(5, round(rooms / 15))
        concierge = max(1, round(rooms / 150))
        restaurant = max(4, round(rooms / 50))
        maintenance = max(2, round(rooms / 125))
        
        return {
            "front_desk": front_desk,
            "housekeeping": housekeeping,
            "concierge": concierge,
            "restaurant": restaurant,
            "maintenance": maintenance
        }
    
    def calculate_occupancy_factor(self, hotel_bookings, hotel_rooms):
        """Calculate occupancy factor based on bookings."""
        if not hotel_bookings or not hotel_rooms:
            return 1.0
            
        # Average bookings
        avg_bookings = sum(b["bookings"] for b in hotel_bookings) / len(hotel_bookings)
        
        # Occupancy percentage
        occupancy = min(1.0, avg_bookings / hotel_rooms)
        
        # Staffing doesn't scale linearly with occupancy - there's a base level needed
        return 0.7 + (0.6 * occupancy)
    
    def calculate_event_staffing_factor(self, nearby_events):
        """Calculate additional staffing needs based on local events."""
        if not nearby_events:
            return 1.0
            
        # Calculate based on total expected attendance
        total_attendance = sum(e["expected_attendance"] for e in nearby_events)
        
        # Give events much more weight in staffing decisions
        # Increase from 1.0-1.3 range to 1.15-1.5 range
        return 1.15 + min(total_attendance / 15000, 0.35)
    
    def calculate_weekend_factor(self, date_str=None):
        """Calculate weekend factor - more staff needed on weekends."""
        if not date_str:
            date = datetime.now()
        else:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
        # Weekend is Friday, Saturday, Sunday
        if date.weekday() >= 4:  # Friday, Saturday, Sunday
            return 1.15
        return 1.0
    
    def calculate_staffing(self, hotel_id, date_str=None):
        """Calculate optimized staffing levels for a hotel."""
        # Get hotel details
        hotel = self.get_hotel_details(hotel_id)
        if not hotel:
            return None
            
        # Get relevant data
        hotel_bookings = self.get_hotel_bookings(hotel_id)
        
        # Base staffing needs
        base_staffing = self.calculate_base_staffing(hotel)
        
        # Calculate staffing factors
        occupancy_factor = self.calculate_occupancy_factor(hotel_bookings, hotel["rooms"])
        weekend_factor = self.calculate_weekend_factor(date_str)
        
        # Event factor depends on hotel location
        event_factor = 1.0
        nearby_events = self.get_nearby_events(hotel["location"], date_str)
        event_factor = self.calculate_event_staffing_factor(nearby_events)
        
        # Seasonal factor - more staff in high season
        seasonal_factor = 1.0
        if not date_str:
            date = datetime.now()
        else:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
        if date.month in [6, 7, 8, 12]:  # Summer and December
            seasonal_factor = 1.1
        
        # Generate staffing forecast for next 7 days
        forecast = []
        today = datetime.now()
        
        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # Update factors for each day
            weekend_factor = self.calculate_weekend_factor(date_str)
            nearby_events = self.get_nearby_events(hotel["location"], date_str)
            event_factor = self.calculate_event_staffing_factor(nearby_events)
            
            # Daily variation in occupancy
            daily_occupancy = occupancy_factor * random.uniform(0.9, 1.1)
            
            # Calculate staff for each department with slight random variation
            daily_staffing = {}
            for dept, base in base_staffing.items():
                # Different departments are affected differently by factors
                if dept == "front_desk":
                    factor = occupancy_factor * weekend_factor * event_factor * 1.05
                elif dept == "housekeeping":
                    factor = daily_occupancy * 1.1
                elif dept == "concierge":
                    factor = event_factor * weekend_factor * 1.2  # Increased from 1.1
                elif dept == "restaurant":
                    factor = occupancy_factor * weekend_factor * event_factor * 1.2  # Added multiplier
                else:  # maintenance
                    factor = seasonal_factor * 0.95
                    
                # Calculate staff needed
                staff = round(base * factor)
                
                # Ensure minimum staffing
                if dept == "front_desk":
                    staff = max(2, staff)
                elif dept == "housekeeping":
                    staff = max(5, staff)
                elif dept == "maintenance":
                    staff = max(2, staff)
                    
                daily_staffing[dept] = staff
            
            # Are there events on this day?
            day_events = [e["name"] for e in nearby_events]
            
            forecast.append({
                "date": date_str,
                "staffing": daily_staffing,
                "total_staff": sum(daily_staffing.values()),
                "events": day_events
            })
        
        # Create staffing explanation
        explanation = generate_staffing_explanation(hotel, occupancy_factor, event_factor, weekend_factor)
        
        # Calculate total costs with dummy hourly rates
        hourly_rates = {
            "front_desk": 18,
            "housekeeping": 15,
            "concierge": 22,
            "restaurant": 17,
            "maintenance": 20
        }
        
        total_weekly_cost = 0
        for day in forecast:
            daily_cost = 0
            for dept, staff in day["staffing"].items():
                dept_cost = staff * hourly_rates[dept] * 8  # 8-hour shifts
                daily_cost += dept_cost
            day["daily_cost"] = daily_cost
            total_weekly_cost += daily_cost
            
        # Return comprehensive staffing data
        return {
            "hotel_id": hotel_id,
            "hotel_name": hotel["name"],
            "location": hotel["location"], 
            "rooms": hotel["rooms"],
            "staffing_factors": {
                "occupancy_factor": round(occupancy_factor, 2),
                "event_factor": round(event_factor, 2),
                "weekend_factor": round(weekend_factor, 2),
                "seasonal_factor": round(seasonal_factor, 2)
            },
            "forecast": forecast,
            "total_weekly_cost": total_weekly_cost,
            "hourly_rates": hourly_rates,
            "explanation": explanation
        }

def generate_staffing_explanation(hotel, occupancy_factor, event_factor, weekend_factor):
    """Generate human-readable explanation for staffing recommendations"""
    explanation = f"Staffing recommendations for {hotel['name']} are based on: "
    
    factors = []
    if occupancy_factor > 1.1:
        factors.append("high projected occupancy rates")
    elif occupancy_factor < 0.9:
        factors.append("lower than average occupancy")
    
    if event_factor > 1.1:
        factors.append("increased demand due to local events")
    
    if weekend_factor > 1.0:
        factors.append("weekend staffing requirements")
    
    explanation += ", ".join(factors)
    
    additional = ""
    if occupancy_factor > 1.1 and event_factor > 1.1:
        additional = " We recommend particular attention to concierge and restaurant staffing to maintain service levels during this high-demand period."
    elif occupancy_factor < 0.9:
        additional = " This provides an opportunity to optimize labor costs while maintaining essential service levels."
    
    return explanation + "." + additional
