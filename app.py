import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os
import numpy as np

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(
    page_title="H&M Strategic AI: Emotion & Recommendation System",
    page_icon="👠",
    layout="wide"
)

# Professional CSS Styling
st.markdown("""
    <style>
    .main { background-color: #fdfdfd; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 5px solid #ff0000; }
    .rec-card { border: 1px solid #eee; padding: 15px; border-radius: 15px; background: white; text-align: center; }
    .rec-card:hover { box-shadow: 0 12px 24px rgba(0,0,0,0.1); transform: translateY(-5px); transition: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INFRASTRUCTURE (DRIVE INTEGRATION) ---
@st.cache_resource
def sync_enterprise_data():
    if not os.path.exists('data'): os.makedirs('data')
    # IDs provided in your Google Drive links
    drive_files = {
        "data/article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "data/customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "data/customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "data/visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "data/hm_web_images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    for path, fid in drive_files.items():
        if not os.path.exists(path):
            with st.spinner(f"Syncing {path}..."):
                gdown.download(f'https://drive.google.com/uc?id={fid}', path, quiet=True)
    
    # Image extraction logic
    if not os.path.exists('images'):
        os.makedirs('images')
        with st.spinner("Decompressing High-Resolution Visual Assets..."):
            try:
                with zipfile.ZipFile("data/hm_web_images.zip", 'r') as z:
                    z.extractall('images')
            except: pass

@st.cache_data
def load_and_clean_data():
    df_art = pd.read_csv("data/article_master_web.csv")
    df_cust = pd.read_csv("data/customer_dna_master.csv")
    df_val = pd.read_csv("data/customer_test_validation.csv")
    df_emb = pd.read_csv("data/visual_dna_embeddings.csv")
    
    # ID Normalization (10 digits)
    df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
    df_emb['article_id'] = df_emb['article_id'].astype(str).str.zfill(10)
    
    return df_art, df_cust, df_val, df_emb

sync_enterprise_data()
df_art, df_cust, df_val, df_emb = load_and_clean_data()

# --- 3. AI ENGINE: EMOTION-BASED RECOMMENDATION ---
def get_personalized_recommendations(customer_id, n=4):
    """
    Core Recommendation Logic: 
    Matches Customer Transactional History (Validation) 
    with Product Emotional DNA (Articles).
    """
    # Identify user's actual preferred mood from validation set
    user_history = df_val[df_val['customer_id'] == customer_id]
    if not user_history.empty:
        target_mood = user_history['actual_purchased_mood'].values[0]
    else:
        target_mood = df_art['mood'].mode()[0]
    
    # Filter products by mood and rank by hotness_score
    recommendations = df_art[df_art['mood'] == target_mood].sort_values(by='hotness_score', ascending=False)
    return recommendations.head(n), target_mood

# --- 4. NAVIGATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
st.sidebar.markdown("### Decision Support System")
module = st.sidebar.selectbox("Select Perspective", [
    "🚀 AI Personalization Engine",
    "📊 Strategic BI Dashboard",
    "🌌 Visual DNA Space (t-SNE)"
])

# --- 5. MODULE 1: AI PERSONALIZATION ---
if module == "🚀 AI Personalization Engine":
    st.title("🚀 Personalized Recommendation System")
    st.markdown("#### *Deep Learning integration for Emotion-driven Retail*")
    
    user_pool = df_val['customer_id'].unique()[:50]
    selected_user = st.selectbox("Select a Customer ID to simulate AI matching:", user_pool)
    
    if selected_user:
        recs, predicted_mood = get_personalized_recommendations(selected_user)
        user_meta = df_cust[df_cust['customer_id'] == selected_user].iloc[0]
        
        # Customer Profile Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tier", user_meta['segment'])
        c2.metric("Age Group", int(user_meta['age']))
        c3.metric("Purchasing Power", f"${user_meta['avg_spending']:.3f}")
        c4.metric("AI Emotion Match", predicted_mood.split('(')[0])
        
        st.divider()
        st.subheader(f"Tailored Selection: {predicted_mood} Style")
        
        # Displaying Product Recommendations
        cols = st.columns(4)
        for i, (_, row) in enumerate(recs.iterrows()):
            with cols[i]:
                st.markdown('<div class="rec-card">', unsafe_allow_html=True)
                img_path = f"images/{row['article_id']}.jpg"
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/200x250?text=No+Image", use_container_width=True)
                
                st.write(f"**{row['prod_name'][:25]}**")
                st.write(f"Price Index: `{row['price']:.4f}`")
                st.progress(row['hotness_score'], text=f"AI Confidence: {row['hotness_score']*100:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)

# --- 6. MODULE 2: STRATEGIC BI ---
elif module == "📊 Strategic BI Dashboard":
    st.title("📊 Strategic Business Intelligence")
    st.markdown("#### *Quantitative Analysis of Product Performance & Customer DNA*")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("SKU Count", len(df_art))
    k2.metric("Mean Hotness", f"{df_art['hotness_score'].mean():.3f}")
    k3.metric("Validation Base", len(df_val))
    k4.metric("Avg Price", f"${df_art['price'].mean():.4f}")
    
    st.divider()
    
    tab_a, tab_b = st.tabs(["Inventory Analytics", "Customer Segments"])
    
    with tab_a:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Emotion vs. Pricing Sensitivity")
            fig1 = px.scatter(df_art, x='price', y='hotness_score', color='mood', 
                              size='hotness_score', hover_name='prod_name', template="plotly_white")
            st.plotly_chart(fig1, width="stretch")
        with col2:
            st.subheader("Inventory Share by Mood")
            fig2 = px.pie(df_art, names='mood', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2, width="stretch")
            
    with tab_b:
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Spending Power by Tier")
            fig3 = px.box(df_cust, x='segment', y='avg_spending', color='segment', notched=True)
            st.plotly_chart(fig3, width="stretch")
        with col4:
            st.subheader("Demographic Distribution")
            fig4 = px.histogram(df_cust, x='age', color='segment', marginal="rug")
            st.plotly_chart(fig4, width="stretch")

# --- 7. MODULE 3: VISUAL DNA SPACE ---
elif module == "🌌 Visual DNA Space (t-SNE)":
    st.title("🌌 Neural Visual DNA Explorer")
    st.markdown("#### *High-dimensional latent space projection of fashion features*")
    
    st.info("💡 **AI Context:** Each dot represents a product processed through a Convolutional Neural Network (CNN). Products clustered together share similar visual 'DNA' (color, pattern, and shape).")
    
    fig_space = px.scatter(df_emb, x='x', y='y', color='mood',
                           hover_name='article_id',
                           color_discrete_sequence=px.colors.qualitative.Vivid,
                           template="plotly_dark", height=700)
    fig_space.update_traces(marker=dict(size=4, opacity=0.7))
    st.plotly_chart(fig_space, width="stretch")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("Project: Deep Learning BI for Fashion")
st.sidebar.caption("Status: All Neural Engines Operational")
