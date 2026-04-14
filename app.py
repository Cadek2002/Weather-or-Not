# This is the launching file for the streamlit app

import streamlit as st
import pandas as pd
import datetime
import requests

def meters_to_miles(meters):
    return meters * 0.000621371

weather_dict = {
    "expected_temp": {"label": "Expected Temp (°F)", "weather_key": "temperature_2m", "min": -50.0, "max": 150.0, "init": 70.0, "step": 0.1, "input_object": None},
    "expected_precip": {"label": "Expected Precip (in)", "weather_key": "precipitation", "min": 0.0, "max": 10.0, "init": 0.0, "step": 0.1, "input_object": None},
    "expected_cloud_cover": {"label": "Expected Cloud Cover (%)", "weather_key": "cloud_cover", "min": 0.0, "max": 100.0, "init": 0.0, "step": 1.0, "input_object": None},
    "expected_wind_speed": {"label": "Expected Wind Speed (mph)", "weather_key": "wind_speed_10m", "min": 0.0, "max": 150.0, "init": 0.0, "step": 0.1, "input_object": None},
    "expected_wind_gust_speed": {"label": "Expected Wind Gust Speed (mph)", "weather_key": "wind_gusts_10m", "min": 0.0, "max": 150.0, "init": 0.0, "step": 0.1, "input_object": None},
    "expected_visibility": {"label": "Expected Visibility (miles)", "weather_key": "visibility", "min": 0.0, "max": 1000.0, "init": 10.0, "step": 0.1, "input_object": None}
}

# --- Initialize session state for weather inputs ---
# This ensures the values don't reset when the page reruns
for key, params in weather_dict.items():
    if key not in st.session_state:
        st.session_state[key] = params["init"]

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
            print(weather_data['hourly'].keys())
            
            # Format our input timing to match API time format
            target_hour = flight_time.strftime('%H:00')
            target_datetime_str = f'{flight_date.isoformat()}T{target_hour}'

            # For imputing exact time weather
            delta = datetime.timedelta(hours=1)
            flight_time_plus1 = (datetime.datetime.combine(flight_date, flight_time) + delta).time()
            target_hour_post = flight_time_plus1.strftime('%H:00')
            target_datetime_str_post = f'{flight_date.isoformat()}T{target_hour_post}'

            times = weather_data['hourly']['time']
            if target_datetime_str in times and target_datetime_str_post in times:
                for key, params in weather_dict.items():
                    # Update the expected weather inputs
                    weather_api_key = params["weather_key"]
                    index = times.index(target_datetime_str)
                    index_post = times.index(target_datetime_str_post)
                    factor = (flight_time.minute) / 60  # Proportion of the hour that has passed
                    # To impute the exact time weather with a weighted average of the current and next hour
                    if key == "expected_visibility":
                        # Convert visibility from meters to miles for just visibility
                        st.session_state[key] = meters_to_miles((1 - factor) * weather_data['hourly'][weather_api_key][index]
                                              + factor * weather_data['hourly'][weather_api_key][index_post])
                    else:
                        st.session_state[key] = ((1 - factor) * weather_data['hourly'][weather_api_key][index]
                                                  + factor * weather_data['hourly'][weather_api_key][index_post])
            else:
                st.warning("Weather data for the selected date and time is not available.")
        except requests.RequestException as e:
            st.error(f"Error fetching weather data: {e}")
    else:
        st.error("Could not find the selected airport in the dataset.")

# Create Weather inputs on sidebar
for key, params in weather_dict.items():
    params["input_object"] = st.sidebar.number_input(
        label=params["label"],
        min_value=params["min"],
        max_value=params["max"],
        value=st.session_state[key],
        step=params["step"]
    )

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
    # This shows when the app first loads before the predict button is clicked
    st.info("Enter the flight parameters in the sidebar and click 'Predict Delay' to see the results.")