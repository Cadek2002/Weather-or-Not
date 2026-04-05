# This is the launching file for the streamlit app

import streamlit as st
import pandas as pd
import numpy as np
import datetime

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

# Weather inputs
# TODO: create automatic weather information gathering using some weather API
expected_temp = st.sidebar.number_input("Expected Temp (°F)", value=70)
expected_precip = st.sidebar.number_input("Expected Precip (in)", min_value=0.0, value=0.0, step=0.1)

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
    st.info("👈 Enter the flight parameters in the sidebar and click 'Predict Delay' to see the results.")