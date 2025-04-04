# -*- coding: utf-8 -*-
"""Untitled3.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1LTtjJFnlOhvTI11dbbDcZpYIh6VsMENt
"""

# Install required libraries (Seaborn is not pre-installed)


# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests

# Function to fetch Wikipedia pageviews
def fetch_wiki_data(article, start_date, end_date):
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article}/daily/{start_date}/{end_date}"
    headers = {
        "User-Agent": "WikiTrafficForecaster/1.0 (your_email@example.com)"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["items"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d%H")
        df = df[["timestamp", "views"]]
        return df
    else:
        print("Error fetching data:", response.status_code)
        return None

# Example: Get data for the article "India"
wiki_data = fetch_wiki_data("India", "20240101", "20240201")

# Check and clean the data
wiki_data.drop_duplicates(inplace=True)
wiki_data.fillna(method="ffill", inplace=True)

# Set 'timestamp' as the index
wiki_data.set_index("timestamp", inplace=True)

# Save cleaned data (optional)
wiki_data.to_csv("cleaned_wiki_traffic.csv")

# Display first 5 rows
wiki_data.head()

plt.figure(figsize=(12, 5))
plt.plot(wiki_data.index, wiki_data["views"], marker="o", linestyle="-", color="blue")
plt.xlabel("Date")
plt.ylabel("Page Views")
plt.title("Wikipedia Page Views for 'India'")
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 5))
sns.lineplot(x=wiki_data.index, y=wiki_data["views"], color="green")
plt.title("Wikipedia Page Traffic (Seaborn)")
plt.xlabel("Date")
plt.ylabel("Views")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()



from prophet import Prophet

# Reset index so timestamp becomes a column again
df_prophet = wiki_data.reset_index()

# Rename columns
df_prophet.columns = ["ds", "y"]

# Display first few rows
df_prophet.head()

# Create the model and fit the data
model = Prophet()
model.fit(df_prophet)

# Make future dates for 30 days
future = model.make_future_dataframe(periods=30)

# Predict future values
forecast = model.predict(future)

# Show the forecast
forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail()

# Plot prediction
model.plot(forecast)
plt.title("Wikipedia Traffic Forecast (Facebook Prophet)")
plt.xlabel("Date")
plt.ylabel("Predicted Page Views")
plt.show()

from statsmodels.tsa.arima.model import ARIMA

# Fit ARIMA model on the original views column
model_arima = ARIMA(wiki_data["views"], order=(5,1,0))
model_fit = model_arima.fit()

# Forecast the next 30 days
forecast_arima = model_fit.forecast(steps=30)

# Show predicted values
print(forecast_arima)

# Plot past + predicted
plt.figure(figsize=(12, 5))
plt.plot(wiki_data.index, wiki_data["views"], label="Actual")
plt.plot(pd.date_range(start=wiki_data.index[-1], periods=30, freq='D'), forecast_arima, label="ARIMA Forecast", color="red")
plt.xlabel("Date")
plt.ylabel("Page Views")
plt.title("ARIMA Forecast of Wikipedia Traffic")
plt.legend()
plt.grid(True)
plt.show()

from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

# Merge actual and predicted values (only for dates already in the dataset)
merged = pd.merge(df_prophet, forecast, on='ds')

# Calculate MAE and RMSE
mae_prophet = mean_absolute_error(merged['y'], merged['yhat'])
rmse_prophet = np.sqrt(mean_squared_error(merged['y'], merged['yhat']))

print(f"📊 Prophet MAE: {mae_prophet:.2f}")
print(f"📊 Prophet RMSE: {rmse_prophet:.2f}")

# Split the last 7 days for testing
train = wiki_data["views"][:-7]
test = wiki_data["views"][-7:]

# Train ARIMA model on training data
model_arima = ARIMA(train, order=(5,1,0))
model_fit = model_arima.fit()

# Predict on test data
forecast_arima = model_fit.forecast(steps=7)

# Calculate MAE and RMSE
mae_arima = mean_absolute_error(test, forecast_arima)
rmse_arima = np.sqrt(mean_squared_error(test, forecast_arima))

print(f"📊 ARIMA MAE: {mae_arima:.2f}")
print(f"📊 ARIMA RMSE: {rmse_arima:.2f}")



import streamlit as st
import pandas as pd
import requests
from prophet import Prophet
import matplotlib.pyplot as plt

# App Title
st.title("📈 Wikipedia Traffic Forecaster")

# User input for article
article = st.text_input("Enter Wikipedia Article Name:", "India")

# Date range input
start_date = st.date_input("Start Date", pd.to_datetime("2024-01-01"))
end_date = st.date_input("End Date", pd.to_datetime("2024-02-01"))

# Fetch data button
if st.button("Fetch & Forecast"):
    with st.spinner("Fetching data..."):
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article}/daily/{start_date:%Y%m%d}/{end_date:%Y%m%d}"
        headers = {"User-Agent": "StreamlitWikiApp/1.0 (example@email.com)"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data["items"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d%H")
            df = df[["timestamp", "views"]]
            df.columns = ["ds", "y"]

            # Forecast
            model = Prophet()
            model.fit(df)
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)

            # Plot
            st.subheader("📊 Forecast")
            fig1 = model.plot(forecast)
            st.pyplot(fig1)

            # Show raw forecast data
            st.subheader("📁 Forecasted Data (Next 30 Days)")
            st.dataframe(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(30))
        else:
            st.error(f"Failed to fetch data. Error code: {response.status_code}")
