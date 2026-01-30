import streamlit as st
import pandas as pd
import gdown
import os
import zipfile
import io
from typing import Optional, Tuple

# Google Drive file IDs
DRIVE_FILES = {
    'article_master_web': '1LBli1p1ee714ndmRC716SGWKBZkiiyzj',
    'customer_dna_web': '1bLxYRUweEX4EJjfz3LFQqR5gVB4gtz9h',
    'customer_test_validation': '11C9ZGG17VkVR9J5qr34WANEdHB8-MM9C',
    'visual_dna_embeddings': '1bs2LUhcdjeMAOlVYiuYHXL38H2r3XnDz',
    'hm_web_images': '1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT'
}

@st.cache_resource
def load_data_from_drive() -> dict:
    """
    Load all datasets from Google Drive with caching.
    Returns a dictionary with all dataframes and image paths.
    """
    data = {}
    
    # Create data directory if not exists
    os.makedirs('data', exist_ok=True)
    
    # Load CSV files
    csv_files = ['article_master_web', 'customer_dna_web', 'customer_test_validation', 'visual_dna_embeddings']
    
    for file_name in csv_files:
        file_path = f'data/{file_name}.csv'
        
        # Download if not exists
        if not os.path.exists(file_path):
            st.info(f"📥 Downloading {file_name}...")
            try:
                url = f"https://drive.google.com/uc?id={DRIVE_FILES[file_name]}"
                gdown.download(url, file_path, quiet=False)
            except Exception as e:
                st.error(f"Error downloading {file_name}: {e}")
                continue
        
        # Load CSV
        try:
            data[file_name] = pd.read_csv(file_path)
            st.success(f"✅ Loaded {file_name}: {len(data[file_name])} rows")
        except Exception as e:
            st.error(f"Error loading {file_name}: {e}")
    
    # Load and extract images
    images_zip_path = 'data/hm_web_images.zip'
    images_dir = 'data/hm_web_images'
    
    if not os.path.exists(images_dir):
        if not os.path.exists(images_zip_path):
            st.info("📥 Downloading product images...")
            try:
                url = f"https://drive.google.com/uc?id={DRIVE_FILES['hm_web_images']}"
                gdown.download(url, images_zip_path, quiet=False)
            except Exception as e:
                st.error(f"Error downloading images: {e}")
        
        # Extract zip
        if os.path.exists(images_zip_path):
            st.info("📦 Extracting product images...")
            try:
                with zipfile.ZipFile(images_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(images_dir)
                st.success("✅ Images extracted successfully")
            except Exception as e:
                st.error(f"Error extracting images: {e}")
    
    data['images_dir'] = images_dir
    return data

def get_image_path(article_id: str, images_dir: str) -> Optional[str]:
    """Get the image path for a given article ID."""
    article_id = str(article_id).zfill(10)
    image_path = os.path.join(images_dir, f"{article_id}.jpg")
    
    if os.path.exists(image_path):
        return image_path
    return None

def filter_products(df: pd.DataFrame, 
                   mood: Optional[str] = None,
                   price_range: Optional[Tuple[float, float]] = None,
                   color: Optional[str] = None,
                   hotness_min: Optional[float] = None) -> pd.DataFrame:
    """Filter products based on criteria."""
    result = df.copy()
    
    if mood and mood != "All Moods":
        result = result[result['mood'] == mood]
    
    if price_range:
        result = result[(result['price'] >= price_range[0]) & (result['price'] <= price_range[1])]
    
    if color and color != "All Colors":
        result = result[result['perceived_colour_master_name'] == color]
    
    if hotness_min:
        result = result[result['hotness_score'] >= hotness_min]
    
    return result
