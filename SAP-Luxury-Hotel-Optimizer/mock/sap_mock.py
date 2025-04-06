import json
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

class SAPMockGenerator:
    def __init__(self):
        self.hotels = []
        self.bookings = []
        self.events = []
        self.competitors = []

    def generate_hotels(self, count=300):
        """Generate mock hotel properties."""
        countries = ["USA", "France", "Germany", "Japan", "Australia"]
        for i in range(count):
            hotel = {
                "hotel_id": f"HOTEL{i+1:04d}",
                "name": f"{fake.company()} Hotel",
                "location": fake.city(),
                "country": random.choice(countries),
                "rooms": random.randint(50, 500),
                "rating": round(random.uniform(3.0, 5.0), 1)
            }
            self.hotels.append(hotel)
        return self.hotels

    def generate_bookings(self):
        """Generate mock booking trends."""
        for hotel in self.hotels:
            for day in range(30):  # Simulate bookings for the next 30 days.
                booking = {
                    "hotel_id": hotel["hotel_id"],
                    "date": fake.date_between(start_date="today", end_date="+30d").strftime("%Y-%m-%d"),
                    "bookings": random.randint(10, hotel["rooms"] // 2)
                }
                self.bookings.append(booking)
        return self.bookings

    def generate_events(self):
        """Generate mock local events."""
        event_types = ["Conference", "Concert", "Festival", "Sports Event"]
        for _ in range(50):
            today = datetime.now()
            event_date = today + timedelta(days=random.randint(0, 6))  # 0-6 days from now
            date_str = event_date.strftime("%Y-%m-%d")
            # Create event with this date
            event = {
                "event_id": f"EVENT{random.randint(1000, 9999)}",
                "name": f"{random.choice(event_types)} in {fake.city()}",
                "date": fake.date_between(start_date="today", end_date="+30d").strftime("%Y-%m-%d"),
                "location": fake.city(),
                "expected_attendance": random.randint(500, 5000)
            }
            self.events.append(event)
        return self.events

    def generate_competitors(self):
        """Generate mock competitor pricing."""
        for hotel in self.hotels:
            competitor = {
                "hotel_id": hotel["hotel_id"],
                "competitor_price": round(random.uniform(80, 500), 2)
            }
            self.competitors.append(competitor)
        return self.competitors

    def export_to_json(self, base_path="data"):
        """Export all generated data to JSON files."""
        with open(f"{base_path}/hotels.json", "w") as f:
            json.dump(self.hotels, f, indent=2)

        with open(f"{base_path}/bookings.json", "w") as f:
            json.dump(self.bookings, f, indent=2)

        with open(f"{base_path}/events.json", "w") as f:
            json.dump(self.events, f, indent=2)

        with open(f"{base_path}/competitors.json", "w") as f:
            json.dump(self.competitors, f, indent=2)

# For standalone execution.
if __name__ == "__main__":
    generator = SAPMockGenerator()
    generator.generate_hotels()
    generator.generate_bookings()
    generator.generate_events()
    generator.generate_competitors()
    generator.export_to_json()
    print("Mock data generated successfully!")

