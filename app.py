import streamlit as st
import pandas as pd
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Water Quality Checker Virtual Lab",
    page_icon="💧",
    layout="wide"
)

# -----------------------------
# FOLDERS
# -----------------------------
os.makedirs("feedback", exist_ok=True)
os.makedirs("reports", exist_ok=True)

FEEDBACK_FILE = "feedback/feedback.csv"
if not os.path.exists(FEEDBACK_FILE):
    pd.DataFrame(columns=["timestamp", "name", "reg_no", "rating", "feedback"]).to_csv(FEEDBACK_FILE, index=False)

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #0f172a;
}
.sub-title {
    font-size: 1.1rem;
    color: #475569;
}
.card {
    background-color: #f8fafc;
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    margin-bottom: 1rem;
}
.small-note {
    font-size: 0.9rem;
    color: #64748b;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HELPERS
# -----------------------------
def classify_parameter(value, ideal_min, ideal_max):
    if ideal_min <= value <= ideal_max:
        return "Good", 20
    elif (ideal_min - 1 <= value < ideal_min) or (ideal_max < value <= ideal_max + 1):
        return "Moderate", 12
    else:
        return "Poor", 5


def evaluate_water_quality(ph, turbidity, hardness, tds, conductivity):
    results = {}

    # pH
    if 6.5 <= ph <= 8.5:
        results["pH"] = ("Good", 20, "Suitable for drinking")
    elif 6.0 <= ph < 6.5 or 8.5 < ph <= 9.0:
        results["pH"] = ("Moderate", 12, "Slightly acidic/basic")
    else:
        results["pH"] = ("Poor", 5, "May cause health and pipe corrosion issues")

    # Turbidity (NTU)
    if turbidity <= 5:
        results["Turbidity"] = ("Good", 20, "Clear water")
    elif turbidity <= 10:
        results["Turbidity"] = ("Moderate", 12, "Slightly cloudy")
    else:
        results["Turbidity"] = ("Poor", 5, "Highly cloudy / contaminated")

    # Hardness (mg/L)
    if hardness <= 200:
        results["Hardness"] = ("Good", 20, "Acceptable hardness")
    elif hardness <= 400:
        results["Hardness"] = ("Moderate", 12, "Moderately hard water")
    else:
        results["Hardness"] = ("Poor", 5, "Very hard water")

    # TDS (mg/L)
    if tds <= 500:
        results["TDS"] = ("Good", 20, "Safe dissolved solids level")
    elif tds <= 1000:
        results["TDS"] = ("Moderate", 12, "Acceptable but not ideal")
    else:
        results["TDS"] = ("Poor", 5, "High dissolved solids")

    # Conductivity (µS/cm)
    if conductivity <= 500:
        results["Conductivity"] = ("Good", 20, "Low ionic contamination")
    elif conductivity <= 1000:
        results["Conductivity"] = ("Moderate", 12, "Moderate ionic concentration")
    else:
        results["Conductivity"] = ("Poor", 5, "High ionic contamination")

    total_score = sum(v[1] for v in results.values())

    if total_score >= 85:
        overall = "Safe for Drinking"
        status_color = "green"
        alert = "Water quality is good and generally safe for domestic use."
    elif total_score >= 60:
        overall = "Needs Treatment"
        status_color = "orange"
        alert = "Water quality is moderate. Filtration or treatment is recommended before drinking."
    else:
        overall = "Unsafe"
        status_color = "red"
        alert = "Water may be unsafe for drinking and requires proper treatment/testing."

    return results, total_score, overall, status_color, alert


def generate_pdf_report(name, reg_no, ph, turbidity, hardness, tds, conductivity, results, total_score, overall, alert):
    file_path = "reports/water_quality_report.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Water Quality Checker Virtual Lab Report", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"Student Name: {name if name else 'Optional / Not Provided'}", styles['Normal']))
    story.append(Paragraph(f"Registration Number: {reg_no if reg_no else 'Optional / Not Provided'}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Input Parameters", styles['Heading2']))
    input_data = [
        ["Parameter", "Value"],
        ["pH", str(ph)],
        ["Turbidity (NTU)", str(turbidity)],
        ["Hardness (mg/L)", str(hardness)],
        ["TDS (mg/L)", str(tds)],
        ["Conductivity (µS/cm)", str(conductivity)]
    ]
    input_table = Table(input_data, colWidths=[220, 250])
    input_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(input_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Parameter Evaluation", styles['Heading2']))
    result_data = [["Parameter", "Status", "Interpretation"]]
    for param, vals in results.items():
        result_data.append([param, vals[0], vals[2]])

    result_table = Table(result_data, colWidths=[140, 100, 230])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(result_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Overall Assessment", styles['Heading2']))
    story.append(Paragraph(f"Water Quality Score: {total_score} / 100", styles['Normal']))
    story.append(Paragraph(f"Overall Status: {overall}", styles['Normal']))
    story.append(Paragraph(f"Health Alert: {alert}", styles['BodyText']))

    doc.build(story)
    return file_path


def save_feedback(name, reg_no, rating, feedback_text):
    row = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "reg_no": reg_no,
        "rating": rating,
        "feedback": feedback_text
    }])
    row.to_csv(FEEDBACK_FILE, mode="a", header=False, index=False)

# -----------------------------
# SIDEBAR
# -----------------------------
menu = st.sidebar.radio(
    "Navigation",
    ["Home", "Theory", "Water Quality Test", "Sample Dataset", "Feedback"]
)

st.sidebar.markdown("---")
student_name = st.sidebar.text_input("Student Name (Optional)")
reg_no = st.sidebar.text_input("Registration Number (Optional)")

# -----------------------------
# HOME
# -----------------------------
if menu == "Home":
    st.markdown('<div class="main-title">💧 Water Quality Checker Virtual Lab</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">A simple educational tool to assess water quality based on common physico-chemical parameters.</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### Objective
        This virtual lab helps students understand how water quality is assessed using common parameters such as:

        - **pH**
        - **Turbidity**
        - **Hardness**
        - **Total Dissolved Solids (TDS)**
        - **Conductivity**

        The app evaluates water quality and classifies it as:
        - **Safe for Drinking**
        - **Needs Treatment**
        - **Unsafe**
        """)

        st.info("This app is designed for **teaching and learning purposes** and demonstrates the concept of water quality assessment.")

    with col2:
        st.success("Recommended workflow:\n1. Study Theory\n2. Enter Water Parameters\n3. Analyze Results\n4. Download Report\n5. Submit Feedback")

# -----------------------------
# THEORY
# -----------------------------
elif menu == "Theory":
    st.header("📘 Theory of Water Quality")
    st.markdown("""
    Water quality is determined by **physical and chemical parameters** that indicate whether water is suitable for drinking or domestic use.

    ### Important Parameters

    #### 1. pH
    - Indicates acidity or alkalinity of water
    - Ideal drinking water range: **6.5 – 8.5**

    #### 2. Turbidity
    - Measures cloudiness of water
    - Lower turbidity indicates clearer water
    - Ideal: **≤ 5 NTU**

    #### 3. Hardness
    - Caused mainly by calcium and magnesium salts
    - High hardness may affect taste and soap lathering

    #### 4. TDS (Total Dissolved Solids)
    - Measures dissolved minerals and salts
    - Ideal: **≤ 500 mg/L**

    #### 5. Conductivity
    - Indicates ionic content in water
    - Higher conductivity may suggest dissolved contamination

    ### Applications
    - Drinking water testing
    - Environmental monitoring
    - Public health awareness
    - Educational laboratory training
    """)

# -----------------------------
# WATER QUALITY TEST
# -----------------------------
elif menu == "Water Quality Test":
    st.header("🧪 Water Quality Test")

    st.markdown("Enter the water quality parameters below and click **Analyze Water Quality**.")

    col1, col2 = st.columns(2)

    with col1:
        ph = st.text_input("pH", placeholder="Enter pH value (e.g., 7.2)")
        turbidity = st.text_input("Turbidity (NTU)", placeholder="Enter turbidity value (e.g., 2.5)")
        hardness = st.text_input("Hardness (mg/L)", placeholder="Enter hardness value (e.g., 150)")

    with col2:
        tds = st.text_input("TDS (mg/L)", placeholder="Enter TDS value (e.g., 300)")
        conductivity = st.text_input("Conductivity (µS/cm)", placeholder="Enter conductivity value (e.g., 450)")

    if st.button("Analyze Water Quality"):
        if not all([ph, turbidity, hardness, tds, conductivity]):
            st.warning("⚠️ Please enter all water quality parameters before analysis.")
        else:
            try:
                ph = float(ph)
                turbidity = float(turbidity)
                hardness = float(hardness)
                tds = float(tds)
                conductivity = float(conductivity)

                results, total_score, overall, status_color, alert = evaluate_water_quality(
                    ph, turbidity, hardness, tds, conductivity
                )

                st.session_state["results"] = results
                st.session_state["total_score"] = total_score
                st.session_state["overall"] = overall
                st.session_state["alert"] = alert
                st.session_state["inputs"] = {
                    "pH": ph,
                    "Turbidity": turbidity,
                    "Hardness": hardness,
                    "TDS": tds,
                    "Conductivity": conductivity
                }

                st.success("Analysis completed successfully!")

            except ValueError:
                st.error("❌ Please enter valid numeric values only.")

    if "results" in st.session_state:
        results = st.session_state["results"]
        total_score = st.session_state["total_score"]
        overall = st.session_state["overall"]
        alert = st.session_state["alert"]
        inputs = st.session_state["inputs"]

        st.subheader("📊 Water Quality Summary")

        c1, c2 = st.columns(2)
        c1.metric("Water Quality Score", f"{total_score} / 100")
        c2.metric("Overall Status", overall)

        result_df = pd.DataFrame([
            [param, vals[0], vals[2]] for param, vals in results.items()
        ], columns=["Parameter", "Status", "Interpretation"])

        st.dataframe(result_df, use_container_width=True)

        if overall == "Safe for Drinking":
            st.success(alert)
        elif overall == "Needs Treatment":
            st.warning(alert)
        else:
            st.error(alert)

        st.subheader("📈 Parameter Values")
        chart_df = pd.DataFrame({
            "Parameter": ["pH", "Turbidity", "Hardness", "TDS", "Conductivity"],
            "Value": [inputs["pH"], inputs["Turbidity"], inputs["Hardness"], inputs["TDS"], inputs["Conductivity"]]
        })
        st.bar_chart(chart_df.set_index("Parameter"))

        pdf_path = generate_pdf_report(
            student_name,
            reg_no,
            inputs["pH"],
            inputs["Turbidity"],
            inputs["Hardness"],
            inputs["TDS"],
            inputs["Conductivity"],
            results,
            total_score,
            overall,
            alert
        )

        with open(pdf_path, "rb") as f:
            st.download_button(
                "📥 Download Water Quality Report (PDF)",
                f,
                file_name="water_quality_report.pdf",
                mime="application/pdf"
            )

# -----------------------------
# SAMPLE DATASET
# -----------------------------
elif menu == "Sample Dataset":
    st.header("📂 Sample Water Quality Dataset")

    st.write("You can download and use this sample dataset for practice or mini project demonstration.")

    sample_data = pd.DataFrame({
        "Sample ID": ["W1", "W2", "W3", "W4", "W5"],
        "pH": [7.2, 6.3, 8.8, 7.0, 5.9],
        "Turbidity (NTU)": [2.1, 7.5, 3.2, 12.0, 9.0],
        "Hardness (mg/L)": [180, 350, 120, 450, 280],
        "TDS (mg/L)": [320, 650, 280, 1200, 800],
        "Conductivity (µS/cm)": [430, 720, 390, 1400, 850]
    })

    st.dataframe(sample_data, use_container_width=True)

    csv = sample_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Sample Dataset (CSV)",
        csv,
        "sample_water_data.csv",
        "text/csv"
    )

# -----------------------------
# FEEDBACK
# -----------------------------
elif menu == "Feedback":
    st.header("⭐ Feedback")
    st.write("Your feedback helps improve this virtual lab.")

    name = st.text_input("Name (Optional)")
    reg_no_fb = st.text_input("Registration Number (Optional)")
    rating = st.slider("Rate this virtual lab", 1, 5, 4)
    feedback_text = st.text_area("Write your feedback")

    if st.button("Submit Feedback"):
        save_feedback(name, reg_no_fb, rating, feedback_text)
        st.success("Thank you for your feedback!")

    if os.path.exists(FEEDBACK_FILE):
        df = pd.read_csv(FEEDBACK_FILE)
        if not df.empty:
            st.subheader("📌 Overall Feedback Summary")
            st.metric("Average Rating", round(df["rating"].mean(), 2))
            st.metric("Total Feedback Entries", len(df))

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("Developed using Streamlit for educational demonstration of water quality assessment.")
