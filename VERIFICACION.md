# Verificación del 3 de noviembre de 2026

Proyecto Supabase exclusivo: `zwpmdgpywgypdmqygsvv`.

- Se reactivó el proyecto y quedó ACTIVE_HEALTHY.
- Se aplicó `separar_minutas_independientes`: tabla `MinutasIndependientes` y bucket privado `minutas-independientes`.
- `schema.sql` ya está aplicado: no volver a ejecutarlo.
- Antes y después: EstudiosPrevios 1687; DocumentosGenerados 5; BitacoraAuditoria 19; MinutasGeneradas 1; archivos históricos 7.
- Nueva tabla: RLS activo, sin acceso anon/authenticated y con SELECT/INSERT/UPDATE para service_role.
- Inserción ficticia comprobada con service_role y revertida dentro de la transacción; no queda registro de prueba.
- El asesor de seguridad solo señala RLS sin políticas (INFO). Es intencional para estas tablas de acceso exclusivo del servidor. Referencia: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy
- 8 pruebas de Minutas y 2 de Estudios Previos aprobadas con datos ficticios. Incluyen Word, encabezados, tablas, validación, contraseña, separación del ZIP y persistencia simulada.
- Estudios Previos integrado mediante Camilalozano/GeneracionEP_Minutas#28.

La prueba real de carga de archivo por la nueva app requiere configurar su clave de servidor y contraseña en Streamlit. No se han copiado ni publicado secretos.
