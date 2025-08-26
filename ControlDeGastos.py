import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px
import os

# ---------------------------
# Configuración
# ---------------------------
st.set_page_config(page_title="Presupuesto Mensual", layout="wide")
st.write("DB_HOST =", os.getenv("DB_HOST"))
st.write("DB_PORT =", os.getenv("DB_PORT"))
USERS = {"Nava": "Nava", "Smarilynr": "Smarilynr"}  # usuarios y passwords

# ---------------------------
# Conexión a Supabase/Postgres
# ---------------------------
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

# ---------------------------
# Funciones de BD
# ---------------------------
def agregar_categoria(nombre, usuario):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO categorias (nombre, usuario) VALUES (%s, %s) ON CONFLICT DO NOTHING", (nombre, usuario))
        conn.commit()
    except Exception as e:
        st.error(f"Error al agregar categoría: {e}")
    finally:
        cur.close()
        conn.close()

def obtener_categorias(usuario):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM categorias WHERE usuario=%s", (usuario,))
    cats = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return cats

def agregar_movimiento(fecha, importe, descripcion, categoria, tipo, usuario):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO movimientos (fecha, importe, descripcion, categoria, tipo, usuario) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (fecha, importe, descripcion, categoria, tipo, usuario))
    conn.commit()
    cur.close()
    conn.close()

def obtener_movimientos(usuario):
    conn = get_connection()
    df = pd.read_sql("SELECT id, fecha, importe, descripcion, categoria, tipo FROM movimientos WHERE usuario=%s",
                     conn, params=(usuario,))
    conn.close()
    return df

def actualizar_movimiento(id_, fecha, importe, descripcion, categoria, tipo, usuario):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""UPDATE movimientos 
                   SET fecha=%s, importe=%s, descripcion=%s, categoria=%s, tipo=%s 
                   WHERE id=%s AND usuario=%s""",
                (fecha, importe, descripcion, categoria, tipo, id_, usuario))
    conn.commit()
    cur.close()
    conn.close()

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
            st.session_state.username = username
            st.success(f"Bienvenido {username} 👋")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

else:
    # ---------------------------
    # Menú Estilizado
    # ---------------------------
    st.sidebar.markdown("## 📌 Menú")
    menu = st.sidebar.selectbox(
        "Selecciona una opción:",
        ["🏠 General", "📝 Registrar Movimiento", "📂 Categorías", "✏️ Editar Movimiento"]
    )

    # ---------------------------
    # Dashboard
    # ---------------------------
    if menu == "🏠 General":
        st.title("💰 Presupuesto Mensual")

        df = obtener_movimientos(st.session_state.username)

        if df.empty:
            st.info("No hay datos aún. Registra tus ingresos y gastos.")
        else:
            total_ingresos = df[df["tipo"]=="Ingreso"]["importe"].sum()
            total_gastos = df[df["tipo"]=="Gasto"]["importe"].sum()
            total_ahorro = df[df["tipo"]=="Ahorro"]["importe"].sum()
            diferencia = total_ingresos - total_gastos - total_ahorro

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ingresos", f"${total_ingresos:.2f}")
            col2.metric("Gastos", f"${total_gastos:.2f}")
            col3.metric("Ahorro/Inversión", f"${total_ahorro:.2f}")
            col4.metric("Balance", f"${diferencia:.2f}")

            st.subheader("📈 Gráficos")

            gastos_df = df[df["tipo"]=="Gasto"]
            if not gastos_df.empty:
                st.subheader("📌 Resumen de Gastos por Categoría")
                resumen_cat = gastos_df.groupby("categoria")["importe"].sum().reset_index()
                resumen_cat = resumen_cat.sort_values(by="importe", ascending=False)

                st.dataframe(resumen_cat, use_container_width=True)

                fig_resumen = px.bar(
                    resumen_cat,
                    x="categoria",
                    y="importe",
                    text="importe",
                    title="Gastos por Categoría",
                    color="categoria"
                )
                st.plotly_chart(fig_resumen, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                df_comp = pd.DataFrame({
                    "Categoría": ["Ingresos", "Gastos", "Ahorro"],
                    "Monto": [total_ingresos, total_gastos, total_ahorro]
                })
                fig1 = px.bar(df_comp, x="Categoría", y="Monto", color="Categoría", text="Monto")
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                if not gastos_df.empty:
                    fig2 = px.pie(gastos_df, names="categoria", values="importe", title="Gastos Variables")
                    st.plotly_chart(fig2, use_container_width=True)

            if not gastos_df.empty:
                st.subheader("📊 Distribución de Gastos Variables")
                fig3 = px.histogram(gastos_df, x="importe", nbins=10, title="Distribución de montos de gastos")
                st.plotly_chart(fig3, use_container_width=True)

            ahorro_df = df[df["tipo"]=="Ahorro"]
            if not ahorro_df.empty:
                fig4 = px.pie(ahorro_df, names="categoria", values="importe", title="Ahorro vs Inversión")
                st.plotly_chart(fig4, use_container_width=True)

            st.subheader("📊 Movimientos")
            st.dataframe(df)

            st.download_button(
                "📥 Descargar movimientos (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                "movimientos.csv",
                "text/csv"
            )

    # ---------------------------
    # Registrar Movimiento
    # ---------------------------
    elif menu == "📝 Registrar Movimiento":
        st.title("📝 Registrar Movimiento")

        tipo = st.radio("Tipo", ["Ingreso", "Gasto", "Ahorro"])
        fecha = st.date_input("Fecha", datetime.today())
        importe = st.number_input("Importe", min_value=0.0, step=0.5)
        descripcion = st.text_input("Descripción")

        categorias = obtener_categorias(st.session_state.username)
        categoria = st.selectbox("Categoría", categorias)

        if st.button("Guardar"):
            agregar_movimiento(str(fecha), importe, descripcion, categoria, tipo, st.session_state.username)
            st.success("Movimiento guardado correctamente ✅")

    # ---------------------------
    # Categorías
    # ---------------------------
    elif menu == "📂 Categorías":
        st.title("📂 Categorías")

        nueva_cat = st.text_input("Nueva categoría")
        if st.button("Agregar categoría"):
            agregar_categoria(nueva_cat, st.session_state.username)
            st.success("Categoría agregada ✅")

    # ---------------------------
    # Editar Movimiento
    # ---------------------------
    elif menu == "✏️ Editar Movimiento":
        st.title("✏️ Editar Movimiento")

        df = obtener_movimientos(st.session_state.username)
        if df.empty:
            st.info("No hay movimientos para editar.")
        else:
            movimiento_id = st.selectbox("Selecciona el ID a editar", df["id"])
            mov = df[df["id"]==movimiento_id].iloc[0]

            with st.form("form_editar"):
                tipo = st.radio("Tipo", ["Ingreso", "Gasto", "Ahorro"], index=["Ingreso","Gasto","Ahorro"].index(mov["tipo"]))
                fecha = st.date_input("Fecha", mov["fecha"])
                importe = st.number_input("Importe", value=float(mov["importe"]), step=0.5)
                descripcion = st.text_input("Descripción", value=mov["descripcion"])
                categorias = obtener_categorias(st.session_state.username)
                categoria = st.selectbox("Categoría", categorias, index=categorias.index(mov["categoria"]))

                guardar = st.form_submit_button("💾 Guardar cambios")
                if guardar:
                    actualizar_movimiento(movimiento_id, str(fecha), importe, descripcion, categoria, tipo, st.session_state.username)
                    st.success("Movimiento actualizado ✅")
                    st.rerun()

