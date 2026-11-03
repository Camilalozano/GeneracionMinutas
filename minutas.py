"""Motor Word que conserva las partes y el formato de la plantilla de referencia."""
import io
import copy
import re
import unicodedata
import zipfile
from pathlib import Path
from lxml import etree
import pandas as pd

TEMPLATE = Path(__file__).parent / 'templates/01_Plantilla_minuta_persona_natural.docx'
VERSION = 'F7_P11_C-V2-seis-campos-2026-v2'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def texto(value):
    return '' if value is None or pd.isna(value) else str(value).strip()

def modalidad(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', texto(value).lower()) if not unicodedata.combining(c))
    value = ' '.join(value.split())
    for prefix in ('contrato de ', 'prestacion de ', 'servicios '):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return {'profesionales': 'PROFESIONALES', 'apoyo a la gestion': 'DE APOYO A LA GESTIÓN',
            'de apoyo a la gestion': 'DE APOYO A LA GESTIÓN'}.get(value)

def validar_minuta(data):
    from referencia import CAMPOS
    errors = []
    for key in CAMPOS:
        value = texto(data.get(key))
        if not value:
            errors.append(f'{key}: falta diligenciar.')
        elif '{{' in value or '}}' in value:
            errors.append(f'{key}: reemplaza las llaves por el dato real.')
    if texto(data.get('numerocontrato')) and not re.fullmatch(r'(?:ATENEA-)?[0-9]+(?:-20[0-9]{2})?', texto(data['numerocontrato']), re.I):
        errors.append('numerocontrato: usa el consecutivo (001) o el número completo (ATENEA-001-2026).')
    if texto(data.get('modalidad')) and not modalidad(data['modalidad']):
        errors.append('modalidad: selecciona PROFESIONALES o DE APOYO A LA GESTIÓN.')
    return errors

def reemplazar(paragraph, replacements):
    nodes = paragraph.xpath('.//w:t', namespaces=NS)
    full = ''.join(n.text or '' for n in nodes)
    spans, pos = [], 0
    for node in nodes:
        end = pos + len(node.text or '')
        spans.append((pos, end, node))
        pos = end
    pattern = '|'.join(re.escape(k) for k in sorted(replacements, key=len, reverse=True))
    matches = list(re.finditer(pattern, full))
    for match in reversed(matches):
        affected = [(a,b,n) for a,b,n in spans if a < match.end() and b > match.start()]
        for i, (a,b,node) in enumerate(affected):
            before = (node.text or '')[:max(0, match.start()-a)]
            after = (node.text or '')[max(0, match.end()-a):] if match.end() < b else ''
            node.text = before + (replacements[match.group()] if i == 0 else '') + after
            node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return bool(matches)

def generar_minuta(data, institucion, plantilla=TEMPLATE):
    from referencia import CAMPOS, INSTITUCION, validar_institucion
    errors = validar_minuta(data) + validar_institucion(institucion)
    if errors:
        raise ValueError('\n'.join(errors))
    values = {k: texto(data.get(k)) for k in CAMPOS}
    values.update({k: texto(institucion.get(k)) for k in INSTITUCION})
    values['modalidad'] = modalidad(values['modalidad'])
    replacements = {'{{'+k+'}}': v for k,v in values.items()}
    output = io.BytesIO()
    with zipfile.ZipFile(plantilla) as source, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            payload = source.read(info.filename)
            if re.fullmatch(r'word/(document|header[0-9]+|footer[0-9]+)\.xml', info.filename):
                root = etree.fromstring(payload)
                changed = False
                for paragraph in root.xpath('.//w:p', namespaces=NS):
                    changed |= reemplazar(paragraph, replacements)
                full = ''.join(root.xpath('//w:t/text()', namespaces=NS))
                if '{{' in full or '}}' in full:
                    raise ValueError('La plantilla contiene variables sin resolver.')
                if changed:
                    payload = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
            target.writestr(copy.copy(info), payload)
    return output.getvalue()
