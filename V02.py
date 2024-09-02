import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import folium_static
import os
import requests

# Function to load data from Excel files
def load_data(file_path):
    return pd.read_excel(file_path)

# Function to check if a postal code is valid
def is_valid_postal_code(postal_code):
    postal_code_str = str(postal_code).split('.')[0]  # Remove any decimals and convert to string
    return postal_code_str.isdigit() and len(postal_code_str) == 6

# Function to retrieve coordinates from OneMap API
def get_coordinates(postal_code, api_token):
    if not is_valid_postal_code(postal_code):
        return None, None
    
    base_url = 'https://www.onemap.gov.sg/api/common/elastic/search'
    params = {
        'searchVal': postal_code,
        'returnGeom': 'Y',
        'getAddrDetails': 'Y',
        'pageNum': 1
    }
    headers = {
        'Authorization': f'Bearer {api_token}'
    }
    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code == 200:
        results = response.json().get('results')
        if results:
            location = results[0]
            return float(location['LATITUDE']), float(location['LONGITUDE'])
    return None, None

# Load all Excel files from the 'data' directory
data_directory = 'data'  # Replace with your actual data directory
event_files = [f for f in os.listdir(data_directory) if f.endswith('.xlsx')]
event_data = {f.split('.')[0]: load_data(os.path.join(data_directory, f)) for f in event_files}

# Streamlit UI
st.title("Event Participants Demographics Dashboard")

# Navigation for selecting the overview or a specific event
page = st.sidebar.selectbox("Select Page", ["Overview"] + list(event_data.keys()))

# Directly include your OneMap API token here
api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzM2JiMTQ0ZjBmZGQ0MDIxMTFiNTE5ZTFmZDMzNjU2MiIsImlzcyI6Imh0dHA6Ly9pbnRlcm5hbC1hbGItb20tcHJkZXppdC1pdC0xMjIzNjk4OTkyLmFwLXNvdXRoZWFzdC0xLmVsYi5hbWF6b25hd3MuY29tL2FwaS92Mi91c2VyL3Bhc3N3b3JkIiwiaWF0IjoxNzI1MjEwNjcxLCJleHAiOjE3MjU0Njk4NzEsIm5iZiI6MTcyNTIxMDY3MSwianRpIjoib1JiazRObEl1ZkROTDJaVCIsInVzZXJfaWQiOjM3NDksImZvcmV2ZXIiOmZhbHNlfQ.4Ln9EauEF92Y2m8wO02Rw4MW2DglhpjNVBZN4ziSYLk"  # Replace with your actual OneMap API token

# Overview Page
if page == "Overview":
    st.header("Overview of All Events")

    # Aggregate data across all events
    all_data = pd.concat(event_data.values(), ignore_index=True)

    # Convert age to integer, handle non-numeric values
    all_data['Age'] = pd.to_numeric(all_data['Age'], errors='coerce')
    all_data = all_data.dropna(subset=['Age'])  # Drop rows where Age is NaN
    all_data['Age'] = all_data['Age'].astype(int)

    # Display aggregated gender distribution pie chart
    st.subheader("Aggregated Gender Distribution")
    gender_counts = all_data['Gender'].value_counts()
    fig_pie = px.pie(all_data, names='Gender', title='Gender Distribution',
                     color_discrete_sequence=px.colors.sequential.RdBu,
                     hole=0.3)
    fig_pie.update_traces(textinfo='percent+label', pull=[0.1, 0], textfont_size=14)
    st.plotly_chart(fig_pie)

    # Categorize ages
    all_data['Age Category'] = pd.cut(all_data['Age'], bins=[0, 12, 18, 35, 50, 100], 
                                      labels=['Child', 'Teenager', 'Youth', 'Adult', 'Elderly'])

    # Display aggregated age distribution bar chart
    st.subheader("Aggregated Age Category Bar Chart")
    age_counts = all_data['Age Category'].value_counts().sort_index()
    fig_bar = px.bar(age_counts, x=age_counts.index, y=age_counts.values,
                     labels={'x': 'Age Category', 'y': 'Number of Participants'},
                     title='Age Distribution by Category',
                     color=age_counts.values,
                     color_continuous_scale=px.colors.sequential.Viridis)
    fig_bar.update_layout(xaxis_title='Age Category', yaxis_title='Count',
                          title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    fig_bar.update_traces(marker_line_width=1.5, marker_line_color='black')
    st.plotly_chart(fig_bar)

# Individual Event Pages
else:
    st.header(f"Dashboard for {page}")
    data = event_data[page]

    # Convert postal codes to integer and validate them
    data['Postal Code'] = pd.to_numeric(data['Postal Code'], errors='coerce')
    data['Valid Postal Code'] = data['Postal Code'].apply(is_valid_postal_code)
    valid_data = data[data['Valid Postal Code']]

    # Create Folium map for valid postal codes
    st.subheader("Participants Distribution by Postal Code")
    # Generate a Folium map for postal codes
    m = folium.Map(location=[1.3521, 103.8198], zoom_start=11)

    for postal_code in data['Postal Code']:
        lat, lng = get_coordinates(str(postal_code), api_token)
        if lat and lng:
            folium.Marker(location=[lat, lng], popup=str(postal_code)).add_to(m)
    # Save the Folium map as an HTML file
    m.save('postal_code_map.html')
    folium_static(m)

    # Display interactive gender distribution pie chart
    st.subheader("Gender Distribution")
    gender_counts = data['Gender'].value_counts()
    fig_pie = px.pie(data, names='Gender', title='Gender Distribution',
                     color_discrete_sequence=px.colors.sequential.RdBu,
                     hole=0.3)
    fig_pie.update_traces(textinfo='percent+label', pull=[0.1, 0], textfont_size=14)
    st.plotly_chart(fig_pie)

    # Convert age to integer, handle non-numeric values
    data['Age'] = pd.to_numeric(data['Age'], errors='coerce')
    data = data.dropna(subset=['Age'])  # Drop rows where Age is NaN
    data['Age'] = data['Age'].astype(int)

    # Categorize ages
    data['Age Category'] = pd.cut(data['Age'], bins=[0, 12, 18, 35, 50, 100], 
                                  labels=['Child', 'Teenager', 'Youth', 'Adult', 'Elderly'])

    # Display interactive age distribution bar chart
    st.subheader("Age Category Bar Chart")
    age_counts = data['Age Category'].value_counts().sort_index()
    fig_bar = px.bar(age_counts, x=age_counts.index, y=age_counts.values,
                     labels={'x': 'Age Category', 'y': 'Number of Participants'},
                     title='Age Distribution by Category',
                     color=age_counts.values,
                     color_continuous_scale=px.colors.sequential.Viridis)
    fig_bar.update_layout(xaxis_title='Age Category', yaxis_title='Count',
                          title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    fig_bar.update_traces(marker_line_width=1.5, marker_line_color='black')
    st.plotly_chart(fig_bar)
