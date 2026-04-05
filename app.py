# This is the launching file for the streamlit app

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests

# --- Initialize session state for weather inputs ---
# This ensures the values don't reset when the page reruns
# TODO: create a better list of values that we will predict on
if "expected_temp" not in st.session_state:
    st.session_state.expected_temp = 70.0
if "expected_precip" not in st.session_state:
    st.session_state.expected_precip = 0.0

# Load the airport codes and airport names
airport_df = pd.read_csv('airport_code_name_lookup.csv')
airport_options = airport_df.apply(lambda row: f"{row['AIRPORT']} ({row['STATION NAME']})", axis=1).tolist()

st.set_page_config(page_title="Weather or Not",
                   page_icon="✈️",
                   layout="wide")
st.title("Weather or Not: Flight Delay Predictor")

# --- Sidebar Inputs ---
st.sidebar.header("Input Parameters")

# Date input
flight_date = st.sidebar.date_input("Date", datetime.date.today())
flight_time = st.sidebar.time_input("Time", datetime.datetime.now().time())

# Airport dropdowns (using placeholder data)
origin_airport = st.sidebar.selectbox("Origin Airport", airport_options)
dest_airport = st.sidebar.selectbox("Destination Airport", airport_options)

# --- Automatic weather fetching ---
if st.sidebar.button("Fetch Weather Forecast", type="secondary"):
    # Get the FAA code from the dropdown selection
    origin_code = origin_airport.split(" ")[0]
    dest_code = dest_airport.split(" ")[0]
    print(origin_code)

    # Get the LAT/LON for the origin airport
    airport_data = airport_df[airport_df['AIRPORT'] == origin_code]
    if not airport_data.empty:
        lat = airport_data.iloc[0]['LAT']
        lon = airport_data.iloc[0]['LON']
        print(lat, lon)

        # Call the Open-Meteo API
        # https://open-meteo.com/en/docs
        # url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=auto"
        hourly_vars = "temperature_2m,precipitation_probability,precipitation,rain,snowfall,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility"
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly={hourly_vars}"
            f"&temperature_unit=fahrenheit"
            f"&precipitation_unit=inch"
            f"&wind_speed_unit=mph"
            f"&timezone=auto"
        )
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check if the request was successful
            weather_data = response.json()
            print(weather_data)
            
            # Format our input timing to match API time format
            target_hour = flight_time.strftime('%H:00')
            target_datetime_str = f'{flight_date.isoformat()}T{target_hour}'

            times = weather_data['hourly']['time']
            if target_datetime_str in times:
                index = times.index(target_datetime_str)
                st.session_state.expected_temp = weather_data['hourly']['temperature_2m'][index]
                st.session_state.expected_precip = weather_data['hourly']['precipitation'][index]
                st.success("Weather forecast fetched successfully!")
            else:
                st.warning("Weather data for the selected date and time is not available.")
        except requests.RequestException as e:
            st.error(f"Error fetching weather data: {e}")
    else:
        st.error("Could not find the selected airport in the dataset.")

# Weather inputs
expected_temp = st.sidebar.number_input("Expected Temp (°F)", value=st.session_state.expected_temp)
expected_precip = st.sidebar.number_input("Expected Precip (in)", min_value=0.0, value=st.session_state.expected_precip, step=0.1)

# Predict button
predict_button = st.sidebar.button("Predict Delay", type="primary")

# --- Main Content Area ---
# if predict_button is clicked, show the prediction results
if predict_button:
    # Creating two columns for the output layout
    col1, col2 = st.columns([1, 2])

    # Placeholder logic for ui demo
    # TODO: replace with actual model
    predicted_delay_mins = 25

    with col1:
        st.subheader("Prediction")
        # st.metric is great for highlighting a single important number
        st.metric(
            label="Estimated Delay",
            value=f"{predicted_delay_mins} mins",
            delta="Weather Impact",
            delta_color="inverse"
        )

    # TODO: determine what data we would actually show here
    with col2:
        st.subheader("Delay Probability")

        # Creating placeholder dummy data for the chart
        chart_data = pd.DataFrame({
            "Probability (%)": [15, 20, 45, 15, 5],
            "Delay Range": ["On Time", "1-15 mins", "15-30 mins", "30-60 mins", "60+ mins"]
        })
        chart_data.set_index("Delay Range", inplace=True)

        # Displaying a bar chart
        st.bar_chart(chart_data)

else:
    # This shows when the app first loads before the button is clicked
    st.info("Enter the flight parameters in the sidebar and click 'Predict Delay' to see the results.")