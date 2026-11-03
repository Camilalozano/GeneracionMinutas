"""Aplicativo Streamlit autónomo para Minutas de persona natural."""
import hmac
import io
import os
import uuid
import zipfile

import pandas as pd
import requests
import streamlit as st

from minutas import (COMPARTIDOS, CONTRATO, INSTITUCION, formulario_minuta,
                     generar_minuta, validar_minuta)
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
if mode == 'Formulario':
    with st.form('minuta'):
        data = {}
        data['contratista'] = st.text_input('Contratista *')
        data['tipo_contrato'] = st.selectbox('Tipo de contrato *',
            ['Prestación de servicios profesionales', 'Prestación de servicios de apoyo a la gestión'])
        data['codigo_objeto'] = st.text_input('Código del objeto *')
        data['objeto_contrato'] = st.text_area('Objeto del contrato *')
        data.update(formulario_minuta(st, dict(config('MINUTA_INSTITUCION', {}))))
        submitted = st.form_submit_button('Generar Minuta')
    if submitted:
        rows = [data]
else:
    fields = [*COMPARTIDOS, *CONTRATO, *INSTITUCION]
    excel = io.BytesIO()
    pd.DataFrame(columns=fields).to_excel(excel, index=False)
    st.download_button('Descargar plantilla Excel de Minutas', excel.getvalue(), 'PlantillaMinutas.xlsx')
    uploaded = st.file_uploader('Excel de Minutas', type=['xlsx'])
    st.caption('Guarda números de contrato y documentos como texto para conservar los ceros iniciales.')
    if st.button('Generar Minutas', disabled=uploaded is None):
        st.session_state.pop('resultado', None)
        try:
            frame = pd.read_excel(uploaded, dtype=str).fillna('')
            if frame.empty:
                st.error('El archivo no contiene registros.')
            else:
                rows = frame.to_dict('records')
        except Exception:
            st.error('No se pudo leer el Excel. Verifica su formato.')

if rows is not None:
    st.session_state.pop('resultado', None)
    errors = [f'Fila {i}: {error}' for i, row in enumerate(rows, 1) for error in validar_minuta(row)]
    if errors:
        for error in errors:
            st.warning(error)
    else:
        try:
            documents = [{'id': str(uuid.uuid4()), 'data': row, 'docx': generar_minuta(row),
                          'actor': actor, 'saved': False} for row in rows]
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
                for i, item in enumerate(documents, 1):
                    package.writestr(f'{i:03d}_Minuta_{item["data"]["numero_contrato"]}.docx', item['docx'])
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
