import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NQAS Dashboard - UP", layout="wide")

st.title("📊 NQAS Dashboard - UP")
st.caption("National Quality Assurance Standards | Uttar Pradesh")

# --- 1. Data Load ---
st.sidebar.header("1. Data Load Karo")
uploaded = st.sidebar.file_uploader("Excel File Upload Karo (.xlsx)", type=["xlsx"])

if uploaded is None:
    st.info("👈 Left side se Excel file upload karo.")
    st.stop()

try:
    df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"File padhne me error: {e}")
    st.stop()

# Column ke naam saaf karo (space / capital ka issue khatam)
df.columns = [str(c).strip() for c in df.columns]

# Column dhoondo - naam thoda alag bhi ho to chalega
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
col_agg = find_col(["aggregated", "area of concern"])

# Agar Facility wala column na mile to District+Table se Facility banao
if col_facility is None:
    if col_district and col_table:
        df["Facility_Name_Temp"] = df[col_district].astype(str) + " - " + df[col_table].astype(str)
        col_facility = "Facility_Name_Temp"
    else:
        df["Facility_Name_Temp"] = "Facility 1"
        col_facility = "Facility_Name_Temp"

if col_overall is None:
    st.error(f"Overall Score wala column nahi mila. Columns hai: {list(df.columns)}")
    st.stop()

# Score ko number banao
df[col_overall] = pd.to_numeric(df[col_overall], errors="coerce")
df = df.dropna(subset=[col_overall])

# --- 2. Filter ---
st.sidebar.header("2. Filter Lagao")

def get_options(col):
    if col is None:
        return ["Sabhi"]
    vals = sorted(df[col].dropna().astype(str).unique().tolist())
    return ["Sabhi (All)"] + vals

def is_all(val):
    return val is None or "sabhi" in str(val).lower() or "all" in str(val).lower()

district_opt = get_options(col_district)
table_opt = get_options(col_table)
area_opt = get_options(col_area)

sel_district = st.sidebar.selectbox("District:", district_opt)
sel_table = st.sidebar.selectbox("Table:", table_opt)
sel_area = st.sidebar.selectbox("Area:", area_opt)

# Filter lagao
fdf = df.copy()
if col_district and not is_all(sel_district):
    fdf = fdf[fdf[col_district].astype(str) == sel_district]
if col_table and not is_all(sel_table):
    fdf = fdf[fdf[col_table].astype(str) == sel_table]
if col_area and not is_all(sel_area):
    fdf = fdf[fdf[col_area].astype(str) == sel_area]

if fdf.empty:
    st.warning("Is filter me koi data nahi hai. Filter ko Sabhi (All) karo.")
    st.stop()

# --- Top Cards - SAHI COUNT ---
# Total Facility = alag-alag Facility ka naam
total_facility = fdf[col_facility].nunique()
avg_overall = fdf[col_overall].mean()
highest = fdf[col_overall].max()
lowest = fdf[col_overall].min()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Facility", total_facility)
c2.metric("Avg Overall", f"{avg_overall:.2f}%")
c3.metric("Highest", f"{highest:.2f}%")
c4.metric("Lowest", f"{lowest:.2f}%")

st.write(f"**District:** {sel_district} | **Table:** {sel_table} | **Area:** {sel_area}")
st.divider()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Chart + Table Wise", "🏥 Facility Wise", "🗺️ District Wise"])

with tab1:
    st.subheader(f"{sel_table} - Chart")
    if col_agg and col_area:
        chart_df = fdf.sort_values(col_overall)
        fig = px.bar(chart_df, x=col_area, y=col_overall, color=col_overall,
                     color_continuous_scale="Oranges", text=col_overall)
        fig.update_layout(xaxis_title="Area", yaxis_title="Avg Score %")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write(fdf)

    st.subheader("Table (Weak se Strong)")
    show_cols = [c for c in [col_area, col_overall] if c]
    st.dataframe(fdf[show_cols].sort_values(col_overall), use_container_width=True)

with tab2:
    st.subheader("Facility Wise Comparison")
    fac_df = fdf.groupby(col_facility, as_index=False)[col_overall].mean().sort_values(col_overall, ascending=False)
    fac_df.columns = ["Facility", "Overall Score"]
    fig2 = px.bar(fac_df, x="Facility", y="Overall Score", color="Overall Score",
                  color_continuous_scale="Blues", text="Overall Score")
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(fac_df, use_container_width=True)

with tab3:
    st.subheader("District Wise Comparison")
    st.caption("Ye graph upar wale Table + Area filter ko manta hai. District filter Sabhi rakho to saare district dikhenge.")
    if col_district:
        # District Wise me District filter ko ignore karte hai taaki compare ho sake,
        # lekin Table + Area filter lagate hai
        ddf = df.copy()
        if col_table and not is_all(sel_table):
            ddf = ddf[ddf[col_table].astype(str) == sel_table]
        if col_area and not is_all(sel_area):
            ddf = ddf[ddf[col_area].astype(str) == sel_area]
        # Agar user ne koi ek District select kiya hai, to sirf wahi dikhao
        if not is_all(sel_district):
            ddf = ddf[ddf[col_district].astype(str) == sel_district]

        dist_df = ddf.groupby(col_district, as_index=False)[col_overall].mean().sort_values(col_overall, ascending=False)
        dist_df.columns = ["District", "Overall Score"]
        fig3 = px.bar(dist_df, x="District", y="Overall Score", color="Overall Score",
                       color_continuous_scale="Blues", text="Overall Score")
        fig3.update_layout(xaxis_tickangle=-45, yaxis_title="Overall Score of Health facility")
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(dist_df, use_container_width=True)
    else:
        st.warning("District wala column nahi mila.")
