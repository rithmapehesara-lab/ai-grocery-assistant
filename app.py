import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import sqlite3
import hashlib
import urllib.parse

st.set_page_config(page_title="AI Smart Grocery Assistant", layout="centered")

# ---------------- PASSWORD HASH ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- DATABASE INIT SAFE ----------------
import os
DB_PATH = os.path.join(os.getcwd(), "shop.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# users table
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# sales table
c.execute("""
CREATE TABLE IF NOT EXISTS sales(
    username TEXT,
    day INTEGER,
    product TEXT,
    quantity INTEGER
)
""")

conn.commit()

# users table
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT,
    password TEXT
)
""")

# sales table
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
    st.sidebar.subheader("Create Account")
    new_user = st.sidebar.text_input("Username")
    new_pass = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Register"):
        c.execute("INSERT INTO users VALUES (?,?)",
                  (new_user, hash_password(new_pass)))
        conn.commit()
        st.sidebar.success("Account created! Now login.")

if menu == "Login":
    st.sidebar.subheader("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        result = c.execute("SELECT * FROM users WHERE username=? AND password=?",
                           (username, hash_password(password))).fetchone()
        if result:
            st.session_state["user"] = username
            st.sidebar.success("Logged in!")
        else:
            st.sidebar.error("Invalid credentials")

if "user" not in st.session_state:
    st.warning("Please login to use the system.")
    st.stop()

# ---------------- BUSINESS CONDITIONS ----------------
st.header("📅 Business Conditions")

weather = st.selectbox("Weather Condition",
                       ["Normal","Rainy","Very Hot"])

festival = st.selectbox("Festival Period",
                        ["No Festival","Festival Week"])

school = st.selectbox("School Season",
                      ["Normal Days","School Opening Week"])

# ---------------- ADD SALES ----------------
st.header("📝 Add Daily Sales Record")

day_input = st.number_input("Day",1,365)

products = ["bread","milk","eggs","rice","sugar","soap","tea","biscuit"]
product_input = st.selectbox("Product Name", products)

qty_input = st.number_input("Quantity Sold",0,1000)

if st.button("Save Sale"):
    c.execute("INSERT INTO sales VALUES (?,?,?,?)",
              (st.session_state["user"], day_input, product_input, qty_input))
    conn.commit()
    st.success("Sale saved successfully!")

# ---------------- LOAD USER DATA ----------------
try:
    df = pd.read_sql_query(
        "SELECT day, product, quantity FROM sales WHERE username=?",
        conn,
        params=(st.session_state["user"],)
    )
except Exception:
    df = pd.DataFrame(columns=["day","product","quantity"])

if len(df) > 0:

    st.subheader("📊 Sales Data")
    st.dataframe(df)

    # dashboard chart
    st.subheader("📈 Product Summary")
    today_sales = df.groupby("product")["quantity"].sum()
    st.bar_chart(today_sales)

    # pivot for ML
    pivot_df = df.pivot_table(index="day",
                              columns="product",
                              values="quantity",
                              aggfunc="sum").fillna(0)

    st.subheader("📉 Sales Trend")
    st.line_chart(pivot_df)

    # ---------------- DEMAND PREDICTION ----------------
    st.header("🔮 Demand Prediction")

    product = st.selectbox("Select Product for Prediction", pivot_df.columns)

    X = pivot_df.index.values.reshape(-1,1)
    y = pivot_df[product].values

    model = LinearRegression()
    model.fit(X,y)

    future_day = st.number_input("Enter Future Day",1,365)
    stock = st.number_input("Current Stock Level",0,1000)

    if st.button("Predict Demand"):

        prediction = model.predict([[future_day]])
        demand = int(prediction[0])

        # contextual adjustments
        if weather == "Rainy":
            demand += int(demand * 0.20)
        elif weather == "Very Hot":
            demand -= int(demand * 0.10)

        if festival == "Festival Week":
            demand += int(demand * 0.30)

        if school == "School Opening Week":
            demand += int(demand * 0.15)

        st.success(f"Predicted Demand: {demand} units")

        if demand > stock:
            reorder = demand - stock
            st.error("⚠️ Stock will run out!")
            st.write(f"Recommended reorder quantity: {reorder} units")
            st.warning("You should reorder today to avoid stock out tomorrow!")
        else:
            st.success("Stock level is sufficient.")

# ---------------- FINANCE MANAGER ----------------
st.header("💰 Daily Finance Manager")

selling_price = st.number_input("Selling Price per unit (Rs)",0,1000,value=100)
cost_price = st.number_input("Cost Price per unit (Rs)",0,1000,value=70)
units_sold = st.number_input("Units Sold Today",0,500)

if st.button("Calculate Finance"):

    revenue = selling_price * units_sold
    cost = cost_price * units_sold
    profit = revenue - cost

    st.success(f"Revenue: Rs {revenue}")
    st.success(f"Cost: Rs {cost}")
    st.success(f"Net Profit: Rs {profit}")

    restock = profit * 0.5
    savings = profit * 0.3
    bills = profit * 0.2

    st.write("### Suggested Allocation")
    st.write(f"Restock Budget: Rs {int(restock)}")
    st.write(f"Savings: Rs {int(savings)}")
    st.write(f"Bills/Expenses: Rs {int(bills)}")

    fig, ax = plt.subplots()
    ax.pie([restock, savings, bills],
           labels=["Restock","Savings","Bills"],
           autopct='%1.1f%%')
    st.pyplot(fig)

# ---------------- WHATSAPP ORDER ----------------
st.header("📦 Supplier Order Assistant")

supplier = st.text_input("Supplier Name")
supplier_phone = st.text_input("Supplier WhatsApp Number (9477xxxxxxx)")
order_product = st.text_input("Product to Order")
order_qty = st.number_input("Quantity",0,1000)

if st.button("Generate WhatsApp Order"):

    message = f"""
Hello {supplier},

I would like to place an order.

Product: {order_product}
Quantity: {order_qty} units

Please deliver tomorrow morning.

Thank you.
"""

    encoded_message = urllib.parse.quote(message)
    whatsapp_link = f"https://wa.me/{supplier_phone}?text={encoded_message}"

    st.success("Click below to send order via WhatsApp")
    st.markdown(f"[📲 Send Order on WhatsApp]({whatsapp_link})")
