import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import sqlite3
import hashlib
import urllib.parse
import os

st.set_page_config(page_title="AI Smart Grocery Assistant", layout="centered")

# ---------------- PASSWORD HASH ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- DATABASE SAFE INIT ----------------
DB_PATH = os.path.join(os.getcwd(), "shop.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# FORCE CLEAN TABLE STRUCTURE (safe reset)
c.execute("DROP TABLE IF EXISTS sales")

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS sales(
    username TEXT,
    day INTEGER,
    product TEXT,
    quantity INTEGER
)
""")

conn.commit()

# ---------------- LOGIN SYSTEM ----------------
st.title("🧠 AI Smart Grocery Business Assistant")

st.sidebar.title("Account")
menu = st.sidebar.selectbox("Login / Register",["Login","Register"])

if menu == "Register":
    new_user = st.sidebar.text_input("Username")
    new_pass = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Register"):
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?)",
                  (new_user, hash_password(new_pass)))
        conn.commit()
        st.sidebar.success("Account created! Please login.")

if menu == "Login":
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        result = c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hash_password(password))
        ).fetchone()

        if result:
            st.session_state["user"] = username
            st.sidebar.success("Logged in!")
        else:
            st.sidebar.error("Invalid credentials")

if "user" not in st.session_state:
    st.warning("Please login to continue.")
    st.stop()

# ---------------- BUSINESS CONDITIONS ----------------
st.header("📅 Business Conditions")

weather = st.selectbox("Weather",["Normal","Rainy","Very Hot"])
festival = st.selectbox("Festival",["No Festival","Festival Week"])
school = st.selectbox("School Season",["Normal","School Opening Week"])

# ---------------- ADD SALES ----------------
st.header("📝 Add Daily Sales")

day_input = st.number_input("Day",1,365)
products = ["bread","milk","eggs","rice","sugar","soap","tea","biscuit"]
product_input = st.selectbox("Product", products)
qty_input = st.number_input("Quantity",0,1000)

if st.button("Save Sale"):
    c.execute(
        "INSERT INTO sales (username, day, product, quantity) VALUES (?,?,?,?)",
        (st.session_state["user"], day_input, product_input, qty_input)
    )
    conn.commit()
    st.success("Sale Saved!")

# ---------------- LOAD DATA SAFE ----------------
try:
    df = pd.read_sql_query(
        "SELECT day, product, quantity FROM sales WHERE username=?",
        conn,
        params=(st.session_state["user"],)
    )
except:
    df = pd.DataFrame(columns=["day","product","quantity"])

if len(df) > 0:

    st.subheader("📊 Sales Data")
    st.dataframe(df)

    pivot_df = df.pivot_table(index="day",
                              columns="product",
                              values="quantity",
                              aggfunc="sum").fillna(0)

    st.subheader("📈 Sales Trend")
    st.line_chart(pivot_df)

    # ---------------- PREDICTION ----------------
    st.header("🔮 Demand Prediction")

    product = st.selectbox("Predict Product", pivot_df.columns)
    X = pivot_df.index.values.reshape(-1,1)
    y = pivot_df[product].values

    model = LinearRegression()
    model.fit(X,y)

    future_day = st.number_input("Future Day",1,365)
    stock = st.number_input("Current Stock",0,1000)

    if st.button("Predict Demand"):
        demand = int(model.predict([[future_day]])[0])

        if weather == "Rainy":
            demand += int(demand*0.2)
        if festival == "Festival Week":
            demand += int(demand*0.3)
        if school == "School Opening Week":
            demand += int(demand*0.15)

        st.success(f"Predicted Demand: {demand}")

        if demand > stock:
            st.error("⚠ Stock Low!")
            st.write(f"Reorder: {demand-stock}")
        else:
            st.success("Stock OK")

# ---------------- FINANCE ----------------
st.header("💰 Daily Finance")

sell = st.number_input("Selling Price",0,1000,value=100)
cost = st.number_input("Cost Price",0,1000,value=70)
units = st.number_input("Units Sold Today",0,500)

if st.button("Calculate Finance"):
    revenue = sell*units
    expense = cost*units
    profit = revenue-expense

    st.success(f"Profit: Rs {profit}")

    restock = profit*0.5
    savings = profit*0.3
    bills = profit*0.2

    fig, ax = plt.subplots()
    ax.pie([restock,savings,bills],
           labels=["Restock","Savings","Bills"],
           autopct='%1.1f%%')
    st.pyplot(fig)

# ---------------- WHATSAPP ----------------
st.header("📦 WhatsApp Order")

supplier = st.text_input("Supplier Name")
phone = st.text_input("Supplier Phone (9477xxxxxxx)")
order_product = st.text_input("Product")
order_qty = st.number_input("Quantity to Order",0,1000)

if st.button("Send WhatsApp Order"):
    message = f"""
Hello {supplier},
Order:
Product: {order_product}
Quantity: {order_qty}
Thank you.
"""
    link = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
    st.markdown(f"[📲 Send on WhatsApp]({link})")
