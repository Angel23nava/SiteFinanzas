import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ---------------------------
# Configuración
# ---------------------------
st.set_page_config(page_title="Dashboard Presupuesto", layout="wide")

USERS = {"Nava": "Nava", "Smarilynr": "Smarilynr"}  # usuarios y passwords

# ---------------------------
# Inicializar BD
# ---------------------------
def init_db():
    conn = sqlite3.connect("presupuesto.db")
    c = conn.cursor()

    # Tabla de categorías
    c.execute('''CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE
                )''')

    # Tabla de movimientos (ingresos/gastos)
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
    conn = sqlite3.connect("presupuesto.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        conn.commit()
    except:
        pass  # ya existe
    conn.close()

def obtener_categorias():
    conn = sqlite3.connect("presupuesto.db")
    c = conn.cursor()
    c.execute("SELECT nombre FROM categorias")
    cats = [row[0] for row in c.fetchall()]
    conn.close()
    return cats

def agregar_movimiento(fecha, importe, descripcion, categoria, tipo):
    conn = sqlite3.connect("presupuesto.db")
    c = conn.cursor()
    c.execute("INSERT INTO movimientos (fecha, importe, descripcion, categoria, tipo) VALUES (?, ?, ?, ?, ?)",
              (fecha, importe, descripcion, categoria, tipo))
    conn.commit()
    conn.close()

def obtener_movimientos():
    conn = sqlite3.connect("presupuesto.db")
    c = conn.cursor()
    c.execute("SELECT fecha, importe, descripcion, categoria, tipo FROM movimientos")
    data = c.fetchall()
    conn.close()
    return pd.DataFrame(data, columns=["Fecha", "Importe", "Descripción", "Categoría", "Tipo"])

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
    # ---------------------------
    # Navegación
    # ---------------------------
    menu = st.sidebar.radio("Menú", ["Dashboard", "Registrar Movimiento", "Categorías"])

    if menu == "Dashboard":
        st.title("💰 Dashboard de Presupuesto")

        df = obtener_movimientos()

        if df.empty:
            st.info("No hay datos aún. Registra tus ingresos y gastos.")
        else:
            # Totales
            total_ingresos = df[df["Tipo"]=="Ingreso"]["Importe"].sum()
            total_gastos = df[df["Tipo"]=="Gasto"]["Importe"].sum()
            diferencia = total_ingresos - total_gastos

            col1, col2, col3 = st.columns(3)
            col1.metric("Ingresos", f"${total_ingresos:.2f}")
            col2.metric("Gastos", f"${total_gastos:.2f}")
            col3.metric("Balance", f"${diferencia:.2f}")

            st.subheader("📊 Movimientos")
            st.dataframe(df)

            # Gráficos
            st.subheader("Distribución por categoría")
            if not df[df["Tipo"]=="Gasto"].empty:
                gastos_cat = df[df["Tipo"]=="Gasto"].groupby("Categoría")["Importe"].sum().reset_index()
                st.bar_chart(gastos_cat.set_index("Categoría"))

    elif menu == "Registrar Movimiento":
        st.title("📝 Registrar Movimiento")

        tipo = st.radio("Tipo", ["Ingreso", "Gasto"])
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
