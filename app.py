# This is the launching file for the streamlit app

import streamlit as st
import pandas as pd
import datetime
import requests
import math
import joblib
from pathlib import Path

def meters_to_miles(meters):
    return meters * 0.000621371

EXPORT_DIR = Path(__file__).parent / "model_export"

@st.cache_resource
def load_artifacts():
    try:
        pipeline = joblib.load(EXPORT_DIR / "flight_delay_pipeline.joblib")
        label_encoder = joblib.load(EXPORT_DIR / "label_encoder.joblib")
        feature_meta = joblib.load(EXPORT_DIR / "feature_metadata.joblib")
        return pipeline, label_encoder, feature_meta
    except FileNotFoundError:
        return None, None, None

weather_dict = {
    "expected_temp": {"label": "Expected Temp (°F)", "weather_key": "temperature_2m", "min": -50.0, "max": 150.0, "init": 70.0, "step": 0.1, "input_object": None},
    "expected_precip": {"label": "Expected Precip (in)", "weather_key": "precipitation", "min": 0.0, "max": 10.0, "init": 0.0, "step": 0.1, "input_object": None},
    "expected_wind_speed": {"label": "Expected Wind Speed (mph)", "weather_key": "wind_speed_10m", "min": 0.0, "max": 150.0, "init": 0.0, "step": 0.1, "input_object": None},
    "expected_wind_gust_speed": {"label": "Expected Wind Gust Speed (mph)", "weather_key": "wind_gusts_10m", "min": 0.0, "max": 150.0, "init": 0.0, "step": 0.1, "input_object": None},
    "expected_cloud_cover": {"label": "Expected Cloud Cover (%)", "weather_key": "cloud_cover", "min": 0.0, "max": 100.0, "init": 0.0, "step": 1.0, "input_object": None},
    "expected_visibility": {"label": "Expected Visibility (miles)", "weather_key": "visibility", "min": 0.0, "max": 1000.0, "init": 10.0, "step": 0.1, "input_object": None},
    "expected_dew_point": {"label": "Expected Dew Point (°F)", "weather_key": "dew_point_2m", "min": -50.0, "max": 150.0, "init": 65.0, "step": 0.1, "input_object": None},
    "expected_relative_humidity": {"label": "Expected Relative Humidity (%)", "weather_key": "relative_humidity_2m", "min": 0.0, "max": 100.0, "init": 50.0, "step": 1.0, "input_object": None},
    "expected_pressure": {"label": "Expected Pressure (hPa)", "weather_key": "pressure_msl", "min": 800.0, "max": 1100.0, "init": 1013.25, "step": 0.1, "input_object": None},
}

# --- Initialize session state for weather inputs ---
# For both origin and destination
# This ensures the values don't reset when the page reruns
for prefix in ["orig_", "dest_"]:
    for key, params in weather_dict.items():
        state_key = f"{prefix}{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = params["init"]

# Load the airport codes and airport names
airport_df = pd.read_csv('airport_code_name_lookup.csv')
airport_options = airport_df.apply(lambda row: f"{row['AIRPORT']} ({row['STATION NAME']})", axis=1).tolist()

pipeline, label_encoder, meta = load_artifacts()

st.set_page_config(page_title="Weather or Not",
                   page_icon="✈️",
                   layout="wide")
# Force a minimum width on the sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 350px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Weather or Not: Flight Delay Predictor")

st.header("Flight information")
col_date, col_time = st.columns(2)
# date and time row
flight_date = col_date.date_input("Date", key="flight_date")
flight_time = col_time.time_input("Time", key="flight_time")
# airport row
col_origin, col_destination = st.columns(2)
origin_airport = col_origin.selectbox("Origin Airport", airport_options)
dest_airport = col_destination.selectbox("Destination Airport", airport_options)

def fetch_airport_weather(airport_str, target_date, target_time, prefix):
    airport_code = airport_str.split(" ")[0]
    airport_data = airport_df[airport_df['AIRPORT'] == airport_code]

    if airport_data.empty:
        st.error(f"Could not find {airport_code} in the dataset.")
        return

    lat = airport_data.iloc[0]['LAT']
    lon = airport_data.iloc[0]['LON']
    hourly_vars = ("temperature_2m,precipitation_probability,precipitation,rain,snowfall,cloud_cover,"
                   "wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,dew_point_2m,"
                   "relative_humidity_2m,pressure_msl")

    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&hourly={hourly_vars}&temperature_unit=fahrenheit&precipitation_unit=inch"
           f"&wind_speed_unit=mph&timezone=auto")
    try:
        response = requests.get(url)
        response.raise_for_status()
        weather_data = response.json()

        target_hour = target_time.strftime('%H:00')
        target_datetime_str = f'{target_date.isoformat()}T{target_hour}'

        delta = datetime.timedelta(hours=1)
        flight_time_plus1 = (datetime.datetime.combine(target_date, target_time) + delta).time()
        target_hour_post = flight_time_plus1.strftime('%H:00')
        target_datetime_str_post = f'{target_date.isoformat()}T{target_hour_post}'

        times = weather_data['hourly']['time']
        if target_datetime_str in times and target_datetime_str_post in times:
            index = times.index(target_datetime_str)
            index_post = times.index(target_datetime_str_post)
            factor = (target_time.minute) / 60

            for key, params in weather_dict.items():
                weather_api_key = params["weather_key"]
                val1 = weather_data['hourly'][weather_api_key][index]
                val2 = weather_data['hourly'][weather_api_key][index_post]
                interp_val = (1 - factor) * val1 + factor * val2

                if key == "expected_visibility":
                    st.session_state[f"{prefix}{key}"] = meters_to_miles(interp_val)
                else:
                    st.session_state[f"{prefix}{key}"] = interp_val
                    print(f"{prefix}{key}, {interp_val=}")
            st.success(f"Successfully fetched weather for {airport_code}.")
        else:
            st.warning(f"Weather data for {airport_code} at the selected time is not available.")
    except requests.RequestException as e:
        st.error(f"Error fetching weather data for {airport_code}: {e}")

# Fetch Weather Button
if st.button("Fetch Weather Forecast", type="secondary"):
    with st.spinner("Fetching weather from Open-Meteo..."):
        fetch_airport_weather(origin_airport, flight_date, flight_time, "orig_")
        fetch_airport_weather(dest_airport, flight_date, flight_time, "dest_")

# --- Main Content: Weather Inputs ---
st.header("Expected Weather")
w_col1, w_col2 = st.columns(2)

with w_col1:
    st.subheader("Departure (Origin)")
    for key, params in weather_dict.items():
        st.number_input(
            label=params["label"], min_value=params["min"], max_value=params["max"],
            value=st.session_state[f"orig_{key}"], step=params["step"], key=f"orig_{key}"
        )

with w_col2:
    st.subheader("Arrival (Destination)")
    for key, params in weather_dict.items():
        st.number_input(
            label=params["label"], min_value=params["min"], max_value=params["max"],
            value=st.session_state[f"dest_{key}"], step=params["step"], key=f"dest_{key}"
        )

# Center the predict button
st.write("")
predict_button = st.button("Predict Delay", type="primary", use_container_width=True)

# --- Dividing Line ---
st.divider()

# --- Model Output Area ---
if predict_button:
    if pipeline is None:
        st.error("Model artifacts not found! Please place the joblib files in a 'model_export' folder next to app.py.")
    else:
        # 1. Derive Temporal Features
        dep_hour = flight_time.hour
        dep_hour_sin = math.sin(2 * math.pi * dep_hour / 24.0)
        dep_hour_cos = math.cos(2 * math.pi * dep_hour / 24.0)
        dep_dow = flight_date.weekday()
        dep_month = flight_date.month
        is_weekend = 1 if dep_dow >= 5 else 0
        rush_hour = 1 if (6 <= dep_hour <= 9) or (15 <= dep_hour <= 18) else 0

        # Placeholders for future logic updates
        days_to_holiday = 14
        flight_density = 100

        # 2. Map Origin Weather
        orig_tmpf = st.session_state["orig_expected_temp"]
        orig_sknt = st.session_state["orig_expected_wind_speed"] * 0.868976 # wind speed in knots
        orig_vsby = st.session_state["orig_expected_visibility"]
        orig_gust = st.session_state["orig_expected_wind_gust_speed"]
        orig_dwpf = st.session_state["orig_expected_dew_point"]
        orig_relh = st.session_state["orig_expected_relative_humidity"]
        orig_mslp = st.session_state["orig_expected_pressure"]
        orig_low_vis = 1 if orig_vsby < 3 else 0
        orig_high_wind = 1 if orig_sknt > 20 else 0
        orig_gusting = 1 if orig_gust > 0 else 0

        # 3. Map Destination Weather
        dest_tmpf = st.session_state["dest_expected_temp"]
        dest_sknt = st.session_state["dest_expected_wind_speed"] * 0.868976
        dest_vsby = st.session_state["dest_expected_visibility"]
        dest_gust = st.session_state["dest_expected_wind_gust_speed"]
        dest_dwpf = st.session_state["dest_expected_dew_point"]
        dest_relh = st.session_state["dest_expected_relative_humidity"]
        dest_mslp = st.session_state["dest_expected_pressure"]
        dest_low_vis = 1 if dest_vsby < 3 else 0
        dest_high_wind = 1 if dest_sknt > 20 else 0
        dest_gusting = 1 if dest_gust > 0 else 0

        # 4. Calculate Deltas
        delta_tmpf = abs(orig_tmpf - dest_tmpf)
        delta_sknt = abs(orig_sknt - dest_sknt)
        delta_vsby = abs(orig_vsby - dest_vsby)

        # 5. Build Input DataFrame
        input_data = {
            "ORIG_tmpf": orig_tmpf, "ORIG_dwpf": orig_dwpf, "ORIG_relh": orig_relh,
            "ORIG_sknt": orig_sknt, "ORIG_vsby": orig_vsby, "ORIG_mslp": orig_mslp,
            "DEST_tmpf": dest_tmpf, "DEST_dwpf": dest_dwpf, "DEST_relh": dest_relh,
            "DEST_sknt": dest_sknt, "DEST_vsby": dest_vsby, "DEST_mslp": dest_mslp,
            "DELTA_tmpf": delta_tmpf, "DELTA_sknt": delta_sknt, "DELTA_vsby": delta_vsby,
            "DEP_HOUR_SIN": dep_hour_sin, "DEP_HOUR_COS": dep_hour_cos,
            "DAYS_TO_HOLIDAY": days_to_holiday, "FLIGHT_DENSITY": flight_density,
            "IS_WEEKEND": is_weekend, "RUSH_HOUR": rush_hour,
            "ORIG_LOW_VIS": orig_low_vis, "ORIG_HIGH_WIND": orig_high_wind, "ORIG_GUSTING": orig_gusting,
            "DEST_LOW_VIS": dest_low_vis, "DEST_HIGH_WIND": dest_high_wind, "DEST_GUSTING": dest_gusting,
            "DEP_DOW": dep_dow, "DEP_MONTH": dep_month,
        }

        X_input = pd.DataFrame([input_data])[meta["all"]]

        # 6. Make Predictions
        pred_encoded = pipeline.predict(X_input)[0]
        pred_label = label_encoder.inverse_transform([pred_encoded])[0]
        prob = pipeline.predict_proba(X_input)[0]
        delay_prob = prob[1] if len(prob) > 1 else prob[0]
        delay_prob_percent = round(delay_prob * 100, 1)

        # 7. UI Output
        res_col1, res_col2 = st.columns([1, 2])

        with res_col1:
            st.subheader("Prediction")
            if pred_label == 1 or str(pred_label).lower() in ["delay", "delayed", "yes", "true"]:
                status = "Delayed"
                status_color = "inverse"
            else:
                status = "On Time"
                status_color = "normal"

            st.metric(
                label="Flight Status",
                value=status,
                delta=f"{delay_prob_percent}% risk of delay",
                delta_color=status_color
            )

        with res_col2:
            st.subheader("Delay Probability")
            chart_data = pd.DataFrame({
                "Probability (%)": [round(prob[0] * 100, 1), delay_prob_percent],
                "Outcome": ["On Time", "Delayed"]
            })
            chart_data.set_index("Outcome", inplace=True)
            st.bar_chart(chart_data)

else:
    st.info("Enter the flight parameters above and click 'Predict Delay' to see the results.")
