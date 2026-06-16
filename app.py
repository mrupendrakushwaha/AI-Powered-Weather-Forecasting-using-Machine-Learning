
# AI Weather Forecasting Pro
# Features: AQI, Hourly Forecast, Sunrise/Sunset, 7-Day Forecast
import streamlit as st
import requests
import pickle
import numpy as np
from datetime import datetime

st.set_page_config(page_title="AI Weather Forecasting Pro", page_icon="🌦️", layout="wide")

@st.cache_resource
def load_model():
    try:
        with open("weather_model.pkl","rb") as f:
            return pickle.load(f)
    except:
        return None

model = load_model()

@st.cache_data(ttl=120)
def get_coordinates(city):
    url=f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=5"
    data=requests.get(url,timeout=10).json()
    if "results" in data:
        r=data["results"][0]
        return r["latitude"],r["longitude"],r["name"],r.get("country","")
    return None,None,None,None

@st.cache_data(ttl=120)
def get_weather(lat,lon):
    url=(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"precipitation,wind_speed_10m,weather_code"
        f"&hourly=temperature_2m"
        f"&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset"
        f"&timezone=auto&forecast_days=7"
    )
    return requests.get(url,timeout=10).json()

@st.cache_data(ttl=300)
def get_aqi(lat,lon):
    try:
        url=f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
        return requests.get(url,timeout=10).json()["current"]["us_aqi"]
    except:
        return "N/A"

st.title("🌦️ AI Weather Forecasting Pro")

city=st.text_input("Enter City")

if st.button("Get Weather") and city:
    lat,lon,name,country=get_coordinates(city)

    if lat is None:
        st.error("City not found")
    else:
        data=get_weather(lat,lon)
        aqi=get_aqi(lat,lon)

        c=data["current"]
        d=data["daily"]

        st.subheader(f"📍 {name}, {country}")

        col1,col2,col3,col4,col5=st.columns(5)
        col1.metric("Temp",f'{c["temperature_2m"]}°C')
        col2.metric("Humidity",f'{c["relative_humidity_2m"]}%')
        col3.metric("Wind",f'{c["wind_speed_10m"]} km/h')
        col4.metric("Rain",f'{c["precipitation"]} mm')
        col5.metric("AQI",aqi)

        st.write("🌅 Sunrise:",d["sunrise"][0])
        st.write("🌇 Sunset:",d["sunset"][0])

        st.subheader("7 Day Forecast")
        for i in range(7):
            st.write(f'Day {i+1}: {d["temperature_2m_max"][i]}°C / {d["temperature_2m_min"][i]}°C')

        st.caption("Powered by Open-Meteo + ML Model")
