import streamlit as st
from pathlib import Path
from datetime import datetime
from PIL import Image, UnidentifiedImageError

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# 1. Configuración de la Suite Médica Premium
st.set_page_config(
    page_title="BI-RADS Intelligence Engine v14.0",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

HOSPITAL_NOMBRE = "Hospital Docencia / Investigación"
LOGO_CANDIDATOS = [
    Path(".streamlit/logo.png"),
    Path("assets/logo.png"),
    Path("logo.png"),
]

PLANTILLA_KEYS = [
    "nombre_paciente", "edad_paciente", "sexo_paciente", "tiene_ca_mama_personal", "tipo_cirugia_mama", "recibio_rt",
    "tiene_protesis", "tiene_portacath", "estado_portacath", "tiene_marcapasos",
    "estado_marcapasos", "indicacion", "metodo", "comp_mammo", "comp_eco",
    "hay_md", "hay_mi", "num_md", "num_mi", "ax_md", "ax_mi", "ed_md", "ed_mi",
]

DEFAULTS = {
    "nombre_paciente": "Paciente_Anónima",
    "edad_paciente": 42,
    "sexo_paciente": "Femenino",
    "tiene_ca_mama_personal": "No",
    "tipo_cirugia_mama": "Cirugía Conservadora (Tumorectomía/Cuadrantectomía)",
    "recibio_rt": False,
    "tiene_protesis": "No",
    "tiene_portacath": False,
    "estado_portacath": "Aspecto conservado (Sin complicaciones)",
    "tiene_marcapasos": False,
    "estado_marcapasos": "Aspecto conservado (Sin complicaciones)",
    "indicacion": "Tamizaje de rutina",
    "metodo": "Mamografía",
    "comp_mammo": "B - Fibroglandular dispersa",
    "comp_eco": "Homogénea adiposa",
    "hay_md": "No",
    "hay_mi": "No",
    "num_md": 1,
    "num_mi": 1,
    "ax_md": "Conservados",
    "ax_mi": "Conservados",
    "ed_md": False,
    "ed_mi": False,
    "perfil_medico": "",
    "plantilla_selector": "— Personalizado —",
    "_plantilla_aplicada": "— Personalizado —",
}

PLANTILLAS_SISTEMA = {
    "Tamizaje normal": {
        "indicacion": "Tamizaje de rutina",
        "tiene_ca_mama_personal": "No",
        "recibio_rt": False,
        "sexo_paciente": "Femenino",
        "tiene_protesis": "No",
        "tiene_portacath": False,
        "tiene_marcapasos": False,
        "metodo": "Mamografía",
        "comp_mammo": "B - Fibroglandular dispersa",
        "hay_md": "No",
        "hay_mi": "No",
        "ax_md": "Conservados",
        "ax_mi": "Conservados",
        "ed_md": False,
        "ed_mi": False,
    },
    "Seguimiento post-Qx": {
        "indicacion": "Seguimiento Oncológico",
        "tiene_ca_mama_personal": "Sí",
        "tipo_cirugia_mama": "Cirugía Conservadora (Tumorectomía/Cuadrantectomía)",
        "recibio_rt": True,
        "sexo_paciente": "Femenino",
        "tiene_protesis": "No",
        "tiene_portacath": False,
        "tiene_marcapasos": False,
        "metodo": "Ecografía (Ultrasonido)",
        "comp_eco": "Heterogénea",
        "hay_md": "No",
        "hay_mi": "No",
        "ax_md": "Conservados",
        "ax_mi": "Conservados",
        "ed_md": False,
        "ed_mi": False,
    },
    "Prequirúrgico": {
        "indicacion": "Estadificación Prequirúrgica",
        "tiene_ca_mama_personal": "Sí",
        "tipo_cirugia_mama": "Sin cirugía de mama",
        "recibio_rt": False,
        "sexo_paciente": "Femenino",
        "tiene_protesis": "No",
        "tiene_portacath": False,
        "tiene_marcapasos": False,
        "metodo": "Mamografía",
        "comp_mammo": "C - Heterogéneamente densa",
        "hay_md": "Sí",
        "hay_mi": "No",
        "num_md": 1,
        "ax_md": "Conservados",
        "ax_mi": "Conservados",
        "ed_md": False,
        "ed_mi": False,
    },
    "Nódulo palpable (Eco)": {
        "indicacion": "Nódulo palpable / Mastalgia",
        "tiene_ca_mama_personal": "No",
        "recibio_rt": False,
        "sexo_paciente": "Femenino",
        "metodo": "Ecografía (Ultrasonido)",
        "comp_eco": "Homogénea fibroglandular",
        "hay_md": "Sí",
        "hay_mi": "No",
        "num_md": 1,
        "ax_md": "Conservados",
        "ax_mi": "Conservados",
        "ed_md": False,
        "ed_mi": False,
    },
}

MODALIDAD_KEYS_FIJAS = {
    "comp_mammo", "comp_eco", "hay_md", "hay_mi", "num_md", "num_mi", "ax_md", "ax_mi", "ed_md", "ed_mi",
}
HISTORICO_VACIO = {"Ecografia": {}, "Mamografia": {}}

def init_historico_estudios():
    if "historico_estudios" not in st.session_state:
        st.session_state.historico_estudios = {"Ecografia": {}, "Mamografia": {}}

def modalidad_historico_key(metodo):
    return "Ecografia" if es_ecografia(metodo) else "Mamografia"

def _claves_hallazgos_dinamicos():
    return (
        "h_", "morf_", "dist_", "asi_", "nml_", "dop_", "loc_", "m_",
        "f_", "ma_", "prev_", "evo_", "plano_", "est_imp_", "ed_", "cal_", "cont_", "roi_",
    )

def es_clave_de_modalidad(key):
    if key in MODALIDAD_KEYS_FIJAS:
        return True
    if key.startswith("up_") or key.startswith("btn_"):
        return True
    return any(key.startswith(p) for p in _claves_hallazgos_dinamicos())

def init_session_state():
    init_historico_estudios()
    if "plantillas_usuario" not in st.session_state:
        st.session_state.plantillas_usuario = {}
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "_ultima_modalidad" not in st.session_state:
        st.session_state._ultima_modalidad = st.session_state.get("metodo", DEFAULTS["metodo"])

def limpiar_claves_modalidad_widgets():
    for key in list(st.session_state.keys()):
        if es_clave_de_modalidad(key):
            del st.session_state[key]

def snapshot_modalidad_actual():
    data = {}
    for key in list(st.session_state.keys()):
        if not es_clave_de_modalidad(key):
            continue
        if key.startswith("up_") or key.startswith("btn_"):
            continue
        data[key] = st.session_state[key]
    return data

def guardar_modalidad_en_historico(metodo):
    init_historico_estudios()
    mod_key = modalidad_historico_key(metodo)
    st.session_state.historico_estudios[mod_key] = snapshot_modalidad_actual()

def aplicar_defaults_modalidad(metodo):
    for k in ("hay_md", "hay_mi", "num_md", "num_mi", "ax_md", "ax_mi", "ed_md", "ed_mi"):
        st.session_state[k] = DEFAULTS[k]
    if es_mamografia(metodo):
        st.session_state["comp_mammo"] = DEFAULTS["comp_mammo"]
    else:
        st.session_state["comp_eco"] = DEFAULTS["comp_eco"]

def cargar_modalidad_desde_historico(metodo):
    init_historico_estudios()
    mod_key = modalidad_historico_key(metodo)
    limpiar_claves_modalidad_widgets()
    snapshot = st.session_state.historico_estudios.get(mod_key, {})
    if snapshot:
        for k, v in snapshot.items():
            st.session_state[k] = v
    else:
        aplicar_defaults_modalidad(metodo)

def _al_cambiar_modalidad():
    anterior = st.session_state.get("_ultima_modalidad")
    if anterior and anterior != st.session_state.metodo:
        guardar_modalidad_en_historico(anterior)
    cargar_modalidad_desde_historico(st.session_state.metodo)
    st.session_state._ultima_modalidad = st.session_state.metodo

def reiniciar_paciente():
    plantillas_guardadas = st.session_state.get("plantillas_usuario", {})
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.plantillas_usuario = plantillas_guardadas
    init_session_state()
    st.session_state.historico_estudios = {"Ecografia": {}, "Mamografia": {}}
    aplicar_defaults_modalidad(st.session_state.metodo)
    st.session_state._ultima_modalidad = st.session_state.metodo

def modalidad_tiene_datos(mod_key):
    return bool(st.session_state.historico_estudios.get(mod_key))

def es_ecografia(metodo):
    return "Ecografía" in metodo

def es_mamografia(metodo):
    return metodo == "Mamografía"

def obtener_tecnica_texto(metodo, tiene_protesis):
    if es_ecografia(metodo):
        return "Ultrasonido mamario de alta resolución con transductor lineal y evaluación Doppler Color."
    texto = "Mamografía digital bilateral en proyecciones estándar."
    if tiene_protesis != "No":
        texto += " Incluye maniobras de Eklund."
    return texto

def obtener_composicion_texto(metodo, sexo_paciente):
    if es_ecografia(metodo):
        comp = st.session_state.get("comp_eco", DEFAULTS["comp_eco"])
        return f"Ecoestructura de fondo tipo {comp.lower()}."
    if sexo_paciente == "Masculino":
        return "Tejido mamario masculino."
    comp = st.session_state.get("comp_mammo", DEFAULTS["comp_mammo"])
    return f"Composición mamaria tipo {comp.split(' - ')[0]}."

def _linea_es_residuo_modalidad(linea, metodo):
    linea_l = linea.lower()
    if es_mamografia(metodo):
        if "**ductos:**" in linea_l:
            return True
        if linea.strip().startswith("- **H"):
            marcadores_eco = (
                "nml", "quiste simple", "nódulo sólido", "nodulo solido",
                "complejo / sólido-líquido", "anecoica", "ecotextura", "doppler",
                "hipoecoica", "isoecoica", "hiperecoica",
            )
            return any(m in linea_l for m in marcadores_eco)
    if es_ecografia(metodo):
        if linea.strip().startswith("- **H"):
            marcadores_mammo = ("calcificaciones", "asimetría", "asimetria", "nódulo (masa)", "nodulo (masa)")
            return any(m in linea_l for m in marcadores_mammo)
    return False

def filtrar_resultado_por_modalidad(resultado, metodo):
    """Depura descriptores/conclusión de la modalidad opuesta."""
    desc_lineas = []
    for linea in resultado.get("descriptores", "").split("\n"):
        if linea.strip() and not _linea_es_residuo_modalidad(linea, metodo):
            desc_lineas.append(linea)
    desc_filtrado = "\n".join(desc_lineas)
    if not desc_filtrado.strip():
        desc_filtrado = "- **Parénquima:** Sin alteraciones estructurales dominantes.\n"

    concl_lineas = []
    for linea in resultado.get("conclusion", "").split("\n"):
        if linea.strip() and not _linea_es_residuo_modalidad(linea, metodo):
            concl_lineas.append(linea)
    concl_filtrada = "\n".join(concl_lineas)
    if not concl_filtrada.strip():
        concl_filtrada = "No se evidencian signos imagenológicos focales sugestivos de malignidad."

    return {
        **resultado,
        "descriptores": desc_filtrado + ("\n" if desc_filtrado else ""),
        "conclusion": concl_filtrada,
    }

def filtrar_resultados_por_modalidad(resultados, metodo):
    return {
        mama: filtrar_resultado_por_modalidad(datos, metodo)
        for mama, datos in resultados.items()
    }

def extraer_config_plantilla():
    return {k: st.session_state.get(k, DEFAULTS.get(k)) for k in PLANTILLA_KEYS}

def aplicar_plantilla(config):
    guardar_modalidad_en_historico(st.session_state.get("_ultima_modalidad", st.session_state.metodo))
    nuevo_metodo = config.get("metodo", st.session_state.metodo)
    if nuevo_metodo != st.session_state.metodo:
        limpiar_claves_modalidad_widgets()
        aplicar_defaults_modalidad(nuevo_metodo)
    for key, value in config.items():
        if key in PLANTILLA_KEYS:
            st.session_state[key] = value
    guardar_modalidad_en_historico(st.session_state.metodo)
    st.session_state._ultima_modalidad = st.session_state.metodo

def todas_las_plantillas():
    return ["— Personalizado —", *PLANTILLAS_SISTEMA.keys(), *st.session_state.get("plantillas_usuario", {}).keys()]

def resolver_logo():
    for path in LOGO_CANDIDATOS:
        if path.exists():
            return path
    return None

def _pdf_texto(texto):
    return texto.encode("latin-1", "replace").decode("latin-1")

def generar_pdf_informe(informe_texto, nombre_paciente, medico="", categoria="", imagen_md=None, imagen_mi=None):
    import io
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    logo = resolver_logo()
    if logo:
        pdf.image(str(logo), x=12, y=12, w=35)
        pdf.set_xy(52, 14)
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(pdf.epw - 40, 8, _pdf_texto(HOSPITAL_NOMBRE), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(52)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(pdf.epw - 40, 5, _pdf_texto("Servicio de Diagnóstico por Imágenes — Unidad de Mastología"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_y(44)
    else:
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 8, _pdf_texto(HOSPITAL_NOMBRE), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, _pdf_texto("Servicio de Diagnóstico por Imágenes — Unidad de Mastología"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(4)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    meta = f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if medico:
        meta += f"  |  Médico: {medico}"
    if categoria:
        meta += f"  |  {categoria}"
    pdf.multi_cell(pdf.epw, 5, _pdf_texto(meta))
    pdf.ln(2)
    pdf.set_draw_color(190, 24, 93)
    pdf.set_line_width(0.6)
    y_line = pdf.get_y()
    pdf.line(12, y_line, 198, y_line)
    pdf.ln(6)

    for linea in informe_texto.split("\n"):
        linea = linea.strip()
        pdf.set_x(pdf.l_margin)
        if not linea:
            pdf.ln(3)
            continue
        es_titulo = linea.isupper() or linea.startswith("INFORME DE")
        if es_titulo and len(linea) < 80:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(pdf.epw, 6, _pdf_texto(linea))
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5.5, _pdf_texto(linea))

    imagenes_anexas = [("Mama Derecha", imagen_md), ("Mama Izquierda", imagen_mi)]
    imagenes_anexas = [(titulo, img) for titulo, img in imagenes_anexas if img]
    if imagenes_anexas:
        pdf.ln(4)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(pdf.epw, 6, _pdf_texto("IMÁGENES ANEXADAS"))
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(pdf.epw, 4, _pdf_texto("Documentación aportada por el operador. No fue analizada ni interpretada automáticamente por el sistema."))
        pdf.ln(2)
        for titulo, img_bytes in imagenes_anexas:
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(pdf.epw, 5, _pdf_texto(titulo + ":"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            try:
                pdf.image(io.BytesIO(img_bytes), x=pdf.l_margin, w=90)
            except Exception:
                pdf.set_font("Helvetica", "I", 8)
                pdf.multi_cell(pdf.epw, 4, _pdf_texto("(No se pudo incrustar la imagen en el PDF.)"))
            pdf.ln(4)

    pdf.ln(8)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw, 4,
        _pdf_texto("Documento generado por BI-RADS Intelligence Engine. Uso clínico bajo responsabilidad del médico tratante."),
    )
    return bytes(pdf.output())

@st.cache_data(show_spinner=False)
def obtener_pdf_bytes(informe_texto, nombre_paciente, medico="", categoria="", imagen_md=None, imagen_mi=None):
    return generar_pdf_informe(informe_texto, nombre_paciente, medico, categoria, imagen_md, imagen_mi)

init_session_state()
# --- FUNCIÓN DE UTILIDAD BI-RADS ---
def valor_birads(cat):
    val = {"1":1, "2":2, "3":3, "4A":4.1, "4B":4.2, "4C":4.3, "5":5, "6":6}
    c = cat.replace("BI-RADS ", "").strip()
    return val.get(c, 1)

def _number_input_restaurable(label, key, default, **kwargs):
    if key not in st.session_state:
        kwargs["value"] = default
    return st.number_input(label, key=key, **kwargs)

def evaluar_riesgo_ahf(banderas):
    """
    Evaluación de riesgo por Antecedente Heredofamiliar (AHF) de cáncer de mama,
    según criterios estándar de tamizaje suplementario (ACS/NCCN, riesgo de por
    vida >= 20-25%). El resultado se estructura conforme a la indicación BI-RADS
    v2025 'Asymptomatic Screening — Elevated risk' (Tabla 4, sección MRI, Reporting
    System, pág. 711 del Manual), que define las subcategorías 'Gene mutation' y
    'Estimated cancer risk' como historia clínica relevante a documentar.

    Esta función es aditiva y no modifica ninguna lógica de evaluación BI-RADS
    de hallazgos (evaluar_nml, categorización de mama, etc.) ya existente.
    """
    etiquetas_ahf = {
        "mutacion_conocida": "Mutación genética patogénica conocida (BRCA1/2, PALB2, TP53, PTEN u otra) en la paciente o un familiar de 1er grado",
        "sindrome_genetico": "Síndrome genético conocido (Li-Fraumeni, Cowden/PTEN, Bannayan-Riley-Ruvalcaba)",
        "familiar_precoz": "Familiar de 1er grado con cáncer de mama diagnosticado a los ≤ 50 años",
        "multiples_familiares": "≥ 2 familiares (1er o 2do grado, mismo lado) con cáncer de mama y/o de ovario",
        "ovario": "Antecedente personal o familiar de cáncer de ovario",
        "masculino": "Familiar masculino con cáncer de mama",
        "ashkenazi": "Ascendencia judía Ashkenazi con antecedente familiar de cáncer de mama/ovario",
        "radioterapia": "Radioterapia torácica entre los 10 y 30 años de edad (ej. Linfoma de Hodgkin)",
    }
    claves_geneticas = ("mutacion_conocida", "sindrome_genetico")

    positivos = [clave for clave, marcado in banderas.items() if marcado and clave in etiquetas_ahf]
    riesgo_elevado = len(positivos) > 0

    subcategoria_indicacion = None
    if any(clave in positivos for clave in claves_geneticas):
        subcategoria_indicacion = "Gene mutation"
    elif riesgo_elevado:
        subcategoria_indicacion = "Estimated cancer risk"

    if riesgo_elevado:
        recomendacion = (
            "Riesgo heredofamiliar ELEVADO (estimado ≥20% de riesgo de por vida). "
            "Se recomienda tamizaje suplementario con Resonancia Magnética (RM) mamaria "
            "contrastada anual, en adición a la mamografía anual, según criterios ACS/NCCN. "
            "Considerar interconsulta con Genética Oncológica."
        )
    else:
        recomendacion = (
            "No se identifican criterios de riesgo heredofamiliar elevado. "
            "Continuar tamizaje estándar según guías vigentes."
        )

    return {
        "riesgo_elevado": riesgo_elevado,
        "criterios_positivos": [etiquetas_ahf[c] for c in positivos],
        "indicacion_estructurada": "Asymptomatic Screening — Elevated risk" if riesgo_elevado else None,
        "subcategoria_indicacion": subcategoria_indicacion,
        "recomendacion": recomendacion,
    }

def es_categoria_critica(cat):
    return cat in ("BI-RADS 4C", "BI-RADS 5")

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

def limpiar_md(texto):
    return texto.replace("**", "").replace("*", "").strip()

def _oracion_hallazgo_focal(cuerpo, es_primero):
    cuerpo = limpiar_md(cuerpo).rstrip(".")
    if not cuerpo:
        return ""
    lc = cuerpo[0].lower() + cuerpo[1:]
    conectores = ("se observa", "se identifica", "se describe", "se evidencia", "imagen")
    if any(cuerpo.lower().startswith(c) for c in conectores):
        texto = cuerpo if cuerpo[0].isupper() else cuerpo[0].upper() + cuerpo[1:]
    elif es_primero:
        texto = f"Se identifica {lc}"
    else:
        texto = f"Asimismo, se identifica {lc}"
    return texto + "."

def descriptores_a_prosa(descriptores):
    oraciones = []
    hallazgo_idx = 0
    for linea in descriptores.split("\n"):
        linea = linea.strip()
        if not linea.startswith("- "):
            continue
        contenido = limpiar_md(linea[2:])
        if ":" not in contenido:
            if contenido:
                oraciones.append(contenido if contenido.endswith(".") else contenido + ".")
            continue
        prefijo, _, cuerpo = contenido.partition(":")
        prefijo, cuerpo = prefijo.strip(), cuerpo.strip()
        if prefijo == "Parénquima":
            if "sin alteraciones" in cuerpo.lower():
                oraciones.append("Parénquima mamario sin alteraciones estructurales dominantes.")
            else:
                oraciones.append(cuerpo if cuerpo.endswith(".") else cuerpo + ".")
        elif prefijo == "Implante":
            txt = cuerpo if cuerpo.lower().startswith("implante") else f"Implante mamario {cuerpo[0].lower()}{cuerpo[1:]}"
            oraciones.append(txt if txt.endswith(".") else txt + ".")
        elif prefijo == "Ductos":
            oraciones.append(f"A nivel retroareolar, sistema ductal {cuerpo.lower().rstrip('.')}.")
        elif prefijo == "Axila":
            if "sospechosa" in cuerpo.lower():
                oraciones.append("En región axilar se evidencian adenopatías morfológicamente sospechosas.")
            elif "intramamario" in cuerpo.lower():
                oraciones.append("Se identifica ganglio intramamario de morfología conservada.")
            else:
                oraciones.append("Región axilar sin evidencia de adenopatías significativas.")
        elif prefijo.startswith("H"):
            oracion = _oracion_hallazgo_focal(cuerpo, hallazgo_idx == 0)
            if oracion:
                oraciones.append(oracion)
                hallazgo_idx += 1
        elif cuerpo:
            oraciones.append(cuerpo if cuerpo.endswith(".") else cuerpo + ".")
    if not oraciones:
        return "Sin hallazgos mamarios significativos."
    return " ".join(oraciones)

def conclusion_a_prosa(conclusion, categoria):
    frases = []
    for linea in conclusion.split("\n"):
        linea = limpiar_md(linea.strip())
        if not linea:
            continue
        if linea.startswith("- "):
            linea = linea[2:]
        if linea.lower().startswith("hallazgo"):
            _, _, linea = linea.partition(":")
            linea = linea.strip()
        if linea.startswith("Implante:") or linea.startswith("Axila:"):
            frases.append(linea if linea.endswith(".") else linea + ".")
        elif linea:
            frases.append(linea if linea.endswith(".") else linea + ".")
    if not frases:
        if categoria == "BI-RADS 1":
            return f"Estudio negativo. Clasificación {categoria}."
        if categoria == "BI-RADS 2":
            return f"Hallazgos benignos. Clasificación {categoria}."
        return f"Clasificación {categoria}."
    texto = " ".join(frases)
    if categoria not in texto:
        texto += f" Impresión: {categoria}."
    return texto

def dispositivos_a_prosa(texto_dispositivos):
    lineas = []
    for linea in texto_dispositivos.split("\n"):
        linea = limpiar_md(linea.strip())
        if not linea.startswith("- "):
            continue
        cuerpo = linea[2:]
        if "reservorio" in cuerpo.lower() or "port-a-cath" in cuerpo.lower():
            if "conservado" in cuerpo.lower():
                lineas.append("Reservorio venoso subcutáneo (Port-a-Cath) de aspecto conservado, sin complicaciones pericatéter evidentes.")
            else:
                detalle = cuerpo.split("asociado a")[-1].strip().rstrip(".") if "asociado" in cuerpo.lower() else cuerpo
                lineas.append(f"Reservorio venoso subcutáneo con hallazgos compatibles con {detalle}.")
        elif "marcapasos" in cuerpo.lower():
            if "conservado" in cuerpo.lower():
                lineas.append("Generador de marcapasos en región infraclavicular, de aspecto conservado.")
            else:
                detalle = cuerpo.split("asociado a")[-1].strip().rstrip(".") if "asociado" in cuerpo.lower() else cuerpo
                lineas.append(f"Generador de marcapasos con hallazgos compatibles con {detalle}.")
    return " ".join(lineas)

def recomendacion_a_prosa(recomendacion, categoria, metodo=None):
    rec = recomendacion.strip()
    if categoria in ("BI-RADS 1", "BI-RADS 2"):
        return "Se sugiere continuar con control de tamizaje anual según guías vigentes."
    if categoria == "BI-RADS 3":
        if metodo and es_mamografia(metodo):
            return "Se recomienda control mamográfico a corto plazo (6 meses) para documentar estabilidad."
        return "Se recomienda control ecográfico a corto plazo (6 meses) para documentar estabilidad."
    if valor_birads(categoria) >= 4:
        if metodo and es_mamografia(metodo):
            return "Se indica correlación histopatológica mediante biopsia estereotáxica o percutánea, según corresponda al hallazgo."
        return "Se indica correlación histopatológica mediante biopsia percutánea ecoguiada o estereotáxica, según corresponda al hallazgo."
    if "marcapasos" in rec.lower():
        return "Seguimiento oncológico anual. Resonancia magnética mamaria teóricamente indicada, pero contraindicada por presencia de dispositivo cardiaco implantable."
    if "resonancia" in rec.lower():
        return "Seguimiento anual con consideración de resonancia magnética mamaria con contraste en contexto de antecedente oncológico."
    return rec if rec.endswith(".") else rec + "."

def generar_informe_pacs(
    metodo, nombre_paciente, edad_paciente, indicacion, antecedente_ca,
    tecnica_texto, composicion_texto, texto_dispositivos,
    resultados, global_cat, global_rec, sexo_paciente="Femenino", tiene_protesis="No",
):
    # Informe basado exclusivamente en la modalidad activa; la otra queda en historico_estudios
    metodo = st.session_state.get("metodo", metodo)
    if es_mamografia(metodo):
        modalidad = "MAMOGRAFÍA BILATERAL"
    elif es_ecografia(metodo):
        modalidad = "ECOGRAFÍA MAMARIA BILATERAL"
    else:
        modalidad = "ESTUDIO MAMARIO BILATERAL"

    tecnica_texto = obtener_tecnica_texto(metodo, tiene_protesis)
    composicion_texto = obtener_composicion_texto(metodo, sexo_paciente)
    resultados = filtrar_resultados_por_modalidad(resultados, metodo)

    antecedente = (
        "sin antecedentes personales de cáncer de mama"
        if antecedente_ca == "Ninguno"
        else antecedente_ca.lower()
    )
    prosa_md = descriptores_a_prosa(resultados["Mama Derecha"]["descriptores"])
    prosa_mi = descriptores_a_prosa(resultados["Mama Izquierda"]["descriptores"])
    imp_md = conclusion_a_prosa(resultados["Mama Derecha"]["conclusion"], resultados["Mama Derecha"]["categoria"])
    imp_mi = conclusion_a_prosa(resultados["Mama Izquierda"]["conclusion"], resultados["Mama Izquierda"]["categoria"])

    seccion_comp = "COMPOSICIÓN MAMARIA" if es_mamografia(metodo) else "ECOESTRUCTURA DE FONDO"

    informe = f"""INFORME DE {modalidad}

Paciente: {nombre_paciente}
Edad: {edad_paciente} años
Indicación del estudio: {indicacion.lower()}.
Antecedentes: {antecedente}.

TÉCNICA
{tecnica_texto}

{seccion_comp}
{composicion_texto.rstrip('.')}."""

    if texto_dispositivos.strip():
        informe += f"""

DISPOSITIVOS Y HALLAZGOS ASOCIADOS
{dispositivos_a_prosa(texto_dispositivos)}"""

    informe += f"""

HALLAZGOS

Mama derecha: {prosa_md}

Mama izquierda: {prosa_mi}

IMPRESIÓN DIAGNÓSTICA

Mama derecha: {imp_md}

Mama izquierda: {imp_mi}

Categoría global de evaluación: {global_cat}.

RECOMENDACIÓN
{recomendacion_a_prosa(global_rec, global_cat, metodo)}"""

    return informe

# 🎨 Estilos — identidad rosa / conciencia cáncer de mama
st.markdown("""
    <style>
    /* Paleta: Rose Quartz · Dusty Rose · legibilidad clínica */
    .stApp {
        background-color: #fdf2f8;
    }
    .block-container {
        color: #0f172a;
    }
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #fff1f2 !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #0f172a !important;
    }

    .main-title-rose {
        color: #be185d !important;
        letter-spacing: 0.3px;
    }
    .accent-subtitle {
        color: #be185d !important;
    }

    .stButton > button:not([kind="secondary"]),
    .stDownloadButton > button {
        background: linear-gradient(135deg, #be185d 0%, #9d174d 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(190, 24, 93, 0.22) !important;
        transition: filter 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton > button:not([kind="secondary"]):hover,
    .stDownloadButton > button:hover {
        filter: brightness(1.06);
        box-shadow: 0 4px 12px rgba(190, 24, 93, 0.28) !important;
    }

    div[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: #fdf2f8 !important;
        color: #9d174d !important;
        border: 2px solid #f9a8d4 !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: #fce7f3 !important;
        border-color: #be185d !important;
        color: #831843 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #fecdd3 !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 4px rgba(190, 24, 93, 0.07) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover,
    div[data-testid="stVerticalBlockBorderWrapper"]:focus-within {
        border-color: #be185d !important;
        box-shadow: 0 2px 10px rgba(190, 24, 93, 0.12) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #be185d !important;
        border-bottom: 3px solid #be185d !important;
        background-color: #fff1f2 !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #9d174d !important;
    }

    .birads-white-text, .birads-white-text * {
        color: #ffffff !important;
    }
    input, .stTextInput input, .stNumberInput input, textarea {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] * {
        color: #0f172a !important;
    }
    div[data-baseweb="select"]:focus-within {
        border-color: #be185d !important;
        box-shadow: 0 0 0 1px #be185d !important;
    }

    .copilot-box {
        background-color: #fff1f2;
        border-left: 4px solid #be185d;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 15px;
        color: #0f172a;
    }
    .copilot-box p {
        color: #0f172a !important;
    }

    hr {
        border-color: #fecdd3 !important;
    }

    .alerta-critica {
        background-color: #140000;
        border: 2px solid #ff073a;
        box-shadow: 0 0 10px #ff073a, 0 0 22px rgba(255, 7, 58, 0.55);
        color: #ff073a;
        padding: 14px 18px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 15px;
        text-align: center;
        margin-bottom: 15px;
        letter-spacing: 0.4px;
        animation: pulse-neon 1.4s ease-in-out infinite alternate;
    }
    @keyframes pulse-neon {
        from { box-shadow: 0 0 8px #ff073a, 0 0 14px rgba(255, 7, 58, 0.35); }
        to { box-shadow: 0 0 16px #ff073a, 0 0 32px rgba(255, 7, 58, 0.75); }
    }
    </style>
""", unsafe_allow_html=True)

# 2. PANEL LATERAL: Control Avanzado del Paciente
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #0f172a; font-family: sans-serif; font-weight: 900; letter-spacing: 1px; margin-bottom:0;'>🩺 BI-RADS ENGINE</h2>", unsafe_allow_html=True)
    st.markdown("<p class='accent-subtitle' style='text-align: center; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-top: 3px;'>Copiloto Multilesional</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #fecdd3; margin: 15px 0;'>", unsafe_allow_html=True)

    st.markdown("<h3 style='color: #0f172a; font-size: 16px;'>👤 Perfil / Plantillas</h3>", unsafe_allow_html=True)
    st.text_input("Médico responsable:", key="perfil_medico", placeholder="Dr. / Dra. ...")

    opciones_plantilla = todas_las_plantillas()
    if st.session_state.plantilla_selector not in opciones_plantilla:
        st.session_state.plantilla_selector = "— Personalizado —"

    plantilla_elegida = st.selectbox("Plantilla de estudio:", opciones_plantilla, key="plantilla_selector")
    if st.button("📋 Aplicar plantilla", use_container_width=True):
        if plantilla_elegida == "— Personalizado —":
            st.info("Seleccione una plantilla distinta de 'Personalizado'.")
        elif plantilla_elegida in PLANTILLAS_SISTEMA:
            aplicar_plantilla(PLANTILLAS_SISTEMA[plantilla_elegida])
            st.session_state._plantilla_aplicada = plantilla_elegida
            st.rerun()
        elif plantilla_elegida in st.session_state.plantillas_usuario:
            aplicar_plantilla(st.session_state.plantillas_usuario[plantilla_elegida])
            st.session_state._plantilla_aplicada = plantilla_elegida
            st.rerun()

    nombre_nueva_pl = st.text_input("Guardar config. actual como:", key="nombre_nueva_plantilla", placeholder="Ej: Mi protocolo FCC")
    if st.button("💾 Guardar plantilla personal", use_container_width=True):
        if nombre_nueva_pl.strip():
            st.session_state.plantillas_usuario[nombre_nueva_pl.strip()] = extraer_config_plantilla()
            st.success(f"Plantilla '{nombre_nueva_pl.strip()}' guardada.")
        else:
            st.warning("Ingrese un nombre para la plantilla.")

    if st.session_state.plantillas_usuario:
        with st.expander("Mis plantillas guardadas"):
            for nombre in st.session_state.plantillas_usuario:
                st.caption(f"• {nombre}")

    st.markdown("<hr style='border-color: #fecdd3; margin: 12px 0;'>", unsafe_allow_html=True)

    st.markdown("<h3 style='color: #0f172a; font-size: 18px;'>📝 Datos de Filiación</h3>", unsafe_allow_html=True)
    nombre_paciente = st.text_input("Paciente / ID:", key="nombre_paciente")
    edad_paciente = st.number_input("Edad:", min_value=15, max_value=110, key="edad_paciente")
    sexo_paciente = st.radio("Sexo Biológico:", ["Femenino", "Masculino"], horizontal=True, key="sexo_paciente")

    st.markdown("<h3 style='color: #0f172a; font-size: 15px; margin-top:10px;'>🎗️ Antecedentes Oncológicos Personales</h3>", unsafe_allow_html=True)
    tiene_ca_mama_personal = st.radio(
        "¿Antecedente personal de Cáncer de Mama?",
        ["No", "Sí"],
        horizontal=True,
        key="tiene_ca_mama_personal",
    )
    if tiene_ca_mama_personal == "Sí":
        tipo_cirugia_mama = st.radio(
            "Tipo de cirugía en la mama afectada:",
            ["Cirugía Conservadora (Tumorectomía/Cuadrantectomía)", "Mastectomía", "Sin cirugía de mama"],
            key="tipo_cirugia_mama",
        )
        if tipo_cirugia_mama.startswith("Cirugía Conservadora"):
            antecedente_ca = "Sí (Cirugía Conservadora)"
        elif tipo_cirugia_mama == "Mastectomía":
            antecedente_ca = "Sí (Mastectomía Radical)"
        else:
            antecedente_ca = "Sí (Sin Cirugía Mamaria)"
    else:
        antecedente_ca = "Ninguno"

    if antecedente_ca != "Ninguno":
        recibio_rt = st.checkbox("Recibió Radioterapia", key="recibio_rt")
    else:
        st.session_state.recibio_rt = False
        recibio_rt = False

    otro_antecedente_oncologico = st.text_input(
        "Otro antecedente oncológico (no mamario / no influye en el estudio):",
        key="otro_antecedente_oncologico",
        placeholder="Ej: Linfoma tratado en 2018, Ca. de tiroides operado...",
    )

    st.markdown("<h3 style='color: #0f172a; font-size: 15px; margin-top:10px;'>🧬 Antecedente Heredofamiliar (AHF)</h3>", unsafe_allow_html=True)
    with st.expander("Evaluar riesgo por AHF"):
        ahf_banderas = {
            "mutacion_conocida": st.checkbox("Mutación genética patogénica conocida (BRCA1/2, PALB2, TP53, PTEN u otra) en la paciente o familiar de 1er grado", key="ahf_mutacion_conocida"),
            "sindrome_genetico": st.checkbox("Síndrome genético conocido (Li-Fraumeni, Cowden/PTEN, Bannayan-Riley-Ruvalcaba)", key="ahf_sindrome_genetico"),
            "familiar_precoz": st.checkbox("Familiar de 1er grado con cáncer de mama diagnosticado ≤ 50 años", key="ahf_familiar_precoz"),
            "multiples_familiares": st.checkbox("≥ 2 familiares (1er o 2do grado, mismo lado) con cáncer de mama y/o ovario", key="ahf_multiples_familiares"),
            "ovario": st.checkbox("Antecedente personal o familiar de cáncer de ovario", key="ahf_ovario"),
            "masculino": st.checkbox("Familiar masculino con cáncer de mama", key="ahf_masculino"),
            "ashkenazi": st.checkbox("Ascendencia judía Ashkenazi con antecedente familiar de mama/ovario", key="ahf_ashkenazi"),
            "radioterapia": st.checkbox("Radioterapia torácica entre los 10-30 años (ej. Linfoma de Hodgkin)", key="ahf_radioterapia"),
        }
    riesgo_ahf = evaluar_riesgo_ahf(ahf_banderas)
    if riesgo_ahf["riesgo_elevado"]:
        st.warning("🧬 Riesgo heredofamiliar ELEVADO — requiere tamizaje suplementario con RM mamaria.")
    else:
        st.caption("🧬 AHF: sin criterios de riesgo elevado identificados.")

    st.markdown("<h3 style='color: #0f172a; font-size: 15px; margin-top:10px;'>⚙️ Dispositivos e Implantes</h3>", unsafe_allow_html=True)
    tiene_protesis = "No"
    if sexo_paciente == "Femenino" or antecedente_ca == "Sí (Mastectomía Radical)":
        tiene_protesis = st.selectbox("Implantes Mamarios:", ["No", "Sí (Bilateral)", "Sí (Solo Derecha)", "Sí (Solo Izquierda)"], key="tiene_protesis")
    
    tiene_portacath = st.checkbox("Port-a-Cath (Reservorio Venoso)", key="tiene_portacath")
    estado_portacath = "No aplica"
    if tiene_portacath:
        estado_portacath = st.selectbox("Estado del Bolsillo (Port-a-Cath):", ["Aspecto conservado (Sin complicaciones)", "Colección pericatéter (Seroma/Hematoma)", "Signos inflamatorios locales", "Sospecha de Trombosis asociada"], key="estado_portacath")

    tiene_marcapasos = st.checkbox("Marcapasos / CDI", key="tiene_marcapasos")
    estado_marcapasos = "No aplica"
    if tiene_marcapasos:
        estado_marcapasos = st.selectbox("Estado del Bolsillo (Marcapasos):", ["Aspecto conservado (Sin complicaciones)", "Colección peridispositivo (Seroma/Hematoma)", "Signos inflamatorios locales"], key="estado_marcapasos")

    indicacion = st.selectbox("Indicación Clínica:", ["Tamizaje de rutina", "Seguimiento Oncológico", "Estadificación Prequirúrgica", "Nódulo palpable / Mastalgia", "Evaluación de dispositivos", "Secreción por el pezón", "Ginecomastia en estudio"], key="indicacion")

    st.markdown("<hr style='border-color: #fecdd3; margin: 12px 0;'>", unsafe_allow_html=True)
    if st.button("🔄 Reiniciar Paciente", use_container_width=True, type="secondary"):
        reiniciar_paciente()
        st.rerun()

# 3. CUERPO PRINCIPAL
st.markdown("<h1 class='main-title-rose' style='font-size: 28px; font-weight: 800; margin-bottom:0;'>ESTACIÓN DE TRABAJO RADIOLÓGICA</h1>", unsafe_allow_html=True)
st.markdown("<p class='accent-subtitle' style='font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-top:2px;'>ACR BI-RADS Atlas v5.0 • Módulo NML (Kim et al. 2025)</p>", unsafe_allow_html=True)
if st.session_state._plantilla_aplicada != "— Personalizado —":
    st.caption(f"📋 Plantilla activa: **{st.session_state._plantilla_aplicada}**")
st.markdown("<br>", unsafe_allow_html=True)

metodo = st.radio(
    "Modalidad de Imagen Actual:",
    ["Ecografía (Ultrasonido)", "Mamografía"],
    horizontal=True,
    key="metodo",
    on_change=_al_cambiar_modalidad,
)
badges = []
if modalidad_tiene_datos("Ecografia"):
    badges.append("Ecografía: datos guardados")
if modalidad_tiene_datos("Mamografia"):
    badges.append("Mamografía: datos guardados")
if badges:
    st.caption("💾 " + "  |  ".join(badges))

tecnica_texto = obtener_tecnica_texto(metodo, tiene_protesis)
composicion_texto = obtener_composicion_texto(metodo, sexo_paciente)

col_datos, col_reporte = st.columns([1.15, 1.25])
resultados = {"Mama Derecha": {}, "Mama Izquierda": {}}

# --- FUNCIÓN REUTILIZABLE DE VISIÓN IA ---
def modulo_vision_ia(clave_mama):
    st.markdown(f"**📸 Imagen representativa para el informe ({clave_mama})**")
    f = st.file_uploader(
        "Cargar imagen representativa (se anexa al informe; no es analizada automáticamente):",
        type=["png", "jpg", "jpeg", "webp", "heic", "heif", "bmp", "tiff"],
        key=f"up_{clave_mama}",
    )
    if f:
        try:
            img = Image.open(f)
            img.load()
        except (UnidentifiedImageError, OSError):
            st.error(
                "⚠️ No se pudo abrir esta imagen. Si la tomaste con un iPhone, puede estar en "
                "formato HEIC no compatible con este dispositivo/navegador: probá exportarla o "
                "compartirla como JPG/PNG y volvé a cargarla."
            )
            st.session_state[f"imagen_informe_{clave_mama}"] = None
            return
        st.image(img, caption="Imagen anexada al informe", use_container_width=True)
        st.caption("ℹ️ Esta imagen se adjunta como documentación al informe. No es interpretada ni señalada automáticamente por el sistema.")
        st.session_state[f"imagen_informe_{clave_mama}"] = f.getvalue()
    else:
        st.session_state[f"imagen_informe_{clave_mama}"] = None

with col_datos:
    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0; font-size: 18px;'>🧬 Evaluación y Caracterización</h3>", unsafe_allow_html=True)
        
        if metodo == "Mamografía":
            comp_global = st.selectbox("Densidad Mamaria (ACR):", ["A - Adiposa", "B - Fibroglandular dispersa", "C - Heterogéneamente densa", "D - Extremadamente densa"], key="comp_mammo") if sexo_paciente == "Femenino" else "Tejido mamario masculino"
            composicion_texto = obtener_composicion_texto(metodo, sexo_paciente)
        else:
            comp_global = st.selectbox("Ecoestructura de Fondo:", ["Homogénea adiposa", "Homogénea fibroglandular", "Heterogénea"], key="comp_eco")
            composicion_texto = obtener_composicion_texto(metodo, sexo_paciente)
            
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
                num_hallazgos = st.number_input("Cantidad de hallazgos a describir:", min_value=1, max_value=5, key=f"num_{clave}")
                
                for i in range(num_hallazgos):
                    with st.expander(f"🔍 Hallazgo Focal {i+1}", expanded=True):
                        opciones = []
                        if metodo == "Mamografía": opciones.extend(["Nódulo (Masa)", "Calcificaciones", "Asimetría"])
                        else: opciones.extend(["Nódulo Sólido", "Quiste Simple", "Complejo / Sólido-Líquido", "Lesión No Masa (NML)"])
                        if antecedente_ca != "Ninguno": opciones.append("Cicatriz / Distorsión Post-Tratamiento")
                        
                        hkey = f"h_{clave}_{i}"
                        if hkey in st.session_state and st.session_state[hkey] not in opciones:
                            del st.session_state[hkey]
                        hallazgo = st.selectbox(f"Tipo de Hallazgo {i+1}:", opciones, key=hkey)
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
                            with c2: med = _number_input_restaurable("Dimensión máxima (mm):", f"m_{clave}_{i}", 12.0, min_value=0.0)
                            
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
                        calibre = _number_input_restaurable("Calibre (mm):", f"cal_{clave}", 1.5, min_value=0.0, step=0.1)
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
alerta_critica = es_categoria_critica(global_cat) or es_categoria_critica(cat_md) or es_categoria_critica(cat_mi)

if alerta_critica:
    st.markdown(
        '<div class="alerta-critica">🚨 CRÍTICO: Coordinar biopsia urgente con Docencia/Investigación</div>',
        unsafe_allow_html=True,
    )

if riesgo_ahf["riesgo_elevado"]:
    st.info(f"🧬 **Riesgo Heredofamiliar Elevado** — {riesgo_ahf['recomendacion']}")

# 5. COLUMNA DERECHA: RESPUESTA DE LA IA
with col_reporte:
    with st.container(border=True):
        st.markdown("<h3 class='accent-subtitle' style='margin-top:0; font-size: 18px;'>🤖 Copiloto IA (BI-RADS 5 + NML)</h3>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="birads-white-text" style="background-color: {marcador_color}; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px;">
                <h2 style="font-size: 28px; font-weight: 900; margin: 0; font-family: system-ui; color: white !important;">{global_cat}</h2>
            </div>
        """, unsafe_allow_html=True)
        if alerta_critica:
            st.markdown(
                '<div class="alerta-critica">🚨 CRÍTICO: Coordinar biopsia urgente con Docencia/Investigación</div>',
                unsafe_allow_html=True,
            )

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
        informe_pacs = generar_informe_pacs(
            metodo, nombre_paciente, edad_paciente, indicacion, antecedente_ca,
            tecnica_texto, composicion_texto, texto_dispositivos,
            resultados, global_cat, global_rec,
            sexo_paciente=sexo_paciente, tiene_protesis=tiene_protesis,
        )
        if riesgo_ahf["riesgo_elevado"]:
            informe_pacs += (
                "\n\nEVALUACIÓN DE RIESGO POR ANTECEDENTE HEREDOFAMILIAR (AHF)\n"
                "Indicación estructurada (BI-RADS v2025): " + riesgo_ahf["indicacion_estructurada"]
                + (f" ({riesgo_ahf['subcategoria_indicacion']})" if riesgo_ahf["subcategoria_indicacion"] else "") + ".\n"
                "Criterios identificados: " + "; ".join(riesgo_ahf["criterios_positivos"]) + ".\n"
                + riesgo_ahf["recomendacion"]
            )
        if otro_antecedente_oncologico.strip():
            informe_pacs += (
                "\n\nOTROS ANTECEDENTES ONCOLÓGICOS (no mamarios, sin impacto directo en la interpretación de este estudio)\n"
                + otro_antecedente_oncologico.strip()
            )
        st.text_area("Informe PACS", value=informe_pacs, height=420, label_visibility="collapsed")

        pdf_bytes = obtener_pdf_bytes(
            informe_pacs,
            nombre_paciente,
            medico=st.session_state.get("perfil_medico", ""),
            categoria=global_cat,
            imagen_md=st.session_state.get("imagen_informe_md"),
            imagen_mi=st.session_state.get("imagen_informe_mi"),
        )
        nombre_archivo = f"Informe_BIRADS_{nombre_paciente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button(
            label="⬇ Descargar Informe PDF",
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf",
            use_container_width=True,
        )
        if not resolver_logo():
            st.caption("💡 Para incluir logo institucional, coloque `logo.png` en la carpeta `.streamlit/` o `assets/`.")

guardar_modalidad_en_historico(st.session_state.metodo)
st.session_state._ultima_modalidad = st.session_state.metodo