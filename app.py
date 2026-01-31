import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gdown
import os
import zipfile
from typing import Optional, Dict, Tuple, List
import warnings
import urllib.request
import requests

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="H & M Fashion BI - Executive Dashboard",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .header-title { font-size: 3.5rem; font-weight: 900; background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; letter-spacing: -1px; }
    .subtitle { font-size: 1.2rem; color: #666; margin-bottom: 2rem; font-weight: 500; }
    
    .tier-premium { background: linear-gradient(135deg, #1e5631 0%, #40916c 100%); color: white; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-premium:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(30, 86, 49, 0.3); }
    
    .tier-trend { background: linear-gradient(135deg, #52b788 0%, #74c69d 100%); color: white; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-trend:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(82, 183, 136, 0.3); }
    
    .tier-stability { background: linear-gradient(135deg, #ffd60a 0%, #ffc300 100%); color: #333; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-stability:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(255, 214, 10, 0.3); }
    
    .tier-liquidation { background: linear-gradient(135deg, #ffb4a2 0%, #ff8b7b 100%); color: white; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-liquidation:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(255, 139, 123, 0.3); }
    
    .product-card { border: 2px solid #e0e0e0; border-radius: 12px; padding: 12px; text-align: center; transition: all 0.3s ease; background: white; position: relative; }
    .product-card:hover { border-color: #E50019; box-shadow: 0 8px 20px rgba(229, 0, 25, 0.2); transform: translateY(-4px); }
    
    .match-badge { position: absolute; top: 10px; right: 10px; background: rgba(229, 0, 25, 0.9); color: white; padding: 4px 8px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; z-index: 10; }
    
    .detail-panel { background: white; border-left: 5px solid #E50019; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-top: 20px; }
    .insight-box { background: #f0f2f6; padding: 15px; border-left: 4px solid #E50019; border-radius: 5px; margin: 10px 0; }
    .metric-badge { background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); color: white; padding: 10px 15px; border-radius: 8px; font-weight: bold; display: inline-block; margin: 5px 5px 5px 0; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'selected_tier' not in st.session_state:
    st.session_state.selected_tier = None
if 'detail_product_id' not in st.session_state:
    st.session_state.detail_product_id = None

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def ensure_data_dir():
    os.makedirs('data', exist_ok=True)

def download_from_drive(file_id: str, file_path: str) -> bool:
    try:
        if os.path.exists(file_path): return True
        try:
            gdown.download(id=file_id, output=file_path, quiet=False, fuzzy=True)
        except:
            url = f"https://drive.google.com/uc?id={file_id}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(file_path, 'wb') as f: f.write(response.content)
        return os.path.exists(file_path)
    except: return False

@st.cache_resource
def load_data_from_drive() -> Dict:
    data = {}
    ensure_data_dir()
    DRIVE_FILES = {
        'article_master_web': '1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK',
        'customer_dna_master': '182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH',
        'customer_test_validation': '1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB',
        'visual_dna_embeddings': '1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54',
        'hm_web_images': '1z27fEDUpgXfiFzb1eUv5i5pbIA_cI7UA'
    }
    csv_files = {
        'article_master_web': 'article_master_web.csv',
        'customer_dna_master': 'customer_dna_master.csv',
        'customer_test_validation': 'customer_test_validation.csv'
    }
    for key, filename in csv_files.items():
        file_path = f'data/{filename}'
        if download_from_drive(DRIVE_FILES[key], file_path):
            data[key] = pd.read_csv(file_path)
    
    images_zip_path, images_dir = 'data/hm_web_images.zip', 'data/hm_web_images'
    if not os.path.exists(images_dir):
        if download_from_drive(DRIVE_FILES['hm_web_images'], images_zip_path):
            if zipfile.is_zipfile(images_zip_path):
                with zipfile.ZipFile(images_zip_path, 'r') as zip_ref: zip_ref.extractall(images_dir)
    
    if os.path.exists(images_dir):
        for root, dirs, files in os.walk(images_dir):
            if any(f.lower().endswith(('.jpg', '.jpeg', '.png')) for f in files):
                images_dir = root
                break
    data['images_dir'] = images_dir if os.path.exists(images_dir) else None
    return data

def get_image_path(article_id: str, images_dir: Optional[str]) -> Optional[str]:
    if not images_dir: return None
    article_id_str = str(article_id).zfill(10)
    for ext in ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG']:
        path = os.path.join(images_dir, f"{article_id_str}{ext}")
        if os.path.exists(path): return path
    for root, dirs, files in os.walk(images_dir):
        for f in files:
            if f.startswith(article_id_str) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                return os.path.join(root, f)
    return None

def get_tier_info(hotness: float) -> Tuple[str, str, str]:
    if hotness > 0.8: return ("💎 Premium Tier", "tier-premium", "Maximize Profit")
    elif hotness > 0.5: return ("🔥 Trend Tier", "tier-trend", "Push Marketing")
    elif hotness > 0.3: return ("⚖️ Stability Tier", "tier-stability", "Gentle Discount")
    else: return ("📉 Liquidation Tier", "tier-liquidation", "Clearance")

def get_smart_recommendations(selected_product: pd.Series, df_articles: pd.DataFrame, n=10) -> pd.DataFrame:
    candidates = df_articles[df_articles['article_id'] != selected_product['article_id']].copy()
    candidates['match_score'] = 0.0
    candidates['match_score'] += (candidates['mood'] == selected_product['mood']) * 0.4
    candidates['match_score'] += (candidates['section_name'] == selected_product['section_name']) * 0.3
    price_sim = 1 - (abs(candidates['price'] - selected_product['price']) / (max(candidates['price'].max(), 1) * 0.5)).clip(0, 1)
    candidates['match_score'] += price_sim * 0.3
    return candidates.nlargest(n, 'match_score')

# ============================================================================
# MAIN APP
# ============================================================================
data = load_data_from_drive()
df_articles = data['article_master_web']
images_dir = data.get('images_dir')

st.sidebar.markdown("## 🎯 H & M Navigation")
page = st.sidebar.radio("Select Page", ["📊 Executive Pulse", "🔍 Inventory & Pricing", "😊 Emotion Analytics", "👥 Customer DNA", "🤖 AI Recommendation"])

if page == "🤖 AI Recommendation":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI Recommendation Engine - Smart Discovery</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: selected_emotion = st.selectbox("Emotion", ["All"] + sorted(df_articles['mood'].unique().tolist()), key="rec_emo")
    with col2: selected_category = st.selectbox("Category", ["All"] + sorted(df_articles['section_name'].unique().tolist()), key="rec_cat")
    with col3: selected_group = st.selectbox("Product Group", ["All"] + sorted(df_articles['product_group_name'].unique().tolist()), key="rec_grp")
    with col4: price_range = st.slider("Price Range", float(df_articles['price'].min()), float(df_articles['price'].max()), (float(df_articles['price'].min()), float(df_articles['price'].max())))
    
    filtered = df_articles.copy()
    if selected_emotion != "All": filtered = filtered[filtered['mood'] == selected_emotion]
    if selected_category != "All": filtered = filtered[filtered['section_name'] == selected_category]
    if selected_group != "All": filtered = filtered[filtered['product_group_name'] == selected_group]
    filtered = filtered[(filtered['price'] >= price_range[0]) & (filtered['price'] <= price_range[1])]
    
    st.divider()
    
    if len(filtered) > 0:
        st.subheader(f"📦 Found {len(filtered)} products")
        cols = st.columns(5)
        for idx, (_, row) in enumerate(filtered.head(15).iterrows()):
            with cols[idx % 5]:
                with st.container(border=True):
                    img = get_image_path(row['article_id'], images_dir)
                    if img: st.image(img, use_column_width=True)
                    else: st.info("📷 No image")
                    st.markdown(f"**{row['prod_name'][:20]}...**")
                    st.caption(f"💰 ${row['price']:.2f} | 🔥 {row['hotness_score']:.2f}")
                    if st.button("View Detail", key=f"btn_{row['article_id']}", use_container_width=True):
                        st.session_state.detail_product_id = row['article_id']
        
        if st.session_state.detail_product_id:
            prod = df_articles[df_articles['article_id'] == st.session_state.detail_product_id].iloc[0]
            st.markdown(f'<div class="detail-panel">', unsafe_allow_html=True)
            col_a, col_b = st.columns([1, 2])
            with col_a:
                img = get_image_path(prod['article_id'], images_dir)
                if img: st.image(img, use_column_width=True)
            with col_b:
                st.markdown(f"## {prod['prod_name']}")
                st.markdown(f"**Category:** {prod['section_name']} | **Group:** {prod['product_group_name']}")
                st.markdown(f"**Emotion:** {prod['mood']}")
                st.markdown(f"### Description")
                st.write(prod.get('detail_desc', 'No description available.'))
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Price", f"${prod['price']:.2f}")
                c2.metric("Hotness", f"{prod['hotness_score']:.2f}")
                tier_name, _, _ = get_tier_info(prod['hotness_score'])
                c3.metric("Tier", tier_name)
            
            st.divider()
            st.subheader("🎯 Smart Match - Similar Products")
            recs = get_smart_recommendations(prod, df_articles)
            r_cols = st.columns(5)
            for r_idx, (_, r_row) in enumerate(recs.iterrows()):
                with r_cols[r_idx % 5]:
                    # Using HTML for Match Score Badge on Image
                    match_pct = int(r_row['match_score'] * 100)
                    img_path = get_image_path(r_row['article_id'], images_dir)
                    
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="match-badge">{match_pct}% Match</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if img_path: st.image(img_path, use_column_width=True)
                    st.markdown(f"**{r_row['prod_name'][:15]}...**")
                    st.caption(f"💰 ${r_row['price']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("Close Detail"):
                st.session_state.detail_product_id = None
                st.rerun()
    else:
        st.warning("No products found.")
else:
    st.info("Please select 'AI Recommendation' page to see the requested features.")
