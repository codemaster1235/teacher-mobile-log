import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from difflib import get_close_matches

# ڈیٹا بیس کنکشن
conn = sqlite3.connect("teacher_mobile_log.db", check_same_thread=False)
cursor = conn.cursor()

# ٹیبل بنائیں اگر موجود نہیں
cursor.execute('''CREATE TABLE IF NOT EXISTS mobile_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, 
    mobile_taken_time TEXT,
    mobile_received_time TEXT,
    date TEXT,
    status TEXT,
    notes TEXT,
    signature TEXT
)''')
conn.commit()

# 🔹 **نام کی مماثلت چیک کرنے والا فنکشن**
def correct_name(input_name):
    cursor.execute("SELECT DISTINCT name FROM mobile_log")
    existing_names = [row[0] for row in cursor.fetchall()]

    close_match = get_close_matches(input_name, existing_names, n=1, cutoff=0.8)
    if close_match:
        return close_match[0]  # سب سے قریب نام تجویز کریں
    return input_name  # اگر مماثل نام نہ ملے تو وہی نام رکھیں

# --- اسکرین 1: استاد کا نام پوچھیں ---
st.title("📱 اساتذہ کا موبائل لاگ سسٹم")
st.header("👤 براہ کرم اپنا پورا نام درج کریں")

name = st.text_input("🔹 مکمل نام:")

if st.button("✅ Submit") and name:
    corrected_name = correct_name(name)  # نام کی درستی چیک کریں
    if corrected_name != name:
        st.warning(f"⚠️ کیا آپ کا نام '{corrected_name}' ہے؟ ہم نے اسے درست کیا ہے۔")
    st.session_state["name"] = corrected_name  # درست شدہ نام کو سیشن میں محفوظ کریں
    st.session_state["page"] = "data_entry"

# --- اسکرین 2: ڈیٹا انٹری کا صفحہ ---
if "page" in st.session_state and st.session_state["page"] == "data_entry":
    name = st.session_state["name"]

    st.header(f"📋 موبائل انٹری - {name}")

    cursor.execute("SELECT * FROM mobile_log WHERE name = ? AND date = ?", (name, datetime.now().strftime("%Y-%m-%d")))
    existing_record = cursor.fetchone()

    if existing_record:
        if existing_record[5] == "Submitted":  # اگر پہلے "Submitted" کیا گیا تھا
            st.info("✅ آپ پہلے ہی موبائل جمع کر چکے ہیں۔")
            receive_now = st.radio("📌 کیا آپ موبائل واپسی کا وقت ابھی درج کرنا چاہتے ہیں؟", ["ہاں", "بعد میں"], index=1)

            if receive_now == "ہاں":
                mobile_received_time = st.time_input("📲 موبائل واپس کرنے کا وقت:")
                if mobile_received_time:
                    formatted_received_time = datetime.strptime(str(mobile_received_time), "%H:%M:%S").strftime("%I:%M %p")
                    cursor.execute("UPDATE mobile_log SET mobile_received_time = ? WHERE name = ? AND date = ?",
                                   (formatted_received_time, name, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success(f"✅ موبائل واپسی کا وقت محفوظ ہو گیا! ({formatted_received_time})")
            else:
                st.info("📌 آپ بعد میں موبائل واپسی کا وقت درج کر سکتے ہیں۔")

    else:
        mobile_taken_time = st.time_input("📲 موبائل جمع کرنے کا وقت:")
        if mobile_taken_time:
            formatted_mobile_taken_time = datetime.strptime(str(mobile_taken_time), "%H:%M:%S").strftime("%I:%M %p")

        status = st.radio("📌 موبائل کی صورتحال:", ["Submitted", "Not Submitted"])
        notes = st.text_area("📝 کوئی خاص نوٹ درج کریں (اگر موبائل نہیں دینا چاہتے):")
        signature = st.text_input("📝 دستخط:")

        if st.button("✅ محفوظ کریں"):
            date = datetime.now().strftime("%Y-%m-%d")

            # اگر "Not Submitted" ہو تو موبائل واپسی کا وقت درج نہ ہو
            mobile_received_time = None if status == "Not Submitted" else ""

            cursor.execute("INSERT INTO mobile_log (name, mobile_taken_time, mobile_received_time, date, status, notes, signature) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (name, formatted_mobile_taken_time, mobile_received_time, date, status, notes, signature))
            conn.commit()
            st.success(f"✅ ریکارڈ کامیابی سے محفوظ ہو گیا! ({formatted_mobile_taken_time})")

# 🔹 **پرانا ریکارڈ دیکھنے کا سیکشن**
st.header("پرانا ڈیٹا دیکھیں")  # 📅 آئیکن ہٹا دیا گیا ہے
selected_date = st.date_input("🔍 تاریخ منتخب کریں:")

if st.button("🔎 ریکارڈ دیکھیں"):
    cursor.execute("SELECT id, name, mobile_taken_time, mobile_received_time, status, notes, signature FROM mobile_log WHERE date = ?", (str(selected_date),))
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["ID", "نام", "موبائل لینے کا وقت", "موبائل واپس کرنے کا وقت", "اسٹیٹس", "نوٹس", "دستخط"])
        st.table(df)

        # 🔹 **پرنٹ کا بٹن**
        st.download_button(
            label="🖨️ پرنٹ کریں",
            data=df.to_csv(index=False),
            file_name=f"mobile_log_{selected_date}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ اس تاریخ کا کوئی ریکارڈ نہیں ملا۔")

# 🔹 **ڈیٹا بیس بند کریں**
conn.close()
