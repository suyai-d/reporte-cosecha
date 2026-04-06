import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Reporte Impacto Tecnológico", page_icon="🚜", layout="wide")

# --- 2. LOGOS SUPERIORES ---
col_logo_izq, col_espacio, col_logo_der = st.columns([1, 4, 1])
with col_logo_izq:
    st.image("CSC.png", width=150)
with col_logo_der:
    st.image("JD.png", width=170)

# --- SIDEBAR: CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración del Reporte")
archivo_subido = st.sidebar.file_uploader("Subir Excel de Cosecha", type=["xlsx", "csv"])
razon_social_input = st.sidebar.text_input("Razón Social del Cliente", placeholder="Ej: Agropecuaria El Ombú S.A.")

umbral_has = st.sidebar.number_input("Filtrar labores menores a (Has):", min_value=0.0, value=2.0, step=0.5)

df_final = pd.DataFrame()

if archivo_subido is not None:
    try:
        df = pd.read_csv(archivo_subido) if archivo_subido.name.endswith('.csv') else pd.read_excel(archivo_subido)
        df.columns = df.columns.str.strip()
        df_base = df[df['Superficie cosechada'] >= umbral_has].copy()

        with st.sidebar.expander("📍 Filtros de Segmentación", expanded=False):
            c_sel = st.multiselect("Cliente:", options=sorted(df_base['Clientes'].unique()),
                                   default=sorted(df_base['Clientes'].unique()))
            df_c = df_base[df_base['Clientes'].isin(c_sel)]
            g_sel = st.multiselect("Granja:", options=sorted(df_c['Granjas'].unique()),
                                   default=sorted(df_c['Granjas'].unique()))
            df_g = df_c[df_c['Granjas'].isin(g_sel)]
            ca_sel = st.multiselect("Campo:", options=sorted(df_g['Campos'].unique()),
                                    default=sorted(df_g['Campos'].unique()))
            df_ca = df_g[df_g['Campos'].isin(ca_sel)]
            cu_sel = st.multiselect("Cultivo:", options=sorted(df_ca['Tipo de cultivo'].unique()),
                                    default=sorted(df_ca['Tipo de cultivo'].unique()))

        df_final = df_ca[df_ca['Tipo de cultivo'].isin(cu_sel)].copy()
        df_final['Primera cosecha'] = pd.to_datetime(df_final['Primera cosecha'])
        df_final['Último cosechado'] = pd.to_datetime(df_final['Último cosechado'])
    except Exception as e:
        st.sidebar.error(f"Error al procesar archivo: {e}")

st.sidebar.divider()
st.sidebar.subheader("⛽ Parámetros de Combustible")
precio_gasoil = st.sidebar.number_input("Precio Gasoil (USD/L)", value=1.0)
ah_hs_l_ha = st.sidebar.number_input("Ahorro HarvestSmart (L/ha)", value=0.6)
ah_pgsa_l_ha = st.sidebar.number_input("Ahorro PGSA (L/ha)", value=0.5)

st.sidebar.subheader("🌾 Parámetros de Grano")
precio_grano_usd = st.sidebar.number_input("Precio Grano (USD/tn)", value=300.0)

c_am, c_psa = st.sidebar.columns(2)
with c_am:
    st.caption("**AutoMaintain**")
    p_sin_am = st.number_input("Sin AM (kg/ha)", value=100.0);
    p_con_am = st.number_input("Con AM (kg/ha)", value=80.0)
with c_psa:
    st.caption("**PSA**")
    p_sin_psa = st.number_input("Sin PSA (kg/ha)", value=100.0);
    p_con_psa = st.number_input("Con PSA (kg/ha)", value=90.0)

st.sidebar.subheader("✨ Calidad (BCR)")
with st.sidebar.expander("Configurar Rotos e Impurezas"):
    st.write("**AutoMaintain**")
    r_am_s = st.number_input("% Rotos s/AM", value=2.0);
    r_am_c = st.number_input("% Rotos c/AM", value=1.0)
    i_am_s = st.number_input("% Imp. s/AM", value=1.5);
    i_am_c = st.number_input("% Imp. c/AM", value=0.5)
    st.divider()
    st.write("**PSA**")
    r_psa_s = st.number_input("% Rotos s/PSA", value=2.0);
    r_psa_c = st.number_input("% Rotos c/PSA", value=1.5)
    i_psa_s = st.number_input("% Imp. s/PSA", value=1.5);
    i_psa_c = st.number_input("% Imp. c/PSA", value=1.0)
    st.info(
        "[Link Cámara Arbitral BCR](https://www.cac.bcr.com.ar/es/arbitraje-y-calidad/liquidacion-y-mermas/liquidacion-de-mercaderia)")

castigo_am = st.sidebar.number_input("% Castigo sin AM", value=1.5) / 100
castigo_psa = st.sidebar.number_input("% Castigo sin PSA", value=1.0) / 100

st.sidebar.divider()
activar_historico = st.sidebar.checkbox("Agregar histórico de uso de tecnología")
archivo_historico = None;
rango_hist = None;
fechas_ordenadas = []

if activar_historico:
    st.sidebar.info(
        "[Link Looker Histórico](https://lookerstudio.google.com/reporting/fea42c5d-6b62-4f18-846e-4a97d90610df)")
    archivo_historico = st.sidebar.file_uploader("Subir archivo CSV Histórico", type=["csv"])
    if archivo_historico:
        df_h_raw = pd.read_csv(archivo_historico)
        meses_map = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sept': 9,
                     'oct': 10, 'nov': 11, 'dic': 12}


        def parse_fecha(texto):
            try:
                partes = texto.split()
                return pd.Timestamp(year=int(partes[1]), month=meses_map[partes[0].lower()], day=1)
            except:
                return pd.Timestamp(year=2000, month=1, day=1)


        fechas_unicas = df_h_raw['Fecha de terminación (Año y mes)'].unique()
        fechas_ordenadas = sorted(fechas_unicas, key=parse_fecha)
        rango_hist = st.sidebar.select_slider("Rango del Histórico", options=fechas_ordenadas,
                                              value=(fechas_ordenadas[0], fechas_ordenadas[-1]))

# --- CUERPO DEL INFORME ---
if archivo_subido is not None and not df_final.empty:
    st.title("🚜 Auditoría de Tecnología en Cosechadoras")
    st.subheader(f"Análisis para: {razon_social_input if razon_social_input else 'Flota Seleccionada'}")

    total_has_segmento = df_final['Superficie cosechada'].sum()
    total_comb = df_final['Combustible total'].sum()
    c_prom = total_comb / total_has_segmento if total_has_segmento > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Inicio", df_final['Primera cosecha'].min().strftime('%d/%m/%Y'))
    c2.metric("Fin", df_final['Último cosechado'].max().strftime('%d/%m/%Y'))
    c3.metric("Total Hectáreas", f"{total_has_segmento:,.1f} Has")
    c4.metric("Consumo Total", f"{total_comb:,.0f} Lts")
    c5.metric("Promedio L/Ha", f"{c_prom:.2f}")

    st.divider()
    st.subheader("🌾 Rendimientos Promedio por Cultivo")
    cultivos_en_data = sorted(list(df_final['Tipo de cultivo'].unique()))
    rtos_cols = st.columns(len(cultivos_en_data))
    dict_rtos = {cult: df_final[df_final['Tipo de cultivo'] == cult]['Peso húmedo'].mean() for cult in cultivos_en_data}
    for i, cult in enumerate(cultivos_en_data):
        rtos_cols[i].metric(f"Rto {cult}", f"{dict_rtos[cult]:.2f} tn/ha")

    st.divider()
    st.subheader("🛠️ Auditoría de Uso e Impacto Económico")
    maquinas_sel = st.multiselect("Seleccionar máquinas para el análisis:",
                                  options=sorted(list(df_final['Nombre de máquina'].unique())),
                                  default=sorted(list(df_final['Nombre de máquina'].unique())))

    if maquinas_sel:
        df_maquinas = df_final[df_final['Nombre de máquina'].isin(maquinas_sel)]
        total_has_maquinas = df_maquinas['Superficie cosechada'].sum()

        t_ahorro_c = 0.0;
        t_ahorro_g = 0.0;
        t_oculto = 0.0
        tecs_av = set();
        tecs_aj = set()

        h1, h2, h3, h4, h5, h6 = st.columns([1.5, 1, 1.5, 1, 1.5, 1])
        h1.caption("**Máquina**");
        h2.caption("**Has**");
        h3.caption("**Tec. Avance**");
        h4.caption("**% Uso**");
        h5.caption("**Tec. Ajuste**");
        h6.caption("**% Uso**")

        for maq in maquinas_sel:
            df_m = df_maquinas[df_maquinas['Nombre de máquina'] == maq]
            h_m = df_m['Superficie cosechada'].sum()
            cult_p = df_m.groupby('Tipo de cultivo')['Superficie cosechada'].sum().idxmax()
            rto_ref = dict_rtos[cult_p]

            r1, r2, r3, r4, r5, r6 = st.columns([1.5, 1, 1.5, 1, 1.5, 1])
            r1.write(f"**{maq}**");
            r2.write(f"{h_m:,.1f}")
            t1 = r3.selectbox(f"T1_{maq}", ["HarvestSmart", "PGSA", "Sin Tecnología"], key=f"t1_{maq}",
                              label_visibility="collapsed")
            u1 = r4.number_input(f"U1_{maq}", 0, 100, 0, step=5, key=f"u1_{maq}", label_visibility="collapsed")
            t2 = r5.selectbox(f"T2_{maq}", ["AutoMaintain", "PSA", "Sin Tecnología"], key=f"t2_{maq}",
                              label_visibility="collapsed")
            u2 = r6.number_input(f"U2_{maq}", 0, 100, 0, step=5, key=f"u2_{maq}", label_visibility="collapsed")

            if t1 != "Sin Tecnología" and u1 > 0: tecs_av.add(t1)
            if t2 != "Sin Tecnología" and u2 > 0: tecs_aj.add(t2)

            v_c = (ah_hs_l_ha if t1 == "HarvestSmart" else (ah_pgsa_l_ha if t1 == "PGSA" else 0)) * precio_gasoil
            v_g = 0
            if t2 == "AutoMaintain":
                v_g = (((p_sin_am - p_con_am) / 1000) * precio_grano_usd) + (precio_grano_usd * rto_ref * castigo_am)
            elif t2 == "PSA":
                v_g = (((p_sin_psa - p_con_psa) / 1000) * precio_grano_usd) + (precio_grano_usd * rto_ref * castigo_psa)

            t_ahorro_c += (h_m * (u1 / 100) * v_c)
            t_ahorro_g += (h_m * (u2 / 100) * v_g)
            t_oculto += (h_m * (1 - u1 / 100) * v_c) + (h_m * (1 - u2 / 100) * v_g)

        st.markdown("---")
        col_res, col_param, col_pie = st.columns([1, 1, 1])
        with col_res:
            st.write("##### 💰 Resultado Económico Actual")
            ah_total = t_ahorro_c + t_ahorro_g
            pot_t = ah_total + t_oculto
            st.markdown(f"<h3 style='color: #28a745; margin-bottom: 0;'>USD {ah_total:,.0f}</h3>",
                        unsafe_allow_html=True)
            st.caption(f"Ahorro Real")
            st.markdown(f"<h3 style='color: #dc3545; margin-bottom: 0;'>USD {t_oculto:,.0f}</h3>",
                        unsafe_allow_html=True)
            st.caption("Costo Oculto")
            st.markdown(f"<h3 style='color: #007bff; margin-bottom: 0;'>USD {pot_t:,.0f}</h3>", unsafe_allow_html=True)
            st.caption("Potencial Total")
            efic = (ah_total / pot_t * 100) if pot_t > 0 else 0
            st.write(f"**Eficiencia: {efic:.1f}%**")
            st.progress(efic / 100)

        with col_param:
            st.write("##### 📝 Detalle de Tecnologías y Calidad")
            if "HarvestSmart" in tecs_av: st.write(f"🚜 **HarvestSmart:** -{ah_hs_l_ha} L/ha")
            if "PGSA" in tecs_av: st.write(f"🚜 **PGSA:** -{ah_pgsa_l_ha} L/ha")
            if "AutoMaintain" in tecs_aj:
                st.write(f"✅ **AutoMaintain:** -{p_sin_am - p_con_am:.0f} kg/ha")
                st.caption(f"Rotos: {r_am_s}% → {r_am_c}% | Imp: {i_am_s}% → {i_am_c}%")
            if "PSA" in tecs_aj:
                st.write(f"✅ **PSA:** -{p_sin_psa - p_con_psa:.0f} kg/ha")
                st.caption(f"Rotos: {r_psa_s}% → {r_psa_c}% | Imp: {i_psa_s}% → {i_psa_c}%")

        with col_pie:
            fig_pie = px.pie(values=[t_ahorro_c, t_ahorro_g, t_oculto], names=['Combustible', 'Granos', 'Costo Oculto'],
                             color_discrete_sequence=['#2ca02c', '#ff7f0e', '#dc3545'], hole=0.4)
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=230);
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- SECCIÓN HISTÓRICO Y COMPARATIVA ---
        if activar_historico and archivo_historico and rango_hist:
            st.divider()
            st.subheader("📈 Evolución de Adopción Tecnológica por Sistema")
            idx_inicio = fechas_ordenadas.index(rango_hist[0])
            idx_fin = fechas_ordenadas.index(rango_hist[1])
            fechas_rango = fechas_ordenadas[idx_inicio:idx_fin + 1]
            df_h = df_h_raw[df_h_raw['Fecha de terminación (Año y mes)'].isin(fechas_rango)].copy()
            df_h['temp_date'] = df_h['Fecha de terminación (Año y mes)'].apply(parse_fecha)
            df_h = df_h.sort_values('temp_date')

            # --- GRÁFICO CON 4 SERIES ---
            fig_h = go.Figure()
            # Harvest Smart (Serie S700 Avance)
            fig_h.add_trace(
                go.Scatter(x=df_h['Fecha de terminación (Año y mes)'], y=df_h['Harvest Smart Activado (%)'] * 100,
                           mode='lines+markers', name='Harvest Smart', line=dict(color='#FFDE00', width=3)))
            # Auto Maintain (Serie S700 Ajuste)
            fig_h.add_trace(
                go.Scatter(x=df_h['Fecha de terminación (Año y mes)'], y=df_h['Auto Maintain Activado (%)'] * 100,
                           mode='lines+markers', name='Auto Maintain', line=dict(color='#367C2B', width=3)))
            # PGSA (Serie S7 Avance)
            fig_h.add_trace(go.Scatter(x=df_h['Fecha de terminación (Año y mes)'],
                                       y=df_h['Automatización de la velocidad de avance Activo (%)'] * 100,
                                       mode='lines+markers', name='PGSA (S7)',
                                       line=dict(color='#007bff', width=3, dash='dash')))
            # PSA (Serie S7 Ajuste)
            fig_h.add_trace(go.Scatter(x=df_h['Fecha de terminación (Año y mes)'],
                                       y=df_h['Automatización de ajustes de cosecha Activo (%)'] * 100,
                                       mode='lines+markers', name='PSA (S7)',
                                       line=dict(color='#28a745', width=3, dash='dash')))

            fig_h.update_layout(hovermode="x unified", yaxis_title="Uso (%)", template="plotly_white", height=400,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_h, use_container_width=True)

            st.subheader("🔄 Participación de Tecnología (Inicio vs. Fin)")
            st.write(f"Distribuí las **{total_has_maquinas:,.1f} Has** totales según la flota de ese momento:")

            col_ini, col_fin = st.columns(2)
            with col_ini:
                st.markdown(f"📅 **Inicio: {rango_hist[0]}**")
                has_s7_ini = st.slider("Has para S7 (PGSA/PSA)", 0.0, float(total_has_maquinas),
                                       float(total_has_maquinas / 2), key="s7_ini")
                has_s700_ini = total_has_maquinas - has_s7_ini
                st.caption(f"S7: {has_s7_ini:,.1f} ha | S700: {has_s700_ini:,.1f} ha")

            with col_fin:
                st.markdown(f"📅 **Fin: {rango_hist[1]}**")
                has_s7_fin = st.slider("Has para S7 (PGSA/PSA)", 0.0, float(total_has_maquinas),
                                       float(total_has_maquinas / 2), key="s7_fin")
                has_s700_fin = total_has_maquinas - has_s7_fin
                st.caption(f"S7: {has_s7_fin:,.1f} ha | S700: {has_s700_fin:,.1f} ha")

            rto_prom = sum(dict_rtos.values()) / len(dict_rtos) if dict_rtos else 0
            v_c_s7 = ah_pgsa_l_ha * precio_gasoil
            v_g_s7 = (((p_sin_psa - p_con_psa) / 1000) * precio_grano_usd) + (precio_grano_usd * rto_prom * castigo_psa)
            v_c_s700 = ah_hs_l_ha * precio_gasoil
            v_g_s700 = (((p_sin_am - p_con_am) / 1000) * precio_grano_usd) + (precio_grano_usd * rto_prom * castigo_am)


            def calcular_impacto_ponderado(row, h_s7, h_s700):
                # Usamos las columnas específicas de cada tecnología del CSV
                u_hs = row['Harvest Smart Activado (%)']
                u_am = row['Auto Maintain Activado (%)']
                u_pgsa = row['Automatización de la velocidad de avance Activo (%)']
                u_psa = row['Automatización de ajustes de cosecha Activo (%)']

                # Para evitar errores si las columnas de S7 vienen vacías (NaN) en datos viejos
                u_pgsa = 0 if pd.isna(u_pgsa) else u_pgsa
                u_psa = 0 if pd.isna(u_psa) else u_psa

                ahorro = (h_s7 * (u_pgsa * v_c_s7 + u_psa * v_g_s7)) + (h_s700 * (u_hs * v_c_s700 + u_am * v_g_s700))
                oculto = (h_s7 * ((1 - u_pgsa) * v_c_s7 + (1 - u_psa) * v_g_s7)) + (
                            h_s700 * ((1 - u_hs) * v_c_s700 + (1 - u_am) * v_g_s700))
                return ahorro, oculto


            h_inicio = df_h.iloc[0];
            h_fin = df_h.iloc[-1]
            ah_ini, oc_ini = calcular_impacto_ponderado(h_inicio, has_s7_ini, has_s700_ini)
            ah_fin, oc_fin = calcular_impacto_ponderado(h_fin, has_s7_fin, has_s700_fin)

            st.markdown("---")
            comp1, comp2 = st.columns(2)
            with comp1:
                st.metric("Ahorro Real (Inicio)", f"USD {ah_ini:,.0f}")
                st.metric("Costo Oculto (Inicio)", f"USD {oc_ini:,.0f}")
            with comp2:
                st.metric("Ahorro Real (Fin)", f"USD {ah_fin:,.0f}", delta=f"↑ USD {ah_fin - ah_ini:,.0f}")
                st.metric("Costo Oculto (Fin)", f"USD {oc_fin:,.0f}")

    with st.expander("📂 Ver registros detallados"):
        st.dataframe(df_final, use_container_width=True)
else:
    st.info("👋 Por favor, carga el archivo de cosecha para iniciar la auditoría.")
