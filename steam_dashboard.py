import streamlit as st
import pandas as pd
import ast
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Steam Genre Research", layout="wide")

# 1. SESSION STATE
if 'profiles' not in st.session_state:
    st.session_state.profiles = {"Default Research": {}}
if 'current_profile' not in st.session_state:
    st.session_state.current_profile = "Default Research"

# 2. LOAD DATA
@st.cache_data
def load_data():
    file_path = 'games_march2025_cleaned.csv'
    
    # 1. ONLY load the essential columns (Total reviews = positive + negative)
    cols = ['name', 'release_date', 'price', 'positive', 'negative', 'tags']
    
    # 2. Optimized loading
    df = pd.read_csv(
        file_path, 
        usecols=cols, 
        low_memory=False,
        # Force numerical columns to use less RAM
        dtype={'positive': 'float32', 'negative': 'float32', 'price': 'str'} 
    )
    
    # 3. Handle dates efficiently
    df['release_date'] = pd.to_datetime(df['release_date'], dayfirst=True, errors='coerce')
    
    # 4. Create review count and immediately drop 'positive'/'negative' to save RAM
    df['total_reviews'] = df['positive'].fillna(0) + df['negative'].fillna(0)
    df = df.drop(columns=['positive', 'negative'])
    
    # 5. Process tags
    def extract_keys(tag_str):
        try: 
            return [str(k).lower().strip() for k in ast.literal_eval(tag_str).keys()]
        except: 
            return []
            
    df['tags_list'] = df['tags'].apply(extract_keys)
    # Drop the original massive 'tags' text column now that we have the list
    df = df.drop(columns=['tags'])
    
    return df

df = load_data()
all_tags = sorted(list(set([tag for sublist in df['tags_list'] for tag in sublist])))

# 3. SIDEBAR: PROFILE & THRESHOLD
st.sidebar.header("📁 Profile Manager")
new_p_name = st.sidebar.text_input("New Profile Name")
if st.sidebar.button("➕ Create Profile"):
    if new_p_name and new_p_name not in st.session_state.profiles:
        st.session_state.profiles[new_p_name] = {}
        st.session_state.current_profile = new_p_name
        st.rerun()

st.session_state.current_profile = st.sidebar.selectbox(
    "Active Profile", 
    options=list(st.session_state.profiles.keys()), 
    index=list(st.session_state.profiles.keys()).index(st.session_state.current_profile)
)

st.sidebar.divider()
st.sidebar.header("⚙️ Global Filters")

# NEW: Date Slider
min_date = df['release_date'].min().to_pydatetime()
max_date = df['release_date'].max().to_pydatetime()
start_date = st.sidebar.slider(
    "Earliest Release Date",
    min_value=min_date,
    max_value=max_date,
    value=datetime(2024, 1, 1) # Default to 2024 and newer
)

# Price & Threshold
paid_only = st.sidebar.toggle("Exclude Free Games", value=True)
threshold = st.sidebar.slider("Success Threshold (Reviews)", 0, 5000, 1000)

# 4. APPLY GLOBAL FILTERS
filtered_df = df.copy()
filtered_df = filtered_df[filtered_df['release_date'] >= pd.to_datetime(start_date)]

if paid_only:
    filtered_df = filtered_df[pd.to_numeric(filtered_df['price'], errors='coerce').fillna(0) > 0]

# 5. MAIN INTERFACE: CATEGORY BUILDER
st.title(f"📊 {st.session_state.current_profile}")
col1, col2 = st.columns([1, 2])

with col1:
    with st.form("add_cat_form", clear_on_submit=True):
        name = st.text_input("Category Name")
        inc = st.multiselect("Inclusions", options=all_tags)
        exc = st.multiselect("Exclusions", options=all_tags)
        if st.form_submit_button("Add to Profile") and name:
            st.session_state.profiles[st.session_state.current_profile][name] = {"inc": inc, "exc": exc}
            st.rerun()
    
    if st.button("🗑️ Clear Profile"):
        st.session_state.profiles[st.session_state.current_profile] = {}
        st.rerun()

# 6. CALCULATE RESULTS
results = []
for cat_name, tags in st.session_state.profiles[st.session_state.current_profile].items():
    inc_tags = [t.lower() for t in tags['inc']]
    exc_tags = [t.lower() for t in tags['exc']]
    
    mask = filtered_df['tags_list'].apply(lambda x: 
        all(t in x for t in inc_tags) and not any(t in x for t in exc_tags)
    )
    matched = filtered_df[mask]
    
    count = len(matched)
    if count > 0:
        hits = len(matched[matched['total_reviews'] >= threshold])
        rate = (hits / count) * 100
        med = matched['total_reviews'].median()
    else:
        rate, med = 0, 0
    
    results.append({"Category": cat_name, "Games": count, "Median": med, "Hit Rate %": round(rate, 2)})

# 7. DISPLAY
if results:
    res_df = pd.DataFrame(results).sort_values("Median", ascending=False)
    with col2:
        st.dataframe(res_df, use_container_width=True, hide_index=True)
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.bar(res_df['Category'], res_df['Games'], color='#d3d3d3')
        ax2 = ax1.twinx()
        ax2.plot(res_df['Category'], res_df['Median'], color='blue', marker='o')
        st.pyplot(fig)