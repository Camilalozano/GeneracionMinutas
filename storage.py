"""Persistencia exclusiva de Minutas; no consulta ni escribe Estudios Previos."""
import hashlib
from urllib.parse import quote

from minutas import TEMPLATE, VERSION, COMPARTIDOS, CONTRATO, INSTITUCION, texto

PROJECT_URL = 'https://zwpmdgpywgypdmqygsvv.supabase.co'
TABLE = 'MinutasIndependientes'
BUCKET = 'minutas-independientes'


def guardar(row, contenido, registro_id, actor, *, url, key, request):
    if url.rstrip('/') != PROJECT_URL:
        raise ValueError('La configuración debe apuntar al proyecto autorizado.')
    if not key:
        raise ValueError('Falta la clave de servidor.')
    headers = {'apikey': key}
    if key.startswith('eyJ'):
        headers['Authorization'] = 'Bearer ' + key
    endpoint = PROJECT_URL + '/rest/v1/' + TABLE
    request('GET', endpoint, headers=headers,
            params={'select': 'id', 'limit': '0'}, timeout=20).raise_for_status()
    path = f'{registro_id}/Minuta.docx'
    # Reuse the generation ID on retry: neither duplicate rows nor duplicate objects.
    request('POST', PROJECT_URL + '/storage/v1/object/' + BUCKET + '/' + quote(path, safe='/'),
            headers={**headers, 'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'x-upsert': 'true'}, data=contenido, timeout=45).raise_for_status()
    record = {
        'id': registro_id, 'actor': actor,
        'numero_contrato': texto(row['numero_contrato']),
        'anio_contrato': int(texto(row['anio_contrato'])),
        'version_plantilla': VERSION,
        'plantilla_sha256': hashlib.sha256(TEMPLATE.read_bytes()).hexdigest(),
        'datos_minuta': {k: texto(row.get(k)) for k in (*COMPARTIDOS, *CONTRATO, *INSTITUCION)},
        'storage_bucket': BUCKET, 'storage_path': path,
        'minuta_sha256': hashlib.sha256(contenido).hexdigest(),
    }
    request('POST', endpoint, headers={**headers, 'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates,return=minimal'},
            params={'on_conflict': 'id'}, json=record, timeout=20).raise_for_status()
    return record
