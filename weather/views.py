from django.shortcuts import render
import requests
from users.models import UserProfile
from datetime import datetime

def weather_view(request):
    profile = UserProfile.objects.get(user=request.user)
    city = request.GET.get('city') or profile.location or 'Delhi'

    try:
        api_key = '96abd0e67bb4f6b8bef607889abde06f'
        
        # Current Weather
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
        current_response = requests.get(current_url)
        weather_data = current_response.json()
        
        if weather_data.get("cod") != 200:
            raise ValueError("City not found")
        
        # Get coordinates for forecast
        lat = weather_data['coord']['lat']
        lon = weather_data['coord']['lon']
        
        # 7-Day Forecast (using One Call API)
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()
        
        # Process forecast data - get one entry per day (at noon)
        daily_forecast = []
        seen_dates = set()
        
        for item in forecast_data['list']:
            # Get date from timestamp
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            # Only take one forecast per day (around noon time)
            if date not in seen_dates and len(daily_forecast) < 7:
                seen_dates.add(date)
                daily_forecast.append({
                    'date': datetime.fromtimestamp(item['dt']).strftime('%a, %b %d'),
                    'temp_max': round(item['main']['temp_max']),
                    'temp_min': round(item['main']['temp_min']),
                    'description': item['weather'][0]['description'].title(),
                    'icon': item['weather'][0]['icon'],
                    'humidity': item['main']['humidity'],
                    'wind_speed': round(item['wind']['speed'], 1)
                })
        
        return render(request, 'weather.html', {
            'weather_data': weather_data,
            'forecast': daily_forecast
        })
        
    except Exception as e:
        return render(request, 'weather.html', {'error': str(e)})