import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import sqlite3

st.set_page_config(page_title="AI Smart Grocery Assistant", layout="centered")

st.title("🧠 AI Smart Grocery Business Assistant")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("shop.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS sales(
    day INTEGER,
    product TEXT,
    quantity INTEGER
)
""")
conn.commit()

# ---------------- EXTERNAL CONDITIONS ----------------
st.header("📅 Business Conditions")

weather = st.selectbox("Weather Condition",
                       ["Normal","Rainy","Very Hot"])

festival = st.selectbox("Festival Period",
                        ["No Festival","Festival Week"])

school = st.selectbox("School Season",
                      ["Normal Days","School Opening Week"])

# ---------------- ADD DAILY SALES ----------------
st.header("📝 Add Daily Sales Record")

day_input = st.number_input("Day",1,365)
product_input = st.text_input("Product Name")
qty_input = st.number_input("Quantity Sold",0,1000)

if st.button("Save Sale"):
    if product_input != "":
        c.execute("INSERT INTO sales VALUES (?,?,?)",
                  (day_input, product_input.lower(), qty_input))
        conn.commit()
        st.success("Sale saved successfully!")

# ---------------- LOAD DATA ----------------
df = pd.read_sql("SELECT * FROM sales", conn)

if len(df) > 0:

    st.subheader("📊 Sales Data")
    st.dataframe(df)

    # pivot data for ML
    pivot_df = df.pivot_table(index="day",
                              columns="product",
                              values="quantity",
                              aggfunc="sum").fillna(0)

    st.subheader("📈 Sales Trend")
    st.line_chart(pivot_df)

    # ---------------- DEMAND PREDICTION ----------------
    st.header("🔮 Demand Prediction")

    product = st.selectbox("Select Product", pivot_df.columns)

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

        if stock < demand:
            reorder = demand - stock
            st.error("⚠️ Stock will run out!")
            st.write(f"Recommended reorder quantity: {reorder} units")
        else:
            st.success("Stock level is sufficient.")

# ---------------- DAILY FINANCE ----------------
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

# ---------------- SUPPLIER MESSAGE ----------------
st.header("📦 Supplier Order Assistant")

supplier = st.text_input("Supplier Name")
order_product = st.text_input("Product to Order")
order_qty = st.number_input("Quantity",0,1000)

if st.button("Generate Supplier Message"):

    message = f"""
Hello {supplier},

I would like to place an order.

Product: {order_product}
Quantity: {order_qty} units

Please deliver tomorrow morning.

Thank you.
"""

    st.text_area("Copy and send via WhatsApp/SMS", message)
