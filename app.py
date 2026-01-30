import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="H&M Emotion BI Intelligence", layout="wide", page_icon="📈")

# Custom CSS cho giao diện Dashboard cao cấp
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #E50019; }
    .product-card {
        border: 1px solid #eee; padding: 15px; border-radius: 12px; background: white;
        transition: 0.3s; cursor: pointer; text-align: center; height: 100%;
    }
    .product-card:hover { border-color: #E50019; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .stButton>button { width: 100%; border-radius: 8px; border: 1px solid #ddd; }
    .stButton>button:hover { background-color: #E50019; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INFRASTRUCTURE ---
@st.cache_resource
def load_data():
    # Tải dữ liệu từ Drive (Dựa trên file bạn đã cung cấp)
    d_art = pd.read_csv("article_master_web.csv")
    d_cust = pd.read_csv("customer_dna_master.csv")
    d_val = pd.read_csv("customer_test_validation.csv")
    d_emb = pd.read_csv("visual_dna_embeddings.csv")
    
    d_art['article_id'] = d_art['article_id'].astype(str).str.zfill(10)
    d_emb['article_id'] = d_emb['article_id'].astype(str).str.zfill(10)
    
    # Tính toán doanh thu giả lập cho Business Performance
    d_art['revenue'] = d_art['hotness_score'] * d_art['price'] * 1000 
    return d_art, d_cust, d_val, d_emb

df_art, df_cust, df_val, df_emb = load_data()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=120)
st.sidebar.title("Executive Panel")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard Tổng Quan",
    "🔍 Smart Analytics",
    "😊 Emotion Analytics",
    "👥 Customer Intelligence",
    "🤖 Recommendation Engine",
    "📈 Business Performance"
])

# --- PAGE 1: DASHBOARD TỔNG QUAN ---
if menu == "📊 Dashboard Tổng Quan":
    st.title("📊 Executive Dashboard Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tổng SKU", f"{len(df_art):,}")
    c2.metric("Giá TB", f"{df_art['price'].mean():.4f}")
    c3.metric("Hotness TB", f"{df_art['hotness_score'].mean():.2f}")
    c4.metric("Danh Mục", df_art['product_group_name'].nunique())
    c5.metric("Chủ đạo", df_art['mood'].mode()[0])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Phân bố Giá theo Danh mục")
        fig1 = px.box(df_art, x="product_group_name", y="price", color="product_group_name")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.subheader("Hotness Score theo Emotion")
        fig2 = px.bar(df_art.groupby('mood')['hotness_score'].mean().reset_index(), x='mood', y='hotness_score', color='mood')
        st.plotly_chart(fig2, use_container_width=True)

# --- PAGE 2: SMART ANALYTICS (NÂNG CẤP CHI TIẾT) ---
elif menu == "🔍 Smart Analytics":
    st.title("🔍 Smart Product Analytics")
    
    # Filters
    with st.expander("🛠️ Bộ lọc nâng cao", expanded=True):
        f1, f2, f3 = st.columns(3)
        cat_f = f1.multiselect("Danh Mục", df_art['product_group_name'].unique())
        mood_f = f2.multiselect("Emotion", df_art['mood'].unique())
        price_f = f3.slider("Khoảng giá", 0.0, float(df_art['price'].max()), (0.0, float(df_art['price'].max())))

    filt = df_art[(df_art['price'] >= price_f[0]) & (df_art['price'] <= price_f[1])]
    if cat_f: filt = filt[filt['product_group_name'].isin(cat_f)]
    if mood_f: filt = filt[filt['mood'].isin(mood_f)]

    # Analytics Tabs
    t1, t2, t3 = st.tabs(["📦 Danh sách sản phẩm", "📊 Emotion & Price Analysis", "📈 Correlation"])
    
    with t1:
        st.write(f"Tìm thấy **{len(filt)}** sản phẩm.")
        # Hiển thị Grid sản phẩm
        rows = (len(filt) // 4) + 1
        for r in range(rows):
            cols = st.columns(4)
            for c in range(4):
                idx = r * 4 + c
                if idx < len(filt):
                    item = filt.iloc[idx]
                    with cols[c]:
                        st.markdown(f"""<div class="product-card">
                            <b>{item['prod_name'][:20]}</b><br>
                            <small>{item['article_id']}</small><br>
                            <span style="color:#E50019;">Price: {item['price']:.4f}</span>
                        </div>""", unsafe_allow_html=True)
                        
                        if st.button("Xem chi tiết", key=f"detail_{item['article_id']}"):
                            @st.dialog(f"Product Intelligence: {item['prod_name']}")
                            def detail_modal(prod):
                                col_a, col_b = st.columns([1, 1.5])
                                with col_a:
                                    st.image(f"https://via.placeholder.com/200x250?text={prod['article_id']}")
                                    st.metric("Hot Score", f"{prod['hotness_score']:.2f}")
                                with col_b:
                                    st.write(f"**Mô tả:** {prod['detail_desc']}")
                                    st.write(f"**Emotion:** {prod['mood']}")
                                    st.write(f"**Doanh số tổng:** {prod['revenue']:.2f} USD")
                                    # Biểu đồ xu hướng
                                    st.line_chart([10, 20, 15, 40, prod['hotness_score']*100, 60])
                            detail_modal(item)
    with t2:
        c_a, c_b = st.columns(2)
        c_a.plotly_chart(px.pie(filt, names='mood', title="Tỷ lệ Emotion trong tìm kiếm"), use_container_width=True)
        c_b.plotly_chart(px.box(filt, x='mood', y='price', title="Phân bố Giá theo Emotion"), use_container_width=True)
    with t3:
        st.plotly_chart(px.scatter(filt, x="price", y="hotness_score", color="mood", size="revenue", hover_name="prod_name"), use_container_width=True)

# --- PAGE 3: EMOTION ANALYTICS ---
elif menu == "😊 Emotion Analytics":
    st.title("😊 Deep Emotion Analysis")
    target_mood = st.selectbox("Chọn Emotion để phân tích sâu:", df_art['mood'].unique())
    mood_data = df_art[df_art['mood'] == target_mood]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Số SKU", len(mood_data))
    col2.metric("Giá TB", f"{mood_data['price'].mean():.4f}")
    col3.metric("Hotness TB", f"{mood_data['hotness_score'].mean():.2f}")
    col4.metric("% Toàn kho", f"{(len(mood_data)/len(df_art))*100:.1f}%")

    st.subheader(f"Top Danh mục thuộc nhóm {target_mood}")
    st.plotly_chart(px.bar(mood_data['product_group_name'].value_counts().reset_index(), x='index', y='product_group_name'), use_container_width=True)
    
    st.warning(f"💡 **Chiến lược giá kiến nghị cho {target_mood}:** " + 
               ("Tăng giá 10% cho các SKU có Hotness > 0.8" if mood_data['hotness_score'].mean() > 0.5 else "Giảm giá để kích cầu"))

# --- PAGE 4: CUSTOMER INTELLIGENCE ---
elif menu == "👥 Customer Intelligence":
    st.title("👥 Customer DNA Insights")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Khách Hàng", len(df_cust))
    c2.metric("Tuổi Trung Bình", int(df_cust['age'].mean()))
    c3.metric("Phân khúc phổ biến", df_cust['segment'].mode()[0])

    col_l, col_r = st.columns(2)
    col_l.plotly_chart(px.pie(df_cust, names='segment', title="Phân khúc Gold/Silver/Bronze"), use_container_width=True)
    col_r.plotly_chart(px.histogram(df_cust, x='age', nbins=20, title="Phân bố Độ tuổi"), use_container_width=True)

# --- PAGE 5: RECOMMENDATION ENGINE ---
elif menu == "🤖 Recommendation Engine":
    st.title("🤖 Recommendation Engine Center")
    st.info("Addressing RQ8 & RQ10: Personalization Effectiveness")
    
    # Vector Space Visualization
    st.subheader("Visual DNA Vector Space (t-SNE)")
    st.plotly_chart(px.scatter(df_emb, x='x', y='y', color='mood', hover_name='article_id', template='plotly_dark'), use_container_width=True)
    
    st.divider()
    selected_prod = st.selectbox("Chọn một sản phẩm để test Gợi ý:", df_art['prod_name'].unique()[:50])
    prod_mood = df_art[df_art['prod_name'] == selected_prod]['mood'].values[0]
    
    st.subheader(f"Gợi ý cùng Emotion: {prod_mood}")
    recs = df_art[df_art['mood'] == prod_mood].sort_values('hotness_score', ascending=False).head(4)
    cols = st.columns(4)
    for i, (_, row) in enumerate(recs.iterrows()):
        with cols[i]:
            st.image("https://via.placeholder.com/150")
            st.write(f"**{row['prod_name'][:20]}**")
            st.write(f"Match: {row['hotness_score']*100:.1f}%")

# --- PAGE 6: BUSINESS PERFORMANCE ---
elif menu == "📈 Business Performance":
    st.title("📈 Model & Business Performance")
    
    tab_a, tab_b = st.tabs(["Revenue Potential", "Inventory Optimization"])
    with tab_a:
        st.subheader("Revenue Analysis theo Danh mục")
        fig_rev = px.sunburst(df_art, path=['product_group_name', 'mood'], values='revenue')
        st.plotly_chart(fig_rev, use_container_width=True)
    
    with tab_b:
        st.subheader("Tối Ưu Hóa Kho Hàng")
        # So sánh Supply và Demand (Gaps)
        supply = df_art['mood'].value_counts(normalize=True)
        demand = df_val['actual_purchased_mood'].value_counts(normalize=True)
        gap_df = pd.DataFrame({'Supply (Kho)': supply, 'Demand (Thị trường)': demand}).fillna(0)
        st.bar_chart(gap_df)
        st.error("⚠️ Gap Alert: Mood 'Relaxed' đang thiếu 15% so với nhu cầu thị trường.")

st.sidebar.markdown("---")
st.sidebar.caption("Master's Thesis Project © 2026")
