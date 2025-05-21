
import streamlit as st
import pandas as pd
import joblib
import io
import os

st.set_page_config(page_title="🎯 Good Speed Predictor (Multi-Model)", layout="centered")
st.title("🚀 Good Speed run Prediction Web App")

# ===== ค้นหาโมเดลที่มีในโฟลเดอร์ =====
model_map = {}
for file in os.listdir():
    if file.startswith("rf_model_") and file.endswith(".pkl"):
        label = file.replace("rf_model_", "").replace(".pkl", "").replace("_", " ").title()
        col_file = file.replace("rf_model_", "feature_columns_")
        if os.path.exists(col_file):
            model_map[label] = (file, col_file)

if not model_map:
    st.error("❌ ไม่พบโมเดลใด ๆ ในโฟลเดอร์ปัจจุบัน")
    st.stop()

# ===== เลือกเวอร์ชันโมเดล =====
model_choice = st.sidebar.selectbox("📦 เลือกเวอร์ชันโมเดล", list(model_map.keys()))
model_file, column_file = model_map[model_choice]

model = joblib.load(model_file)
columns = joblib.load(column_file)

st.sidebar.success(f"✅ โหลดโมเดล: {model_choice}")

# ===== เลือกรูปแบบการใส่ข้อมูล =====
mode = st.radio("📌 เลือกรูปแบบการใส่ข้อมูล", ["✍️ กรอกค่าด้วยตนเอง", "📤 อัปโหลดไฟล์ Excel (.xlsx)"])

# ===== ฟังก์ชันเตรียม input =====
def encode_input(df_input, columns):
    df_input = df_input.copy()
    for col in ["Can Size", "Drink Type", "Coil type", "OV type", "Design type", "Customer", "IC type"]:
        if col in df_input.columns:
            df_input[col] = df_input[col].astype(str)
    df_encoded = pd.get_dummies(df_input)
    for col in columns:
        if col not in df_encoded:
            df_encoded[col] = 0
    return df_encoded[columns]

# ===== โหมด 1: กรอกค่าด้วยตนเอง =====
if mode == "✍️ กรอกค่าด้วยตนเอง":
    with st.form("manual_form"):
        can_size = st.selectbox("Can Size", ["Slim 180", "Slim 190", "Slim 250"])
        drink_type = st.selectbox("Drink Type", ["Retort", "Non Retrot"])
        good_qty = st.number_input("Good Qty (Can)", value=600000)
        spoilage = st.number_input("Spoilage (Can)", value=500)
        coil_type = st.selectbox("Coil Type", ["0.245", "0.26", "0.27"])
        ov_type = st.selectbox("OV Type", ["OV RETORT-AK", "OV retrot PFASNI"])
        design_type = st.selectbox("Design Type", ["Level 2 Solid (2 day)", "Level 4 Halftone (4 day)"])
        customer = st.selectbox("Customer", ["บริษัท มาลีกรุ๊ป จำกัด (มหาชน)", "บริษัท โอสถสภา จำกัด (มหาชน)"])
        ic_type = st.selectbox("IC Type", ["Internal Coat BPANI PPG2012-820E", "Internal Coat(VL)4020W01M"])
        avg_speed_month = st.number_input("Average Speed Month Before", value=47000)
        avg_speed_week = st.number_input("Average Speed Week Before", value=48000)
        submitted = st.form_submit_button("🔮 พยากรณ์")

    if submitted:
        df_input = pd.DataFrame([{
            "Can Size": can_size,
            "Drink Type": drink_type,
            "Good Qty (Can)": good_qty,
            "Spoilage (Can)": spoilage,
            "Coil type": coil_type,
            "OV type": ov_type,
            "Design type": design_type,
            "Customer": customer,
            "IC type": ic_type,
            "Average speed month before": avg_speed_month,
            "Average speed week before": avg_speed_week
        }])
        df_encoded = encode_input(df_input, columns)
        df_input["Predicted Good Speed run"] = model.predict(df_encoded)
        st.success(f"📈 ผลการพยากรณ์: {df_input['Predicted Good Speed run'].iloc[0]:,.2f} cans/hour")
        st.write(df_input)

# ===== โหมด 2: Upload Excel =====
elif mode == "📤 อัปโหลดไฟล์ Excel (.xlsx)":
    uploaded_file = st.file_uploader("เลือกไฟล์ Excel ที่ต้องการพยากรณ์", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("📋 ตัวอย่างข้อมูลที่อัปโหลด", df.head())
            df_encoded = encode_input(df, columns)
            df["Predicted Good Speed run"] = model.predict(df_encoded)
            st.success("✅ พยากรณ์สำเร็จ")
            st.dataframe(df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)

            st.download_button(
                label="📥 ดาวน์โหลดผลลัพธ์เป็น Excel",
                data=output.getvalue(),
                file_name="predicted_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
