import streamlit as st
import requests

st.set_page_config(page_title="AI Weather Forecasting")

st.title("🌦 AI Powered Weather Forecasting System")
st.write("Developed by Mr. Upendra Kushwaha")

city = st.text_input("Enter City Name")

weather_codes = {
    0: "SUN",
    1: "SUN",
    2: "PARTLY CLOUDY",
    3: "CLOUDY",
    45: "FOG",
    48: "FOG",
    51: "DRIZZLE",
    53: "DRIZZLE",
    55: "DRIZZLE",
    61: "RAIN",
    63: "RAIN",
    65: "RAIN",
    71: "SNOW",
    73: "SNOW",
    75: "SNOW",
    95: "THUNDERSTORM"
}

if st.button("Predict Weather"):

    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_data = requests.get(geo_url).json()

    if "results" in geo_data:

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,wind_speed_10m,weather_code"
        )

        data = requests.get(weather_url).json()

        temp = data["current"]["temperature_2m"]
        wind = data["current"]["wind_speed_10m"]
        code = data["current"]["weather_code"]

        result = weather_codes.get(code, "UNKNOWN")

        st.success(f"Weather Condition: {result}")
        st.write(f"🌡 Temperature: {temp} °C")
        st.write(f"💨 Wind Speed: {wind} km/h")

        if "SUN" in result:
            st.image("https://cdn-icons-png.flaticon.com/512/869/869869.png")

        elif "FOG" in result:
            st.image("https://cdn-icons-png.flaticon.com/512/4005/4005901.png")

        elif "RAIN" in result:
            st.image("https://cdn-icons-png.flaticon.com/512/3351/3351979.png")

        elif "SNOW" in result:
            st.image("https://cdn-icons-png.flaticon.com/512/642/642102.png")

        elif "DRIZZLE" in result:
            st.image("https://cdn-icons-png.flaticon.com/512/414/414974.png")

    else:
        st.error("City not found")
