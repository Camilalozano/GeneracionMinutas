"""Seis campos del Excel y configuración institucional privada."""
import re
from pathlib import Path
import pandas as pd
from minutas import texto

CAMPOS = ('numerocontrato', 'nombrecontratista', 'cedula', 'modalidad', 'objeto', 'cdp')
INSTITUCION = ('ordenador_nombre', 'ordenador_documento', 'acto_delegacion',
              'entidad_nombre', 'entidad_nit', 'acto_nombramiento', 'acto_posesion',
              'anio_cdp', 'cdp_expedidor')
EXCEL_TEMPLATE = Path(__file__).parent / 'templates/BaseVFMinuta.xlsx'

def validar_institucion(config):
    missing = [k for k in INSTITUCION if not texto(config.get(k))]
    errors = ['Falta configurar MINUTA_INSTITUCION en Secrets: ' + ', '.join(missing)] if missing else []
    if texto(config.get('anio_cdp')) and not re.fullmatch(r'20[0-9]{2}', texto(config['anio_cdp'])):
        errors.append('MINUTA_INSTITUCION.anio_cdp debe contener cuatro dígitos (2000–2099).')
    if any('{{' in texto(config.get(k)) or '}}' in texto(config.get(k)) for k in INSTITUCION):
        errors.append('La configuración institucional contiene variables sin completar.')
    return errors

def leer_excel(source):
    frame = pd.read_excel(source, header=None, dtype=str, keep_default_na=False)
    if frame.empty:
        raise ValueError('El archivo está vacío.')
    headers = [texto(v) for v in frame.iloc[0]]
    if len(headers) != len(CAMPOS) or set(headers) != set(CAMPOS):
        raise ValueError('El Excel debe contener exactamente estas seis columnas, sin duplicados: ' + ', '.join(CAMPOS))
    frame = frame.iloc[1:].copy()
    frame.columns = headers
    frame = frame.map(texto)
    frame = frame.loc[frame.ne('').any(axis=1)]
    if frame.empty:
        raise ValueError('El archivo no contiene registros. Completa una fila por minuta.')
    return [(int(index) + 1, row.to_dict()) for index, row in frame.iterrows()]

def datos_archivo(data, institucion):
    match = re.fullmatch(r'(?:ATENEA-)?([0-9]+)(?:-(20[0-9]{2}))?', texto(data['numerocontrato']), re.I)
    if not match:
        raise ValueError('Número de contrato no válido.')
    return {**data, 'numero_contrato': match[1], 'anio_contrato': match[2] or texto(institucion['anio_cdp'])}
