import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import requests
import os

# Function to check if a postal code is valid
def is_valid_postal_code(postal_code):
    postal_code_str = str(postal_code).split('.')[0]  # Remove any decimals and convert to string
    return postal_code_str.isdigit() and len(postal_code_str) == 6

# Function to retrieve coordinates from OneMap API
def get_coordinates(postal_code, api_token):
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
            return location['LATITUDE'], location['LONGITUDE']
    return None, None

# OneMap API token
API_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzM2JiMTQ0ZjBmZGQ0MDIxMTFiNTE5ZTFmZDMzNjU2MiIsImlzcyI6Imh0dHA6Ly9pbnRlcm5hbC1hbGItb20tcHJkZXppdC1pdC0xMjIzNjk4OTkyLmFwLXNvdXRoZWFzdC0xLmVsYi5hbWF6b25hd3MuY29tL2FwaS92Mi91c2VyL3Bhc3N3b3JkIiwiaWF0IjoxNzIwNzc0OTk1LCJleHAiOjE3MjEwMzQxOTUsIm5iZiI6MTcyMDc3NDk5NSwianRpIjoiWjFrRThxQVpJUERpZVd5MCIsInVzZXJfaWQiOjM3NDksImZvcmV2ZXIiOmZhbHNlfQ.Co3uWY58EkdlGBxHF2ObNV8EkN8CSsVPCLmxrMwIGQA'  # Replace with your OneMap API token

# Function to create a Folium map
@st.cache_resource
def create_folium_map(df, api_token):
    coordinates = []

    # Iterate over each postal code in the DataFrame
    for postal_code in df['postal_code']:
        if is_valid_postal_code(postal_code):
            lat, lng = get_coordinates(str(postal_code).split('.')[0], api_token)
            if lat and lng:
                coordinates.append({'postal_code': postal_code, 'latitude': lat, 'longitude': lng})
        else:
            print(f"Invalid postal code: {postal_code}")

    # Convert the list of coordinates to a DataFrame
    coordinates_df = pd.DataFrame(coordinates)

    # Drop rows with missing coordinates
    coordinates_df.dropna(subset=['latitude', 'longitude'], inplace=True)

    # Create a Folium map centered around Singapore
    map_singapore = folium.Map(location=[1.3521, 103.8198], zoom_start=12, width='100%', height='800px')

    # Add markers to the Folium map
    for _, row in coordinates_df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=row['postal_code'],
        ).add_to(map_singapore)

    return map_singapore

# Set page config
st.set_page_config(page_title="Kampung Spirit Dashboard", page_icon=":bar_chart:", layout="wide")

# Add custom CSS
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
            padding: 20px;
        }
        .sidebar .sidebar-content {
            background-color: #343a40;
            color: white;
        }
        .block-container {
            padding-top: 20px;
        }
        h1 {
            color: #4CAF50;
        }
        .stButton>button {
            color: white;
            background-color: #4CAF50;
            border-radius: 8px;
        }
        .css-18ni7ap.e8zbici2 {
            background-color: #343a40;
        }
        .css-qbe2hs.e1fqkh3o5 {
            color: white;
        }
        .css-1v3fvcr.ex0cdmw0 {
            color: white;
        }
        .footer {
            text-align: center;
            padding: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Path to the directory containing Excel files
excel_files_dir = 'main'  # Replace with the actual path to your Excel files

# Get a list of all Excel files in the directory
excel_files = [f for f in os.listdir(excel_files_dir) if f.endswith('.xlsx')]

# Create a dictionary to map display names to file names
excel_files_display = {os.path.splitext(f)[0]: f for f in excel_files}

# Create a sidebar for selecting the event
st.sidebar.title("Select Event")
selected_event_display = st.sidebar.selectbox("Choose an event", list(excel_files_display.keys()))

# Get the corresponding file name
selected_file = excel_files_display[selected_event_display]

# Load the selected Excel file
file_path = os.path.join(excel_files_dir, selected_file)
df = pd.read_excel(file_path)

# Ensure that age category columns contain only numeric values
age_categories = ['Child', 'Teenager', 'Youth', 'Adult', 'Elderly']
df[age_categories] = df[age_categories].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

# Calculate the total number of participants in each age category
age_distribution = df[age_categories].sum().reset_index()
age_distribution.columns = ['Age Category', 'Count']

# Determine the correct column name for race
race_column_name = 'What is your race?' if 'What is your race?' in df.columns else 'Race'

# Create a sidebar for selecting visualization type
st.sidebar.title("Dashboard")
chart_type = st.sidebar.selectbox(
    "Select chart type",
    ["Race Distribution", "Age Distribution", "Postal Code Map"]
)

st.title("Kampung Spirit Dashboard")
st.markdown(f"""
    <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px;">
        Explore the data for {selected_event_display} on race distribution, age distribution, and postal codes for the event participants.
    </div>
""", unsafe_allow_html=True)

if chart_type == "Race Distribution":
    fig = px.pie(df, names=race_column_name, title="Race Distribution", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True, height=800)
elif chart_type == "Age Distribution":
    fig = px.bar(age_distribution, x='Age Category', y='Count', title="Age Distribution", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True, height=800)
elif chart_type == "Postal Code Map":
    map_singapore = create_folium_map(df, API_TOKEN)
    folium_static(map_singapore)

# Add footer
st.markdown("""
    <div class="footer">
        <hr>
        <p style="color: grey;">&copy; 2024 Kampung Spirit Dashboard. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)
