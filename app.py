import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re, io

st.set_page_config(page_title="NQAS Dashboard - UP", layout="wide")

st.markdown("""
<style>
.top-bar{background:#1A5276;color:white;padding:10px 15px;border-radius:5px;display:flex;justify-content:space-between;align-items:center}
.top-bar h2{margin:0;color:white;font-size:22px}
.metric-line{background:#f0f2f6;padding:8px 10px;font-weight:700;color:#1A5276;border-radius:5px;margin:8px 0px}
.highlight-box{background:#FEF9E7;border:2px solid #F1C40F;padding:10px;border-radius:8px;margin:10px 0px}
.step-box{background:#EAF2F8;border:1px solid #2E86C1;padding:10px;border-radius:8px;margin:5px 0px}
</style>
<div class="top-bar"><h2>🏥 NQAS Dashboard - UP</h2><div>Excel Load Karo</div></div>
""", unsafe_allow_html=True)

st.sidebar.header("1. Data Load Karo")
uploaded = st.sidebar.file_uploader("Excel File Upload Karo (.xlsx)", type=["xlsx"])
if uploaded is None:
    st.info("👈 Left side se Excel file upload karo.")
    st.stop()

df = pd.read_excel(uploaded)
df.columns = [str(c).strip() for c in df.columns]
for c in df.columns:
    if c not in ["PDF_File","Name of the facility","District","Date of External Assessment"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

TABLE_MAP = {
    "Table 2 - Indicators": ["State certification score of the facility","Virtual assessment score of the facility","Patient Satisfaction Score","Service Availability","Drugs Availability","Diagnostic Availability","Outcome Indicators"],
    "Table 3 - Area Wise (8 Areas)": ["Area Service Provision","Area Patients Right","Area Inputs","Area Support Services","Area Wellness Clinical Services","Area Infection Control","Area Quality Management","Area Outcome"],
    "Table 4 - Theme Wise (12 Themes)": ["Oral health care","Care for Common Ophthalmic and ENT","Care in pregnancy Childbirth","Childhood Adolescent Health Services","Drugs Diagnostics","Elderly Palliative health care","Emergency Medical Services","Family Planning","Management of Communicable Diseases","Management of Mental Health Ailments","Management of Non Communicable Diseases","Neonatal Infant Health Services"],
}
TABLE_5_LABEL = "Table 5 - Standard Wise (50 Standards)"
AREA_MAP = {"Service Provision":"Area Service Provision","Patients Right":"Area Patients Right","Inputs":"Area Inputs","Support Services":"Area Support Services","Wellness & Clinical":"Area Wellness Clinical Services","Infection Control":"Area Infection Control","Quality Management":"Area Quality Management","Outcome":"Area Outcome"}

LETTER_LABEL = {
    "A": "A- Service Provision",
    "B": "B- Patients Right",
    "C": "C- Inputs",
    "D": "D- Support Services",
    "E": "E- Wellness Clinical Services",
    "F": "F- Infection Control",
    "G": "G- Quality Management",
    "H": "H- Outcome"
}

# ===== FILTER BAR - Sabhi ki jagah All =====
f1, f2, f3, f4 = st.columns([1.3, 1.8, 1.8, 1.3])
with f1:
    dist_list = ["All District"] + sorted(df["District"].dropna().astype(str).unique().tolist()) if "District" in df.columns else ["All District"]
    sel_dist = st.selectbox("District:", dist_list)
with f2:
    sel_table = st.selectbox("Table:", ["Table 2 - Indicators","Table 3 - Area Wise (8 Areas)","Table 4 - Theme Wise (12 Themes)", TABLE_5_LABEL], index=1)
with f3:
    temp_df = df.copy()
    if sel_dist != "All District":
        temp_df = temp_df[temp_df["District"].astype(str)==sel_dist]
    fac_list = ["All Facility"] + sorted(temp_df["Name of the facility"].dropna().astype(str).unique().tolist()) if "Name of the facility" in df.columns else ["All Facility"]
    sel_fac = st.selectbox("Facility Select Karo:", fac_list)
with f4:
    sel_area = st.selectbox("Area:", ["All Area","Service Provision","Patients Right","Inputs","Support Services","Wellness & Clinical","Infection Control","Quality Management","Outcome"])

c_btn1, c_btn2 = st.columns([1,1])
with c_btn1:
    st.button("🔍 Apply Filter", use_container_width=True)
with c_btn2:
    if st.button("↺ Reset", use_container_width=True):
        st.rerun()

# ===== 2-STEP DROPDOWN - SIRF TABLE 5 PE =====
table5_all_cols = [c for c in df.columns if re.match(r"^[A-H]\d+-", c)]
short_to_full = {}
for c in table5_all_cols:
    short = c.split("-")[0].strip()
    short_to_full[short] = c

sel_standards = []
if sel_table == TABLE_5_LABEL:
    st.markdown(f"""<div class="highlight-box">✅ <b>Table 5 Select Hai</b> &nbsp;|&nbsp; Total Standard: {len(table5_all_cols)} &nbsp;|&nbsp; Step 1 chunte hi Chart ban jayega, Step 2 sirf kam karne ke liye hai</div>""", unsafe_allow_html=True)

    all_letters = sorted(list(set([s[0] for s in short_to_full.keys()])))
    col_step1, col_step2 = st.columns(2)
    with col_step1:
        st.markdown("<div class='step-box'><b>Step 1 - Area Chuno:</b></div>", unsafe_allow_html=True)
        sel_letters = st.multiselect(
            "1️⃣ Area Select Karo:",
            options=all_letters,
            default=[],
            placeholder="Dropdown kholo - A- Service Provision, B- Patients Right... chuno",
            format_func=lambda x: LETTER_LABEL.get(x, x),
            help="A- Service Provision chunoge to sirf A wale Standard ka Chart banega.",
            key="letter_multi"
        )
    with col_step2:
        st.markdown("<div class='step-box'><b>Step 2 - Standard Chuno (Zaroori Nahi):</b></div>", unsafe_allow_html=True)
        if len(sel_letters)==0:
            st.info("👈 Pehle Step 1 se Area chuno, tabhi Chart banega.")
            sel_short = []
            filtered_shorts = []
        else:
            filtered_shorts = [s for s in sorted(short_to_full.keys()) if s[0] in sel_letters]
            sel_labels = [LETTER_LABEL.get(l, l) for l in sel_letters]
            st.caption(f"Step 1 me chuney: {', '.join(sel_labels)} → Total {len(filtered_shorts)} Standard: {', '.join(filtered_shorts)}")
            sel_short = st.multiselect(
                "2️⃣ Standard - Agar kam karna hai to yahan se hatao / chuno, warna khaali chhodo:",
                options=filtered_shorts,
                default=[],
                placeholder="Khaali chhodo to saare aa jayenge - A1, A2...",
                help="Khaali chhodo to Step 1 wale saare Standard ka Chart banega.",
                key="std_multi_dropdown"
            )
        if len(sel_letters)>0 and len(sel_short)==0:
            sel_short = filtered_shorts
            st.info(f"ℹ️ Step 2 khaali hai, isliye Step 1 wale saare {len(sel_short)} Standard ka Chart ban raha hai.")
        sel_standards = [short_to_full[s] for s in sel_short]

    if len(sel_letters)==0:
        st.info("👆 Step 1 se pehle Area chuno - jaise A- Service Provision.")
        st.stop()
    else:
        sel_labels2 = [LETTER_LABEL.get(l, l) for l in sel_letters]
        st.success(f"✅ Chuney hue: Area = {', '.join(sel_labels2)}  |  Standard = {', '.join(sel_short)}  |  Total: {len(sel_standards)}")
else:
    st.caption("ℹ️ Area + Standard wala 2-Step Dropdown sirf **Table 5 - Standard Wise** select karne pe khulega.")

# --- Filter lagao ---
fdf = df.copy()
if sel_dist != "All District" and "District" in df.columns:
    fdf = fdf[fdf["District"].astype(str)==sel_dist]
if sel_fac != "All Facility" and "Name of the facility" in df.columns:
    fdf = fdf[fdf["Name of the facility"].astype(str)==sel_fac]
if fdf.empty:
    st.warning("Is filter me koi Facility nahi hai")
    st.stop()

col_overall = "Overall Score of Health facility"
total = len(fdf)
avg_overall = fdf[col_overall].mean() if col_overall in fdf.columns else 0
highest = fdf[col_overall].max() if col_overall in fdf.columns else 0
lowest = fdf[col_overall].min() if col_overall in fdf.columns else 0
avg_pss = fdf["Patient Satisfaction Score"].mean() if "Patient Satisfaction Score" in fdf.columns else 0
st.markdown(f"""<div class="metric-line">Total: {total} &nbsp;|&nbsp; Avg Overall: {avg_overall:.2f}% &nbsp;|&nbsp; Highest: {highest:.2f}% &nbsp;|&nbsp; Lowest: {lowest:.2f}% &nbsp;|&nbsp; Avg PSS: {avg_pss:.2f}% &nbsp;|&nbsp; District: {sel_dist} &nbsp;|&nbsp; Facility: {sel_fac} &nbsp;|&nbsp; Table: {sel_table}</div>""", unsafe_allow_html=True)

if sel_table == TABLE_5_LABEL:
    cols = [c for c in sel_standards if c in fdf.columns]
    short = [c.split("-")[0] for c in cols]
else:
    cols = [c for c in TABLE_MAP.get(sel_table, []) if c in fdf.columns]
    short = [c.replace("Area ","").replace(" Score","") for c in cols]
if sel_area not in ["All Area","",None] and sel_table.startswith("Table 3"):
    if sel_area in AREA_MAP:
        cols = [AREA_MAP[sel_area]]
        short = [sel_area]
if not cols:
    st.error("Is Table ke column Excel me nahi mile.")
    st.stop()

vals = [fdf[c].mean() for c in cols]
chart_df = pd.DataFrame({"Indicator / Area / Standard": [full[:70] for full in cols], "Avg Score %": [f"{v:.2f}" for v in vals]}).sort_values("Avg Score %")

colors = ["#27AE60" if v>=70 else "#F39C12" if v>=50 else "#E74C3C" for v in vals]
fig = go.Figure()
if len(cols) > 15:
    fig.add_trace(go.Bar(y=short, x=vals, orientation="h", marker_color=colors, text=[f"{v:.2f}%" for v in vals], textposition="outside"))
    fig.update_layout(xaxis_range=[0,100], height=600)
else:
    fig.add_trace(go.Bar(x=short, y=vals, marker_color=colors, text=[f"{v:.2f}%" for v in vals], textposition="outside"))
    fig.update_layout(yaxis_range=[0,100], height=550, xaxis_tickangle=-30)
fig.update_layout(title=f"{sel_table} - {sel_fac if sel_fac!='All Facility' else sel_dist}", yaxis_title="Avg Score %")

st.markdown("### 📥 Export Karo")
e1, e2, e3, e4 = st.columns(4)
def to_excel_bytes(sheets_dict):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for name, d in sheets_dict.items():
            d.to_excel(w, sheet_name=name[:31], index=False)
    buf.seek(0)
    return buf.getvalue()
with e1:
    st.download_button("📥 Data Export", data=to_excel_bytes({"Filtered Facility": fdf}), file_name=f"Filtered_{sel_dist}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with e2:
    try:
        g = df.groupby("District").agg(Count=("Name of the facility","count"), AvgOverall=(col_overall,"mean"), AvgPSS=("Patient Satisfaction Score","mean")).reset_index().sort_values("AvgOverall", ascending=False)
    except:
        g = pd.DataFrame()
    area_cols = TABLE_MAP["Table 3 - Area Wise (8 Areas)"]
    area_df = pd.DataFrame({"Area": area_cols, "Avg Score": [f"{fdf[c].mean():.2f}" if c in fdf.columns else "0.00" for c in area_cols]})
    st.download_button("📄 Full Report", data=to_excel_bytes({"Filtered Facility": fdf, "District Wise": g, "Area Wise": area_df}), file_name="Full_Report_NQAS.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with e3:
    st.download_button("📊 Chart Data Excel", data=to_excel_bytes({"Chart Data": chart_df}), file_name=f"Chart_{sel_table[:10]}_{sel_dist}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with e4:
    try:
        png_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
        st.download_button("🖼️ Chart PNG Export", data=png_bytes, file_name=f"Chart_{sel_table[:10]}_{sel_dist}.png", mime="image/png", use_container_width=True)
    except Exception as ex:
        pass
        
        #st.info("PNG ke liye Chart pe Camera 📷 icon dabao")

tab1, tab2, tab3 = st.tabs(["📊 Chart + Table Wise", "🏥 Facility Wise", "🗺️ District Wise"])
with tab1:
    st.markdown(f"<h4 style='text-align:center'>{sel_table} - Chart ({sel_fac if sel_fac!='All Facility' else sel_dist})</h4>", unsafe_allow_html=True)
    c_chart, c_table = st.columns([1.4, 1])
    with c_chart:
        st.plotly_chart(fig, use_container_width=True)
    with c_table:
        st.markdown(f"<h5 style='text-align:center'>{sel_table} - Table (Weak se Strong)</h5>", unsafe_allow_html=True)
        st.dataframe(chart_df, use_container_width=True, height=550)
with tab2:
    st.subheader("Facility Wise")
    show_cols = ["Name of the facility","District", col_overall, "Patient Satisfaction Score", "Area Service Provision","Area Inputs","Area Infection Control","Area Quality Management"]
    show_cols = [c for c in show_cols if c in fdf.columns]
    disp = fdf[show_cols].copy()
    for c in disp.columns:
        if c not in ["Name of the facility","District"]:
            disp[c] = disp[c].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    st.dataframe(disp.sort_values(col_overall, ascending=False) if col_overall in fdf.columns else disp, use_container_width=True)
with tab3:
    st.subheader("District Wise")
    if "District" in df.columns and col_overall in df.columns:
        g2 = df.groupby("District").agg(Count=("Name of the facility","count"), AvgOverall=(col_overall,"mean"), AvgPSS=("Patient Satisfaction Score","mean")).reset_index().sort_values("AvgOverall", ascending=False)
        g2["AvgOverall"] = g2["AvgOverall"].map(lambda x: f"{x:.2f}")
        g2["AvgPSS"] = g2["AvgPSS"].map(lambda x: f"{x:.2f}")
        g2.columns = ["District","Facility Count","Avg Overall %","Avg PSS %"]
        st.dataframe(g2, use_container_width=True)
        g3 = df.groupby("District").agg(AvgOverall=(col_overall,"mean")).reset_index().sort_values("AvgOverall", ascending=False)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=g3["District"], y=g3["AvgOverall"], marker_color=["#27AE60" if v>=70 else "#F39C12" for v in g3["AvgOverall"]], text=[f"{v:.2f}%" for v in g3["AvgOverall"]], textposition="outside"))
        fig3.update_layout(yaxis_range=[0,100], xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig3, use_container_width=True)
