"""
Add mock GPS tracking data to existing loads for demo purposes.
Uses OSRM (Open Source Routing Machine) to generate realistic routes that follow actual roads.
"""

from datetime import datetime, timedelta
import random
import requests
from app.database import SessionLocal
from app.models import Load

# Real city coordinates for realistic routes across the US
LOCATIONS = {
    # Fuel Terminals (Origin points)
    "Houston Terminal": {"lat": 29.7604, "lng": -95.3698, "address": "1234 Port Blvd, Houston, TX 77002"},
    "Atlanta Terminal": {"lat": 33.7490, "lng": -84.3880, "address": "5678 Hartsfield Rd, Atlanta, GA 30320"},
    "Dallas Terminal": {"lat": 32.7767, "lng": -96.7970, "address": "9101 Commerce St, Dallas, TX 75202"},
    "Memphis Terminal": {"lat": 35.1495, "lng": -90.0490, "address": "3456 Depot Ave, Memphis, TN 38103"},
    "Chicago Terminal": {"lat": 41.8781, "lng": -87.6298, "address": "2200 Industrial Pkwy, Chicago, IL 60616"},
    "Los Angeles Terminal": {"lat": 33.7701, "lng": -118.1937, "address": "1500 Harbor Blvd, Los Angeles, CA 90731"},
    "New Orleans Terminal": {"lat": 29.9511, "lng": -90.0715, "address": "7800 River Rd, New Orleans, LA 70131"},
    "Phoenix Terminal": {"lat": 33.4484, "lng": -112.0740, "address": "3200 S 24th St, Phoenix, AZ 85034"},
    "San Antonio Terminal": {"lat": 29.4241, "lng": -98.4936, "address": "1500 E Commerce St, San Antonio, TX 78205"},

    # Gas Station Sites (Destination points) - Spread across different regions
    "SITE001": {"lat": 33.7490, "lng": -84.3880, "address": "100 Peachtree St NE, Atlanta, GA 30303"},  # Downtown Gas Station
    "SITE002": {"lat": 32.7555, "lng": -97.3308, "address": "4500 Highway 287, Fort Worth, TX 76117"},  # Highway Stop #42
    "SITE003": {"lat": 29.5500, "lng": -95.0900, "address": "8900 Bay Area Blvd, Houston, TX 77058"},  # Suburban Fuel Center
    "SITE004": {"lat": 33.9425, "lng": -118.4081, "address": "6201 W Imperial Hwy, Los Angeles, CA 90045"},  # Airport Fuel Depot
    "SITE005": {"lat": 41.7300, "lng": -87.7040, "address": "3300 S Cicero Ave, Chicago, IL 60623"},  # Industrial Park Station

    # Additional site codes that might be in the database
    "SITE-ATL-001": {"lat": 33.7490, "lng": -84.3880, "address": "100 Peachtree St NE, Atlanta, GA 30303"},
    "SITE-DFW-001": {"lat": 32.7555, "lng": -97.3308, "address": "4500 Highway 287, Fort Worth, TX 76117"},
    "SITE-HOU-001": {"lat": 29.5500, "lng": -95.0900, "address": "8900 Bay Area Blvd, Houston, TX 77058"},
    "SITE-LAX-001": {"lat": 33.9425, "lng": -118.4081, "address": "6201 W Imperial Hwy, Los Angeles, CA 90045"},
    "SITE-CHI-001": {"lat": 41.7300, "lng": -87.7040, "address": "3300 S Cicero Ave, Chicago, IL 60623"},
}


def get_route_from_osrm(origin, destination):
    """
    Get actual road route from OSRM public API.

    Args:
        origin: Dict with lat/lng
        destination: Dict with lat/lng

    Returns:
        List of [lng, lat] coordinates along the route, or None if failed
    """
    try:
        # OSRM expects lng,lat format
        url = f"http://router.project-osrm.org/route/v1/driving/{origin['lng']},{origin['lat']};{destination['lng']},{destination['lat']}"
        params = {
            'overview': 'full',  # Get full route geometry
            'geometries': 'geojson'  # Return as GeoJSON
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data['code'] == 'Ok' and data['routes']:
            # Extract coordinates from GeoJSON geometry
            coordinates = data['routes'][0]['geometry']['coordinates']
            return coordinates  # Returns [[lng, lat], [lng, lat], ...]

        return None

    except Exception as e:
        print(f"  OSRM API error: {e}")
        return None


def interpolate_route(origin, destination, num_points=10, progress=0.5):
    """
    Generate GPS points along a route from origin to destination.
    Uses OSRM to follow actual roads when possible, falls back to linear interpolation.

    Args:
        origin: Dict with lat/lng
        destination: Dict with lat/lng
        num_points: Number of tracking points to generate
        progress: How far along the route (0.0 to 1.0)

    Returns:
        List of tracking points with lat, lng, timestamp, speed
    """
    points = []
    now = datetime.utcnow()

    # Calculate total points based on progress
    actual_points = int(num_points * progress)

    if actual_points == 0:
        return []

    # Try to get real route from OSRM
    route_coords = get_route_from_osrm(origin, destination)

    if route_coords:
        # Use OSRM route - sample points along it
        total_route_points = len(route_coords)
        total_distance_to_cover = int(total_route_points * progress)

        # Sample evenly along the completed portion of the route
        for i in range(actual_points):
            idx = int((i / actual_points) * total_distance_to_cover)
            idx = min(idx, total_route_points - 1)

            lng, lat = route_coords[idx]  # OSRM returns [lng, lat]

            # Timestamp going backwards from now
            timestamp = now - timedelta(hours=(actual_points - i) * 0.5)

            # Random speed between 55-70 mph (typical highway speeds)
            speed = random.randint(55, 70)

            points.append({
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "timestamp": timestamp.isoformat(),
                "speed": speed
            })
    else:
        # Fallback to linear interpolation if OSRM fails
        print("  Falling back to linear interpolation")
        for i in range(actual_points):
            ratio = i / num_points
            lat = origin['lat'] + (destination['lat'] - origin['lat']) * ratio
            lng = origin['lng'] + (destination['lng'] - origin['lng']) * ratio

            # Add some random variation
            lat += random.uniform(-0.02, 0.02)
            lng += random.uniform(-0.02, 0.02)

            timestamp = now - timedelta(hours=(actual_points - i) * 0.5)
            speed = random.randint(55, 70)

            points.append({
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "timestamp": timestamp.isoformat(),
                "speed": speed
            })

    return points


def add_tracking_to_loads():
    """Add mock tracking data to all active loads."""
    db = SessionLocal()

    try:
        loads = db.query(Load).filter(
            Load.status.in_(['scheduled', 'in_transit'])
        ).all()

        print(f"Found {len(loads)} active loads")

        for load in loads:
            # Determine origin and destination
            origin_key = load.origin_terminal or "Houston Terminal"

            # Get destination from site
            if load.destination_site:
                dest_key = load.destination_site.consignee_code
            else:
                dest_key = "SITE-ATL-001"

            origin = LOCATIONS.get(origin_key, LOCATIONS["Houston Terminal"])
            destination = LOCATIONS.get(dest_key, LOCATIONS["SITE001"])

            # Generate tracking points based on status
            if load.status == 'in_transit':
                progress = random.uniform(0.3, 0.8)  # 30-80% complete
                num_points = 20
            else:  # scheduled
                progress = 0.0  # Not started yet
                num_points = 0

            tracking_points = interpolate_route(origin, destination, num_points, progress)

            # Update load
            load.tracking_points = tracking_points
            load.origin_address = origin.get('address', '')
            load.destination_address = destination.get('address', '')

            # Set shipped_at for in_transit loads
            if load.status == 'in_transit':
                load.shipped_at = datetime.utcnow() - timedelta(hours=random.randint(2, 12))

            print(f"  Updated {load.po_number}: {len(tracking_points)} tracking points")

        db.commit()
        print(f"\nSuccessfully added tracking data to {len(loads)} loads")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_tracking_to_loads()
