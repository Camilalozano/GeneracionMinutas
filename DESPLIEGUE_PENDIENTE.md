# Despliegue pendiente

Streamlit Community Cloud no puede acceder al repositorio privado `Camilalozano/GeneracionMinutas`: el formulario muestra que repositorio, rama y archivo no existen. GitHub sí confirma su existencia y permisos de lectura/escritura para la conexión de Codex. Son conexiones diferentes.

1. Autorizar a Streamlit el acceso a este repositorio privado en su conexión GitHub. No es necesario volver público el repositorio.
2. Crear app con repositorio `Camilalozano/GeneracionMinutas`, rama `main`, entrada `streamlit_app.py`, Python 3.12. Nombre propuesto: `generacionminutas-atenea` (todavía no publicado).
3. Introducir directamente en Secrets `SUPABASE_URL = "https://zwpmdgpywgypdmqygsvv.supabase.co"`, una `SUPABASE_SERVICE_ROLE_KEY` válida y `ADMIN_PASSWORD`. No enviar claves por chat ni subirlas al repositorio.
4. La tabla y bucket ya fueron creados y verificados: no repetir `schema.sql`.
5. Comprobar generación y descarga; luego guardado de un registro autorizado y su archivo.

Sin contraseña ni clave, el aplicativo permite generación y descarga local, pero no guardado en Supabase.
