import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="NQAS Dashboard - UP", layout="wide")

# --- Neeli Patti Wala Header ---
st.markdown("""
<style>
.top-bar{background:#1a4a6e;color:white;padding:10px 15px;border-radius:5px;display:flex;justify-content:space-between;align-items:center}
.top-bar h2{margin:0;color:white;font-size:22px}
.metric-line{background:#f0f2f6;padding:8px 10px;font-weight:700;color:#1a4a6e;border-radius:5px;margin:8px 0px}
</style>
<div class="top-bar"><h2>📊 NQAS Dashboard - UP</h2><div>Excel Load Karo &nbsp;|&nbsp; Full Report &nbsp;|&nbsp; Data Export &nbsp;|&nbsp; Chart Export</div></div>
""", unsafe_allow_html=True)

st.sidebar.header("1. Data Load Karo")
uploaded = st.sidebar.file_uploader("Excel File Upload Karo (.xlsx)", type=["xlsx"])
if uploaded is None:
    st.info("👈 Left side se Excel file upload karo.")
    st.stop()

try:
    df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"File error: {e}")
    st.stop()

df.columns = [str(c).strip() for c in df.columns]

def find_col(keywords):
    for c in df.columns:
        cl = c.lower()
        if any(k in cl for k in keywords):
            return c
    return None

col_district = find_col(["district", "zilla", "janpad"])
col_table = find_col(["table", "refer table"])
col_area = find_col(["area of concern", "area", "concern"])
col_facility = find_col(["facility", "hospital", "health facility", "name of", "institution"])
col_overall = find_col(["overall score"])
col_pss = find_col(["pss", "patient satisfaction", "satisfaction score"])
col_agg = find_col(["aggregated", "area of concern"])

if col_facility is None:
    if col_district and col_table:
        df["Facility_Name_Temp"] = df[col_district].astype(str) + " - " + df[col_table].astype(str)
        col_facility = "Facility_Name_Temp"
    else:
        df["Facility_Name_Temp"] = "Facility 1"
        col_facility = "Facility_Name_Temp"

if col_overall is None:
    st.error(f"Overall Score column nahi mila. Columns: {list(df.columns)}")
    st.stop()

df[col_overall] = pd.to_numeric(df[col_overall], errors="coerce")
df = df.dropna(subset=[col_overall])
if col_pss:
    df[col_pss] = pd.to_numeric(df[col_pss], errors="coerce")

# --- Upar Wale Filter ---
def get_options(col):
    if col is None: return ["Sabhi District" if "district" in str(col).lower() else "Sabhi"]
    vals = sorted(df[col].dropna().astype(str).unique().tolist())
    return ["Sabhi"] + vals

def is_all(v): return v is None or "sabhi" in str(v).lower() or "all" in str(v).lower()

f1, f2, f3, f4 = st.columns([2,2,2,1.2])
with f1:
    sel_district = st.selectbox("District:", get_options(col_district))
with f2:
    sel_table = st.selectbox("Table:", get_options(col_table))
with f3:
    sel_area = st.selectbox("Area:", get_options(col_area))
with f4:
    st.write("")
    st.write("")
    apply_btn = st.button("🔍 Apply Filter")

fdf = df.copy()
if col_district and not is_all(sel_district):
    fdf = fdf[fdf[col_district].astype(str) == sel_district]
if col_table and not is_all(sel_table):
    fdf = fdf[fdf[col_table].astype(str) == sel_table]
if col_area and not is_all(sel_area):
    fdf = fdf[fdf[col_area].astype(str) == sel_area]

if fdf.empty:
    st.warning("Is filter me koi data nahi hai.")
    st.stop()

total_fac = fdf[col_facility].nunique()
avg_overall = fdf[col_overall].mean()
highest = fdf[col_overall].max()
lowest = fdf[col_overall].min()
avg_pss = fdf[col_pss].mean() if col_pss else avg_overall

# --- Metric Line - Photo Jaisa ---
st.markdown(f"""<div class="metric-line">Total: {total_fac} &nbsp;|&nbsp; Avg Overall: {avg_overall:.2f}% &nbsp;|&nbsp; Highest: {highest:.2f}% &nbsp;|&nbsp; Lowest: {lowest:.2f}% &nbsp;|&nbsp; Avg PSS: {avg_pss:.2f}% &nbsp;|&nbsp; District: {sel_district} &nbsp;|&nbsp; Table: {sel_table}</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Chart + Table Wise", "🏥 Facility Wise", "🗺️ District Wise"])

with tab1:
    st.markdown(f"<h4 style='text-align:center'>{sel_table} - Chart ({sel_district})</h4>", unsafe_allow_html=True)
    # Area wise Average - Photo jaisa
    if col_area:
        area_df = fdf.groupby(col_area, as_index=False)[col_overall].mean().sort_values(col_overall)
        area_df.columns = ["Area", "Avg Score"]
        # Color: 70 se kam Orange, 70+ Green
        area_df["Color"] = area_df["Avg Score"].apply(lambda x: "#FF8C00" if x < 70 else "#2EAF62")
        # Table ke liye full naam
        area_df["FullName"] = area_df["Area"]
        c_chart, c_table = st.columns([1.4, 1])
        with c_chart:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=area_df["Area"], y=area_df["Avg Score"], marker_color=area_df["Color"], text=area_df["Avg Score"].round(1).astype(str)+"%", textposition="outside"))
            fig.update_layout(title=f"{sel_table}", yaxis_title="Avg Score %", yaxis_range=[0,100], height=550, xaxis_tickangle=-30, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with c_table:
            st.markdown(f"<h5 style='text-align:center'>{sel_table} - Table (Weak se Strong)</h5>", unsafe_allow_html=True)
            show_df = area_df[["FullName","Avg Score"]].sort_values("Avg Score")
            show_df.columns = ["Indicator / Area / Standard", "Avg Score %"]
            # Color wali table
            def color_row(val):
                try:
                    v=float(val)
                    if v < 65: return "background-color:#FFF2CC"
                    elif v < 70: return "background-color:#FFE699"
                    else: return "background-color:#D9EAD3"
                except: return ""
            st.dataframe(show_df.style.applymap(color_row, subset=["Avg Score %"]).format({"Avg Score %":"{:.2f}"}), use_container_width=True, height=550)
    else:
        st.dataframe(fdf, use_container_width=True)

with tab2:
    st.subheader("Facility Wise Comparison")
    fac_df = fdf.groupby(col_facility, as_index=False)[col_overall].mean().sort_values(col_overall, ascending=False)
    fac_df.columns = ["Facility", "Overall Score"]
    fac_df["Color"] = fac_df["Overall Score"].apply(lambda x: "#FF8C00" if x < 70 else "#2EAF62")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=fac_df["Facility"], y=fac_df["Overall Score"], marker_color=fac_df["Color"], text=fac_df["Overall Score"].round(1).astype(str)+"%", textposition="outside"))
    fig2.update_layout(yaxis_range=[0,100], xaxis_tickangle=-45, height=500)
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(fac_df[["Facility","Overall Score"]].sort_values("Overall Score"), use_container_width=True)

with tab3:
    st.subheader("District Wise Comparison")
    if col_district:
        ddf = df.copy()
        if col_table and not is_all(sel_table):
            ddf = ddf[ddf[col_table].astype(str) == sel_table]
        if col_area and not is_all(sel_area):
            ddf = ddf[ddf[col_area].astype(str) == sel_area]
        dist_df = ddf.groupby(col_district, as_index=False)[col_overall].mean().sort_values(col_overall, ascending=False)
        dist_df.columns = ["District", "Overall Score"]
        dist_df["Color"] = dist_df["Overall Score"].apply(lambda x: "#FF8C00" if x < 70 else "#2EAF62")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=dist_df["District"], y=dist_df["Overall Score"], marker_color=dist_df["Color"], text=dist_df["Overall Score"].round(1).astype(str)+"%", textposition="outside"))
        fig3.update_layout(yaxis_range=[0,100], xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(dist_df[["District","Overall Score"]], use_container_width=True)
