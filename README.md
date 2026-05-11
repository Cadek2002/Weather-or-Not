# Weather-or-Not
Flight delay prediction models and prototype interface.

## Flight Data Guide

1) Fetch Model Data from BTS Flight Records https://transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGK&QO_fu146_anzr=b0-gvzr
    Or Download our pre-compiled dataset https://michiganstate-my.sharepoint.com/:u:/g/personal/koweckca_msu_edu/IQDm_Hkwv1rpRLX5Njs-BNy2AZIqybM3pxtHFlrTxvBQ4LU?e=IQmzZ0
2) Place all files in a single directory
3) Duplicate the example_params_file.json and rename it to params_file.json
4) Input the directory to the downloaded dataset and the desired artifact output directory into the json file
5) Run the notebook.

## Prototype
Run `streamlit run app.py` to start running the prototype web app locally.
You may need to download necessary dependencies first, which can be done by 
running `pip install -r requirements.txt` in the terminal.

The steamlit hosted webapp is available at https://weather-or-not-ish48lyykk4yi3g4hacmbr.streamlit.app/
(though it may be required to spin up depending on the frequency of use).
