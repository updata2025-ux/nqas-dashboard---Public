dimport streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(page_title="NQAS Dashboard - UP", layout="wide")

st.markdown("""
<style>
.top-bar{background:#1A5276;color:white;padding:10px 15px;border-radius:5px;display:flex;justify-content:space-between;align-items:center}
.top-bar h2{margin:0;color:white;font-size:22px}
.metric-line{background:#f0f2f6;padding:8px 10px;font-weight:700;color:#1A5276;border-radius:5px;margin:8px 0px}
</style>
<div class="top-bar"><h2>🏥 NQAS Dashboard - UP</h2><div>Excel Load Karo &nbsp;|&nbsp; Full Report &nbsp;|&nbsp; Data Export &nbsp;|&nbsp; Chart Export</div></div>
""", unsafe_allow_html=True)

st.sidebar.header("1. Data Load Karo")
uploaded = st.sidebar.file_uploader("Excel File Upload Karo (.xlsx)", type=["xlsx"])
if uploaded is None:
    st.info("👈 Left side se Excel file upload karo.")
    st.stop()

df = pd.read_excel(uploaded)
df.columns = [str(c).strip() for c in df.columns]
# Tkinter wale code jaisa - Facility/District chhod ke sab numeric banao
for c in df.columns:
    if c not in ["PDF_File","Name of the facility","District","Date of External Assessment"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# === Tumhare purane code wala TABLE_MAP - Yahi asli logic hai ===
TABLE_MAP = {
    "Table 2 - Indicators": ["State certification score of the facility","Virtual assessment score of the facility","Patient Satisfaction Score","Service Availability","Drugs Availability","Diagnostic Availability","Outcome Indicators"],
    "Table 3 - Area Wise (8 Areas)": ["Area Service Provision","Area Patients Right","Area Inputs","Area Support Services","Area Wellness Clinical Services","Area Infection Control","Area Quality Management","Area Outcome"],
    "Table 4 - Theme Wise (12 Themes)": ["Oral health care","Care for Common Ophthalmic and ENT","Care in pregnancy Childbirth","Childhood Adolescent Health Services","Drugs Diagnostics","Elderly Palliative health care","Emergency Medical Services","Family Planning","Management of Communicable Diseases","Management of Mental Health Ailments","Management of Non Communicable Diseases","Neonatal Infant Health Services"],
}
TABLE_5_LABEL = "Table 5 - Standard Wise (50 Standards)"
AREA_MAP = {"Service Provision":"Area Service Provision","Patients Right":"Area Patients Right","Inputs":"Area Inputs","Support Services":"Area Support Services","Wellness & Clinical":"Area Wellness Clinical Services","Infection Control":"Area Infection Control","Quality Management":"Area Quality Management","Outcome":"Area Outcome"}

# --- Filter Bar - Photo jaisa ---
f1, f2, f3, f4, f5 = st.columns([1.5, 2, 1.5, 1, 0.8])
with f1:
    dist_list = ["Sabhi District"] + sorted(df["District"].dropna().astype(str).unique().tolist()) if "District" in df.columns else ["Sabhi District"]
    sel_dist = st.selectbox("District:", dist_list)
with f2:
    sel_table = st.selectbox("Table:", ["Table 2 - Indicators","Table 3 - Area Wise (8 Areas)","Table 4 - Theme Wise (12 Themes)", TABLE_5_LABEL], index=1)
with f3:
    sel_area = st.selectbox("Area:", ["Sabhi Area","Service Provision","Patients Right","Inputs","Support Services","Wellness & Clinical","Infection Control","Quality Management","Outcome"])
with f4:
    st.write(""); st.write("")
    st.button("🔍 Apply Filter")
with f5:
    st.write(""); st.write("")
    if st.button("↺ Reset"):
        st.rerun()

# --- Filter lagao ---
fdf = df.copy()
if sel_dist != "Sabhi District" and "District" in df.columns:
    fdf = fdf[fdf["District"].astype(str)==sel_dist]
if fdf.empty:
    st.warning("Is District me koi Facility nahi hai")
    st.stop()

col_overall = "Overall Score of Health facility"
total = len(fdf)
avg_overall = fdf[col_overall].mean() if col_overall in fdf.columns else 0
highest = fdf[col_overall].max() if col_overall in fdf.columns else 0
lowest = fdf[col_overall].min() if col_overall in fdf.columns else 0
avg_pss = fdf["Patient Satisfaction Score"].mean() if "Patient Satisfaction Score" in fdf.columns else 0

st.markdown(f"""<div class="metric-line">Total: {total} &nbsp;|&nbsp; Avg Overall: {avg_overall:.2f}% &nbsp;|&nbsp; Highest: {highest:.2f}% &nbsp;|&nbsp; Lowest: {lowest:.2f}% &nbsp;|&nbsp; Avg PSS: {avg_pss:.2f}% &nbsp;|&nbsp; District: {sel_dist} &nbsp;|&nbsp; Table: {sel_table}</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Chart + Table Wise", "🏥 Facility Wise", "🗺️ District Wise"])

with tab1:
    # --- Column chuno - Tkinter wala logic ---
    if sel_table == TABLE_5_LABEL:
        cols = [c for c in df.columns if re.match(r"^[A-H]\d+-", c)]
        short = [c.split("-")[0] for c in cols]
    else:
        cols = [c for c in TABLE_MAP.get(sel_table, []) if c in fdf.columns]
        short = [c.replace("Area ","").replace(" Score","") for c in cols]

    # Agar Area select hai aur Table 3 hai to sirf 1 column
    if sel_area not in ["Sabhi Area","",None] and sel_table.startswith("Table 3"):
        if sel_area in AREA_MAP:
            cols = [AREA_MAP[sel_area]]
            short = [sel_area]

    if not cols:
        st.error(f"Is Table ke column Excel me nahi mile. Excel ke columns: {list(df.columns)}")
        st.stop()

    vals = [fdf[c].mean() for c in cols]

    st.markdown(f"<h4 style='text-align:center'>{sel_table} - Chart ({sel_dist})</h4>", unsafe_allow_html=True)
    c_chart, c_table = st.columns([1.4, 1])
    with c_chart:
        colors = ["#27AE60" if v>=70 else "#F39C12" if v>=50 else "#E74C3C" for v in vals]
        fig = go.Figure()
        if len(cols) > 15:
            fig.add_trace(go.Bar(y=short, x=vals, orientation="h", marker_color=colors, text=[f"{v:.1f}%" for v in vals], textposition="outside"))
            fig.update_layout(xaxis_range=[0,100], height=600)
        else:
            fig.add_trace(go.Bar(x=short, y=vals, marker_color=colors, text=[f"{v:.1f}%" for v in vals], textposition="outside"))
            fig.update_layout(yaxis_range=[0,100], height=550, xaxis_tickangle=-30)
        fig.update_layout(title=sel_table, yaxis_title="Avg Score %")
        st.plotly_chart(fig, use_container_width=True)
    with c_table:
        st.markdown(f"<h5 style='text-align:center'>{sel_table} - Table (Weak se Strong)</h5>", unsafe_allow_html=True)
        table_df = pd.DataFrame({"Indicator / Area / Standard": [f"{s} - {full[:60]}" for s, full in zip(short, cols)], "Avg Score %": vals}).sort_values("Avg Score %")
        st.dataframe(table_df, use_container_width=True, height=550)

with tab2:
    st.subheader("Facility Wise")
    show_cols = ["Name of the facility","District", col_overall, "Patient Satisfaction Score", "Area Service Provision","Area Inputs","Area Infection Control","Area Quality Management"]
    show_cols = [c for c in show_cols if c in fdf.columns]
    st.dataframe(fdf[show_cols].sort_values(col_overall, ascending=False) if col_overall in fdf.columns else fdf[show_cols], use_container_width=True)

with tab3:
    st.subheader("District Wise")
    if "District" in df.columns and col_overall in df.columns:
        g = df.groupby("District").agg(Count=("Name of the facility","count"), AvgOverall=(col_overall,"mean"), AvgPSS=("Patient Satisfaction Score","mean")).reset_index().sort_values("AvgOverall", ascending=False)
        g.columns = ["District","Facility Count","Avg Overall %","Avg PSS %"]
        st.dataframe(g, use_container_width=True)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=g["District"], y=g["Avg Overall %"], marker_color=["#27AE60" if v>=70 else "#F39C12" for v in g["Avg Overall %"]], text=g["Avg Overall %"].round(1).astype(str)+"%", textposition="outside"))
        fig3.update_layout(yaxis_range=[0,100], xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig3, use_container_width=True)
