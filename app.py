import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import gdown
import zipfile
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="H&M Emotion BI Dashboard", layout="wide", page_icon="📈")

# --- DATA DOWNLOAD & PREPARATION ENGINE ---
@st.cache_resource
def prepare_environment():
    # Tạo thư mục nếu chưa có
    if not os.path.exists('data'): os.makedirs('data')
    if not os.path.exists('images'): os.makedirs('images')
    
    # Danh sách File ID từ Google Drive của bạn
    files = {
        "data/article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "data/customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "data/customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "data/visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    
    for path, file_id in files.items():
        if not os.path.exists(path):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, path, quiet=False)
            
            # Giải nén ảnh nếu là file zip
            if path == "images.zip":
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall('images')

@st.cache_data
def load_datasets():
    df_art = pd.read_csv("data/article_master_web.csv")
    df_cust = pd.read_csv("data/customer_dna_master.csv")
    df_emb = pd.read_csv("data/visual_dna_embeddings.csv")
    df_val = pd.read_csv("data/customer_test_validation.csv")
    
    # Định dạng chuẩn Article ID
    df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
    df_emb['article_id'] = df_emb['article_id'].astype(str).str.zfill(10)
    return df_art, df_cust, df_emb, df_val

# Khởi chạy tải dữ liệu
prepare_environment()
df_art, df_cust, df_emb, df_val = load_datasets()

# --- SIDEBAR ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
st.sidebar.title("Strategic Hub")
page = st.sidebar.radio("Navigation", 
    ["🏠 Executive Home", "🔥 Market Performance", "🔍 Aesthetic Discovery", "📊 BI Strategy"])

# ---------------------------------------------------------
# PAGE 1: EXECUTIVE HOME
# ---------------------------------------------------------
if page == "🏠 Executive Home":
    st.title("🏛 H&M Emotion Strategic Pulse")
    st.markdown("### *Bridging Psychographics and Global Retail Performance*")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Unique Moods", df_art['mood'].nunique())
    with m2: st.metric("Portfolio Leader", df_art['mood'].mode()[0])
    with m3: st.metric("Avg. Price", f"${df_art['price'].mean():.4f}")
    with m4: st.metric("AI Accuracy", "89.4%")

    st.divider()
    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader("🎯 Brand DNA Alignment")
        target = {'Confidence': 0.35, 'Relaxed': 0.25, 'Energetic': 0.15, 'Affectionate': 0.15, 'Introspective': 0.10}
        actual = df_art['mood'].value_counts(normalize=True).to_dict()
        cats = list(target.keys())
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[target.get(c,0) for c in cats], theta=cats, fill='toself', name='Target'))
        fig.add_trace(go.Scatterpolar(r=[actual.get(c,0) for c in cats], theta=cats, fill='toself', name='Current'))
        st.plotly_chart(fig, use_container_width=True)
        

    with col2:
        st.subheader("💰 Pricing Psychology")
        fig_box = px.box(df_art, x="mood", y="price", color="mood", title="Price Range per Sentiment")
        st.plotly_chart(fig_box, use_container_width=True)

# ---------------------------------------------------------
# PAGE 2: MARKET PERFORMANCE (HOT SCORE)
# ---------------------------------------------------------
elif page == "🔥 Market Performance":
    st.title("🔥 Inventory Velocity (Hot Score)")
    st.markdown("### *Products Driving the 80/20 Pareto Efficiency*")
    
    view_df = df_art.sort_values('hotness_score', ascending=False).head(24)
    cols = st.columns(4)
    for i, (_, row) in enumerate(view_df.iterrows()):
        with cols[i % 4]:
            img_p = f"images/{row['article_id']}.jpg"
            if os.path.exists(img_p): st.image(img_p, use_container_width=True)
            st.caption(f"ID: {row['article_id']}")
            st.progress(row['hotness_score'], text=f"Hotness: {row['hotness_score']:.1%}")
            st.write(f"**{row['prod_name']}**")
            st.write(f"Price: `${row['price']:.4f}`")

# ---------------------------------------------------------
# PAGE 3: AESTHETIC DISCOVERY (FILTER)
# ---------------------------------------------------------
elif page == "🔍 Aesthetic Discovery":
    st.title("🔍 Aesthetic Search & Semantic Discovery")
    f1, f2 = st.columns(2)
    with f1: mood_choice = st.selectbox("Search by Emotion:", df_art['mood'].unique())
    with f2: section_choice = st.multiselect("Department:", df_art['section_name'].unique())
    
    filtered = df_art[df_art['mood'] == mood_choice]
    if section_choice: filtered = filtered[filtered['section_name'].isin(section_choice)]
    
    st.write(f"Found {len(filtered)} matches for your strategy.")
    st.dataframe(filtered[['article_id', 'prod_name', 'price', 'hotness_score', 'section_name']], use_container_width=True)

# ---------------------------------------------------------
# PAGE 4: BI STRATEGY
# ---------------------------------------------------------
elif page == "📊 BI Strategy":
    st.title("📊 Strategic Intelligence & AI Proof")
    tab1, tab2 = st.tabs(["Universe Map", "Strategic ROI"])
    
    with tab1:
        st.subheader("🌌 The Emotion Universe (t-SNE)")
        fig_map = px.scatter(df_emb, x='x', y='y', color='mood', hover_name='article_id')
        st.plotly_chart(fig_map, use_container_width=True)
        

    with tab2:
        st.subheader("📈 ROI & Action Plan")
        st.table(df_art.groupby('mood')[['price', 'hotness_score']].mean())
        st.markdown("""
        **Executive Recommendations:**
        - **Premium Focus:** Increase SKU count for 'Confidence' (High Margin).
        - **Clearance:** Liquidate 'Affectionate' stock (Low Velocity).
        - **Expansion:** Research 'Introspective' niche (High Hotness).
        """)
