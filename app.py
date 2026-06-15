import streamlit as st
import requests
import joblib
import numpy as np

# Load model
model = joblib.load("weather_model.pkl")

weather_labels = {
    0: "drizzle",
    1: "fog",
    2: "rain",
    3: "snow",
    4: "sun"
}

st.set_page_config(page_title="AI Weather Forecasting")

st.title("🌦 AI Powered Weather Forecasting System")
st.write("Developed by Mr. Upendra Kushwaha")

city = st.text_input("Enter City Name")

if st.button("Predict Weather"):

    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"

    geo_data = requests.get(geo_url).json()

    if "results" in geo_data:

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,wind_speed_10m"
        )

        weather_data = requests.get(weather_url).json()

        temp = weather_data["current"]["temperature_2m"]
        wind = weather_data["current"]["wind_speed_10m"]

        precipitation = 0
        temp_max = temp
        temp_min = temp - 3

        input_data = np.array([
            [precipitation, temp_max, temp_min, wind]
        ])

        prediction = model.predict(input_data)[0]

        result = weather_labels[int(prediction)]

        st.success(f"Predicted Weather: {result.upper()}")

        st.write(f"🌡 Temperature: {temp} °C")
        st.write(f"💨 Wind Speed: {wind} km/h")

        if result == "rain":
            st.image("https://cdn-icons-png.flaticon.com/512/3351/3351979.png")

        elif result == "sun":
            st.image("https://cdn-icons-png.flaticon.com/512/869/869869.png")

        elif result == "fog":
            st.image("https://cdn-icons-png.flaticon.com/512/4005/4005901.png")

        elif result == "snow":
            st.image("https://cdn-icons-png.flaticon.com/512/642/642102.png")

        elif result == "drizzle":
            st.image("https://cdn-icons-png.flaticon.com/512/414/414974.png")

    else:
        st.error("City not found")
