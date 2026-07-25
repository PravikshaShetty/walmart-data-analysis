import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Walmart Sales Dashboard", layout="wide")
st.title("📊 Walmart Sales Analysis Dashboard")

# --- Connect to Neon ---
DB_CONNECTION = st.secrets["DB_CONNECTION"]
engine = create_engine(DB_CONNECTION)

# --- Q1: Payment method breakdown ---
st.subheader("Payment Method Breakdown")
q1 = """
    SELECT payment_method, COUNT(*) as no_payments, SUM(quantity) as no_qty_sold
    FROM walmart
    GROUP BY payment_method
"""
df1 = pd.read_sql(text(q1), engine)
col1, col2 = st.columns(2)
with col1:
    st.bar_chart(df1.set_index("payment_method")["no_payments"])
with col2:
    st.dataframe(df1)

# --- Q2: Highest-rated category per branch ---
st.subheader("Top Rated Category per Branch")
q2 = """
    SELECT * FROM (
        SELECT branch, category, AVG(rating) as avg_rating,
               RANK() OVER (PARTITION BY branch ORDER BY AVG(rating) DESC) as rank
        FROM walmart
        GROUP BY branch, category
    ) sub
    WHERE rank = 1
"""
df2 = pd.read_sql(text(q2), engine)
st.dataframe(df2)

# --- Q3: Busiest day per branch ---
st.subheader("Busiest Day per Branch")
q3 = """
    SELECT * FROM (
        SELECT branch,
               TO_CHAR(TO_DATE(date, 'DD/MM/YY'), 'DAY') as day_name,
               COUNT(*) as no_transactions,
               RANK() OVER (PARTITION BY branch ORDER BY COUNT(*) DESC) as rank
        FROM walmart
        GROUP BY branch, day_name
    ) sub
    WHERE rank = 1
"""
df3 = pd.read_sql(text(q3), engine)
st.dataframe(df3.drop(columns=["rank"]))

# --- Q6: Total profit by category ---
st.subheader("Total Profit by Category")
q6 = """
    SELECT category, SUM(total) as total_revenue
    FROM walmart
    GROUP BY category
    ORDER BY total_revenue DESC
"""
df6 = pd.read_sql(text(q6), engine)
st.bar_chart(df6.set_index("category")["total_revenue"])

# --- Q7: Most common payment method per branch ---
st.subheader("Preferred Payment Method per Branch")
q7 = """
    WITH cte AS (
        SELECT branch, payment_method,
               COUNT(*) as total_trans,
               RANK() OVER (PARTITION BY branch ORDER BY COUNT(*) DESC) as rank
        FROM walmart
        GROUP BY branch, payment_method
    )
    SELECT branch, payment_method, total_trans FROM cte WHERE rank = 1
"""
df7 = pd.read_sql(text(q7), engine)
st.dataframe(df7)

# --- Q8: Sales by shift (Morning/Afternoon/Evening) ---
st.subheader("Sales by Time of Day")
q8 = """
    SELECT
        CASE
            WHEN EXTRACT(HOUR FROM (time::time)) < 12 THEN 'Morning'
            WHEN EXTRACT(HOUR FROM (time::time)) BETWEEN 12 AND 17 THEN 'Afternoon'
            ELSE 'Evening'
        END as day_time,
        COUNT(*) as no_invoices
    FROM walmart
    GROUP BY day_time
    ORDER BY no_invoices DESC
"""
df8 = pd.read_sql(text(q8), engine)
st.bar_chart(df8.set_index("day_time")["no_invoices"])

# --- Q9: Branches with highest revenue decrease (2023 vs 2022) ---
st.subheader("Top 5 Branches: Revenue Decrease (2023 vs 2022)")
q9 = """
    WITH revenue_2022 AS (
        SELECT branch, SUM(total) as revenue
        FROM walmart
        WHERE EXTRACT(YEAR FROM TO_DATE(date, 'DD/MM/YY')) = 2022
        GROUP BY branch
    ),
    revenue_2023 AS (
        SELECT branch, SUM(total) as revenue
        FROM walmart
        WHERE EXTRACT(YEAR FROM TO_DATE(date, 'DD/MM/YY')) = 2023
        GROUP BY branch
    )
    SELECT
        ls.branch,
        ls.revenue as last_year_revenue,
        cs.revenue as cr_year_revenue,
        ROUND((ls.revenue - cs.revenue)::numeric / ls.revenue::numeric * 100, 2) as rev_dec_ratio
    FROM revenue_2022 as ls
    JOIN revenue_2023 as cs ON ls.branch = cs.branch
    WHERE ls.revenue > cs.revenue
    ORDER BY rev_dec_ratio DESC
    LIMIT 5
"""
df9 = pd.read_sql(text(q9), engine)
st.dataframe(df9)

