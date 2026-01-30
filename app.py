import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os

# --- 1. SETTINGS & ENTERPRISE THEME ---
st.set_page_config(page_title="H&M AI Strategic Intelligence", layout="wide", page_icon="📈")

# Custom CSS cho giao diện Dashboard cao cấp
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    .main-card { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
    .rec-container { border: 1px solid #E0E0E0; border-radius: 12px; padding: 15px; background: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA INFRASTRUCTURE ---
@st.cache_resource
def load_enterprise_data():
    # Thư mục chứa data
    if not os.path.exists('data'): os.makedirs('data')
    
    files = {
        "articles": ("1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK", "data/article_master.csv"),
        "customers": ("182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH", "data/customer_dna.csv"),
        "validation": ("1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB", "data/validation.csv"),
        "embeddings": ("1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54", "data/embeddings.csv"),
        "images": ("1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT", "data/images.zip")
    }
    
    for key, (fid, path) in files.items():
        if not os.path.exists(path):
            gdown.download(f'https://drive.google.com/uc?id={fid}', path, quiet=True)
            
    if not os.path.exists('images'):
        with zipfile.ZipFile("data/images.zip", 'r') as z:
            z.extractall('images')

    df_art = pd.read_csv("data/article_master.csv")
    df_cust = pd.read_csv("data/customer_dna.csv")
    df_val = pd.read_csv("data/validation.csv")
    df_emb = pd.read_csv("data/embeddings.csv")
    
    # Chuẩn hóa ID
    for df in [df_art, df_emb]: df['article_id'] = df['article_id'].astype(str).str.zfill(10)
    
    return df_art, df_cust, df_val, df_emb

df_art, df_cust, df_val, df_emb = load_enterprise_data()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=120)
st.sidebar.title("Intelligence Hub")
menu = st.sidebar.radio("Executive Modules", [
    "🎯 AI Personal Recommender",
    "📊 Inventory Strategy BI",
    "🌌 Neural Visual Exploration"
])

# --- 4. MODULE 1: PERSONALIZED RECOMMENDATIONS (THE CORE) ---
if menu == "🎯 AI Personal Recommender":
    st.title("🚀 Deep Learning Personalization Engine")
    st.markdown("### Individualized Customer DNA Matching")
    
    # Giả lập chọn khách hàng
    c_list = df_val['customer_id'].unique()[:50]
    selected_cid = st.selectbox("Select Customer for Profile Analysis:", c_list)
    
    if selected_cid:
        # 1. Profile Analysis
        c_info = df_cust[df_cust['customer_id'] == selected_cid].iloc[0]
        v_info = df_val[df_val['customer_id'] == selected_cid].iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown(f"<div class='stat-card'>Tier<br><b>{c_info['segment']}</b></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='stat-card'>Age<br><b>{int(c_info['age'])}</b></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='stat-card'>Affinity<br><b>{v_info['actual_purchased_mood']}</b></div>", unsafe_allow_html=True)
        with col4: st.markdown(f"<div class='stat-card'>Spending<br><b>{c_info['avg_spending']:.3f}</b></div>", unsafe_allow_html=True)

        st.divider()
        
        # 2. Recommendation Logic (Nghiên cứu yêu cầu: Thêm Categories)
        st.subheader("🛍️ AI Suggested Multi-Category Bundle")
        target_mood = v_info['actual_purchased_mood']
        
        # Lấy sản phẩm hot từ các Category khác nhau để tạo bundle chuyên nghiệp
        categories = df_art['product_group_name'].unique()[:4]
        rec_cols = st.columns(4)
        
        for i, cat in enumerate(categories):
            with rec_cols[i]:
                # Logic: Cùng mood, đúng category, hot nhất
                item = df_art[(df_art['mood'] == target_mood) & (df_art['product_group_name'] == cat)].sort_values('hotness_score', ascending=False).head(1)
                if not item.empty:
                    row = item.iloc[0]
                    st.markdown('<div class="rec-container">', unsafe_allow_html=True)
                    img_path = f"images/{row['article_id']}.jpg"
                    if os.path.exists(img_path): st.image(img_path, use_container_width=True)
                    st.write(f"**{cat}**")
                    st.caption(f"{row['prod_name'][:25]}...")
                    st.metric("Match Score", f"{row['hotness_score']*100:.1f}%")
                    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MODULE 2: STRATEGIC BI (RESEARCH ORIENTED) ---
elif menu == "📊 Inventory Strategy BI":
    st.title("📊 Strategic Inventory Analytics")
    st.markdown("### Addressing Research Questions: Pricing & Market Gaps")

    tab1, tab2 = st.tabs(["💰 Pricing Strategy", "📉 Demand-Supply Gap"])
    
    with tab1:
        st.subheader("Price Distribution by Emotional Design (Mood)")
        fig_box = px.box(df_art, x="mood", y="price", color="mood", notched=True, template="plotly_white")
        st.plotly_chart(fig_box, width="stretch")
        st.info("💡 Insight: Nhóm 'Confidence (Professional)' thường có dải giá cao hơn và độ tập trung Hotness ổn định hơn.")

    with tab2:
        st.subheader("Market Gap Analysis (Category-wise)")
        # So sánh cung (Article) và cầu (Validation)
        supply = df_art['mood'].value_counts(normalize=True).reset_index()
        demand = df_val['actual_purchased_mood'].value_counts(normalize=True).reset_index()
        
        fig_gap = go.Figure()
        fig_gap.add_trace(go.Bar(x=supply['mood'], y=supply['proportion'], name='Inventory Supply'))
        fig_gap.add_trace(go.Bar(x=demand['actual_purchased_mood'], y=demand['proportion'], name='Customer Demand'))
        fig_gap.update_layout(barmode='group', title="Supply vs Demand mismatch by Mood")
        st.plotly_chart(fig_gap, width="stretch")

# --- 6. MODULE 3: NEURAL VISUAL EXPLORATION ---
elif menu == "🌌 Neural Visual Exploration":
    st.title("🌌 Visual DNA Latent Space")
    st.markdown("### Deep Learning Feature Mapping (t-SNE)")
    
    fig_map = px.scatter(df_emb, x='x', y='y', color='mood', hover_name='article_id',
                         template='plotly_dark', height=700,
                         color_discrete_sequence=px.colors.qualitative.Prism)
    fig_map.update_traces(marker=dict(size=4, opacity=0.8))
    st.plotly_chart(fig_map, width="stretch")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("Enterprise AI Solution v3.1")
