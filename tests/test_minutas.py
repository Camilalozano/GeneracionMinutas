import ast
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from lxml import etree

import pandas as pd
from docx import Document

import minutas

ROOT = Path(__file__).resolve().parents[1]


def ep_functions(source):
    tree = ast.parse(source)
    wanted = {'replace_text_in_paragraph', 'diligenciar_documento'}
    module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted], type_ignores=[])
    scope = {'Document': Document}
    exec(compile(module, '<ep>', 'exec'), scope)
    return scope['diligenciar_documento']


def fixture():
    data = {key: 'Dato de prueba' for key in (*minutas.CONTRATO, *minutas.INSTITUCION)}
    data.update(minutas.DEFAULTS)
    data.update(contratista='PERSONA DE PRUEBA', tipo_contrato='Prestación de servicios profesionales',
                codigo_objeto='COD-PRUEBA', objeto_contrato='Prestar servicios de análisis de información.',
                numero_contrato='001', anio_contrato='2026', cdp_fecha='15/01/2026',
                contratista_documento='0012345', cdp_numero='0009')
    return data


class Progress:
    def progress(self, value):
        assert 0 <= value <= 1
    def text(self, value):
        pass


class MinutasTest(unittest.TestCase):
    def test_all_parts_resolved_and_source_intact(self):
        before = minutas.TEMPLATE.read_bytes()
        output = minutas.generar_minuta(fixture())
        with zipfile.ZipFile(io.BytesIO(output)) as z:
            xml = ''.join(''.join(etree.fromstring(z.read(n)).itertext()) for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
        self.assertNotIn('{{', xml)
        self.assertIn('ATENEA-001-2026', xml)
        self.assertIn('0012345', xml)
        self.assertIn('15 de enero de 2026', xml)
        self.assertIn('09/12/2025', xml)
        self.assertEqual(before, minutas.TEMPLATE.read_bytes())

    def test_split_runs_and_table_header(self):
        doc = Document()
        p = doc.add_paragraph()
        p.add_run('Antes ').italic = True
        p.add_run('{{contr').bold = True
        p.add_run('atista}} después')
        doc.sections[0].header.add_paragraph('{{numero_contrato}}')
        doc.add_table(rows=1, cols=1).cell(0,0).text = '{{cdp_numero}}'
        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)
        result = Document(io.BytesIO(minutas.generar_minuta(fixture(), stream)))
        self.assertEqual(result.paragraphs[0].text, 'Antes PERSONA DE PRUEBA después')
        self.assertTrue(result.paragraphs[0].runs[0].italic)
        self.assertEqual(result.tables[0].cell(0,0).text, '0009')
        self.assertIn('001', '\n'.join(p.text for p in result.sections[0].header.paragraphs))

    def test_reject_missing_wrong_date_and_unsupported_contract(self):
        for key, value in [('contratista', ''), ('cdp_fecha', '31/02/2026'),
                           ('tipo_contrato', 'Compraventa'), ('anio_contrato', '2026.0'),
                           ('numero_contrato', 'ATENEA-001-2026'), ('ordenador_nombre', float('nan'))]:
            with self.subTest(key=key):
                data = fixture(); data[key] = value
                with self.assertRaises(ValueError):
                    minutas.generar_minuta(data)




    def test_spanish_labels_are_not_mojibake(self):
        source = (ROOT/'minutas.py').read_text(encoding='utf-8')
        self.assertNotIn('\u00c3', source)
        self.assertNotIn('\u00c2', source)
        self.assertIn('N\u00famero de contrato', minutas.CONTRATO['numero_contrato'])



if __name__ == '__main__':
    unittest.main()
