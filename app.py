import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO
import zipfile
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="H&M AI Stylist | Psychographic Intelligence",
    page_icon="👗",
    layout="wide"
)

# --- 2. PROFESSIONAL CSS (FIXED TYPO) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    .product-card { border: 1px solid #eee; padding: 10px; border-radius: 10px; background: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GOOGLE DRIVE ID CONFIG ---
FILE_IDS = {
    "article_csv": "1qYtRpJU9yKdqrcvmE7wUFC-QmU87NSyv",
    "customer_dna": "1ZrEvTcVb0DKS6cIv4vZf-jod9EGH4srK",
    "seasonal_trends": "1vS2vDuhHCifie9wRLOoa70t02UUOI0bs",
    "images_zip": "1X5q8o8fnR-MGBjBzhZf5gH8URNKD2uJA"
}

def get_drive_url(file_id):
    return f'https://drive.google.com/uc?export=download&id={file_id}'

# --- 4. DATA LOADING & AUTO-CLEANING (FIXES KEYERROR) ---
@st.cache_data(show_spinner=False)
def load_and_clean_data():
    try:
        articles = pd.read_csv(get_drive_url(FILE_IDS["article_csv"]))
        dna = pd.read_csv(get_drive_url(FILE_IDS["customer_dna"]))
        seasonal = pd.read_csv(get_drive_url(FILE_IDS["seasonal_trends"]))
        
        # Standardize Columns: Remove spaces and hidden index columns
        for df in [articles, dna, seasonal]:
            df.columns = df.columns.str.strip()
            if 'Unnamed: 0' in df.columns:
                df.drop(columns=['Unnamed: 0'], inplace=True)
                
        return articles, dna, seasonal
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return None, None, None

@st.cache_resource(show_spinner=False)
def extract_images():
    target_path = "images"
    if not os.path.exists(target_path):
        os.makedirs(target_path)
        try:
            r = requests.get(get_drive_url(FILE_IDS["images_zip"]), stream=True)
            with zipfile.ZipFile(BytesIO(r.content)) as z:
                z.extractall(target_path)
        except Exception as e:
            st.sidebar.warning("Image library is pending download...")
    return True

# --- INITIALIZE ---
with st.spinner('Syncing AI Stylist Assets...'):
    articles, dna, seasonal = load_and_clean_data()
    extract_images()

# --- 5. MAIN APPLICATION LOGIC ---
if articles is not None and dna is not None:
    # --- SIDEBAR: PERSONALIZATION ---
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
    st.sidebar.title("Stylist Control Center")
    
    # Dynamic Column Detection for DNA
    id_col = 'customer_id' if 'customer_id' in dna.columns else dna.columns[0]
    price_col = 'avg_price' if 'avg_price' in dna.columns else dna.columns[1]
    count_col = 'transaction_count' if 'transaction_count' in dna.columns else dna.columns[2]

    st.sidebar.subheader("👤 Client Profile")
    user_id = st.sidebar.selectbox("Select DNA Signature", dna[id_col].unique()[:50])
    u_info = dna[dna[id_col] == user_id].iloc[0]
    
    st.sidebar.metric("Price Affinity", f"${u_info[price_col]:.3f}")
    st.sidebar.metric("Purchase Depth", f"{int(u_info[count_col])} items")
    
    st.sidebar.divider()
    
    # Dynamic Column Detection for Articles
    mood_col = 'mood' if 'mood' in articles.columns else 'Mood'
    selected_mood = st.sidebar.radio("Target Style Mood", articles[mood_col].unique())

    # --- MAIN CONTENT ---
    st.title("👗 H&M AI Stylist: Psychographic Experience")
    st.markdown(f"**Current Recommendation Engine:** *{selected_mood} Mode*")

    tab1, tab2, tab3 = st.tabs(["🛍️ Smart Collection", "📈 Seasonal DNA", "🧬 Model Methodology"])

    # TAB 1: PRODUCT GRID
    with tab1:
        # We sort by Hotness Score derived from 31M transactions
        hot_col = 'hotness_score' if 'hotness_score' in articles.columns else articles.columns[-1]
        display_df = articles[articles[mood_col] == selected_mood].sort_values(by=hot_col, ascending=False).head(20)
        
        cols = st.columns(4)
        for i, (idx, row) in enumerate(display_df.iterrows()):
            with cols[i % 4]:
                # Path construction: images/010/010127001.jpg
                img_path = os.path.join("images", str(row['image_path']))
                
                if os.path.exists(img_path):
                    st.image(Image.open(img_path), use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/200x300.png?text=H%26M+Style", use_container_width=True)
                
                st.markdown(f"**{row['prod_name']}**")
                st.caption(f"{row.get('garment_group_name', 'H&M Premium')}")
                
                # Scientific Hotness Indicator
                st.progress(float(row[hot_col]), text=f"Popularity: {row[hot_col]:.2f}")
                
                with st.expander("AI Stylist Insights"):
                    st.write(row.get('detail_desc', "A versatile piece designed for comfort and style."))

    # TAB 2: SEASONAL TRENDS (plotly)
    with tab2:
        st.subheader("Seasonal Mood Density Chart")
        # Visualizing the seasonality of moods
        mood_list = list(articles[mood_col].unique())
        fig = px.area(seasonal, x="month", y=mood_list,
                      color_discrete_sequence=px.colors.qualitative.Bold,
                      template="plotly_white")
        fig.update_layout(xaxis_title="Month", yaxis_title="Trend Intensity")
        st.plotly_chart(fig, use_container_width=True)

    # TAB 3: METHODOLOGY
    with tab3:
        st.subheader("How the Stylist Works")
        st.info("""
        **Data Scale:** 31 Million Transactions analyzed.  
        **Optimization:** 25:100 Stratified Sampling applied for web performance.  
        **Accuracy:** Professional Mode achieves 0.91 Recall for workwear detection.  
        **Inference:** Visual DNA extracted via ResNet50 Convolutional Neural Network.
        """)
        st.write("Current User DNA Vector:")
        st.json(u_info.to_dict())

else:
    st.error("Connection Interrupted: Ensure Google Drive files are shared as 'Anyone with the link can view'.")
