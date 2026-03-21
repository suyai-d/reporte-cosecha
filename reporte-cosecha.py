import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Reporte Cosecha | Conci", layout="wide", page_icon="🚜")

# --- 2. LOGOS SUPERIORES ---
# Creamos 3 columnas para empujar los logos a las puntas
col_logo_izq, col_espacio, col_logo_der = st.columns([1, 4, 1])

with col_logo_izq:
    # Logo del concesionario
    st.image("CSC.png", width=150)

with col_logo_der:
    # Logo de John Deere
    st.image("JD.png", width=170)

# --- SIDEBAR: ENTRADA DE DATOS Y FILTROS ---
st.sidebar.header("Configuración del Reporte")
archivo_subido = st.sidebar.file_uploader("Subir Excel de Cosecha (CSV o XLSX)", type=["xlsx", "csv"])
razon_social_input = st.sidebar.text_input("Razón Social del Cliente", placeholder="Ej: Agropecuaria El Ombú S.A.")

umbral_has = st.sidebar.number_input(
    "Filtrar labores menores a (Has):",
    min_value=0.0, value=2.0, step=0.5
)

# --- CARGA Y PROCESAMIENTO ---
if archivo_subido is not None:
    try:
        if archivo_subido.name.endswith('.csv'):
            df = pd.read_csv(archivo_subido)
        else:
            df = pd.read_excel(archivo_subido)

        df_base = df[df['Superficie cosechada'] >= umbral_has].copy()

        # FILTROS DE UBICACIÓN
        st.sidebar.subheader("Filtros de Ubicación")
        lista_clientes = ["Todos"] + sorted(list(df_base['Clientes'].unique()))
        cliente_sel = st.sidebar.selectbox("Cliente", lista_clientes)
        df_filt = df_base.copy()
        if cliente_sel != "Todos": df_filt = df_filt[df_filt['Clientes'] == cliente_sel]

        lista_granjas = ["Todas"] + sorted(list(df_filt['Granjas'].unique()))
        granja_sel = st.sidebar.selectbox("Granja", lista_granjas)
        if granja_sel != "Todas": df_filt = df_filt[df_filt['Granjas'] == granja_sel]

        lista_campos = ["Todos"] + sorted(list(df_filt['Campos'].unique()))
        campo_sel = st.sidebar.selectbox("Campo", lista_campos)
        if campo_sel != "Todos": df_filt = df_filt[df_filt['Campos'] == campo_sel]

        # SECCIÓN DE TECNOLOGÍA EN EL SIDEBAR (Abajo de todo)
        st.sidebar.divider()
        ver_tecnologia = st.sidebar.checkbox("Añadir Tecnología de Cosecha")

        # Variables de ROI con valores estándar
        ah_hs = 0.6;
        ah_pgsa = 0.6;
        cal_am = 20.0;
        cal_pgsa = 20.0

        if ver_tecnologia:
            st.sidebar.subheader("Configuración ROI (USD/ha)")
            ah_hs = st.sidebar.number_input("Ahorro Combustible HarvestSmart", value=0.6)
            ah_pgsa = st.sidebar.number_input("Ahorro Combustible PGSA", value=0.6)
            cal_am = st.sidebar.number_input("Calidad/Pérdidas AutoMaintain", value=20.0)
            cal_pgsa = st.sidebar.number_input("Calidad/Pérdidas HSA", value=20.0)

        if not df_filt.empty:
            df_filt['Primera cosecha'] = pd.to_datetime(df_filt['Primera cosecha'])
            df_filt['Último cosechado'] = pd.to_datetime(df_filt['Último cosechado'])

            # --- SECCIÓN 1: CABECERA Y KPIs ---
            st.title("🚜 Reporte de Cosecha")
            titulo_cliente = razon_social_input if razon_social_input else (
                cliente_sel if cliente_sel != "Todos" else "Flota Total")
            st.subheader(f"Análisis para: {titulo_cliente}")

            total_has = df_filt['Superficie cosechada'].sum()
            total_comb = df_filt['Combustible total'].sum()
            c_prom = total_comb / total_has if total_has > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Inicio", df_filt['Primera cosecha'].min().strftime('%d/%m/%Y'))
            c2.metric("Fin", df_filt['Último cosechado'].max().strftime('%d/%m/%Y'))
            c3.metric("Total Hectáreas", f"{total_has:,.2f} Has")
            c4.metric("Combustible", f"{total_comb:,.0f} Lts", delta=f"{c_prom:.2f} L/Ha", delta_color="inverse")

            st.divider()

            # --- SECCIÓN 2: EVOLUCIÓN TEMPORAL (RESTAURADO) ---
            st.subheader("📅 Evolución Diaria y Acumulada")
            df_diario = df_filt.groupby(df_filt['Último cosechado'].dt.date)['Superficie cosechada'].sum().reset_index()
            df_diario.columns = ['Fecha', 'Hectareas']
            df_diario['Acumulado'] = df_diario['Hectareas'].cumsum()

            fig_temp = make_subplots(specs=[[{"secondary_y": True}]])
            fig_temp.add_trace(
                go.Bar(x=df_diario['Fecha'], y=df_diario['Hectareas'], name="Has/Día", marker_color='#2ca02c',
                       opacity=0.7), secondary_y=False)
            fig_temp.add_trace(
                go.Scatter(x=df_diario['Fecha'], y=df_diario['Acumulado'], name="Acumulado", mode='lines+markers',
                           line=dict(color='#1f77b4', width=3)), secondary_y=True)
            st.plotly_chart(fig_temp, use_container_width=True)

            # --- SECCIÓN 3: DESEMPEÑO DE FLOTA (RESTAURADO) ---
            st.subheader("⚙️ Desempeño de Flota y Operadores")
            col_izq, col_der = st.columns(2)
            with col_izq:
                df_maq_graf = df_filt.groupby('Nombre de máquina')[
                    'Superficie cosechada'].sum().reset_index().sort_values('Superficie cosechada', ascending=False)
                st.plotly_chart(
                    px.bar(df_maq_graf, x='Nombre de máquina', y='Superficie cosechada', title="Hectáreas por Máquina",
                           color_discrete_sequence=['#ff7f0e']), use_container_width=True)
            with col_der:
                df_op = df_filt.groupby('Operadores')['Superficie cosechada'].sum().reset_index().sort_values(
                    'Superficie cosechada', ascending=False)
                st.plotly_chart(px.bar(df_op, x='Operadores', y='Superficie cosechada', title="Hectáreas por Operador",
                                       color_discrete_sequence=['#9467bd']), use_container_width=True)

            # --- SECCIÓN 4: BOXPLOT FLUJO (t/h) ---
            st.subheader("📈 Eficiencia de Alimentación (t/h)")
            st.plotly_chart(px.box(df_filt, x='Nombre de máquina', y='Rendimiento (húmedo)', color='Nombre de máquina',
                                   points="all"), use_container_width=True)

            # --- SECCIÓN 5: ANÁLISIS AGRONÓMICO (RESTAURADO) ---
            st.divider()
            st.subheader("🌱 Análisis por Cultivo y Variedad")
            lista_cultivos = ["Todos"] + sorted(list(df_filt['Tipo de cultivo'].unique()))
            cult_sel = st.selectbox("Filtrar por cultivo:", lista_cultivos)
            df_cul = df_filt if cult_sel == "Todos" else df_filt[df_filt['Tipo de cultivo'] == cult_sel]
            label_x = 'Tipo de cultivo' if cult_sel == "Todos" else 'Variedades'

            c_a1, c_a2, c_a3 = st.columns(3)
            with c_a1:
                st.plotly_chart(px.bar(df_cul.groupby(label_x)['Superficie cosechada'].sum().reset_index(), x=label_x,
                                       y='Superficie cosechada', title="Superficie (Has)",
                                       color_discrete_sequence=['#2ca02c']), use_container_width=True)
            with c_a2:
                st.plotly_chart(
                    px.bar(df_cul.groupby(label_x)['Peso húmedo'].mean().reset_index(), x=label_x, y='Peso húmedo',
                           title="Rinde (t/ha)", color_discrete_sequence=['#8bc34a']), use_container_width=True)
            with c_a3:
                st.plotly_chart(
                    px.bar(df_cul.groupby(label_x)['Índice de combustible (área)'].mean().reset_index(), x=label_x,
                           y='Índice de combustible (área)', title="Consumo (L/ha)",
                           color_discrete_sequence=['#ff7f0e']), use_container_width=True)

            # BOXPLOT VARIEDAD (RESTAURADO)
            st.write(f"**Estabilidad de Rinde por Variedad ({cult_sel}) - t/ha**")
            st.plotly_chart(px.box(df_cul, x='Variedades', y='Peso húmedo', color='Variedades', points="all"),
                            use_container_width=True)

            # --- SECCIÓN 6: TECNOLOGÍA Y ROI ---
            if ver_tecnologia:
                st.divider()
                st.subheader("🛠️ Auditoría Tecnológica e Impacto Económico")

                maquinas_disponibles = sorted(list(df_filt['Nombre de máquina'].unique()))
                maquinas_sel = st.multiselect("Máquinas a auditar:", maquinas_disponibles, default=maquinas_disponibles)

                if maquinas_sel:
                    h1, h2, h3, h4, h5, h6 = st.columns([1.5, 1, 1.5, 1, 1.5, 1])
                    h1.caption("**Máquina**");
                    h2.caption("**Has**");
                    h3.caption("**Tec. Avance**");
                    h4.caption("**% Uso**");
                    h5.caption("**Tec. Ajuste**");
                    h6.caption("**% Uso**")

                    total_ahorro = 0.0;
                    total_oculto = 0.0

                    for maq in maquinas_sel:
                        h_m = df_filt[df_filt['Nombre de máquina'] == maq]['Superficie cosechada'].sum()
                        r1, r2, r3, r4, r5, r6 = st.columns([1.5, 1, 1.5, 1, 1.5, 1])

                        r1.write(f"**{maq}**");
                        r2.write(f"{h_m:,.1f}")
                        t1 = r3.selectbox(f"T1_{maq}", ["HarvestSmart", "PGSA", "Sin Tecnología"], key=f"t1_{maq}",
                                          label_visibility="collapsed")
                        u1 = r4.number_input(f"U1_{maq}", 0, 100, 0, step=5, key=f"u1_{maq}",
                                             label_visibility="collapsed")
                        t2 = r5.selectbox(f"T2_{maq}", ["AutoMaintain", "HSA", "Sin Tecnología"], key=f"t2_{maq}",
                                          label_visibility="collapsed")
                        u2 = r6.number_input(f"U2_{maq}", 0, 100, 0, step=5, key=f"u2_{maq}",
                                             label_visibility="collapsed")

                        # Cálculo ROI
                        v1 = ah_hs if t1 == "HarvestSmart" else (ah_pgsa if t1 == "PGSA" else 0)
                        v2 = cal_am if t2 == "AutoMaintain" else (cal_pgsa if t2 == "HSA" else 0)

                        ah_real = (h_m * (u1 / 100) * v1) + (h_m * (u2 / 100) * v2)
                        ah_pot = (h_m * v1) + (h_m * v2)
                        total_ahorro += ah_real;
                        total_oculto += (ah_pot - ah_real)

                    st.markdown("---")
                    res1, res2, res3 = st.columns(3)
                    res1.metric("Ahorro Real", f"USD {total_ahorro:,.2f}")
                    res2.metric("Costo Oculto", f"USD {total_oculto:,.2f}", delta=f"-{total_oculto:,.2f}",
                                delta_color="inverse")
                    res3.metric("Potencial Total", f"USD {(total_ahorro + total_oculto):,.2f}")

            with st.expander("📂 Ver Tabla de Datos"):
                st.dataframe(df_filt, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👋 Sube el archivo de cosecha para comenzar.")