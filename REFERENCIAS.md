# Plantillas y seis campos

El formulario y `templates/BaseVFMinuta.xlsx` usan exactamente estas columnas:
`numerocontrato`, `nombrecontratista`, `cedula`, `modalidad`, `objeto`, `cdp`.
Una fila genera una minuta. Los identificadores deben ingresarse como texto para conservar ceros iniciales.
Modalidades: `PROFESIONALES` y `DE APOYO A LA GESTIÓN`; también se admiten sus nombres completos.
El contrato se imprime como se ingresa: consecutivo, consecutivo-año o ATENEA-consecutivo-año.

El Word se deriva del F7_P11_C V2 suministrado por la usuaria. Conserva cláusulas,
estilos, imágenes, encabezados y pies. El título corresponde a la modalidad.
Los campos de paginación se actualizan al abrir en Word.

Configurar `[MINUTA_INSTITUCION]` en Secrets según `.streamlit/secrets.toml.example`.
Los datos institucionales reales nunca deben incluirse en el repositorio público.
El año y cargo del CDP se toman de esa sección, sin columnas adicionales en el Excel.
Al generar, estos datos se incorporan al Word descargado por el usuario.

No cambia la tabla ni el bucket de Supabase. El JSON conserva los seis campos originales;
las columnas de compatibilidad guardan el consecutivo y el año indicado en el número,
o el año institucional cuando solo se ingresa el consecutivo. Los registros históricos permanecen intactos.

Generación y descarga públicas. Solo el guardado opcional requiere clave administrativa.
