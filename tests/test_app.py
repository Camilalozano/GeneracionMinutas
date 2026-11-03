import io
import unittest
import zipfile
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from test_minutas import fixture, institucion, ROOT
from referencia import datos_archivo
from storage import guardar, PROJECT_URL, TABLE, BUCKET


class AppTests(unittest.TestCase):
    @patch('requests.request', side_effect=AssertionError('Sin red en pruebas'))
    def test_form_only_generates_minuta_and_clears_invalid_result(self, _):
        app = AppTest.from_file(str(ROOT/'streamlit_app.py'), default_timeout=30)
        app.secrets['ADMIN_PASSWORD'] = 'test-only'
        app.secrets['SUPABASE_SERVICE_ROLE_KEY'] = 'sb_secret_test'
        app.secrets['MINUTA_INSTITUCION'] = institucion()
        app.run()
        self.assertFalse(app.exception)
        data = fixture()
        for field in app.text_input:
            if field.key and field.key.startswith('minuta_'):
                field.set_value(data[field.key[7:]])
        app.text_area[0].set_value(data['objeto'])
        next(b for b in app.button if b.label == 'Generar Minuta').click().run()
        self.assertFalse(app.exception)
        with zipfile.ZipFile(io.BytesIO(app.session_state['resultado']['zip'])) as z:
            self.assertEqual(z.namelist(), ['001_Minuta_001.docx'])
        save = next(b for b in app.button if b.label == 'Guardar Minutas en Supabase')
        self.assertTrue(save.disabled)
        next(f for f in app.text_input if f.label == 'Clave administrativa para guardar').set_value('test-only').run()
        self.assertFalse(next(b for b in app.button if b.label == 'Guardar Minutas en Supabase').disabled)
        app.text_input(key='minuta_cdp').set_value('')
        next(b for b in app.button if b.label == 'Generar Minuta').click().run()
        self.assertNotIn('resultado', app.session_state)
        self.assertTrue(app.warning)

    def test_password_does_not_block_public_form_or_excel(self):
        app = AppTest.from_file(str(ROOT/'streamlit_app.py'))
        app.secrets['ADMIN_PASSWORD'] = 'test-only'
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(any(b.label == 'Generar Minuta' for b in app.button))
        self.assertFalse(any('clave' in f.label.lower() or 'contraseña' in f.label.lower() for f in app.text_input))
        app.radio[0].set_value('Excel').run()
        self.assertFalse(app.exception)
        self.assertTrue(any(b.label == 'Generar Minutas' for b in app.button))

    def test_storage_exclusive_and_idempotent(self):
        calls = []
        class Response:
            def raise_for_status(self):
                pass
        def request(*a, **kw):
            calls.append((a, kw))
            return Response()
        record = guardar(datos_archivo(fixture(),institucion()), b'word', 'test-id', 'Test', url=PROJECT_URL,
                         key='sb_secret_test', request=request)
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[0][0][1].endswith(TABLE))
        self.assertIn(BUCKET, calls[1][0][1])
        self.assertEqual(calls[2][1]['params'], {'on_conflict':'id'})
        self.assertNotIn('estudio_previo_snapshot', record)
        self.assertNotIn('sb_secret_test', str(record))
        with self.assertRaises(ValueError):
            guardar(fixture(), b'word', 'id', '', url='https://other.test', key='x', request=request)

    def test_preflight_failure_prevents_upload(self):
        calls = []
        def fail(*a, **kw):
            calls.append(a)
            raise RuntimeError('offline')
        with self.assertRaises(RuntimeError):
            guardar(fixture(), b'word', 'id', '', url=PROJECT_URL, key='x', request=fail)
        self.assertEqual(len(calls), 1)
