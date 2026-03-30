# This is the launching file for the streamlit app

import streamlit as st
import joblib  # for loading the models
import pandas as pd

st.title("Weather or Not: Flight Delay Predictor")

if st.button("Predict Delay"):
    st.write("Predicting Delay...")