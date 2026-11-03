"""Aplicativo Streamlit autónomo para Minutas de persona natural."""
import hmac
import io
import os
import uuid
import zipfile

import pandas as pd
import requests
import streamlit as st

from minutas import generar_minuta, validar_minuta
from referencia import EXCEL_TEMPLATE, leer_excel, validar_institucion, datos_archivo
from storage import guardar, PROJECT_URL


def config(name, default=''):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except FileNotFoundError:
        return os.getenv(name, default)


st.set_page_config(page_title='Atenea · Generación de Minutas', page_icon='📄', layout='wide')
st.title('Generación de Minutas')
st.caption('Minutas de persona natural · Formulario y carga masiva independientes')

# La captura, generación y descarga son públicas.
actor = st.sidebar.text_input('Responsable de la generación')
mode = st.radio('Captura de datos', ['Formulario', 'Excel'])
rows = None
institucion = dict(config('MINUTA_INSTITUCION', {}))
if mode == 'Formulario':
    with st.form('minuta'):
        data = {}
        data['numerocontrato'] = st.text_input('Número de contrato *', key='minuta_numerocontrato', help='Escribe el número tal como debe aparecer: 001 o ATENEA-001-2026.')
        data['nombrecontratista'] = st.text_input('Nombre del contratista *', key='minuta_nombrecontratista')
        data['cedula'] = st.text_input('Cédula del contratista *', key='minuta_cedula')
        data['modalidad'] = st.selectbox('Modalidad *', ['PROFESIONALES', 'DE APOYO A LA GESTIÓN'], key='minuta_modalidad')
        data['objeto'] = st.text_area('Objeto del contrato *', key='minuta_objeto')
        data['cdp'] = st.text_input('Número del CDP *', key='minuta_cdp')
        submitted = st.form_submit_button('Generar Minuta')
    if submitted:
        rows = [(1, data)]
else:
    st.download_button('Descargar plantilla Excel de Minutas', EXCEL_TEMPLATE.read_bytes(), 'BaseVFMinuta.xlsx')
    uploaded = st.file_uploader('Excel de Minutas', type=['xlsx'])
    st.caption('Guarda números de contrato y documentos como texto para conservar los ceros iniciales.')
    if st.button('Generar Minutas', disabled=uploaded is None):
        st.session_state.pop('resultado', None)
        try:
            rows = leer_excel(uploaded)
        except ValueError as error:
            st.error(str(error))
        except Exception:
            st.error('No se pudo leer el Excel. Verifica su formato.')

if rows is not None:
    st.session_state.pop('resultado', None)
    errors = validar_institucion(institucion) + [f'Fila {i}: {error}' for i, row in rows for error in validar_minuta(row)]
    if errors:
        for error in errors:
            st.warning(error)
    else:
        try:
            documents = [{'id': str(uuid.uuid4()), 'data': datos_archivo(row, institucion), 'docx': generar_minuta(row, institucion),
                          'actor': actor, 'saved': False} for _, row in rows]
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
                for i, item in enumerate(documents, 1):
                    package.writestr(f'{i:03d}_Minuta_{item["data"]["numerocontrato"]}.docx', item['docx'])
            st.session_state['resultado'] = {'documents': documents, 'zip': archive.getvalue()}
        except Exception:
            st.error('No se pudo generar la minuta. Verifica la plantilla y los datos.')

result = st.session_state.get('resultado')
if result:
    st.success(f'{len(result["documents"])} minuta(s) generada(s).')
    st.download_button('Descargar Minutas (ZIP)', result['zip'], 'Minutas.zip', 'application/zip')
    if len(result['documents']) == 1:
        st.download_button('Descargar Minuta (Word)', result['documents'][0]['docx'], 'Minuta.docx',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    # La clave administrativa solo protege el guardado; nunca bloquea el uso.
    password = config('ADMIN_PASSWORD')
    entered = ''
    if password and config('SUPABASE_SERVICE_ROLE_KEY'):
        with st.expander('Guardado administrativo (opcional)'):
            entered = st.text_input('Clave administrativa para guardar', type='password')
    enabled = bool(password and config('SUPABASE_SERVICE_ROLE_KEY')
                   and hmac.compare_digest(entered, str(password)))
    if st.button('Guardar Minutas en Supabase', disabled=not enabled):
        for item in result['documents']:
            if item['saved']:
                continue
            try:
                guardar(item['data'], item['docx'], item['id'], item['actor'],
                        url=config('SUPABASE_URL', PROJECT_URL),
                        key=config('SUPABASE_SERVICE_ROLE_KEY'), request=requests.request)
                item['saved'] = True
            except Exception:
                st.warning('No se confirmó el guardado. La descarga está disponible; puedes reintentar sin duplicar registros.')
    saved = sum(item['saved'] for item in result['documents'])
    st.caption(f'Guardadas en Supabase: {saved} de {len(result["documents"])}.')
