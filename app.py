import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(
    page_title="H&M Strategic Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thẩm mỹ: Custom CSS để giao diện giống Dashboard doanh nghiệp
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stPlotlyChart { background-color: #ffffff; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- GOOGLE DRIVE FILE IDS ---
FILES = {
    "articles": "1LBli1p1ee714ndmRC716SGWKBZkiiyzj",
    "customer": "1bLxYRUweEX4EJjfz3LFQqR5gVB4gtz9h",
    "validation": "11C9ZGG17VkVR9J5qr34WANEdHB8-MM9C",
    "embeddings": "1bs2LUhcdjeMAOlVYiuYHXL38H2r3XnDz",
    "images_zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
}

@st.cache_resource
def initialize_system():
    if not os.path.exists('data'): os.makedirs('data')
    
    # Download CSVs
    for name, file_id in FILES.items():
        if name != "images_zip":
            path = f"data/{name}.csv"
            if not os.path.exists(path):
                gdown.download(f'https://drive.google.com/uc?id={file_id}', path, quiet=True)
    
    # Download & Extract Images
    if not os.path.exists('images'):
        with st.spinner("🚀 Đang khởi tạo kho hình ảnh 3GB (Chỉ thực hiện lần đầu)..."):
            zip_path = "images.zip"
            gdown.download(f'https://drive.google.com/uc?id={FILES["images_zip"]}', zip_path, quiet=False)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall('images')
            os.remove(zip_path)
            
    return (pd.read_csv("data/articles.csv"), 
            pd.read_csv("data/customer.csv"), 
            pd.read_csv("data/embeddings.csv"),
            pd.read_csv("data/validation.csv"))

# Load Data
try:
    df_art, df_cust, df_emb, df_val = initialize_system()
except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
st.sidebar.title("H&M BI Center")
menu = st.sidebar.radio("Menu Chiến lược", ["📈 Tổng quan thị trường", "🎯 Phân tích Khách hàng", "🏬 Quản trị Kho hàng"])

# --- TAB 1: TỔNG QUAN THỊ TRƯỜNG (MARKET OVERVIEW) ---
if menu == "📈 Tổng quan thị trường":
    st.title("📈 Market Strategic Overview")
    
    # KPI Top Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng mã hàng", f"{len(df_art):,}", "Active")
    c2.metric("Mood dẫn đầu", df_art['mood'].mode()[0], "High Demand")
    c3.metric("Phân khúc Gold", f"{len(df_cust[df_cust['segment'] == 'Gold']):,}", "+12%")
    c4.metric("Avg Pareto Score", f"{df_art['hotness_score'].mean():.2f}")

    st.markdown("---")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("Phân bổ cơ cấu theo Nhóm ngành (Section)")
        fig_sec = px.sunburst(df_art, path=['section_name', 'product_group_name', 'mood'], 
                              values='hotness_score', color='hotness_score',
                              color_continuous_scale='RdBu')
        st.plotly_chart(fig_sec, use_container_width=True)

    with col_right:
        st.subheader("Tương quan Giá & Độ phổ biến (Pareto)")
        fig_scatter = px.scatter(df_art, x="price", y="hotness_score", color="mood",
                                 size="hotness_score", hover_data=['prod_name'],
                                 title="Biểu đồ phân tán Giá vs. Hotness")
        st.plotly_chart(fig_scatter, use_container_width=True)

# --- TAB 2: PHÂN TÍCH KHÁCH HÀNG (CUSTOMER INTELLIGENCE) ---
elif menu == "🎯 Phân tích Khách hàng":
    st.title("🎯 Customer DNA & Recommendations")
    
    # Bảng tra cứu thông minh
    st.subheader("Danh sách Khách hàng mục tiêu")
    search_q = st.text_input("Tìm kiếm ID Khách hàng hoặc lọc theo Segment", "")
    
    display_cust = df_cust
    if search_q:
        display_cust = df_cust[df_cust['customer_id'].str.contains(search_q) | df_cust['segment'].str.contains(search_q)]
    
    st.dataframe(display_cust.head(10), use_container_width=True)

    st.markdown("---")
    
    selected_cid = st.selectbox("Chọn một ID Khách hàng để phân tích DNA:", df_cust['customer_id'].head(100))
    
    if selected_cid:
        prof_col, rec_col = st.columns([1, 2])
        
        with prof_col:
            c_info = df_cust[df_cust['customer_id'] == selected_cid].iloc[0]
            st.markdown(f"### Profile: {c_info['segment']}")
            st.write(f"🎂 **Tuổi:** {c_info['age']}")
            st.write(f"💰 **Chi tiêu TB:** {c_info['avg_spending']:.4f}")
            st.write(f"🛒 **Tần suất mua:** {c_info['purchase_count']} lần")
            
            # Validation thực tế từ Section 10
            v_info = df_val[df_val['customer_id'] == selected_cid]
            if not v_info.empty:
                st.info(f"**Gu thực tế từ Test Set:** {v_info['actual_purchased_mood'].values[0]}")
                pref_mood = v_info['actual_purchased_mood'].values[0]
            else:
                pref_mood = "Relaxed"

        with rec_col:
            st.subheader(f"Gợi ý tối ưu cho phong cách {pref_mood}")
            recs = df_art[(df_art['mood'] == pref_mood)].sort_values(by='hotness_score', ascending=False).head(4)
            r_cols = st.columns(4)
            for idx, (_, r) in enumerate(recs.iterrows()):
                aid = str(r['article_id']).zfill(10)
                img_p = f"images/{aid}.jpg"
                if os.path.exists(img_p):
                    r_cols[idx].image(Image.open(img_p), use_column_width=True)
                    r_cols[idx].caption(f"Score: {r['hotness_score']:.2f}")

# --- TAB 3: QUẢN TRỊ KHO HÀNG (INVENTORY & SHOWROOM) ---
elif menu == "🏬 Quản trị Kho hàng":
    st.title("🏬 Enterprise Inventory Explorer")
    
    # Bộ lọc nâng cao
    col1, col2, col3 = st.columns(3)
    with col1:
        f_section = st.multiselect("Phân khúc (Section):", df_art['section_name'].unique())
    with col2:
        f_group = st.multiselect("Nhóm (Product Group):", df_art['product_group_name'].unique())
    with col3:
        f_mood = st.multiselect("Phong cách (Mood):", df_art['mood'].unique())

    # Áp dụng filter
    query = df_art.copy()
    if f_section: query = query[query['section_name'].isin(f_section)]
    if f_group: query = query[query['product_group_name'].isin(f_group)]
    if f_mood: query = query[query['mood'].isin(f_mood)]

    st.write(f"Tìm thấy **{len(query)}** sản phẩm phù hợp.")
    
    # Hiển thị Showroom dạng lưới (Grid)
    items_per_page = 20
    for i in range(0, items_per_page, 5):
        cols = st.columns(5)
        for j in range(5):
            idx = i + j
            if idx < len(query):
                item = query.iloc[idx]
                aid = str(item['article_id']).zfill(10)
                with cols[j]:
                    img_path = f"images/{aid}.jpg"
                    if os.path.exists(img_path):
                        st.image(Image.open(img_path), use_column_width=True)
                    st.markdown(f"**{item['prod_name'][:20]}...**")
                    st.markdown(f"💰 Price: `{item['price']:.4f}`")
                    st.progress(item['hotness_score'], text=f"Hotness: {item['hotness_score']:.2f}")
                    with st.expander("Chi tiết mô tả"):
                        st.write(item['detail_desc'])
