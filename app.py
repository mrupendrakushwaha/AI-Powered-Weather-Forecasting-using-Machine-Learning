import streamlit as st
import requests
import pickle
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Weather Forecasting",
    page_icon="🌦️",
    layout="wide"
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
    }

    /* Main title */
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #56CCF2, #2F80ED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #aaa;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Weather card */
    .weather-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .weather-card h2 {
        font-size: 1.1rem;
        color: #ccc;
        margin-bottom: 0.3rem;
    }
    .weather-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: white;
    }
    .weather-card .unit {
        font-size: 0.85rem;
        color: #aaa;
    }

    /* Condition badge */
    .condition-badge {
        display: inline-block;
        background: linear-gradient(90deg, #2F80ED, #56CCF2);
        color: white;
        font-size: 1.6rem;
        font-weight: 800;
        padding: 0.5rem 2rem;
        border-radius: 50px;
        margin: 1rem 0;
        letter-spacing: 2px;
    }

    /* Forecast card */
    .forecast-card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1rem 0.5rem;
        text-align: center;
        margin: 0.2rem;
    }
    .forecast-day { font-size: 0.85rem; color: #aaa; }
    .forecast-icon { font-size: 1.8rem; margin: 0.3rem 0; }
    .forecast-temp { font-size: 1rem; font-weight: 700; color: white; }
    .forecast-cond { font-size: 0.75rem; color: #88aaff; margin-top: 0.2rem; }

    /* Alert box */
    .alert-box {
        background: rgba(255,80,80,0.15);
        border: 1px solid rgba(255,80,80,0.4);
        border-radius: 12px;
        padding: 0.8rem 1.2rem;
        color: #ff9999;
        font-weight: 600;
        margin: 0.5rem 0;
    }

    /* Section headers */
    .section-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #56CCF2;
        border-bottom: 1px solid rgba(86,204,242,0.3);
        padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────────────────
WEATHER_CODES = {
    0: ("SUN", "☀️"), 1: ("SUN", "🌤️"), 2: ("PARTLY CLOUDY", "⛅"),
    3: ("CLOUDY", "☁️"), 45: ("FOG", "🌫️"), 48: ("FOG", "🌫️"),
    51: ("DRIZZLE", "🌦️"), 53: ("DRIZZLE", "🌦️"), 55: ("DRIZZLE", "🌦️"),
    61: ("RAIN", "🌧️"), 63: ("RAIN", "🌧️"), 65: ("RAIN", "🌧️"),
    71: ("SNOW", "❄️"), 73: ("SNOW", "❄️"), 75: ("SNOW", "❄️"),
    95: ("THUNDERSTORM", "⛈️"), 96: ("THUNDERSTORM", "⛈️"), 99: ("THUNDERSTORM", "⛈️")
}

CONDITION_TO_LABEL = {"SUN": 0, "DRIZZLE": 1, "RAIN": 2, "SNOW": 3, "FOG": 4,
                      "PARTLY CLOUDY": 5, "CLOUDY": 6, "THUNDERSTORM": 7}
LABEL_TO_CONDITION = {v: k for k, v in CONDITION_TO_LABEL.items()}

# ─── Load ML Model ───────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        with open("weather_model.pkl", "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

model = load_model()

# ─── API Calls ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_coordinates(city):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        data = requests.get(url, timeout=10).json()
        if "results" in data:
            r = data["results"][0]
            return r["latitude"], r["longitude"], r.get("country", ""), r.get("name", city)
    except Exception:
        pass
    return None, None, None, None

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            &current=temperature_2m,relative_humidity_2m,apparent_temperature,
            precipitation,wind_speed_10m,weather_code,uv_index,cloud_cover
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,wind_speed_10m_max"
            f"&timezone=auto&forecast_days=7"
        )
        return requests.get(url, timeout=10).json()
    except Exception:
        return None

def ml_predict(precipitation, temp_max, temp_min, wind):
    """Use ML model if available, else fallback to rule-based."""
    if model is not None:
        try:
            features = np.array([[precipitation, temp_max, temp_min, wind]])
            pred = model.predict(features)[0]
            return LABEL_TO_CONDITION.get(int(pred), None)
        except Exception:
            pass
    return None

def get_alerts(temp, wind, precipitation):
    alerts = []
    if temp > 40:
        alerts.append("🔥 Extreme Heat Warning — Stay indoors, drink water!")
    elif temp < -5:
        alerts.append("🧊 Freezing Temperature — Dress warmly!")
    if wind > 60:
        alerts.append("💨 High Wind Alert — Avoid outdoor activities!")
    if precipitation > 10:
        alerts.append("🌊 Heavy Rain — Flooding possible in low areas!")
    return alerts

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🌦️ AI Weather Forecasting</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Powered by Machine Learning + Real-Time Data • by Mr. Upendra Kushwaha</div>', unsafe_allow_html=True)

# ─── Search Bar ─────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1])
with col_input:
    city = st.text_input("", placeholder="🔍  Enter city name (e.g. Mumbai, London, New York)...",
                         label_visibility="collapsed")
with col_btn:
    search = st.button("Get Weather", use_container_width=True, type="primary")

# ─── Main Logic ─────────────────────────────────────────────────────────────
if search and city.strip():
    lat, lon, country, city_name = get_coordinates(city.strip())

    if lat is None:
        st.error("❌ City not found. Please check the spelling and try again.")
    else:
        data = get_weather(lat, lon)

        if data is None:
            st.error("❌ Could not fetch weather data. Please try again.")
        else:
            curr = data["current"]
            daily = data["daily"]

            temp        = curr["temperature_2m"]
            feels_like  = curr["apparent_temperature"]
            humidity    = curr["relative_humidity_2m"]
            wind        = curr["wind_speed_10m"]
            precip      = curr["precipitation"]
            uv          = curr.get("uv_index", "N/A")
            cloud       = curr.get("cloud_cover", 0)

            # Weather condition
            cond_name, cond_icon = WEATHER_CODES.get(code, ("UNKNOWN", "🌡️"))
            if cloud > 60 and cond_name == "SUN":
                cond_name = "PARTLY CLOUDY"
                cond_icon = "⛅"

            # ML prediction (for the day's forecast features)
            temp_max_today = daily["temperature_2m_max"][0]
            temp_min_today = daily["temperature_2m_min"][0]
            ml_pred = ml_predict(precip, temp_max_today, temp_min_today, wind)

            # ── Location + Condition ──────────────────────────────────────
            st.markdown(f"### 📍 {city_name}, {country}")
            st.markdown(f'<div style="text-align:center"><span class="condition-badge">{cond_icon} {cond_name}</span></div>', unsafe_allow_html=True)

            if ml_pred and ml_pred != cond_name:
                st.info(f"🤖 **ML Model Prediction:** {ml_pred}  |  📡 **Live API:** {cond_name}")
            elif ml_pred:
                st.success(f"✅ ML Model & Live API both agree: **{ml_pred}**")

            # ── Alerts ────────────────────────────────────────────────────
            alerts = get_alerts(temp, wind, precip)
            for a in alerts:
                st.markdown(f'<div class="alert-box">{a}</div>', unsafe_allow_html=True)

            # ── Current Metrics ───────────────────────────────────────────
            st.markdown('<div class="section-header">📊 Current Conditions</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            metrics = [
                (c1, "🌡️ Temperature", f"{temp}°C", f"Feels {feels_like}°C"),
                (c2, "💧 Humidity", f"{humidity}%", "Relative"),
                (c3, "💨 Wind Speed", f"{wind} km/h", "Current"),
                (c4, "🌧️ Precipitation", f"{precip} mm", "Now"),
                (c5, "☀️ UV Index", str(uv), "Current"),
                (c6, "📈 Max Today", f"{temp_max_today}°C", f"Min {temp_min_today}°C"),
            ]
            for col, label, val, delta in metrics:
                with col:
                    st.markdown(f"""
                    <div class="weather-card">
                        <h2>{label}</h2>
                        <div class="value">{val}</div>
                        <div class="unit">{delta}</div>
                    </div>""", unsafe_allow_html=True)

            # ── 7-Day Forecast ────────────────────────────────────────────
            st.markdown('<div class="section-header">📅 7-Day Forecast</div>', unsafe_allow_html=True)
            fcols = st.columns(7)
            for i, col in enumerate(fcols):
                day_date =today = datetime.now(ZoneInfo("Asia/Kolkata"))  + timedelta(days=i)
                day_name = "Today" if i == 0 else day_date.strftime("%a")
                fc_code = daily["weather_code"][i]
                fc_cond, fc_icon = WEATHER_CODES.get(fc_code, ("?", "🌡️"))
                fc_max = daily["temperature_2m_max"][i]
                fc_min = daily["temperature_2m_min"][i]
                with col:
                    st.markdown(f"""
                    <div class="forecast-card">
                        <div class="forecast-day">{day_name}<br>{day_date.strftime("%d %b")}</div>
                        <div class="forecast-icon">{fc_icon}</div>
                        <div class="forecast-temp">{fc_max}° / {fc_min}°</div>
                        <div class="forecast-cond">{fc_cond}</div>
                    </div>""", unsafe_allow_html=True)

            # ── Temperature Chart ─────────────────────────────────────────
            st.markdown('<div class="section-header">📈 Temperature Trend (7 Days)</div>', unsafe_allow_html=True)
            days_labels = [(datetime.now() + timedelta(days=i)).strftime("%a %d") for i in range(7)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=days_labels, y=daily["temperature_2m_max"],
                name="Max Temp", mode="lines+markers",
                line=dict(color="#FF6B6B", width=3),
                marker=dict(size=8, color="#FF6B6B")
            ))
            fig.add_trace(go.Scatter(
                x=days_labels, y=daily["temperature_2m_min"],
                name="Min Temp", mode="lines+markers",
                line=dict(color="#56CCF2", width=3),
                marker=dict(size=8, color="#56CCF2"),
                fill="tonexty", fillcolor="rgba(86,204,242,0.1)"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), legend=dict(font=dict(color="white")),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="white"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="white",
                           title="Temperature (°C)"),
                margin=dict(l=10, r=10, t=10, b=10), height=320
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Precipitation Bar Chart ───────────────────────────────────
            st.markdown('<div class="section-header">🌧️ Precipitation Forecast (7 Days)</div>', unsafe_allow_html=True)
            fig2 = go.Figure(go.Bar(
                x=days_labels,
                y=daily["precipitation_sum"],
                marker_color=["#2F80ED" if v > 5 else "#56CCF2" for v in daily["precipitation_sum"]],
                name="Precipitation (mm)"
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="white"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="white",
                           title="Precipitation (mm)"),
                margin=dict(l=10, r=10, t=10, b=10), height=280
            )
            st.plotly_chart(fig2, use_container_width=True)

            # ── ML Feature Importance Info ────────────────────────────────
            if model is not None:
                st.markdown('<div class="section-header">🤖 ML Model Info</div>', unsafe_allow_html=True)
                try:
                    importances = model.feature_importances_
                    feat_names = ["Precipitation", "Temp Max", "Temp Min", "Wind Speed"]
                    fig3 = px.bar(
                        x=feat_names, y=importances,
                        labels={"x": "Feature", "y": "Importance"},
                        color=importances,
                        color_continuous_scale="Blues"
                    )
                    fig3.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="white"),
                        xaxis=dict(color="white"),
                        yaxis=dict(color="white", gridcolor="rgba(255,255,255,0.1)"),
                        coloraxis_showscale=False,
                        margin=dict(l=10, r=10, t=10, b=10), height=260
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                    st.caption("📌 Which features your trained Random Forest relies on most for weather prediction.")
                except Exception:
                    st.info("ML model loaded. Feature importance not available for this model type.")

         # ── Footer ────────────────────────────────────────────────────
            st.markdown("---")

            current_time = datetime.now(
                ZoneInfo("Asia/Kolkata")
            ).strftime("%d %b %Y, %I:%M %p")

            st.caption(
                f"🕒 Last updated: {current_time} • "
                f"📍 Coordinates: {lat:.2f}°N, {lon:.2f}°E • "
                f"Data: Open-Meteo API"
            )

elif search:
    st.warning("⚠️ Please enter a city name.")

else:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0; color: #aaa;">
        <div style="font-size: 5rem;">🌍</div>
        <div style="font-size: 1.3rem; color: #ccc; margin-top: 1rem;">
            Enter any city name above to get started
        </div>
        <div style="margin-top: 1rem; font-size: 0.9rem;">
            ✅ Real-time weather | 🤖 ML prediction |
            📅 7-day forecast | 📈 Interactive charts
        </div>
    </div>
    """, unsafe_allow_html=True)
