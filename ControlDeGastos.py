import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import os

# ---------------------------
# Configuración
# ---------------------------
st.set_page_config(page_title="Dashboard Presupuesto", layout="wide")

USERS = {"Nava": "Nava", "Smarilynr": "Smarilynr"}  # usuarios y passwords

DB_FILE = "presupuesto.db"
CSV_FILE = "movimientos.csv"

# ---------------------------
# Inicializar BD
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    importe REAL,
                    descripcion TEXT,
                    categoria TEXT,
                    tipo TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Funciones de BD
# ---------------------------
def agregar_categoria(nombre):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        conn.commit()
    except:
        pass
    conn.close()

def obtener_categorias():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT nombre FROM categorias")
    cats = [row[0] for row in c.fetchall()]
    conn.close()
    return cats

def agregar_movimiento(fecha, importe, descripcion, categoria, tipo):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO movimientos (fecha, importe, descripcion, categoria, tipo) VALUES (?, ?, ?, ?, ?)",
              (fecha, importe, descripcion, categoria, tipo))
    conn.commit()
    conn.close()
    exportar_movimientos_csv()

def obtener_movimientos():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, fecha, importe, descripcion, categoria, tipo FROM movimientos")
    data = c.fetchall()
    conn.close()
    return pd.DataFrame(data, columns=["ID", "Fecha", "Importe", "Descripción", "Categoría", "Tipo"])

def actualizar_movimiento(id_, fecha, importe, descripcion, categoria, tipo):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""UPDATE movimientos 
                 SET fecha=?, importe=?, descripcion=?, categoria=?, tipo=? 
                 WHERE id=?""",
              (fecha, importe, descripcion, categoria, tipo, id_))
    conn.commit()
    conn.close()
    exportar_movimientos_csv()

def exportar_movimientos_csv():
    df = obtener_movimientos()
    if not df.empty:
        df.to_csv(CSV_FILE, index=False, encoding="utf-8")

# ---------------------------
# Login
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔑 Login")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.success(f"Bienvenido {username} 👋")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

else:
    menu = st.sidebar.radio("Menú", ["Dashboard", "Registrar Movimiento", "Categorías", "Editar Movimiento"])

    if menu == "Dashboard":
        st.title("💰 Dashboard de Presupuesto")

        df = obtener_movimientos()

        if df.empty:
            st.info("No hay datos aún. Registra tus ingresos y gastos.")
        else:
            total_ingresos = df[df["Tipo"]=="Ingreso"]["Importe"].sum()
            total_gastos = df[df["Tipo"]=="Gasto"]["Importe"].sum()
            total_ahorro = df[df["Tipo"]=="Ahorro"]["Importe"].sum()
            diferencia = total_ingresos - total_gastos - total_ahorro

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ingresos", f"${total_ingresos:.2f}")
            col2.metric("Gastos", f"${total_gastos:.2f}")
            col3.metric("Ahorro/Inversión", f"${total_ahorro:.2f}")
            col4.metric("Balance", f"${diferencia:.2f}")

            st.subheader("📈 Gráficos")
            col1, col2 = st.columns(2)

            with col1:
                df_comp = pd.DataFrame({
                    "Categoría": ["Ingresos", "Gastos", "Ahorro"],
                    "Monto": [total_ingresos, total_gastos, total_ahorro]
                })
                fig1 = px.bar(df_comp, x="Categoría", y="Monto", color="Categoría", text="Monto")
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                gastos_df = df[df["Tipo"]=="Gasto"]
                if not gastos_df.empty:
                    fig2 = px.pie(gastos_df, names="Categoría", values="Importe", title="Gastos Variables")
                    st.plotly_chart(fig2, use_container_width=True)

            ahorro_df = df[df["Tipo"]=="Ahorro"]
            if not ahorro_df.empty:
                fig3 = px.pie(ahorro_df, names="Categoría", values="Importe", title="Ahorro vs Inversión")
                st.plotly_chart(fig3, use_container_width=True)

            st.subheader("📊 Movimientos")
            st.dataframe(df)

            st.download_button(
                "📥 Descargar movimientos (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                "movimientos.csv",
                "text/csv"
            )

    elif menu == "Registrar Movimiento":
        st.title("📝 Registrar Movimiento")

        tipo = st.radio("Tipo", ["Ingreso", "Gasto", "Ahorro"])
        fecha = st.date_input("Fecha", datetime.today())
        importe = st.number_input("Importe", min_value=0.0, step=0.5)
        descripcion = st.text_input("Descripción")

        categorias = obtener_categorias()
        categoria = st.selectbox("Categoría", categorias)

        if st.button("Guardar"):
            agregar_movimiento(str(fecha), importe, descripcion, categoria, tipo)
            st.success("Movimiento guardado correctamente ✅")

    elif menu == "Categorías":
        st.title("📂 Categorías")

        nueva_cat = st.text_input("Nueva categoría")
        if st.button("Agregar categoría"):
            agregar_categoria(nueva_cat)
            st.success("Categoría agregada ✅")

        st.subheader("Categorías existentes")
        st.write(obtener_categorias())

    elif menu == "Editar Movimiento":
        st.title("✏️ Editar Movimiento")

        df = obtener_movimientos()
        if df.empty:
            st.info("No hay movimientos para editar.")
        else:
            movimiento_id = st.selectbox("Selecciona el ID a editar", df["ID"])
            mov = df[df["ID"]==movimiento_id].iloc[0]

            with st.form("form_editar"):
                tipo = st.radio("Tipo", ["Ingreso", "Gasto", "Ahorro"], index=["Ingreso","Gasto","Ahorro"].index(mov["Tipo"]))
                fecha = st.date_input("Fecha", datetime.strptime(mov["Fecha"], "%Y-%m-%d"))
                importe = st.number_input("Importe", value=float(mov["Importe"]), step=0.5)
                descripcion = st.text_input("Descripción", value=mov["Descripción"])
                categorias = obtener_categorias()
                categoria = st.selectbox("Categoría", categorias, index=categorias.index(mov["Categoría"]))

                guardar = st.form_submit_button("💾 Guardar cambios")
                if guardar:
                    actualizar_movimiento(movimiento_id, str(fecha), importe, descripcion, categoria, tipo)
                    st.success("Movimiento actualizado ✅")
                    st.rerun()
