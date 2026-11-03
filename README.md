# Generación de Minutas

Aplicativo Streamlit independiente para minutas de persona natural. Extraído de Camilalozano/GeneracionEP_Minutas, commit `5dbf684`, conservando la plantilla y el motor de reemplazo de texto.

## Funciones

- Formulario propio y carga masiva con Excel exclusivo de Minutas.
- Botón Generar Minuta / Generar Minutas, sin generar estudios previos.
- Descarga Word individual y ZIP masivo.
- Guardado explícito en `MinutasIndependientes` y bucket privado `minutas-independientes`.
- Reintentos con el mismo UUID; las descargas siguen disponibles si Supabase falla.
- Contraseña requerida para habilitar persistencia. Sin contraseña funciona en modo local de descarga.

## Ejecutar

```sh
pip install -r requirements.txt
streamlit run streamlit_app.py
python -m unittest discover -s tests -v
```

## Desplegar

1. Crear una app Streamlit desde `Camilalozano/GeneracionMinutas`, rama `main`, archivo `streamlit_app.py`, Python 3.12.
2. Configurar Secrets según `.streamlit/secrets.toml.example`. Introducir los valores directamente en Streamlit, nunca por chat ni en GitHub.
3. Configurar una contraseña de acceso y una clave de servidor de Supabase. El código solo acepta la URL del proyecto `zwpmdgpywgypdmqygsvv`.
4. Crear la tabla y bucket del archivo `schema.sql` después de inspeccionar el proyecto y respaldar el esquema. No ejecutar sobre otro proyecto.
5. Probar con datos ficticios: descarga de una minuta, guardado confirmado y acceso privado al archivo.

## Conservación del histórico

No se modifica `EstudiosPrevios`, `DocumentosGenerados`, `BitacoraAuditoria`, `MinutasGeneradas` ni el bucket `documentos-generados`. La nueva tabla no necesita un estudio previo ni su snapshot. El histórico combinado se conserva íntegro en su ubicación original; no se copia automáticamente.

La separación es por tablas y almacenamiento dentro del proyecto autorizado. Las claves de servidor tienen privilegios amplios dentro de ese proyecto; no hay aislamiento físico de bases ni restricción de credenciales por aplicativo.

Si la carga del Word termina pero falla el registro, puede quedar un archivo sin fila. Reintentar Guardar reutiliza el UUID y la ruta y completa el registro sin duplicarlo. No se borran objetos automáticamente.
