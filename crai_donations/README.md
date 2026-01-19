# Módulo CRAI - Donaciones de Libros

## Descripción

Módulo completo para la gestión de donaciones de libros al Centro de Recursos para el Aprendizaje y la Investigación (CRAI). Permite registrar, aprobar y certificar donaciones individuales, grupales y externas.

## Características Principales

### 1. Tipos de Donación
- **Individual**: Donación de un solo estudiante
- **Grupal**: Donación de varios estudiantes de la misma carrera
- **Externa**: Donación de personas o instituciones externas

### 2. Workflow de Aprobación
1. **Borrador**: El bibliotecario crea la solicitud
2. **Enviada**: Se envía para aprobación
3. **Aprobada/Rechazada**: El aprobador revisa y decide
4. **Certificado Emitido**: Se genera certificado oficial

### 3. Gestión de Libros
- Registro detallado de cada libro donado
- Campos: título, autor, ISBN, editorial, año, edición
- Control de cantidad y estado del libro
- Cálculo automático de costos (para donaciones de estudiantes)

### 4. Requisitos por Tipo

#### Donaciones de Estudiantes (Individual/Grupal)
- Selección de estudiante(s) de la base de datos
- **Obligatorio**: Adjuntar factura de compra
- **Obligatorio**: Especificar costo de cada libro
- Validación de carrera (misma carrera para donaciones grupales)

#### Donaciones Externas
- Datos del donante: nombre, email, teléfono, organización
- No requiere factura ni costos
- Proceso simplificado

### 5. Sistema de Certificados
- Número único secuencial (CERT-XXXXXX)
- Código de verificación anti-falsificación (formato: XXXX-XXXX-XXXX-XXXX)
- Generado mediante hash SHA-256
- Reporte PDF profesional con toda la información
- Incluye lista completa de libros donados

### 6. Notificaciones por Email
- **Al enviar**: Notifica a aprobadores
- **Al aprobar**: Notifica al donante
- **Al rechazar**: Notifica al donante con motivo
- **Al emitir certificado**: Envía PDF adjunto

### 7. Seguridad y Permisos

#### Grupos de Usuario
- **Bibliotecario (Librarian)**: Puede crear y gestionar solicitudes de su campus
- **Aprobador (Donation Approver)**: Puede aprobar/rechazar todas las solicitudes
- **Administrador (Admin)**: Control total

#### Reglas de Visibilidad
- Bibliotecarios: Solo ven donaciones de sus campus asignados
- Aprobadores: Ven todas las donaciones
- Admin: Control total

### 8. Validaciones Implementadas

#### Datos del Donante
- Estudiante obligatorio para donaciones individual/grupal
- Nombre obligatorio para donaciones externas
- Al menos 2 estudiantes para donaciones grupales (solicitante + grupo)

#### Libros
- Al menos un libro antes de enviar
- Cantidad mínima: 1
- Costo obligatorio para donaciones de estudiantes
- Año de publicación entre 1500 y año actual + 1

#### Documentos
- Factura obligatoria para donaciones de estudiantes antes de aprobar

#### Workflow
- No se puede editar después de enviar
- Solo aprobadores pueden aprobar/rechazar
- No se puede eliminar donaciones aprobadas
- Certificado solo para donaciones aprobadas
- Rechazo requiere motivo obligatorio

## Instalación

### Dependencias
```
- crai_base
- crai_students
- mail
```

### Pasos
1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar lista de aplicaciones
3. Instalar "CRAI - Donaciones de Libros"

## Configuración

### 1. Asignar Grupo de Aprobador
Ir a: **Ajustes → Usuarios y Compañías → Usuarios**
- Seleccionar usuario
- En pestaña "CRAI", activar "CRAI Donation Approver"

### 2. Configurar Notificaciones
Ir a: **Ajustes → CRAI → Donaciones de Libros**
- Habilitar notificaciones por email
- Email adicional del aprobador (opcional)
- Días de validez del certificado

### 3. Asignar Campus a Bibliotecarios
Ir a: **Ajustes → Usuarios**
- Seleccionar bibliotecario
- En pestaña "CRAI", asignar campus

## Uso

### Para Bibliotecarios

#### Crear Donación Individual
1. Ir a: **CRAI Monitoreo → Donaciones → Todas las Solicitudes**
2. Clic en "Crear"
3. Seleccionar tipo: "Donación Individual"
4. Seleccionar estudiante y campus
5. Agregar libros en la pestaña "Libros Donados"
6. Adjuntar factura en "Factura y Documentos"
7. Clic en "Enviar para Aprobación"

#### Crear Donación Grupal
1. Similar a individual
2. Tipo: "Donación Grupal"
3. Seleccionar estudiante líder
4. En "Estudiantes del Grupo", agregar otros participantes
5. Nota: Solo estudiantes de la misma carrera

#### Crear Donación Externa
1. Tipo: "Donación Externa"
2. Ingresar datos del donante externo
3. Agregar libros (no requiere costos ni factura)
4. Enviar para aprobación

### Para Aprobadores

#### Revisar Solicitud
1. Ir a: **Donaciones → Pendientes de Aprobación**
2. Abrir solicitud
3. Revisar información, libros y documentos

#### Aprobar
1. Clic en "Aprobar Donación"
2. Se notifica automáticamente al donante

#### Rechazar
1. Clic en "Rechazar"
2. Ingresar motivo detallado del rechazo
3. Confirmar

#### Generar Certificado
1. Abrir donación aprobada
2. Clic en "Generar Certificado"
3. Se crea certificado con número y código únicos
4. Se envía automáticamente por email
5. Se puede reimprimir con "Imprimir Certificado"

## Reportes y Análisis

### Dashboard
**Donaciones → Dashboard**
- Gráficos por estado, tipo, campus
- Tabla pivote configurable
- Filtros avanzados

### Vistas Disponibles
- **Lista**: Vista tabular completa
- **Formulario**: Detalle de donación
- **Kanban**: Vista por tarjetas
- **Calendario**: Vista temporal por fecha de envío
- **Gráfico**: Análisis visual
- **Pivote**: Análisis multidimensional

## Campos Técnicos Importantes

### Modelo Principal: crai.donation
- `name`: Número de solicitud (DON-XXXXX)
- `donation_type`: Tipo de donación
- `state`: Estado del workflow
- `student_id`: Estudiante (para individual/grupal)
- `group_student_ids`: Estudiantes adicionales (grupal)
- `external_donor_*`: Datos donante externo
- `book_ids`: Libros donados (One2many)
- `certificate_number`: Número de certificado
- `certificate_code`: Código de verificación
- `rejection_reason`: Motivo de rechazo

### Modelo de Libros: crai.donation.book
- `title`: Título del libro
- `author`: Autor
- `isbn`: ISBN
- `publisher`: Editorial
- `publication_year`: Año de publicación
- `quantity`: Cantidad de ejemplares
- `cost`: Costo unitario
- `condition`: Estado del libro

## Secuencias
- Donaciones: `DON-00001`
- Certificados: `CERT-000001`

## Plantillas de Email
1. `email_template_donation_submitted`: Nueva solicitud → Aprobador
2. `email_template_donation_approved`: Aprobación → Donante
3. `email_template_donation_rejected`: Rechazo → Donante
4. `email_template_certificate_issued`: Certificado → Donante (con PDF)

## Seguridad

### Anti-Falsificación de Certificados
- Código de verificación único generado con SHA-256
- Formato: XXXX-XXXX-XXXX-XXXX
- No replicable ni predecible
- Basado en: ID, nombre, timestamp, número aleatorio

### Prevención de Edición
- Estados read-only después de enviar
- Solo Admin puede volver a borrador
- No se pueden eliminar donaciones con certificado

## Personalización

### Cambiar Logo en Certificado
Editar: `report/donation_certificate_template.xml`
- Buscar sección de encabezado
- Agregar imagen con `<img>` tag

### Modificar Texto del Certificado
Editar: `report/donation_certificate_template.xml`
- Sección "Cuerpo del certificado"
- Mantener variables de QWeb

### Agregar Campos Personalizados
1. Extender modelo en Python
2. Agregar en vistas XML
3. Actualizar módulo

## Soporte Técnico

Para problemas o consultas:
1. Revisar logs de Odoo
2. Verificar permisos de usuario
3. Confirmar configuración de email
4. Validar secuencias activas

## Versiones
- **Versión actual**: 17.0.1.0.0
- **Compatible con**: Odoo 17.0
- **Última actualización**: 2025

## Créditos
- **Autor**: UMET CRAI
- **Licencia**: LGPL-3
- **Categoría**: Library/CRAI

## Changelog

### v17.0.1.0.0
- Release inicial
- Gestión completa de donaciones (individual, grupal, externa)
- Sistema de aprobación con roles
- Generación de certificados con código único
- Notificaciones por email
- Reportes y dashboard
- Validaciones completas
- Seguridad por campus
