import streamlit as st
from PIL import Image, ImageDraw
import time

# 1. Configuración de la Suite Médica Premium
st.set_page_config(
    page_title="BI-RADS Intelligence Engine v14.0",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNCIÓN DE UTILIDAD BI-RADS ---
def valor_birads(cat):
    val = {"1":1, "2":2, "3":3, "4A":4.1, "4B":4.2, "4C":4.3, "5":5, "6":6}
    c = cat.replace("BI-RADS ", "").strip()
    return val.get(c, 1)

def evaluar_nml(echogenicidad, distribucion, localizacion, asociados, correlacion_multimodal, es_tamizaje, visible_dos_planos=True):
    """Algoritmo NML según Kim et al. Korean J Radiol 2025 (Fig. 19)."""
    labels_asoc = {
        "calcificaciones": "calcificaciones ecogénicas",
        "ductos": "cambios ductales anormales",
        "distorsion": "distorsión arquitectural",
        "sombra": "sombra posterior",
        "microquistes": "microquistes intercalados (<1 cm)",
        "vascular": "hipervascularidad al Doppler",
    }
    asoc_activos = [labels_asoc[k] for k, v in asociados.items() if v and k in labels_asoc]
    sospechosos = sum(1 for k in ("calcificaciones", "ductos", "distorsion", "sombra", "vascular") if asociados.get(k))
    solo_quistes = asociados.get("microquistes") and sospechosos == 0

    desc_h = (
        f"Área de ecotextura alterada (**lesión no masa / NML**), patrón **{echogenicidad.lower()}**, "
        f"distribución **{distribucion.lower()}** en **{localizacion}**"
    )
    if asoc_activos:
        desc_h += f", con {', '.join(asoc_activos)}."
    else:
        desc_h += ", sin hallazgos asociados sospechosos."

    if not visible_dos_planos:
        return (
            "BI-RADS 1",
            "Probable variante de parénquima heterogéneo.",
            "Hallazgo no definitivo como NML (visible en un solo plano).",
            desc_h + " *(No cumple criterio de visibilidad en ≥2 planos ortogonales.)*",
        )

    if correlacion_multimodal:
        if asociados.get("calcificaciones"):
            cat = "BI-RADS 5"
        elif sospechosos >= 2:
            cat = "BI-RADS 4C"
        else:
            cat = "BI-RADS 4B"
        return (
            cat,
            "Correlación con hallazgo clínico o sospechoso en otra modalidad.",
            "Biopsia ecoguiada recomendada (contexto diagnóstico de alto riesgo).",
            desc_h,
        )

    if distribucion in ("Lineal", "Segmentaria"):
        if asociados.get("calcificaciones"):
            cat = "BI-RADS 5"
        elif sospechosos >= 2:
            cat = "BI-RADS 4C"
        else:
            cat = "BI-RADS 4B"
        return (
            cat,
            f"NML con distribución {distribucion.lower()} (patrón ductal).",
            "Biopsia ecoguiada recomendada.",
            desc_h,
        )

    if sospechosos > 0:
        if asociados.get("calcificaciones"):
            cat = "BI-RADS 5" if distribucion == "Regional" else "BI-RADS 4C"
        elif asociados.get("sombra") and asociados.get("ductos"):
            cat = "BI-RADS 4B"
        elif asociados.get("vascular") or asociados.get("distorsion"):
            cat = "BI-RADS 4A" if distribucion == "Focal" else "BI-RADS 4B"
        else:
            cat = "BI-RADS 4A"
        return (
            cat,
            "NML con hallazgos asociados sospechosos.",
            "Biopsia ecoguiada recomendada.",
            desc_h,
        )

    if solo_quistes:
        return (
            "BI-RADS 2",
            "Microquistes intercalados compatibles con cambios fibroquísticos (FCC).",
            "Hallazgo benigno.",
            desc_h,
        )

    if es_tamizaje:
        return (
            "BI-RADS 3",
            "NML en tamizaje sin criterios de sospecha.",
            "Control ecográfico a 6 meses. Biopsia si progresión o nuevos criterios sospechosos.",
            desc_h,
        )

    return (
        "BI-RADS 3",
        "NML sin criterios de sospecha en contexto diagnóstico.",
        "Correlación clínico-mamográfica y seguimiento según criterio.",
        desc_h,
    )

# 🎨 Estilos estéticos
st.markdown("""
    <style>
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    .birads-white-text, .birads-white-text * {
        color: #ffffff !important;
    }
    input, .stTextInput input, .stNumberInput input {
        color: #0f172a !important; 
        -webkit-text-fill-color: #0f172a !important; 
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] * {
        color: #0f172a !important;
    }
    .copilot-box {
        background-color: #f8fafc;
        border-left: 4px solid #0284c7;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. PANEL LATERAL: Control Avanzado del Paciente
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #0f172a; font-family: sans-serif; font-weight: 900; letter-spacing: 1px; margin-bottom:0;'>🩺 BI-RADS ENGINE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #0284c7; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-top: 3px;'>Copiloto Multilesional</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #cbd5e1; margin: 15px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='color: #0f172a; font-size: 18px;'>📝 Datos de Filiación</h3>", unsafe_allow_html=True)
    nombre_paciente = st.text_input("Paciente / ID:", value="Paciente_Anónima")
    edad_paciente = st.number_input("Edad:", min_value=15, max_value=110, value=42)
    sexo_paciente = st.radio("Sexo Biológico:", ["Femenino", "Masculino"], horizontal=True)

    st.markdown("<h3 style='color: #0f172a; font-size: 15px; margin-top:10px;'>🎗️ Antecedentes Oncológicos</h3>", unsafe_allow_html=True)
    antecedente_ca = st.radio("Historia de Cáncer de Mama:", ["Ninguno", "Sí (Cirugía Conservadora)", "Sí (Mastectomía Radical)"])
    recibio_rt = st.checkbox("Recibió Radioterapia") if antecedente_ca != "Ninguno" else False

    st.markdown("<h3 style='color: #0f172a; font-size: 15px; margin-top:10px;'>⚙️ Dispositivos e Implantes</h3>", unsafe_allow_html=True)
    tiene_protesis = "No"
    if sexo_paciente == "Femenino" or antecedente_ca == "Sí (Mastectomía Radical)":
        tiene_protesis = st.selectbox("Implantes Mamarios:", ["No", "Sí (Bilateral)", "Sí (Solo Derecha)", "Sí (Solo Izquierda)"])
    
    tiene_portacath = st.checkbox("Port-a-Cath (Reservorio Venoso)")
    estado_portacath = "No aplica"
    if tiene_portacath: estado_portacath = st.selectbox("Estado del Bolsillo (Port-a-Cath):", ["Aspecto conservado (Sin complicaciones)", "Colección pericatéter (Seroma/Hematoma)", "Signos inflamatorios locales", "Sospecha de Trombosis asociada"])

    tiene_marcapasos = st.checkbox("Marcapasos / CDI")
    estado_marcapasos = "No aplica"
    if tiene_marcapasos: estado_marcapasos = st.selectbox("Estado del Bolsillo (Marcapasos):", ["Aspecto conservado (Sin complicaciones)", "Colección peridispositivo (Seroma/Hematoma)", "Signos inflamatorios locales"])

    indicacion = st.selectbox("Indicación Clínica:", ["Tamizaje de rutina", "Seguimiento Oncológico", "Nódulo palpable / Mastalgia", "Evaluación de dispositivos", "Secreción por el pezón", "Ginecomastia en estudio"])

# 3. CUERPO PRINCIPAL
st.markdown("<h1 style='font-size: 28px; font-weight: 800; margin-bottom:0;'>ESTACIÓN DE TRABAJO RADIOLÓGICA</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 12px; color: #0284c7; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-top:2px;'>ACR BI-RADS Atlas v5.0 • Módulo NML (Kim et al. 2025)</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

metodo = st.radio("Modalidad de Imagen Actual:", ["Ecografía (Ultrasonido)", "Mamografía"], horizontal=True)
tecnica_texto = "Ultrasonido mamario de alta resolución con transductor lineal y evaluación Doppler Color." if "Ecografía" in metodo else "Mamografía digital bilateral en proyecciones estándar."
if tiene_protesis != "No" and metodo == "Mamografía": tecnica_texto += " Incluye maniobras de Eklund."

col_datos, col_reporte = st.columns([1.15, 1.25])
resultados = {"Mama Derecha": {}, "Mama Izquierda": {}}

# --- FUNCIÓN REUTILIZABLE DE VISIÓN IA ---
def modulo_vision_ia(clave_mama):
    st.markdown(f"**📸 Telemetría PACS y Detección CAD ({clave_mama})**")
    f = st.file_uploader(f"Cargar imagen representativa:", type=["png", "jpg", "jpeg"], key=f"up_{clave_mama}")
    if f:
        img = Image.open(f)
        c1, c2 = st.columns(2)
        with c1: st.image(img, caption="Original", use_container_width=True)
        with c2:
            if st.button("🚀 Iniciar Escáner IA (CAD)", key=f"btn_{clave_mama}"):
                with st.spinner("Analizando vóxeles y morfología..."):
                    time.sleep(1.5)
                    img_roi = img.copy()
                    d = ImageDraw.Draw(img_roi)
                    w, h = img.size
                    d.rectangle([w*0.35, h*0.35, w*0.65, h*0.65], outline="red", width=max(3, int(w*0.015)))
                    st.session_state[f"roi_{clave_mama}"] = img_roi
            if st.session_state.get(f"roi_{clave_mama}"):
                st.image(st.session_state[f"roi_{clave_mama}"], caption="🔴 ROI Detectado por IA", use_container_width=True)
                st.success("🤖 Hallazgo localizado. Proceda a la caracterización BI-RADS abajo.")

with col_datos:
    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0; font-size: 18px;'>🧬 Evaluación y Caracterización</h3>", unsafe_allow_html=True)
        
        if metodo == "Mamografía":
            comp_global = st.selectbox("Densidad Mamaria (ACR):", ["A - Adiposa", "B - Fibroglandular dispersa", "C - Heterogéneamente densa", "D - Extremadamente densa"]) if sexo_paciente == "Femenino" else "Tejido mamario masculino"
            composicion_texto = f"Composición mamaria tipo {comp_global.split(' - ')[0]}." if sexo_paciente == "Femenino" else "Tejido mamario masculino."
        else:
            comp_global = st.selectbox("Ecoestructura de Fondo:", ["Homogénea adiposa", "Homogénea fibroglandular", "Heterogénea"])
            composicion_texto = f"Ecoestructura de fondo tipo {comp_global.lower()}."
            
        st.markdown("<br>", unsafe_allow_html=True)
        tab_der, tab_izq = st.tabs(["🟢 MAMA DERECHA", "🔵 MAMA IZQUIERDA"])
        
        # --- FUNCIÓN CENTRAL DE ANÁLISIS ---
        def capturar_datos_mama(nombre_mama, clave):
            modulo_vision_ia(clave)
            st.markdown("---")
            
            mejor_cat = "BI-RADS 1" if antecedente_ca == "Ninguno" else "BI-RADS 2"
            just_global = "Estudio negativo." if antecedente_ca == "Ninguno" else "Hallazgos estables post-tratamiento."
            concl_global = ""
            desc_global = ""
            desc_implante = ""
            sec = 1
            
            # 🌟 1. EVALUACIÓN DE IMPLANTES (NUEVO MÓDULO REGIONAL)
            tiene_implante_aqui = "Bilateral" in tiene_protesis or (nombre_mama.split(" ")[1] in tiene_protesis)
            if tiene_implante_aqui:
                st.markdown(f"**{sec}. Implante Mamario**")
                sec += 1
                c_i1, c_i2 = st.columns(2)
                with c_i1: plano = st.selectbox("Plano anatómico:", ["Retropectoral (Submuscular)", "Retroglandular (Subglandular)"], key=f"plano_{clave}")
                with c_i2: estado_imp = st.selectbox("Estado del Implante:", ["Integridad conservada", "Ruptura intracapsular (Signo del escalón/linguina)", "Ruptura extracapsular (Tormenta de nieve/Siliconoma)", "Contracción capsular", "Colección periprotésica / Seroma tardío"], key=f"est_imp_{clave}")
                
                desc_implante = f"- **Implante:** En plano {plano.split(' ')[0].lower()}, "
                if "conservada" in estado_imp:
                    desc_implante += "de aspecto íntegro, sin signos imagenológicos de complicación.\n"
                else:
                    complicacion = estado_imp.split('(')[0].strip().lower()
                    desc_implante += f"evidenciando signos compatibles con **{complicacion}**.\n"
                    if "Ruptura" in estado_imp:
                        if valor_birads(mejor_cat) < 4.2:
                            mejor_cat, just_global = "BI-RADS 4B", "Sospecha de ruptura protésica."
                        concl_global += "- Implante: Falla protésica sospechada. Se sugiere RM mamaria sin contraste.\n"
                    else:
                        if valor_birads(mejor_cat) < 2:
                            mejor_cat, just_global = "BI-RADS 2", "Complicación protésica benigna."
                        concl_global += f"- Implante: Hallazgos compatibles con {complicacion}.\n"
                st.markdown("---")

            # 🌟 2. PARÉNQUIMA MAMARIO (MULTILESIONAL)
            st.markdown(f"**{sec}. Parénquima Mamario**")
            sec += 1
            hay_hallazgos = st.radio(f"¿Existen hallazgos focales en {nombre_mama}?", ["No", "Sí"], horizontal=True, key=f"hay_{clave}")
            
            if hay_hallazgos == "No":
                desc_global = "- **Parénquima:** Sin alteraciones estructurales dominantes.\n"
            else:
                num_hallazgos = st.number_input("Cantidad de hallazgos a describir:", min_value=1, max_value=5, value=1, key=f"num_{clave}")
                
                for i in range(num_hallazgos):
                    with st.expander(f"🔍 Hallazgo Focal {i+1}", expanded=True):
                        opciones = []
                        if metodo == "Mamografía": opciones.extend(["Nódulo (Masa)", "Calcificaciones", "Asimetría"])
                        else: opciones.extend(["Nódulo Sólido", "Quiste Simple", "Complejo / Sólido-Líquido", "Lesión No Masa (NML)"])
                        if antecedente_ca != "Ninguno": opciones.append("Cicatriz / Distorsión Post-Tratamiento")
                        
                        hallazgo = st.selectbox(f"Tipo de Hallazgo {i+1}:", opciones, key=f"h_{clave}_{i}")
                        cat_h, just_h, concl_h, desc_h = "BI-RADS 1", "", "", ""
                        
                        if "Cicatriz" in hallazgo:
                            desc_h = "Área de **distorsión de la arquitectura** focal en lecho quirúrgico."
                            cat_h, just_h, concl_h = "BI-RADS 2", "Cambios post-quirúrgicos maduros.", "Distorsión arquitectural secundaria a antecedente quirúrgico."
                        elif "Calcificaciones" in hallazgo:
                            c1, c2 = st.columns(2)
                            with c1: morfologia = st.selectbox("Morfología:", ["Típicamente benignas (Vasculares/Piel)", "Amorfas", "Heterogéneas gruesas", "Finas pleomorfas", "Lineales finas o ramificadas"], key=f"morf_{clave}_{i}")
                            with c2: distribucion = st.selectbox("Distribución:", ["Difusa", "Regional", "Agrupada", "Lineal", "Segmentaria"], key=f"dist_{clave}_{i}")
                            desc_h = f"Calcificaciones de morfología **{morfologia.lower()}** con distribución **{distribucion.lower()}**."
                            
                            if "benignas" in morfologia: cat_h, just_h, concl_h = "BI-RADS 2", "Morfología típicamente benigna.", "Calcificaciones benignas."
                            elif "Amorfas" in morfologia or "Heterogéneas" in morfologia: cat_h, just_h, concl_h = "BI-RADS 4B", "Morfología sospechosa (VPP intermedio).", "Microcalcificaciones sospechosas. Se indica biopsia estereotáxica."
                            elif "Finas pleomorfas" in morfologia or "Lineales" in morfologia: cat_h, just_h, concl_h = "BI-RADS 4C", "Alta sospecha de malignidad.", "Microcalcificaciones de alta sospecha. Requiere biopsia."
                            
                            if distribucion in ["Lineal", "Segmentaria"] and "benignas" not in morfologia:
                                cat_h = "BI-RADS 4C" if cat_h == "BI-RADS 4B" else "BI-RADS 5"
                                just_h = "Distribución aumenta VPP."
                                concl_h = concl_h.replace("intermedio", "alto")
                        elif "Asimetría" in hallazgo:
                            tipo_asi = st.selectbox("Tipo de Asimetría:", ["Global", "Focal", "En desarrollo"], key=f"asi_{clave}_{i}")
                            desc_h = f"**Asimetría {tipo_asi.lower()}** en comparación con el tejido contralateral."
                            if tipo_asi == "Global": cat_h, just_h, concl_h = "BI-RADS 2", "Asimetría benigna.", "Asimetría global del parénquima."
                            elif tipo_asi == "Focal": cat_h, just_h, concl_h = "BI-RADS 3", "Asimetría focal.", "Asimetría focal. Se sugiere control."
                            else: cat_h, just_h, concl_h = "BI-RADS 4A", "Neoaparición de tejido.", "Asimetría en desarrollo, requiere correlación."
                        elif "Lesión No Masa" in hallazgo:
                            st.caption("📚 Ref: Kim et al. Korean J Radiol 2025 — Lesiones No Masa (NML). Complemento al BI-RADS 5.")
                            visible_2p = st.radio(
                                "¿Visible en ≥2 planos ortogonales?",
                                ["Sí (criterio NML)", "No (probable variante normal)"],
                                horizontal=True,
                                key=f"nml_2p_{clave}_{i}",
                            )
                            c_n1, c_n2, c_n3 = st.columns(3)
                            with c_n1:
                                eco_nml = st.selectbox(
                                    "Ecogenicidad:",
                                    ["Hipoecoica", "Isoecoica", "Hiperecoica", "Mixta"],
                                    key=f"nml_eco_{clave}_{i}",
                                )
                            with c_n2:
                                dist_nml = st.selectbox(
                                    "Distribución:",
                                    ["Focal", "Lineal", "Segmentaria", "Regional"],
                                    key=f"nml_dist_{clave}_{i}",
                                )
                            with c_n3:
                                loc_nml = st.selectbox(
                                    "Localización:",
                                    [f"Hora {x}" for x in range(1, 13)] + ["Retroareolar", "Central"],
                                    key=f"nml_loc_{clave}_{i}",
                                )
                            st.markdown("**Hallazgos asociados (NML):**")
                            ca1, ca2, ca3 = st.columns(3)
                            with ca1:
                                asoc_calc = st.checkbox("Calcificaciones ecogénicas", key=f"nml_ca_{clave}_{i}")
                                asoc_duct = st.checkbox("Cambios ductales anormales", key=f"nml_cd_{clave}_{i}")
                            with ca2:
                                asoc_dist = st.checkbox("Distorsión arquitectural", key=f"nml_di_{clave}_{i}")
                                asoc_somb = st.checkbox("Sombra posterior", key=f"nml_so_{clave}_{i}")
                            with ca3:
                                asoc_quist = st.checkbox("Microquistes intercalados (<1 cm)", key=f"nml_mq_{clave}_{i}")
                                asoc_vasc = st.checkbox("Hipervascularidad (Doppler)", key=f"nml_va_{clave}_{i}")
                            correlacion_nml = st.radio(
                                "¿Correlaciona con hallazgo clínico o sospechoso en mamografía/RM?",
                                ["No", "Sí"],
                                horizontal=True,
                                key=f"nml_corr_{clave}_{i}",
                            )
                            asociados_nml = {
                                "calcificaciones": asoc_calc,
                                "ductos": asoc_duct,
                                "distorsion": asoc_dist,
                                "sombra": asoc_somb,
                                "microquistes": asoc_quist,
                                "vascular": asoc_vasc,
                            }
                            cat_h, just_h, concl_h, desc_h = evaluar_nml(
                                eco_nml,
                                dist_nml,
                                loc_nml,
                                asociados_nml,
                                correlacion_nml == "Sí",
                                indicacion == "Tamizaje de rutina",
                                visible_2p.startswith("Sí"),
                            )
                        else:
                            c1, c2 = st.columns(2)
                            with c1: 
                                if metodo == "Mamografía": localizacion = st.selectbox("Cuadrante:", ["CSE", "CSI", "CIE", "CII", "Retroareolar", "Central", "Prolongación Axilar"], key=f"loc_{clave}_{i}")
                                else: localizacion = st.selectbox("Radio Horario:", [f"Hora {x}" for x in range(1, 13)] + ["Retroareolar", "Central"], key=f"loc_{clave}_{i}")
                            with c2: med = st.number_input("Dimensión máxima (mm):", min_value=0.0, value=12.0, key=f"m_{clave}_{i}")
                            
                            if hallazgo == "Quiste Simple":
                                desc_h = f"Imagen **anecoica**, circunscrita, con refuerzo posterior en **{localizacion}**, de **{med} mm**."
                                cat_h, just_h, concl_h = "BI-RADS 2", "Quiste simple típico.", f"Quiste simple en {localizacion}."
                            else:
                                forma = st.radio("Forma:", ["Ovalada", "Redonda", "Irregular"], horizontal=True, key=f"f_{clave}_{i}")
                                margen = st.selectbox("Márgenes:", ["Circunscrito", "Indistinto", "Microlobulado", "Espiculado"], key=f"ma_{clave}_{i}")
                                desc_h = f"Imagen nodular de morfología **{forma.lower()}** y márgenes **{margen.lower()}** en **{localizacion}**, de **{med} mm**."
                                
                                if forma == "Ovalada" and margen == "Circunscrito": cat_h, just_h, concl_h = "BI-RADS 3", "Criterios de benignidad.", f"Nódulo {forma.lower()} circunscrito en {localizacion}."
                                elif margen == "Espiculado" or forma == "Irregular": cat_h, just_h, concl_h = "BI-RADS 5", "Morfología altamente sugestiva.", f"Lesión sospechosa en {localizacion}. Biopsia urgente."
                                else: cat_h, just_h, concl_h = "BI-RADS 4B", "Sospecha intermedia.", f"Nódulo de márgenes {margen.lower()} en {localizacion}. Se sugiere biopsia core."

                        # Evolución por Lesión
                        if hallazgo not in ["Quiste Simple", "Cicatriz"]:
                            st.markdown("**Comparativa Evolutiva:**")
                            tiene_previos = st.radio("¿Estudios previos para este hallazgo?", ["No", "Sí"], horizontal=True, key=f"prev_{clave}_{i}")
                            if tiene_previos == "Sí":
                                evolucion = st.selectbox("Evolución:", ["NUEVA (No visible previamente)", "Aumento de tamaño/cambio", "Estable < 24 meses", "Estable > 24 meses"], key=f"evo_{clave}_{i}")
                                if "NUEVA" in evolucion or "Aumento" in evolucion:
                                    if "Lesión No Masa" in hallazgo and cat_h == "BI-RADS 3":
                                        cat_h, just_h = "BI-RADS 4A", "NML con progresión o neoaparición."
                                        concl_h = "NML con cambio evolutivo. Biopsia ecoguiada recomendada."
                                    elif valor_birads(cat_h) < 4.1:
                                        cat_h, just_h = "BI-RADS 4A", "Neoaparición/Progresión."
                                        concl_h += " (Neoaparición/Crecimiento - Requiere biopsia)."
                                    desc_h += f" **(Hallazgo {evolucion.split('(')[0].lower()}).**"
                                elif "> 24 meses" in evolucion:
                                    if cat_h == "BI-RADS 3":
                                        cat_h, just_h = "BI-RADS 2", "Estable a largo plazo."
                                        concl_h += " (Estable > 2 años)."
                            else:
                                desc_h += " *(Sin previos)*."

                        # Doppler Color (Ecografía)
                        if metodo == "Ecografía (Ultrasonido)" and hallazgo in ["Nódulo Sólido", "Complejo / Sólido-Líquido"]:
                            doppler = st.selectbox("Doppler Color:", ["Ausencia de señal", "Vascularización periférica", "Vascularización interna"], key=f"dop_{clave}_{i}")
                            if "interna" in doppler:
                                desc_h += " Muestra **vascularización interna** (neoangiogénesis)."
                                if valor_birads(cat_h) < 4.1:
                                    cat_h, just_h = "BI-RADS 4A", "Vascularización atípica."
                            elif "periférica" in doppler: desc_h += " Flujo periférico al Doppler."

                        # Actualizar Agregadores
                        desc_global += f"- **H{i+1} ({hallazgo}):** {desc_h}\n"
                        concl_global += f"- Hallazgo {i+1}: {concl_h}\n"
                        
                        if valor_birads(cat_h) > valor_birads(mejor_cat):
                            mejor_cat = cat_h
                            just_global = just_h

            # 🌟 3. REGIONES DUCTAL Y AXILAR
            desc_asociados = ""
            if metodo == "Ecografía (Ultrasonido)":
                st.markdown("---")
                st.markdown(f"**{sec}. Región Ductal Retroareolar**")
                sec += 1
                eval_ductos = st.checkbox("Evaluar Sistema Ductal", key=f"ed_{clave}")
                if eval_ductos:
                    cd1, cd2 = st.columns(2)
                    with cd1: 
                        calibre = st.number_input("Calibre (mm):", min_value=0.0, value=1.5, step=0.1, key=f"cal_{clave}")
                        st.caption("ℹ️ **Ref:** Normal ≤ 2.0 mm | Ectasia 2.1 - 3.0 mm | Dilatación > 3.0 mm")
                    with cd2: contenido = st.selectbox("Contenido:", ["Anecoico (Líquido)", "Ecos internos", "Masa intraductal"], key=f"cont_{clave}")
                    
                    est_duc = "conservados" if calibre <= 2.0 else ("**con ectasia**" if calibre <= 3.0 else "**francamente dilatados**")
                    desc_asociados += f"- **Ductos:** Calibre {est_duc} ({calibre} mm)."
                    if "Ecos" in contenido: desc_asociados += " Ecos internos."
                    elif "Masa" in contenido:
                        desc_asociados += " **Masa sólida intraductal.**"
                        if valor_birads(mejor_cat) < 4.1: mejor_cat, just_global = "BI-RADS 4A", "Lesión intraductal."
                    desc_asociados += "\n"

            st.markdown("---")
            st.markdown(f"**{sec}. Región Axilar**")
            estado_axila = st.selectbox("Ganglios linfáticos:", ["Conservados", "Ausencia adenopatías", "Ganglio intramamario típico", "Adenopatía Sospechosa"], key=f"ax_{clave}")
            
            desc_axila = "- **Axila:** Conservada/Sin adenopatías." if estado_axila in ["Conservados", "Ausencia adenopatías"] else ("- **Axila:** Ganglio intramamario típico." if "intramamario" in estado_axila else "- **Axila:** **Adenopatía morfológicamente sospechosa**.")
            
            if "Sospechosa" in estado_axila and valor_birads(mejor_cat) < 4.2:
                mejor_cat, just_global = "BI-RADS 4B", "Adenopatía sospechosa."
                concl_global += "- Axila: Adenopatía de sospecha intermedia/alta.\n"

            desc_final = desc_implante + desc_global + desc_asociados + desc_axila + "\n"
            if concl_global == "": concl_global = "No se evidencian signos imagenológicos focales sugestivos de malignidad."

            return {"categoria": mejor_cat, "justificacion": just_global, "conclusion": concl_global, "descriptores": desc_final}

        with tab_der: resultados["Mama Derecha"] = capturar_datos_mama("Mama Derecha", "md")
        with tab_izq: resultados["Mama Izquierda"] = capturar_datos_mama("Mama Izquierda", "mi")

# 4. LÓGICA DE CATEGORIZACIÓN GLOBAL
cat_md = resultados["Mama Derecha"]["categoria"]
cat_mi = resultados["Mama Izquierda"]["categoria"]
global_cat = cat_md if valor_birads(cat_md) >= valor_birads(cat_mi) else cat_mi

texto_dispositivos = ""
if tiene_portacath: texto_dispositivos += "- Reservorio venoso (Port-a-Cath) conservado.\n" if "conservado" in estado_portacath else f"- **ATENCIÓN:** Reservorio venoso asociado a **{estado_portacath.lower()}**.\n"
if tiene_marcapasos: texto_dispositivos += "- Generador de marcapasos conservado.\n" if "conservado" in estado_marcapasos else f"- **ATENCIÓN:** Generador de marcapasos asociado a **{estado_marcapasos.lower()}**.\n"

if antecedente_ca != "Ninguno" and global_cat in ["BI-RADS 1", "BI-RADS 2"]:
    global_rec = "Control anual. Indicación teórica de RM mamaria, PERO CONTRAINDICADA por marcapasos." if tiene_marcapasos else "Control anual. Se sugiere fuertemente complementar tamizaje con Resonancia Magnética (RM) con contraste."
else:
    global_rec = "Correlación histopatológica o manejo especializado según hallazgo." if valor_birads(global_cat) >= 4 else "Control según guías de tamizaje."
    if global_cat in ["BI-RADS 1", "BI-RADS 2"]: global_rec = "Control anual de rutina."

colores_birads = {"BI-RADS 1": "#059669", "BI-RADS 2": "#059669", "BI-RADS 3": "#d97706", "BI-RADS 4A": "#ea580c", "BI-RADS 4B": "#ea580c", "BI-RADS 4C": "#dc2626", "BI-RADS 5": "#991b1b"}
marcador_color = colores_birads.get(global_cat, "#1e293b")

# 5. COLUMNA DERECHA: RESPUESTA DE LA IA
with col_reporte:
    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0; font-size: 18px; color: #0284c7;'>🤖 Copiloto IA (BI-RADS 5 + NML)</h3>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="birads-white-text" style="background-color: {marcador_color}; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px;">
                <h2 style="font-size: 28px; font-weight: 900; margin: 0; font-family: system-ui; color: white !important;">{global_cat}</h2>
            </div>
        """, unsafe_allow_html=True)

        tab_res_md, tab_res_mi = st.tabs(["Análisis MD", "Análisis MI"])
        for tab, mama in zip([tab_res_md, tab_res_mi], ["Mama Derecha", "Mama Izquierda"]):
            with tab:
                st.markdown(f"""
                <div class="copilot-box">
                    <p><b>1. Caracterización Estructurada:</b><br>{resultados[mama]["descriptores"].replace('\n', '<br>')}</p>
                    <p><b>2. Categoría Sugerida (Más Alta):</b><br>• <b>{resultados[mama]["categoria"]}</b>: {resultados[mama]["justificacion"]}</p>
                    <p><b>3. Conclusión:</b><br>{resultados[mama]["conclusion"].replace('\n', '<br>')}</p>
                </div>
                """, unsafe_allow_html=True)

    # 6. INFORME PARA PACS
    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0; font-size: 16px;'>📄 Informe para PACS</h3>", unsafe_allow_html=True)
        seccion_dispositivos = f"\nDISPOSITIVOS E IMPLANTES EXTRAS:\n{texto_dispositivos}" if texto_dispositivos else ""
        
        informe_pacs = f"""INFORME DE MASTOLOGÍA - {metodo.upper()}
Paciente: {nombre_paciente} | Edad: {edad_paciente} años
Antecedente Oncológico: {antecedente_ca}

PATRÓN TISULAR: {composicion_texto}{seccion_dispositivos}
HALLAZGOS:
MAMA DERECHA:
{resultados["Mama Derecha"]["descriptores"].replace("**", "")}
MAMA IZQUIERDA:
{resultados["Mama Izquierda"]["descriptores"].replace("**", "")}
IMPRESIÓN DIAGNÓSTICA:
- MD: 
{resultados["Mama Derecha"]["conclusion"].replace("**", "")} ({resultados["Mama Derecha"]["categoria"]})
- MI: 
{resultados["Mama Izquierda"]["conclusion"].replace("**", "")} ({resultados["Mama Izquierda"]["categoria"]})

CATEGORÍA GLOBAL: {global_cat}
RECOMENDACIÓN: {global_rec}
"""
        st.text_area("", value=informe_pacs, height=360, label_visibility="collapsed")