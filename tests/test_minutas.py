import io
import sys
import unittest
import zipfile
from pathlib import Path
from lxml import etree
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from minutas import generar_minuta, validar_minuta, modalidad, TEMPLATE, NS
from referencia import CAMPOS, INSTITUCION, EXCEL_TEMPLATE, leer_excel, datos_archivo

def fixture():
    return dict(zip(CAMPOS, ['001','PERSONA FICTICIA','000123','PROFESIONALES','Prestar servicios de prueba & verificación.','00045']))

def institucion():
    return {**{k:'DATO INSTITUCIONAL DE PRUEBA' for k in INSTITUCION},'anio_cdp':'2026'}

class MotorTests(unittest.TestCase):
    def test_both_modalities_and_preserved_package(self):
        for mode in ['PROFESIONALES', 'DE APOYO A LA GESTIÓN']:
            row={**fixture(),'modalidad':mode}
            with zipfile.ZipFile(io.BytesIO(generar_minuta(row,institucion()))) as result, zipfile.ZipFile(TEMPLATE) as source:
                root=etree.fromstring(result.read('word/document.xml'))
                text=''.join(root.xpath('//w:t/text()',namespaces=NS))
                self.assertIn('PRESTACIÓN DE SERVICIOS '+mode+' No. 001',text)
                for key in ('nombrecontratista','cedula','objeto','cdp'): self.assertIn(row[key],text)
                self.assertNotIn('{{',text)
                self.assertEqual(source.namelist(),result.namelist())
                for name in source.namelist():
                    if name!='word/document.xml': self.assertEqual(source.read(name),result.read(name),name)

    def test_invalid_data_and_missing_configuration(self):
        self.assertTrue(validar_minuta({**fixture(),'numerocontrato':'../test'}))
        self.assertTrue(validar_minuta({**fixture(),'cdp':''}))
        self.assertTrue(validar_minuta({**fixture(),'modalidad':'compraventa'}))
        with self.assertRaises(ValueError): generar_minuta(fixture(),{})
        self.assertEqual(modalidad('Prestación de servicios de apoyo a la gestión'),'DE APOYO A LA GESTIÓN')

    def test_excel_headers_text_and_validation(self):
        import openpyxl
        wb=openpyxl.load_workbook(EXCEL_TEMPLATE)
        self.assertEqual(tuple(c.value for c in wb.active[1]),CAMPOS)
        self.assertEqual(wb.active['A2'].number_format,'@')
        self.assertEqual(wb.active['C2'].number_format,'@')
        self.assertTrue(wb.active.data_validations.dataValidation)
        with self.assertRaises(ValueError): leer_excel(EXCEL_TEMPLATE)

    def test_excel_read_retains_zeros_and_row_numbers(self):
        from unittest.mock import patch
        import pandas as pd
        frame=pd.DataFrame([list(CAMPOS),list(fixture().values()),['']*6])
        with patch('pandas.read_excel',return_value=frame):
            rows=leer_excel(io.BytesIO())
        self.assertEqual(rows,[(2,fixture())])
        frame.iloc[0,1]='cedula'
        with patch('pandas.read_excel',return_value=frame), self.assertRaises(ValueError): leer_excel(io.BytesIO())

    def test_database_compatibility(self):
        row=datos_archivo({**fixture(),'numerocontrato':'ATENEA-001-2027'},institucion())
        self.assertEqual(row['numero_contrato'],'001')
        self.assertEqual(row['anio_contrato'],'2027')
        self.assertEqual(row['numerocontrato'],'ATENEA-001-2027')
