import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NQAS Dashboard - UP", layout="wide", page_icon="📊")

st.markdown("""
<style>
.main { background-color: #f8f9fa; }
h1 { color: #0B3D6B; }
</style>
""", unsafe_allow_html=True)

st.title("📊 NQAS Dashboard - UP")
st.caption("National Quality Assurance Standards | Uttar Pradesh")

# --- SIDEBAR: EXCEL UPLOAD ---
st.sidebar.header("1. Data Load Karo")
uploaded = st.sidebar.file_uploader("Excel File Upload Karo (.xlsx)", type=["xlsx", "xls"])

if uploaded is None:
    st.info("👈 Pehle Sidebar se apni Excel File (PDF to Excel.xlsx) upload karo")
    st.markdown("""
    **Excel me ye Columns hone chahiye:**
    - `District` | `Facility` | `Table` | `Area / Indicator` | `Score %`
    - Agar naam thode alag hai to bhi chalega, code auto-detect kar lega.
    """)
    st.stop()

# --- DATA LOAD ---
try:
    df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Excel khulne me dikkat: {e}")
    st.stop()

# Column naam saaf karo
df.columns = [str(c).strip() for c in df.columns]

# Column Auto-Detect
def find_col(keywords):
    for c in df.columns:
        for k in keywords:
            if k.lower() in c.lower():
                return c
    return None

col_dist = find_col(["district"]) or df.columns[0]
col_fac = find_col(["facility", "hospital", "phc", "chc"]) or df.columns[1]
col_table = find_col(["table"]) or "Table"
col_area = find_col(["area", "indicator", "standard"]) or df.columns[3]
col_score = find_col(["score", "avg", "percentage", "%"]) or df.columns[-1]

# Agar Table column nahi hai to bana do
if col_table not in df.columns:
    df["Table"] = "Table 3 - Area Wise (8 Areas)"

df[col_score] = pd.to_numeric(df[col_score], errors='coerce')
df = df.dropna(subset=[col_score])

# --- FILTERS ---
st.sidebar.header("2. Filter Lagao")
all_dist = sorted(df[col_dist].dropna().unique().tolist())
sel_dist = st.sidebar.selectbox("District:", ["Sabhi District"] + all_dist)

all_table = sorted(df[col_table].dropna().unique().tolist())
sel_table = st.sidebar.selectbox("Table:", all_table)

df_f = df[df[col_table] == sel_table].copy()
if sel_dist != "Sabhi District":
    df_f = df_f[df_f[col_dist] == sel_dist]

# Area Filter
all_area = sorted(df_f[col_area].dropna().unique().tolist())
sel_area = st.sidebar.selectbox("Area:", ["Sabhi Area"] + all_area)
if sel_area != "Sabhi Area":
    df_f = df_f[df_f[col_area] == sel_area]

# --- TOP STATS ---
# Facility wise avg nikalna
fac_avg = df_f.groupby([col_dist, col_fac])[col_score].mean().reset_index()

total_fac = fac_avg[col_fac].nunique()
avg_overall = fac_avg[col_score].mean() if total_fac > 0 else 0
highest = fac_avg[col_score].max() if total_fac > 0 else 0
lowest = fac_avg[col_score].min() if total_fac > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Facility", total_fac)
c2.metric("Avg Overall", f"{avg_overall:.2f}%")
c3.metric("Highest", f"{highest:.2f}%")
c4.metric("Lowest", f"{lowest:.2f}%")

st.markdown(f"**District:** {sel_dist} | **Table:** {sel_table} | **Area:** {sel_area}")
st.divider()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📈 Chart + Table Wise", "🏥 Facility Wise", "🗺️ District Wise"])

with tab1:
    # Area wise avg
    area_avg = df_f.groupby(col_area)[col_score].mean().reset_index().sort_values(col_score)
    area_avg[col_score] = area_avg[col_score].round(2)

    col_chart, col_table_view = st.columns([1.3, 1])

    with col_chart:
        st.subheader(f"{sel_table} - Chart")
        # Color: 70 se upar green, neeche orange
        area_avg['Color'] = area_avg[col_score].apply(lambda x: "#2ca02c" if x >= 70 else "#ff8c00")
        fig = px.bar(area_avg, x=col_area, y=col_score, text=col_score,
                     labels={col_area: "Area", col_score: "Avg Score %"},
                     color='Color', color_discrete_map="identity")
        fig.update_layout(xaxis_tickangle=-35, height=450, showlegend=False)
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with col_table_view:
        st.subheader("Table (Weak se Strong)")
        st.dataframe(area_avg.sort_values(col_score), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Facility Wise Ranking")
    fac_table = fac_avg.sort_values(col_score, ascending=False)
    fac_table[col_score] = fac_table[col_score].round(2)
    st.dataframe(fac_table, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Facility Data Download (CSV)", fac_table.to_csv(index=False), "facility_wise.csv", "text/csv")

with tab3:
    st.subheader("District Wise Comparison")
    dist_avg = df.groupby(col_dist)[col_score].mean().reset_index().sort_values(col_score, ascending=False)
    dist_avg[col_score] = dist_avg[col_score].round(2)
    fig2 = px.bar(dist_avg, x=col_dist, y=col_score, text=col_score, color=col_score, color_continuous_scale="Blues")
    fig2.update_layout(xaxis_tickangle=-30, height=400)
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(dist_avg, use_container_width=True, hide_index=True)

# --- FULL DATA EXPORT ---
st.divider()
st.download_button("📥 Full Filtered Data Export (Excel)", df_f.to_csv(index=False), "NQAS_Filtered.csv", "text/csv")