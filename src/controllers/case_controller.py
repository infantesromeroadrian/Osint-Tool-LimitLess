import streamlit as st
import os
from datetime import datetime
from pathlib import Path
from services.case_service import CaseService

class CaseController:
    """Controller for case management interface."""
    
    def __init__(self):
        """Initialize the case controller."""
        self.case_service = CaseService()

    def render(self):
        """Render the case management interface."""
        st.title("📁 Gestión de Casos")
        st.write("Crea, selecciona y gestiona casos de investigación OSINT.")
        
        # Display active case if any
        active_case_id = self.case_service.get_active_case()
        if active_case_id:
            active_case = self.case_service.get_case_info(active_case_id)
            if active_case:
                st.success(f"Caso activo: **{active_case['name']}** (ID: {active_case_id})")
            else:
                st.warning("El caso activo ya no existe. Por favor selecciona otro caso.")
                self.case_service.clear_active_case()
        else:
            st.info("No hay ningún caso activo. Selecciona o crea un caso para comenzar.")
        
        # Create tabs for different case management functions
        tab1, tab2, tab3 = st.tabs(["Crear Nuevo Caso", "Seleccionar Caso", "Eliminar Caso"])
        
        with tab1:
            self._render_create_case()
            
        with tab2:
            self._render_select_case()
            
        with tab3:
            self._render_delete_case()
            
    def _render_create_case(self):
        """Render the create case section."""
        st.header("Crear Nuevo Caso")
        st.write("Crea un nuevo caso para comenzar una investigación desde cero.")
        
        case_name = st.text_input("Nombre del Caso", key="case_name_input")
        description = st.text_area("Descripción (opcional)", key="case_description_input")
        
        if st.button("🆕 Crear Caso", key="create_case_button"):
            if not case_name:
                st.error("El nombre del caso es obligatorio.")
                return
                
            with st.spinner("Creando nuevo caso..."):
                success, result = self.case_service.create_case(case_name, description)
                
                if success:
                    st.success(f"Caso creado con éxito: {case_name}")
                    
                    # Ask if user wants to set as active
                    if st.checkbox("Establecer como caso activo", value=True, key="set_active_checkbox"):
                        self.case_service.set_active_case(result)
                        st.success(f"Caso '{case_name}' establecido como caso activo.")
                        st.info("Recarga la página para ver los cambios en todas las pestañas.")
                        
                else:
                    st.error(f"Error al crear el caso: {result}")
                    
    def _render_select_case(self):
        """Render the select case section."""
        st.header("Seleccionar Caso")
        st.write("Selecciona un caso existente para trabajar con él.")
        
        # Get list of cases
        cases = self.case_service.get_cases()
        
        if not cases:
            st.info("No hay casos disponibles. Crea un nuevo caso primero.")
            return
            
        # Format cases for selection
        case_options = {f"{case['name']} (Creado: {self._format_date(case['created_at'])})": case["id"] for case in cases}
        
        # Case selection
        selected_case_name = st.selectbox(
            "Selecciona un caso", 
            list(case_options.keys()),
            key="select_case_dropdown"
        )
        
        selected_case_id = case_options[selected_case_name]
        selected_case = self.case_service.get_case_info(selected_case_id)
        
        if selected_case:
            # Show case details
            st.subheader("Detalles del Caso")
            st.write(f"**Nombre:** {selected_case['name']}")
            st.write(f"**ID:** {selected_case['id']}")
            st.write(f"**Creado:** {self._format_date(selected_case['created_at'])}")
            st.write(f"**Última modificación:** {self._format_date(selected_case['last_modified'])}")
            
            if selected_case.get('description'):
                st.write(f"**Descripción:** {selected_case['description']}")
            
            # Set as active button
            if st.button("📌 Establecer como Caso Activo", key="set_active_button"):
                if self.case_service.set_active_case(selected_case_id):
                    st.success(f"Caso '{selected_case['name']}' establecido como caso activo.")
                    st.info("Recarga la página para ver los cambios en todas las pestañas.")
                else:
                    st.error("Error al establecer el caso como activo.")
    
    def _render_delete_case(self):
        """Render the delete case section."""
        st.header("Eliminar Caso")
        st.write("⚠️ **PRECAUCIÓN:** Eliminar un caso borrará todos los datos asociados permanentemente.")
        
        # Get list of cases
        cases = self.case_service.get_cases()
        
        if not cases:
            st.info("No hay casos disponibles para eliminar.")
            return
            
        # Format cases for selection
        case_options = {f"{case['name']} (Creado: {self._format_date(case['created_at'])})": case["id"] for case in cases}
        
        # Case selection
        selected_case_name = st.selectbox(
            "Selecciona un caso para eliminar", 
            list(case_options.keys()),
            key="delete_case_dropdown"
        )
        
        selected_case_id = case_options[selected_case_name]
        
        # Confirmation
        st.warning(f"¿Estás seguro de que deseas eliminar el caso '{selected_case_name}'? Esta acción no se puede deshacer.")
        
        confirm = st.text_input("Escribe 'ELIMINAR' para confirmar", key="delete_confirmation")
        
        if st.button("🗑️ Eliminar Caso", key="delete_case_button"):
            if confirm != "ELIMINAR":
                st.error("Por favor, escribe 'ELIMINAR' para confirmar la eliminación.")
                return
                
            with st.spinner("Eliminando caso..."):
                active_case_id = self.case_service.get_active_case()
                
                # Clear active case if we're deleting it
                if active_case_id == selected_case_id:
                    self.case_service.clear_active_case()
                
                if self.case_service.delete_case(selected_case_id):
                    st.success(f"Caso '{selected_case_name}' eliminado con éxito.")
                    
                    if active_case_id == selected_case_id:
                        st.info("El caso eliminado era el caso activo. Por favor selecciona un nuevo caso activo.")
                    
                else:
                    st.error("Error al eliminar el caso.")
    
    def _format_date(self, date_string):
        """Format ISO date string to readable format."""
        try:
            dt = datetime.fromisoformat(date_string)
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return date_string 