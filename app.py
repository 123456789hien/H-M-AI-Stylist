import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO
import zipfile
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="H&M AI Stylist Pro", page_icon="👗", layout="wide")

# --- 2. GOOGLE DRIVE ID CONFIG ---
FILE_IDS = {
    "article_csv": "1qYtRpJU9yKdqrcvmE7wUFC-QmU87NSyv",
    "customer_dna": "1ZrEvTcVb0DKS6cIv4vZf-jod9EGH4srK",
    "seasonal_trends": "1vS2vDuhHCifie9wRLOoa70t02UUOI0bs",
    "images_zip": "1X5q8o8fnR-MGBjBzhZf5gH8URNKD2uJA"
}

# Robust Download Function to bypass Google Drive scan warnings
def download_file_from_google_drive(file_id):
    URL = "https://docs.google.com/uc?export=download&confirm=t"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    return response.content

# --- 3. DATA LOADING WITH VALIDATION ---
@st.cache_data(show_spinner=False)
def load_and_validate_data():
    try:
        # Loading via bytes to ensure stability
        articles = pd.read_csv(BytesIO(download_file_from_google_drive(FILE_IDS["article_csv"])))
        dna = pd.read_csv(BytesIO(download_file_from_google_drive(FILE_IDS["customer_dna"])))
        seasonal = pd.read_csv(BytesIO(download_file_from_google_drive(FILE_IDS["seasonal_trends"])))
        
        for df in [articles, dna, seasonal]:
            df.columns = df.columns.str.strip()
            if 'Unnamed: 0' in df.columns:
                df.drop(columns=['Unnamed: 0'], inplace=True)
        
        # Check if DNA is empty
        if dna.empty:
            st.error("The DNA database is empty. Please check your CSV file.")
            return None, None, None
            
        return articles, dna, seasonal
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None, None, None

@st.cache_resource(show_spinner=False)
def extract_images():
    if not os.path.exists("images"):
        os.makedirs("images")
        try:
            content = download_file_from_google_drive(FILE_IDS["images_zip"])
            with zipfile.ZipFile(BytesIO(content)) as z:
                z.extractall("images")
        except:
            pass 
    return True

# --- 4. APP EXECUTION ---
articles, dna, seasonal = load_and_validate_data()
extract_images()

if articles is not None and not dna.empty:
    st.sidebar.title("Stylist Control Center")
    
    # Identify Columns Safely
    id_col = next((c for c in dna.columns if 'id' in c.lower()), dna.columns[0])
    
    # Filter out nulls from selection
    user_options = dna[id_col].dropna().unique()[:50]
    
    if len(user_options) > 0:
        user_id = st.sidebar.selectbox("👤 Select Client DNA Signature", user_options)
        
        # Safe filtering to prevent IndexError
        user_rows = dna[dna[id_col] == user_id]
        if not user_rows.empty:
            u_info = user_rows.iloc[0]
            
            # Show Metrics
            val_col = next((c for c in dna.columns if 'price' in c.lower() or 'val' in c.lower()), dna.columns[1])
            st.sidebar.metric("Price affinity", f"${u_info[val_col]:.2f}")
            
            # Mood selection
            mood_col = next((c for c in articles.columns if 'mood' in c.lower()), articles.columns[0])
            selected_mood = st.sidebar.radio("Target Mood", articles[mood_col].unique())

            # --- MAIN TABS ---
            tab1, tab2 = st.tabs(["🛍️ Collection", "📈 Trends"])
            
            with tab1:
                st.header(f"Curated {selected_mood} Styles")
                # Grid view
                display_df = articles[articles[mood_col] == selected_mood].head(12)
                cols = st.columns(4)
                for i, (idx, row) in enumerate(display_df.iterrows()):
                    with cols[i % 4]:
                        img_path = os.path.join("images", str(row.get('image_path', '')))
                        if os.path.exists(img_path):
                            st.image(Image.open(img_path), use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/200", use_container_width=True)
                        st.write(f"**{row.get('prod_name', 'H&M Item')}**")
            
            with tab2:
                st.subheader("Seasonal Intelligence")
                fig = px.line(seasonal, x=seasonal.columns[0], y=seasonal.columns[1:])
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.sidebar.warning("User data not found.")
    else:
        st.error("No valid IDs found in the DNA file.")
else:
    st.warning("Please verify that your Google Drive files are shared as 'Anyone with the link can view'.")
