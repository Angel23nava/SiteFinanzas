# ControlDeGastos.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Presupuesto", layout="wide")
st.title("💰 Dashboard de Presupuesto Interactivo")

mes = st.text_input("Mes:", "Junio")

default_ingresos = {
    "Concepto": ["Salario", "Freelance", "Otros"],
    "Esperado": [2700, 500, 100],
    "Real": [2748.5, 400, 0]
}

default_facturas = {
    "Concepto": ["Hipoteca", "Luz", "Teléfono", "Internet", "Tarjeta crédito"],
    "Gasto previsto": [450, 50, 45, 60, 79.9],
    "Gasto real": [450, 50, 45, 60, 79.9]
}

default_gastos = {
    "Categoría": ["Transporte", "Alimentación", "Ropa", "Entretenimiento", "Tecnología", "Salud", "Mascotas", "Otros"],
    "Gasto previsto": [150, 500, 50, 150, 100, 50, 50, 50],
    "Gasto real": [165.55, 450, 70, 140, 120, 40, 30, 50]
}

default_ahorro = {
    "Concepto": ["Ahorro", "Inversión"],
    "Cantidad final": [1200, 840]
}

st.sidebar.header("Editar Datos")
df_ingresos = st.sidebar.data_editor(pd.DataFrame(default_ingresos))
df_facturas = st.sidebar.data_editor(pd.DataFrame(default_facturas))
df_gastos = st.sidebar.data_editor(pd.DataFrame(default_gastos))
df_ahorro = st.sidebar.data_editor(pd.DataFrame(default_ahorro))

total_ingresos = df_ingresos["Real"].sum()
total_facturas = df_facturas["Gasto real"].sum()
total_gastos = df_gastos["Gasto real"].sum()
total_ahorro = df_ahorro["Cantidad final"].sum()
total_gastos_totales = total_facturas + total_gastos
diferencia = total_ingresos - total_gastos_totales - total_ahorro

st.subheader(f"📊 Resumen presupuesto {mes}")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Ingresos", f"${total_ingresos:.2f}")
col2.metric("Facturas y Crédito", f"${total_facturas:.2f}")
col3.metric("Gastos Variables", f"${total_gastos:.2f}")
col4.metric("Ahorro e Inversión", f"${total_ahorro:.2f}")
col5.metric("Diferencia", f"${diferencia:.2f}")

st.subheader("📈 Gráficos")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Ingresos vs Gastos")
    df_comparacion = pd.DataFrame({
        "Categoría": ["Ingresos", "Gastos Totales"],
        "Monto": [total_ingresos, total_gastos_totales]
    })
    fig1 = px.bar(df_comparacion, x="Categoría", y="Monto", color="Categoría", text="Monto")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Distribución Gastos Variables")
    fig2 = px.pie(df_gastos, names="Categoría", values="Gasto real", title="Gastos Variables")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Ahorro e Inversión")
fig3 = px.pie(df_ahorro, names="Concepto", values="Cantidad final", title="Ahorro vs Inversión")
st.plotly_chart(fig3, use_container_width=True)
