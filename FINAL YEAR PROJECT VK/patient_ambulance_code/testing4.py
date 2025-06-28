import serial
import requests
import time
import folium
from openrouteservice import Client
import geocoder

# 🔹 Replace with your API Keys
GEOAPIFY_API_KEY = "929484060a4346e7be2db28f35176fa8" 
THING_SPEAK_API_KEY = "5HHH886RFYQDMKOK"
GEOAPIFY_GC_KEY = "08aa362babe543c8a5f1d0219eae7e24"
ORS_API_KEY = "5b3ce3597851110001cf6248bccb776c74de40c3b9692f34efca4f4e"
TOMTOM_API_KEY = "1MiQ5XvGvGIa4OJ2qxeJcAWWkbAqrpMB"
SERIAL_PORT = "COM5"
BAUD_RATE = 115200  

# Function to get location
def get_location():
    # Get accurate location using GPS
    g = geocoder.ip('me')  # Fetch GPS-based location
    if g.latlng:
        latitude, longitude = g.latlng
    else:
        print("❌ Error fetching GPS-based location")
        return None, None

    # Reverse Geocoding to get address
    geoapify_url = f"https://api.geoapify.com/v1/geocode/reverse?lat={latitude}&lon={longitude}&apiKey={GEOAPIFY_GC_KEY}"
    response = requests.get(geoapify_url)

    if response.status_code == 200:
        data = response.json()
        if data.get("features"):
            address = data["features"][0]["properties"].get("formatted", "Unknown Address")
            city = data["features"][0]["properties"].get("city", "Unknown City")
            country = data["features"][0]["properties"].get("country", "Unknown Country")

            print(f"\n📍 Location Identified!")
            print(f"🏙 City: {city}, 🌍 Country: {country}")
            print(f"🗺 Coordinates: {latitude}, {longitude}")
            print(f"🏠 Address: {address}\n")
            return latitude, longitude
        else:
            print("❌ No address data found")
            return latitude, longitude
    else:
        print("❌ Error fetching address data")
        return latitude, longitude


# Function to find nearest hospitals
def get_nearest_hospitals(coords):
    url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital&filter=circle:{coords[1]},{coords[0]},7500&bias=proximity:{coords[1]},{coords[0]}&limit=10&apiKey={GEOAPIFY_API_KEY}"
    response = requests.get(url)
    hospitals = response.json().get("features", [])
    
    if not hospitals:
        print("🚨 No hospitals found in your area. Skipping to patient monitoring...\n")
        return []
    
    hospital_list = []
    for hospital in hospitals:
        name = hospital["properties"].get("name", "Unknown Hospital")
        lat = hospital["geometry"]["coordinates"][1]
        lon = hospital["geometry"]["coordinates"][0]
        hospital_list.append({"name": name, "lat": lat, "lon": lon})
    return hospital_list

# Function to get hospital details with retry mechanism
def get_hospital_details(ambulance, hospitals):
    ors_client = Client(key=ORS_API_KEY)
    best_hospital = None
    min_time = float('inf')
    min_distance = float('inf')
    
    for hospital in hospitals:
        coords = [[ambulance[1], ambulance[0]], [hospital["lon"], hospital["lat"]]]
        
        # Retry mechanism for ORS API calls
        for attempt in range(3):  # Retry up to 3 times
            try:
                route = ors_client.directions(coordinates=coords, profile='driving-car', format='geojson')
                break  # If successful, exit retry loop
            except Exception as e:
                print(f"⚠ ORS API Rate Limit Exceeded. Retrying in 60s... (Attempt {attempt+1}/3)")
                time.sleep(60)  # Wait for 60 seconds before retrying
        else:
            print("❌ Failed to fetch ORS route after 3 attempts. Skipping hospital.")
            continue  # Skip this hospital and move to the next
        
        distance = route["features"][0]["properties"]["segments"][0]["distance"] / 1000  
        duration = route["features"][0]["properties"]["segments"][0]["duration"] / 60  
        
        traffic_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={TOMTOM_API_KEY}&point={hospital['lat']},{hospital['lon']}"
        traffic_response = requests.get(traffic_url).json()
        traffic_speed = traffic_response.get("flowSegmentData", {}).get("currentSpeed", 0)
        traffic_status = "High" if traffic_speed < 20 else "Moderate" if 20 <= traffic_speed <= 40 else "Low"
        
        hospital["distance_km"] = round(distance, 2)
        hospital["duration_min"] = round(duration, 2)
        hospital["traffic"] = traffic_status
        
        if best_hospital is None or duration < min_time or (duration == min_time and distance < min_distance):
            min_time = duration
            min_distance = distance
            best_hospital = hospital
    
    return best_hospital, hospitals

# Function to generate an interactive map
def generate_map(ambulance, best_hospital):
    m = folium.Map(location=ambulance, zoom_start=14)
    folium.Marker(location=ambulance, popup="🚑 Ambulance", icon=folium.Icon(color='blue')).add_to(m)
    
    if best_hospital:
        folium.Marker(location=(best_hospital["lat"], best_hospital["lon"]), popup=f'🏥 {best_hospital["name"]}', icon=folium.Icon(color='red')).add_to(m)
        ors_client = Client(key=ORS_API_KEY)
        coords = [[ambulance[1], ambulance[0]], [best_hospital["lon"], best_hospital["lat"]]]
        route = ors_client.directions(coordinates=coords, profile='driving-car', format='geojson')
        steps = route["features"][0]["properties"]["segments"][0]["steps"]
        directions = "<br>".join([f'Step {i+1}: {step["instruction"]}' for i, step in enumerate(steps)])
        
        # Realistic Route on Map
        route_coords = [(point[1], point[0]) for point in route["features"][0]["geometry"]["coordinates"]]
        route_line = folium.PolyLine(route_coords, color='black', weight=5, opacity=0.7)
        route_popup = folium.Popup(directions, parse_html=True, max_width=450)
        route_line.add_child(route_popup)
        m.add_child(route_line)
    
    m.save("ambulance_route.html")
    print("📌 Map saved as ambulance_route.html")
   

# Execution
latitude, longitude = get_location()
if latitude and longitude:
    hospitals = get_nearest_hospitals((latitude, longitude))
    if hospitals:
        best_hospital, updated_hospitals = get_hospital_details((latitude, longitude), hospitals)
        print("Top 10 Nearest Hospitals \n")
        for h in updated_hospitals:
            print(f'🏥 {h["name"]} - {h["distance_km"]} km, ⏳ {h["duration_min"]} min, 🚦 Traffic: {h["traffic"]}')
    while hospitals:
        best_hospital, updated_hospitals = get_hospital_details((latitude, longitude), hospitals)       
        print(f'⭐ Best Hospital: {best_hospital["name"]} - {best_hospital["duration_min"]} min')
        user_response = input("Is this hospital acceptable? (yes/no): ").strip().lower()
        
        if user_response == "yes":
            generate_map((latitude, longitude), best_hospital)
            break
        else:
            hospitals.remove(best_hospital)

        if not hospitals:
            print("No suitable hospital found 🥺...")
print("\n")

# Open Serial Connection
try:
    Arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
except Exception as e:
    print("🚨 Error: Could not connect to Arduino.", e)
    exit()

count = 0
while count < 15:
    try:
        data = Arduino.readline().decode().strip()
        if data:
            values = data.split(',')
            if len(values) == 4:
                temp, humidity, ecg, pulse = values
                count += 1
                print(f'📊 Patient Vitals {count}/15: 🌡 {temp}°C | 💧 {humidity}% | 💓 {ecg} | ❤ {pulse} BPM')
                url = f"https://api.thingspeak.com/update?api_key={THING_SPEAK_API_KEY}&field1={temp}&field2={humidity}&field3={ecg}&field4={pulse}"
                response = requests.get(url)
                print("📡 ThingSpeak Update Success! ✅" if response.text != "0" else "⚠ ThingSpeak Update Failed!")
        time.sleep(15)
    except Exception as e:
        print("⚠ Error:", e)

print("✅ Data upload completed! 🎉 Exiting program.")
