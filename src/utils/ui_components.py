import streamlit as st
from utils.case_path_resolver import CasePathResolver

def show_active_case_indicator():
    """
    Muestra un indicador del caso activo en la interfaz.
    Esta función debe llamarse al principio de cada pestaña.
    """
    case_resolver = CasePathResolver()
    active_case_info = case_resolver.get_active_case_info()
    
    if active_case_info:
        # Mostrar caso activo como un indicador de éxito
        st.sidebar.success(f"📁 Caso activo: **{active_case_info['name']}**")
    else:
        # Mostrar advertencia si no hay caso activo
        st.sidebar.warning("⚠️ No hay caso activo seleccionado. Los datos se guardarán en ubicaciones predeterminadas.")
        st.sidebar.info("Para separar investigaciones, crea y selecciona un caso en la pestaña 'Gestión de Casos'.")
    
    # Agregar un separador visual
    st.sidebar.markdown("---") 