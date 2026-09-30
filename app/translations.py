# -*- coding: utf-8 -*-
"""Catálogo de textos ES/EN del panel.

Diseño deliberadamente simple (diccionario plano, sin gettext/Flask-Babel):
evita añadir una dependencia nueva a los dos árboles de build (Debian 10 ya
instala dependencias via pip3 sin repos oficiales) y sin un paso de
compilación .po -> .mo. Cada clave es "seccion.nombre"; falta una traducción
en el idioma activo -> se cae a inglés -> si tampoco existe ahí, se muestra
la propia clave (nunca una página rota).
"""

DEFAULT_LANG = 'en'   # el idioma por defecto del build publicado (convención de TurnKey)
SUPPORTED_LANGS = ('en', 'es')

TRANSLATIONS = {
    'es': {
        # --- Navegación / cabecera (compartido por todas las páginas) ---
        'nav.clients':        'Clientes VPN',
        'nav.ranges':          'Rangos de acceso',
        'nav.staticip':        'IP fija',
        'nav.map':              'Mapa',
        'nav.admin':            'Administración',
        'nav.logs':            'Log de conexiones',
        'nav.help':             'Ayuda',
        'nav.logout':           'Cerrar sesión',
        'nav.lang_switch':      'Idioma',

        # --- Login ---
        'login.title':          'OpenVPN Manager',
        'login.username':       'Usuario',
        'login.password':       'Contraseña',
        'login.submit':         'Entrar',
        'login.footer':         'Autenticación vía Linux PAM',
        'login.fail':           'Usuario o contraseña incorrectos',
        'login.locked':         'Demasiados intentos. Espera unos minutos e inténtalo de nuevo.',

        # --- Contraseña: mostrar/ocultar (compartido en varios formularios) ---
        'pw.show':               'Mostrar contraseña',
        'pw.hide':                'Ocultar contraseña',

        # --- Página "Clientes VPN" (index.html) ---
        'idx.maintenance_active':    'Modo mantenimiento activo',
        'idx.maintenance_count':     '{n} cliente(s) bloqueado(s) por mantenimiento',
        'idx.maintenance_off_tip':   'Desbloquea solo los clientes bloqueados por el modo mantenimiento. Los bloqueos manuales (botón Bloquear de cada fila) no se ven afectados',
        'idx.maintenance_off_btn':   'Desactivar mantenimiento',
        'idx.maintenance_on_tip':    'Bloquear a todos los clientes excepto los que elijas. Útil para tareas de mantenimiento',
        'idx.maintenance_on_btn':    'Activar modo mantenimiento',
        'idx.stat_active':           'Activos',
        'idx.stat_expired':          'Caducados',
        'idx.stat_revoked':          'Revocados',
        'idx.new_client_title':      'Nuevo cliente VPN',
        'idx.new_client_tip':        'Crear un nuevo certificado de cliente VPN',
        'idx.add_client_btn':        '+ Añadir cliente',
        'idx.f_name_label':          'Nombre del cliente',
        'idx.f_name_placeholder':    'ej: juan-portatil',
        'idx.email_placeholder':     'usuario@dominio.com',
        'idx.f_email_label':         'Email',
        'idx.f_months_label':        'Validez (meses)',
        'idx.days_suffix':           'días',
        'idx.f_pass_label':          'Contraseña de clave',
        'idx.optional':              '(opcional)',
        'idx.f_pass_placeholder':    'Deja en blanco para clave sin cifrar',
        'idx.f_pass_hint':           'Si se establece, el .ovpn requerirá esta contraseña al importar.',
        'idx.f_ranges_label':        'Rangos de acceso',
        'idx.f_ranges_optional':     '(opcional, CIDR)',
        'idx.f_ranges_hint':         'Redes que el cliente enrutará por la VPN. Una por línea o separadas por comas.',
        'idx.ranges_placeholder':    'ej: 192.168.1.0/24\n10.0.0.0/8',
        'idx.create_btn':            'Crear cliente',
        'idx.cancel_btn':            'Cancelar',
        'idx.clients_table_title':   'Clientes VPN',
        'idx.show_revoked':          'Mostrar revocados ({n})',
        'idx.hide_revoked':          'Ocultar revocados ({n})',
        'idx.th_name':               'Nombre',
        'idx.th_email':              'Email',
        'idx.th_connection':         'Conexión',
        'idx.th_status':             'Estado',
        'idx.th_expiry':             'Caducidad',
        'idx.th_ranges':             'Rangos de acceso',
        'idx.th_actions':            'Acciones',
        'idx.pw_protected_tip':      'Clave protegida con contraseña',
        'idx.connected':             'Conectado',
        'idx.disconnected':          'Desconectado',
        'idx.status_revoked':        'Revocado',
        'idx.status_expired':        'Caducado',
        'idx.status_active':         'Activo',
        'idx.blocked_badge':         'Bloqueado',
        'idx.expiring_soon_tip':     'Este certificado caduca en menos de 30 días. Renuévalo pronto para evitar que el cliente pierda el acceso',
        'idx.no_restriction':        'Sin restricción',
        'idx.static_ip_tip':         'IP fija dentro del túnel VPN — útil para reglas de firewall/servicios que necesiten identificar siempre a este cliente por la misma dirección',
        'idx.download_tip':          'Descargar el fichero .ovpn para configurar el cliente VPN',
        'idx.download_btn':          '.ovpn',
        'idx.renew_tip':             'Renovar el certificado del cliente y ampliar su fecha de caducidad',
        'idx.renew_btn':             'Renovar',
        'idx.disconnect_confirm':    '¿Desconectar a {name} de la VPN ahora?',
        'idx.disconnect_tip':        'Cerrar la sesión VPN activa ahora mismo (puede reconectarse después)',
        'idx.disconnect_btn':        'Desconectar',
        'idx.unblock_tip':           'Permitir que este cliente vuelva a conectarse a la VPN',
        'idx.unblock_btn':           'Desbloquear',
        'idx.block_confirm':         '¿Bloquear a {name}? No podrá conectarse hasta que lo desbloquees.',
        'idx.block_tip':             'Desconectar e impedir que se vuelva a conectar hasta que lo desbloquees',
        'idx.block_btn':             'Bloquear',
        'idx.revoke_confirm':        '¿Revocar el cliente {name}? Esta acción no se puede deshacer.',
        'idx.revoke_tip':            'Revocar el certificado permanentemente. El cliente no podrá conectarse nunca más',
        'idx.revoke_btn':            'Revocar',
        'idx.no_clients':            'No hay clientes VPN creados todavía.',
        'idx.renew_modal_title':     'Renovar certificado',
        'idx.renew_modal_client':    'Cliente:',
        'idx.renew_email_required':  '(cliente sin metadata — requerido para renovar)',
        'idx.renew_months_label':    'Nueva validez (meses)',
        'idx.renew_pass_label':      'Nueva contraseña de clave',
        'idx.renew_pass_placeholder':'Deja en blanco para no cifrar',
        'idx.renew_ranges_optional': '(CIDR — vacío = mantener los actuales)',
        'idx.renew_ranges_hint':     'Si dejas el campo vacío se conservan los rangos existentes.',
        'idx.renew_warning':         '⚠ Se revocará el certificado actual y se emitirá uno nuevo.',
        'idx.confirm_renew_btn':     'Confirmar renovación',
        'idx.maint_modal_title':     'Activar modo mantenimiento',
        'idx.maint_modal_subtitle':  'Selecciona los clientes que NO se bloquearán (por ejemplo, tu propia conexión). El resto serán desconectados y no podrán reconectarse.',
        'idx.maint_connected_badge': 'Conectado',
        'idx.maint_already_blocked': 'Ya bloqueado',
        'idx.maint_warning':         'Marca al menos tu propio cliente para no perder el acceso remoto.',
        'idx.maint_activate_tip':    'Bloquear y desconectar a todos los clientes no marcados',
        'idx.maint_activate_confirm':'¿Activar modo mantenimiento? Los clientes no marcados serán bloqueados.',
        'idx.maint_activate_btn':    'Activar mantenimiento',

        # --- Mensajes flash (app.py) ---
        'flash.invalid_name':            'Nombre inválido: solo letras, números, guiones y guiones bajos.',
        'flash.invalid_email':           'Email inválido.',
        'flash.invalid_months':          'Validez debe ser entre 1 y 1200 meses.',
        'flash.create_failed':           'Error al crear el cliente VPN. Revisa los logs del sistema.',
        'flash.create_ok':               'Cliente "{name}" creado (validez: {months} mes{plural})',
        'flash.create_ok_pass':          ', clave protegida con contraseña',
        'flash.create_ok_ranges':        ', rangos: {ranges}',
        'flash.invalid_client_name':     'Nombre de cliente inválido.',
        'flash.block_ok':                'Cliente "{name}" bloqueado. No podrá reconectarse.',
        'flash.unblock_ok':              'Cliente "{name}" desbloqueado. Ya puede conectarse.',
        'flash.staticip_reason_required':'Indica el motivo por el que este cliente necesita IP fija — es una asignación deliberada, conviene dejar constancia de para qué.',
        'flash.staticip_already_assigned':'"{name}" ya tiene una IP fija asignada.',
        'flash.staticip_auto_failed':    'No se pudo asignar IP fija automáticamente: rango agotado o mal configurado.',
        'flash.staticip_assigned':       'IP fija asignada a "{name}": {ip}. Se aplicará en su próxima conexión.',
        'flash.staticip_not_assigned':   '"{name}" no tiene IP fija asignada.',
        'flash.staticip_released':       'IP fija retirada de "{name}". Volverá al pool dinámico en su próxima conexión.',
        'flash.maintenance_on_ok':       'Modo mantenimiento activado. {n} cliente(s) bloqueado(s).',
        'flash.maintenance_off_ok':      'Modo mantenimiento desactivado. {n} cliente(s) desbloqueado(s).',
        'flash.disconnect_ok':           'Cliente "{name}" desconectado correctamente.',
        'flash.not_connected':           '"{name}" ya no está conectado.',
        'flash.mgmt_unavailable':        'Interfaz de gestión OpenVPN no disponible (puerto 7505). Añade "management 127.0.0.1 7505" a /etc/openvpn/server.conf y reinicia OpenVPN.',
        'flash.disconnect_error':        'Error inesperado al desconectar "{name}". Revisa los logs.',
        'flash.revoke_failed':           'Error al revocar "{name}". Revisa los logs del sistema.',
        'flash.revoke_ok':               'Cliente "{name}" revocado correctamente.',
        'flash.renew_email_required':    'Se necesita un email válido para el cliente "{name}" para renovar.',
        'flash.renew_revoke_failed':     'Error al revocar durante la renovación. Revisa los logs.',
        'flash.renew_reissue_failed':    'Error al reemitir el certificado. Revisa los logs del sistema.',
        'flash.renew_ok':                'Cliente "{name}" renovado correctamente ({months} mes{plural}).',
        'flash.client_not_found':        '"{name}" no existe.',
        'flash.ranges_updated':          'Rango de acceso de "{name}" actualizado: {ranges}. Se aplicará en su próxima conexión (no hace falta reenviar el .ovpn).',
        'flash.ranges_removed':          'Rango de acceso de "{name}" eliminado — vuelve a acceso sin restricción en su próxima conexión.',
        'flash.ovpn_not_found':          'No se encontró el perfil .ovpn para "{name}".',
        'flash.invalid_panel_username':  'Nombre de usuario inválido: minúsculas, números, "-" o "_", empezando por una letra (3-32 caracteres).',
        'flash.invalid_panel_username_simple': 'Nombre de usuario inválido.',
        'flash.panel_user_exists':       'El usuario "{name}" ya existe en el sistema.',
        'flash.password_no_newlines':    'La contraseña no puede contener saltos de línea.',
        'flash.password_too_short':      'La contraseña debe tener al menos 8 caracteres.',
        'flash.passwords_mismatch':      'Las contraseñas no coinciden.',
        'flash.panel_user_create_failed':'Error creando el usuario. Revisa los logs del sistema.',
        'flash.panel_user_created':      'Usuario "{name}" creado. Puede entrar al panel pero no tiene acceso a shell ni a SSH.',
        'flash.reset_password_failed':   'Error restableciendo la contraseña de "{name}": {err}',
        'flash.reset_password_ok':       'Contraseña de "{name}" restablecida correctamente.',
        'flash.delete_user_failed':      'Error eliminando "{name}": {err}',
        'flash.delete_user_ok':          'Usuario "{name}" eliminado.',
        'flash.check_logs':              'revisa los logs del sistema',
        'flash.not_panel_user':          'Ese usuario no pertenece al grupo de usuarios del panel.',
        'flash.staticip_no_range':       'No se pudo calcular el rango de IP fija de este servidor.',
        'flash.staticip_invalid_ip':     '"{ip}" no es una dirección IPv4 válida.',
        'flash.staticip_out_of_range':   '{ip} está fuera del rango de IP fija de este servidor ({net}).',
        'flash.staticip_reserved_block': 'Ese bloque está reservado y no se puede asignar a un cliente.',
        'flash.staticip_invalid_offset': '{ip} no es una dirección de cliente válida dentro de su bloque. ¿Quisiste decir {suggested}?',
        'flash.staticip_ip_taken':       '{ip} ya está asignada a otro cliente.',

        # --- Página "IP fija" (staticip.html) ---
        'sip.card_title':            'Rango de IP fija de este servidor',
        'sip.range_prefix':          'Rango reservado:',
        'sip.range_suffix':          '(contiguo al pool dinámico de OpenVPN, no interfiere con las IPs que se reparten normalmente). Cada cliente con IP fija ocupa un bloque propio dentro de este rango.',
        'sip.range_error':           'No se pudo calcular el rango de IP fija en este servidor — revisa que <code>/etc/openvpn/server.conf</code> tenga una línea <code>server</code> válida.',
        'sip.clients_title':         'Clientes con IP fija ({assigned} de {total})',
        'sip.th_name':                'Nombre',
        'sip.th_staticip':            'IP fija',
        'sip.th_reason':              'Motivo',
        'sip.th_actions':             'Acciones',
        'sip.unassigned_badge':      'Sin asignar',
        'sip.no_reason':             '(sin motivo registrado)',
        'sip.release_confirm':       '¿Quitar la IP fija de {name} ({ip})? Volverá al pool dinámico en su próxima conexión.',
        'sip.release_btn':           'Quitar',
        'sip.assign_btn':            'Asignar IP fija',
        'sip.no_clients':            'No hay clientes activos todavía.',
        'sip.modal_title':           'Asignar IP fija',
        'sip.modal_client':          'Cliente:',
        'sip.mode_auto':             'Automática (siguiente libre)',
        'sip.mode_manual':           'Elegir IP manualmente',
        'sip.desired_ip_label':      'IP deseada',
        'sip.desired_ip_optional':   '(dirección de cliente dentro del rango de IP fija)',
        'sip.desired_ip_hint':       'Debe caer dentro de {net} y no estar ya asignada a otro cliente. Si no es válida, el panel te sugiere la dirección correcta más cercana.',
        'sip.range_fallback':        'el rango de IP fija',
        'sip.reason_label':          'Motivo',
        'sip.reason_placeholder':    'ej: regla de firewall en el servidor de facturación que identifica a este cliente por IP fija',
        'sip.reason_hint':           'Obligatorio — la IP fija es para casos concretos; deja constancia de por qué la necesita este cliente.',
        'sip.confirm_assign_btn':    'Confirmar asignación',

        # --- Página "Rangos de acceso" (access_ranges.html) ---
        'ar.intro':                  'Los rangos de acceso definen a qué redes puede llegar cada cliente una vez conectado. Se aplican mediante un cortafuegos real en el servidor (no dependen del .ovpn del cliente), así que puedes cambiarlos aquí sin renovar su certificado ni reenviarle un fichero nuevo — el nuevo rango se aplica en su próxima conexión.',
        'ar.clients_title':          'Clientes con rango restringido ({restricted} de {total})',
        'ar.th_name':                'Nombre',
        'ar.th_ranges':              'Rangos de acceso',
        'ar.th_actions':             'Acciones',
        'ar.static_ip_title':        'IP fija dentro del túnel VPN',
        'ar.no_restriction':         'Sin restricción',
        'ar.edit_btn':               'Editar rango',
        'ar.no_clients':             'No hay clientes activos todavía.',
        'ar.modal_title':            'Editar rango de acceso',
        'ar.modal_client':           'Cliente:',
        'ar.ranges_optional':        '(CIDR — vacío = sin restricción)',
        'ar.ranges_hint':            'Se aplica en la próxima conexión del cliente — no toca su certificado ni su .ovpn, no hace falta reenviarle nada.',
        'ar.save_btn':               'Guardar rango',

        # --- Página "Log de conexiones" (logs.html) ---
        'log.title':                 'Log de conexiones',
        'log.tab_vpn_tip':           'Eventos del servidor OpenVPN: conexiones, desconexiones, errores TLS…',
        'log.tab_vpn':               'OpenVPN',
        'log.tab_audit_tip':         'Acciones realizadas desde este panel: logins, clientes creados, revocados, bloqueados…',
        'log.tab_audit':             'Auditoría Manager',
        'log.quick_filter_label':    'Filtro rápido:',
        'log.filter_all_tip':        'Mostrar todas las líneas del log sin filtrar',
        'log.filter_all':            'Todos',
        'log.filter_events_vpn_tip': 'Mostrar solo eventos de clientes que se conectan o desconectan del servidor VPN',
        'log.filter_events_audit_tip':'Mostrar solo acciones de administración: logins, crear, revocar, bloquear, etc.',
        'log.filter_events_vpn':     'Conexiones / Desconexiones',
        'log.filter_events_audit':   'Eventos relevantes',
        'log.search_label':          'Buscar:',
        'log.search_placeholder':    'cliente, IP, evento…',
        'log.search_tip':            'Escribe el nombre de un cliente, una IP o cualquier texto para buscar en el log. La coincidencia se resalta en amarillo',
        'log.last_label':            'Últimas:',
        'log.last_tip':              'Número máximo de líneas a mostrar. Con filtro activo se analizan hasta 5× más líneas para tener suficientes resultados',
        'log.lines_option':          '{n} líneas',
        'log.filter_btn_tip':        'Aplicar la búsqueda de texto al log actual',
        'log.filter_btn':            'Filtrar',
        'log.clear_search_tip':      'Borrar el texto de búsqueda y mostrar todas las líneas (conserva el filtro rápido activo)',
        'log.clear_search_btn':      'Limpiar búsqueda',
        'log.refresh_tip':           'Recargar el log para ver las entradas más recientes. Se actualiza automáticamente cada 30 s si no hay búsqueda activa',
        'log.refresh_btn':           'Actualizar',
        'log.empty_vpn':             'No hay entradas en el log de OpenVPN',
        'log.empty_audit':           'No hay entradas en el log de auditoría',
        'log.empty_search_suffix':   ' que coincidan con "{search}"',
        'log.lines_shown':           '{n} línea(s) mostradas',

        # --- Página "Administración" (admin_users.html) ---
        'adm.create_title':          'Crear usuario del panel',
        'adm.create_intro':          'Crea una cuenta que puede iniciar sesión en este panel para gestionar los clientes VPN, pero que <strong>no tiene acceso a la shell del sistema ni por SSH</strong> (se crea sin shell y en un grupo bloqueado explícitamente en la configuración de SSH).',
        'adm.username_label':        'Nombre de usuario',
        'adm.password_label':        'Contraseña',
        'adm.password2_label':       'Repetir contraseña',
        'adm.create_btn':            'Crear usuario',
        'adm.users_title':           'Usuarios del panel ({n})',
        'adm.th_user':               'Usuario',
        'adm.th_access':             'Acceso',
        'adm.th_actions':            'Acciones',
        'adm.panel_only_badge':      'Solo panel — sin shell/SSH',
        'adm.reset_tip':             'No se puede "ver" la contraseña actual (se guarda como hash, no reversible) — se le asigna una nueva',
        'adm.reset_btn':             'Restablecer contraseña',
        'adm.delete_confirm':        '¿Eliminar el usuario {name}? Esta acción no se puede deshacer.',
        'adm.delete_btn':            'Eliminar',
        'adm.no_users':              'Todavía no hay usuarios del panel creados.',
        'adm.reset_modal_title':     'Restablecer contraseña',
        'adm.reset_modal_user':      'Usuario:',
        'adm.reset_modal_suffix':    '— no se puede ver la contraseña actual, solo asignarle una nueva.',
        'adm.new_password_label':    'Nueva contraseña',
        'adm.new_password2_label':   'Repetir nueva contraseña',
        'adm.reset_confirm_btn':     'Restablecer',

        # --- Página "Ayuda" (help.html) ---
        'help.page_title':    'Guía de uso — OpenVPN Manager',
        'help.page_subtitle': 'Pulsa cualquier sección para expandirla. Haz clic de nuevo para cerrarla.',

        'help.create.title':    'Añadir cliente VPN',
        'help.create.subtitle': 'Crear un nuevo certificado y perfil de conexión',
        'help.create.body': """<p>Genera un certificado único para un usuario o dispositivo. El resultado es un fichero <strong>.ovpn</strong> que el cliente importa en su aplicación de OpenVPN.</p>
        <ul>
          <li><strong>Nombre:</strong> identificador único del cliente. Solo letras, números, guiones y guiones bajos. No puede repetirse. Ejemplo: <code>juan-portatil</code>, <code>oficina-madrid</code>.</li>
          <li><strong>Email:</strong> se almacena como referencia interna. No se envía a ningún sitio automáticamente.</li>
          <li><strong>Validez (meses):</strong> tiempo de vida del certificado. Al caducar, el cliente no podrá conectarse hasta que se renueve. Por defecto 24 meses.</li>
          <li><strong>Contraseña de clave</strong> (opcional): cifra la clave privada dentro del .ovpn. El cliente deberá introducirla cada vez que importe o use el perfil.</li>
          <li><strong>Rangos de acceso</strong> (opcional, CIDR): redes internas a las que se restringe el acceso de este cliente. Ejemplo: <code>192.168.1.0/24</code>. Si se deja vacío, el cliente puede acceder a todo lo que permita el servidor. Se aplica con un <strong>cortafuegos real en el servidor</strong>, no solo con rutas del lado del cliente — ver la sección "Rangos de acceso y cortafuegos" más abajo para el detalle.</li>
        </ul>
        <div class="info-box">&#128161; El fichero .ovpn contiene todo lo necesario: certificados, clave privada y configuración del servidor. Es suficiente con compartir ese único fichero con el usuario.</div>""",

        'help.download.title':    'Descargar .ovpn',
        'help.download.subtitle': 'Obtener el perfil de conexión para el cliente',
        'help.download.body': """<p>Descarga el fichero de configuración que el usuario debe importar en su aplicación VPN (OpenVPN Connect, Tunnelblick, NetworkManager, etc.).</p>
        <ol class="step-list">
          <li>Pulsa el botón <strong>&#11123; .ovpn</strong> en la fila del cliente.</li>
          <li>Envía el fichero descargado al usuario de forma segura (correo cifrado, SFTP, etc.).</li>
          <li>El usuario lo importa en su aplicación y se conecta con su usuario/contraseña de clave si la tiene.</li>
        </ol>
        <div class="warn-box">&#9888; El .ovpn contiene la clave privada del cliente. Trátalo como una contraseña: no lo compartas por canales inseguros como WhatsApp o correo sin cifrar.</div>""",

        'help.renew.title':    'Renovar certificado',
        'help.renew.subtitle': 'Extender la fecha de caducidad de un cliente',
        'help.renew.body': """<p>Cuando un certificado está a punto de caducar o ya ha caducado <span class="badge-demo bd-expired">Caducado</span>, hay que renovarlo para que el cliente pueda seguir conectándose.</p>
        <p>La renovación hace dos cosas automáticamente:</p>
        <ul>
          <li>Revoca el certificado antiguo (ya no es válido).</li>
          <li>Emite un certificado nuevo con la validez que elijas.</li>
        </ul>
        <p>El usuario deberá <strong>descargar e importar el nuevo .ovpn</strong> — el anterior dejará de funcionar.</p>
        <div class="warn-box">&#9888; Recuerda enviar el nuevo .ovpn al usuario tras renovar. Si el cliente intenta conectarse con el perfil viejo recibirá un error de certificado.</div>""",

        'help.disconnect.title':    'Desconectar',
        'help.disconnect.subtitle': 'Cerrar la sesión VPN activa puntualmente',
        'help.disconnect.body': """<p>Cierra la sesión VPN de un cliente que esté <span class="conn-dot dot-on"></span><strong>Conectado</strong> en este momento. El cliente recibe una señal de cierre limpio y su aplicación le mostrará "desconectado".</p>
        <p><strong>Efecto temporal:</strong> el cliente podrá volver a conectarse inmediatamente después con el mismo .ovpn. Si quieres impedir la reconexión, usa <strong>Bloquear</strong>.</p>
        <div class="info-box">&#128161; Solo aparece el botón de desconectar cuando el cliente está activamente conectado en ese momento.</div>""",

        'help.block.title':    'Bloquear / Desbloquear',
        'help.block.subtitle': 'Impedir temporalmente que un cliente se conecte',
        'help.block.body': """<p>Bloquear a un cliente hace dos cosas al mismo tiempo:</p>
        <ul>
          <li>Si está conectado, lo desconecta inmediatamente.</li>
          <li>Escribe la directiva <code>disable</code> en su fichero de configuración individual (CCD), impidiendo cualquier reconexión futura mientras esté bloqueado.</li>
        </ul>
        <p>El cliente aparecerá con la etiqueta <span class="badge-demo bd-blocked">&#128274; Bloqueado</span> en la tabla.</p>
        <p><strong>Desbloquear</strong> elimina esa restricción y el cliente puede volver a conectarse con el mismo .ovpn sin necesidad de emitir uno nuevo.</p>
        <div class="info-box">&#128161; Útil cuando un empleado está de baja temporal, hay sospechas de mal uso, o simplemente quieres pausar el acceso sin revocar el certificado definitivamente.</div>""",

        'help.revoke.title':    'Revocar certificado',
        'help.revoke.subtitle': 'Invalidar permanentemente el acceso de un cliente',
        'help.revoke.body': """<p>Añade el certificado del cliente a la <strong>Lista de Revocación de Certificados (CRL)</strong> del servidor. A partir de ese momento el servidor rechaza cualquier intento de conexión con ese certificado, aunque el .ovpn siga en el dispositivo del usuario.</p>
        <p>El cliente aparecerá como <span class="badge-demo bd-revoked">Revocado</span> en la tabla y no podrá realizar ninguna acción sobre él excepto verlo.</p>
        <div class="danger-box">&#10006; <strong>Esta acción es irreversible.</strong> Si el usuario necesita volver a conectarse en el futuro, habrá que crearle un cliente nuevo con un nombre diferente o usar la función Renovar antes de revocar.</div>
        <div class="warn-box">&#9888; Usa esta opción cuando un usuario causa baja definitiva o un dispositivo con .ovpn se pierde o es robado.</div>""",

        'help.maintenance.title':    'Modo mantenimiento',
        'help.maintenance.subtitle': 'Bloquear a todos los clientes de una sola vez',
        'help.maintenance.body': """<p>Bloquea a todos los clientes VPN activos de golpe, excepto los que tú marques como protegidos en el diálogo. Los bloqueados son desconectados y no pueden reconectarse hasta que se desactive el mantenimiento.</p>
        <p>Cuando hay clientes bloqueados, aparece la barra amarilla de mantenimiento en la parte superior de la pantalla. Desde ahí puedes desactivarlo con un solo clic, desbloqueando a todos a la vez.</p>
        <div class="warn-box">&#9888; <strong>Marca siempre tu propio cliente VPN como protegido</strong> antes de activar el mantenimiento. Si no lo haces, perderás el acceso remoto y tendrás que acceder físicamente o por otra vía al servidor para desactivarlo.</div>
        <div class="info-box">&#128161; Ideal para actualizaciones del servidor, cambios de configuración de red o cualquier tarea que requiera que nadie esté conectado a la VPN.</div>""",

        'help.firewall.title':    'Rangos de acceso y cortafuegos',
        'help.firewall.subtitle': 'Cómo se restringe de verdad a qué redes llega cada cliente',
        'help.firewall.body': """<p>"Rangos de acceso" limita a qué redes internas puede llegar un cliente concreto una vez conectado a la VPN — por ejemplo, un proveedor externo que solo debe alcanzar el servidor de un departamento, no toda la oficina.</p>
        <p><strong>Se aplica con un cortafuegos real en el propio servidor</strong>, no con una simple sugerencia de rutas al cliente. Un usuario que intente saltárselo añadiendo rutas manuales en su propio ordenador no consigue nada: el servidor rechaza igualmente cualquier paquete hacia un destino que no esté en su rango autorizado.</p>
        <p>Un proceso aparte (fuera del propio OpenVPN) vigila constantemente quién está conectado y con qué rango, y mantiene las reglas del cortafuegos sincronizadas — por eso, tras conectarse, puede haber un margen de un par de segundos antes de que la restricción quede aplicada del todo.</p>
        <ul>
          <li>Se puede fijar al crear el cliente o al renovarlo, en el campo <strong>Rangos de acceso</strong> (formato CIDR, uno o varios separados por comas o saltos de línea).</li>
          <li>También se puede cambiar en cualquier momento desde la pestaña <strong>Rangos de acceso</strong>, sin renovar el certificado ni reenviar un .ovpn nuevo al cliente — el rango es una cuestión de a qué puede llegar, independiente de su certificado, que solo dice quién es.</li>
          <li>Vacío = sin restricción, el cliente accede a todo lo que el servidor permita (comportamiento de siempre).</li>
          <li>Renovar un cliente no borra su rango configurado — se conserva salvo que lo cambies explícitamente.</li>
          <li>El fichero <strong>.ovpn</strong> del cliente nunca se modifica con estas reglas — permanece igual desde que se generó. Todo el control ocurre en el servidor, así que nunca hace falta reenviarle un .ovpn nuevo por cambiar su rango.</li>
        </ul>
        <div class="info-box">&#128161; Si un cliente restringido no consigue llegar a algo que debería, revisa primero que el rango CIDR incluya de verdad esa dirección — un error de tecleo aquí (por ejemplo <code>/24</code> en vez de <code>/32</code>) es la causa más común.</div>""",

        'help.staticip.title':    'IP fija',
        'help.staticip.subtitle': 'Asignar a un cliente siempre la misma dirección dentro del túnel VPN',
        'help.staticip.body': """<p>Por defecto, la dirección IP que recibe un cliente dentro del túnel VPN puede cambiar entre una conexión y otra (se asigna de un grupo compartido). La <strong>IP fija</strong> le reserva siempre la misma dirección a un cliente concreto.</p>
        <p>Es útil para casos muy concretos donde algo <strong>fuera</strong> de este panel necesita identificar siempre al mismo cliente por su dirección — por ejemplo, una regla de cortafuegos en otro servidor, o una integración externa que da acceso solo a una IP determinada. No es necesaria para el uso normal de la VPN.</p>
        <p>Se gestiona desde la pestaña <strong>IP fija</strong>, no desde el listado de clientes:</p>
        <ul>
          <li><strong>Automática:</strong> el panel elige la siguiente dirección libre dentro del rango reservado para IP fija.</li>
          <li><strong>Manual:</strong> escribes tú la dirección exacta que quieres — el panel valida que sea correcta y esté libre, y si no lo es, sugiere la más cercana válida.</li>
          <li><strong>Motivo</strong> (obligatorio): hay que anotar para qué se asigna. Al ser una asignación deliberada y no algo rutinario, queda constancia de por qué la tiene cada cliente — visible en la propia pestaña.</li>
        </ul>
        <p>La IP fija se conserva al renovar el cliente o cambiarle el rango de acceso, y se retira con el botón <strong>Quitar</strong> cuando ya no haga falta, liberando esa dirección para otro cliente.</p>
        <div class="info-box">&#128161; La IP fija y los "Rangos de acceso" son independientes y compatibles entre sí — un cliente puede tener ambos, solo uno, o ninguno.</div>""",

        'help.map.title':    'Mapa',
        'help.map.subtitle': 'De dónde se conectó cada cliente por última vez',
        'help.map.body': """<p>Muestra la ubicación aproximada (a nivel de ciudad) desde la que cada cliente estableció su última conexión — un punto por cliente, que se sobrescribe en cada conexión nueva. No se guarda un historial de ubicaciones pasadas.</p>
        <p><strong>Cómo se calcula:</strong> la IP real del cliente (la misma que ya ve el propio servidor OpenVPN al aceptar la conexión) se busca en una base de datos de geolocalización descargada y almacenada en este mismo servidor. Esa IP <strong>nunca se envía a ningún servicio externo</strong> — toda la resolución ocurre en local.</p>
        <p>Lo único que sale de este servidor hacia fuera es la descarga periódica (mensual) de la propia base de datos, y las teselas del mapa que pide el navegador del administrador a OpenStreetMap al ver esta página — ninguna de las dos cosas incluye datos de ningún cliente.</p>
        <p>Un cliente aparece en <strong>"Sin ubicación disponible"</strong> si todavía no se ha conectado nunca, si se conectó desde una IP privada/local (habitual en pruebas dentro de la misma red), o si esa IP no tiene registro en la base de datos.</p>
        <div class="info-box">&#128161; La precisión es a nivel de ciudad, no de dirección exacta — suficiente para detectar patrones o accesos inesperados, no para una localización precisa.</div>""",

        'help.status.title':    'Estados de los clientes',
        'help.status.subtitle': 'Qué significa cada etiqueta y punto de color',
        'help.status.body': """<p><strong>Columna Conexión:</strong></p>
        <ul>
          <li><span class="conn-dot dot-on"></span><strong>Conectado</strong> — el cliente tiene una sesión VPN activa ahora mismo. Dato en tiempo real consultado al servidor OpenVPN.</li>
          <li><span class="conn-dot dot-off"></span><strong>Desconectado</strong> — no hay sesión activa en este momento.</li>
        </ul>
        <p style="margin-top:10px"><strong>Columna Estado:</strong></p>
        <ul>
          <li><span class="badge-demo bd-active">Activo</span> — certificado válido y dentro de la fecha de caducidad.</li>
          <li><span class="badge-demo bd-expired">Caducado</span> — el certificado ha expirado. El cliente no puede conectarse hasta que se renueve.</li>
          <li><span class="badge-demo bd-revoked">Revocado</span> — acceso denegado permanentemente.</li>
          <li><span class="badge-demo bd-blocked">&#128274; Bloqueado</span> — acceso suspendido temporalmente. Se puede desbloquear.</li>
        </ul>
        <div class="info-box">&#128161; El estado de conexión se actualiza automáticamente cada pocos segundos en "Clientes VPN", sin recargar la página.</div>""",

        'help.logs.title':    'Log de conexiones',
        'help.logs.subtitle': 'Qué muestran las dos pestañas del visor de logs',
        'help.logs.body': """<p><strong>&#127760; OpenVPN</strong> — eventos del servidor VPN: quién se conecta, desde qué IP, cuándo se desconecta, errores de certificado, etc. Fuente: <code>journalctl -u openvpn@server</code>.</p>
        <p><strong>&#128274; Auditoría Manager</strong> — acciones realizadas a través de este panel web: inicios de sesión, clientes creados, revocados, bloqueados, etc. Fuente: <code>/var/log/openvpn-gui.log</code>.</p>
        <p>Usa el filtro <strong>Conexiones / Desconexiones</strong> para ver solo los eventos de entrada y salida de clientes, ignorando el ruido del sistema.</p>
        <p>La página se refresca automáticamente cada 30 segundos cuando no hay búsqueda activa.</p>
        <div class="info-box">&#128161; Si buscas el historial de un cliente concreto, escribe su nombre en el campo de búsqueda. La coincidencia se resalta en amarillo en los resultados.</div>""",

        'help.concepts.title':    'Conceptos clave',
        'help.concepts.subtitle': 'PKI, certificados, CRL y rangos CIDR explicados',
        'help.concepts.body': """<p><strong>Certificado de cliente:</strong> un documento digital único que identifica a cada usuario ante el servidor VPN. Es el equivalente a una llave. Sin él, es imposible conectarse.</p>
        <p><strong>PKI (Infraestructura de Clave Pública):</strong> el sistema de ficheros en el servidor que gestiona todos los certificados. Reside en <code>/etc/openvpn/easy-rsa/</code>.</p>
        <p><strong>CRL (Lista de Revocación de Certificados):</strong> lista negra de certificados invalidados. El servidor la consulta en cada intento de conexión. Cuando revocas un cliente, su certificado se añade aquí.</p>
        <p><strong>CCD (Client Config Directory):</strong> carpeta con un fichero de configuración individual por cliente (<code>/etc/openvpn/server.ccd/</code>). El bloqueo funciona escribiendo <code>disable</code> en ese fichero.</p>
        <p><strong>Rangos CIDR:</strong> forma compacta de escribir rangos de IPs. Ejemplos:</p>
        <ul>
          <li><code>192.168.1.0/24</code> → IPs de la 192.168.1.0 a la 192.168.1.255 (256 hosts)</li>
          <li><code>10.0.0.0/8</code> → toda la red 10.x.x.x (16 millones de hosts)</li>
          <li><code>172.16.5.10/32</code> → un único host</li>
        </ul>
        <p><strong>Fichero .ovpn:</strong> perfil de configuración todo-en-uno. Incluye la dirección del servidor, el certificado del cliente, su clave privada y la clave de autenticación TLS. Es suficiente con este fichero para conectarse.</p>
        <div class="warn-box">&#9888; El fichero .ovpn es equivalente a una contraseña. Quien lo tenga puede conectarse a la VPN. Guárdalo y compártelo de forma segura.</div>""",

        # --- Página "Mapa" (map.html) ---
        'map.title':                 'Última conexión de cada cliente',
        'map.intro':                 'Muestra la ubicación aproximada (a nivel de ciudad) desde la que se conectó cada cliente por última vez, calculada localmente en este servidor a partir de su IP real — esa IP nunca se envía a ningún servicio externo.',
        'map.db_pending':            'La base de datos de geolocalización aún no se ha descargado. Los nuevos clientes que se conecten no tendrán ubicación hasta que se complete la primera descarga automática.',
        'map.no_location_title':     'Sin ubicación disponible ({n})',
        'map.th_name':                'Nombre',
        'map.th_ip':                  'Última IP',
        'map.th_reason':              'Motivo',
        'map.never_connected':       'Aún no se ha conectado nunca',
        'map.private_or_unresolved': 'IP privada/local, o sin datos en la base de geolocalización',
        'map.history_title':         'Historial de conexión por cliente',
        'map.history_intro':         'Hasta las 5 últimas IPs distintas desde las que se ha conectado cada cliente — más reciente primero. Si siempre se conecta desde el mismo sitio, solo aparece una.',
        'map.th_history':            'Historial de IPs',
        'map.history_no_data':       'Sin datos de ubicación',
        'map.popup_last_connection': 'Última conexión',
        'map.empty_no_data':         'Todavía no hay ninguna ubicación registrada.',
    },
    'en': {
        # --- Nav / header (shared by every page) ---
        'nav.clients':        'VPN Clients',
        'nav.ranges':          'Access Ranges',
        'nav.staticip':        'Static IP',
        'nav.map':              'Map',
        'nav.admin':            'Administration',
        'nav.logs':            'Connection Log',
        'nav.help':             'Help',
        'nav.logout':           'Log out',
        'nav.lang_switch':      'Language',

        # --- Login ---
        'login.title':          'OpenVPN Manager',
        'login.username':       'Username',
        'login.password':       'Password',
        'login.submit':         'Sign in',
        'login.footer':         'Authenticated via Linux PAM',
        'login.fail':           'Incorrect username or password',
        'login.locked':         'Too many attempts. Wait a few minutes and try again.',

        # --- Password show/hide (shared by several forms) ---
        'pw.show':               'Show password',
        'pw.hide':                'Hide password',

        # --- "VPN Clients" page (index.html) ---
        'idx.maintenance_active':    'Maintenance mode active',
        'idx.maintenance_count':     '{n} client(s) blocked by maintenance mode',
        'idx.maintenance_off_tip':   'Only unblocks clients blocked by maintenance mode. Manual blocks (the Block button on each row) are not affected',
        'idx.maintenance_off_btn':   'Turn off maintenance mode',
        'idx.maintenance_on_tip':    'Block every client except the ones you choose. Useful for maintenance work',
        'idx.maintenance_on_btn':    'Turn on maintenance mode',
        'idx.stat_active':           'Active',
        'idx.stat_expired':          'Expired',
        'idx.stat_revoked':          'Revoked',
        'idx.new_client_title':      'New VPN client',
        'idx.new_client_tip':        'Create a new VPN client certificate',
        'idx.add_client_btn':        '+ Add client',
        'idx.f_name_label':          'Client name',
        'idx.f_name_placeholder':    'e.g.: john-laptop',
        'idx.email_placeholder':     'user@domain.com',
        'idx.f_email_label':         'Email',
        'idx.f_months_label':        'Validity (months)',
        'idx.days_suffix':           'days',
        'idx.f_pass_label':          'Key password',
        'idx.optional':              '(optional)',
        'idx.f_pass_placeholder':    'Leave blank for an unencrypted key',
        'idx.f_pass_hint':           'If set, importing the .ovpn will require this password.',
        'idx.f_ranges_label':        'Access ranges',
        'idx.f_ranges_optional':     '(optional, CIDR)',
        'idx.f_ranges_hint':         'Networks the client will route through the VPN. One per line or comma-separated.',
        'idx.ranges_placeholder':    'e.g.: 192.168.1.0/24\n10.0.0.0/8',
        'idx.create_btn':            'Create client',
        'idx.cancel_btn':            'Cancel',
        'idx.clients_table_title':   'VPN Clients',
        'idx.show_revoked':          'Show revoked ({n})',
        'idx.hide_revoked':          'Hide revoked ({n})',
        'idx.th_name':               'Name',
        'idx.th_email':              'Email',
        'idx.th_connection':         'Connection',
        'idx.th_status':             'Status',
        'idx.th_expiry':             'Expiry',
        'idx.th_ranges':             'Access ranges',
        'idx.th_actions':            'Actions',
        'idx.pw_protected_tip':      'Key protected with a password',
        'idx.connected':             'Connected',
        'idx.disconnected':          'Disconnected',
        'idx.status_revoked':        'Revoked',
        'idx.status_expired':        'Expired',
        'idx.status_active':         'Active',
        'idx.blocked_badge':         'Blocked',
        'idx.expiring_soon_tip':     'This certificate expires in less than 30 days. Renew it soon so the client doesn’t lose access',
        'idx.no_restriction':        'No restriction',
        'idx.static_ip_tip':         'Static IP inside the VPN tunnel — useful for firewall rules/services that need to always identify this client by the same address',
        'idx.download_tip':          'Download the .ovpn file to set up the VPN client',
        'idx.download_btn':          '.ovpn',
        'idx.renew_tip':             'Renew the client’s certificate and extend its expiry date',
        'idx.renew_btn':             'Renew',
        'idx.disconnect_confirm':    'Disconnect {name} from the VPN now?',
        'idx.disconnect_tip':        'Close the active VPN session right now (it can reconnect afterwards)',
        'idx.disconnect_btn':        'Disconnect',
        'idx.unblock_tip':           'Allow this client to connect to the VPN again',
        'idx.unblock_btn':           'Unblock',
        'idx.block_confirm':         'Block {name}? It won’t be able to connect until you unblock it.',
        'idx.block_tip':             'Disconnect it and prevent it from reconnecting until you unblock it',
        'idx.block_btn':             'Block',
        'idx.revoke_confirm':        'Revoke client {name}? This action cannot be undone.',
        'idx.revoke_tip':            'Permanently revoke the certificate. The client will never be able to connect again',
        'idx.revoke_btn':            'Revoke',
        'idx.no_clients':            'No VPN clients created yet.',
        'idx.renew_modal_title':     'Renew certificate',
        'idx.renew_modal_client':    'Client:',
        'idx.renew_email_required':  '(client with no metadata — required to renew)',
        'idx.renew_months_label':    'New validity (months)',
        'idx.renew_pass_label':      'New key password',
        'idx.renew_pass_placeholder':'Leave blank to not encrypt',
        'idx.renew_ranges_optional': '(CIDR — empty = keep the current ones)',
        'idx.renew_ranges_hint':     'Leaving this field empty keeps the existing ranges.',
        'idx.renew_warning':         '⚠ The current certificate will be revoked and a new one issued.',
        'idx.confirm_renew_btn':     'Confirm renewal',
        'idx.maint_modal_title':     'Turn on maintenance mode',
        'idx.maint_modal_subtitle':  'Select the clients that will NOT be blocked (e.g. your own connection). The rest will be disconnected and unable to reconnect.',
        'idx.maint_connected_badge': 'Connected',
        'idx.maint_already_blocked': 'Already blocked',
        'idx.maint_warning':         '⚠ Check at least your own client so you don’t lose remote access.',
        'idx.maint_activate_tip':    'Block and disconnect every unchecked client',
        'idx.maint_activate_confirm':'Turn on maintenance mode? Unchecked clients will be blocked.',
        'idx.maint_activate_btn':    'Turn on maintenance',

        # --- Flash messages (app.py) ---
        'flash.invalid_name':            'Invalid name: letters, numbers, hyphens and underscores only.',
        'flash.invalid_email':           'Invalid email.',
        'flash.invalid_months':          'Validity must be between 1 and 1200 months.',
        'flash.create_failed':           'Error creating the VPN client. Check the system logs.',
        'flash.create_ok':               'Client "{name}" created (validity: {months} month{plural})',
        'flash.create_ok_pass':          ', key password-protected',
        'flash.create_ok_ranges':        ', ranges: {ranges}',
        'flash.invalid_client_name':     'Invalid client name.',
        'flash.block_ok':                'Client "{name}" blocked. It won’t be able to reconnect.',
        'flash.unblock_ok':              'Client "{name}" unblocked. It can connect again.',
        'flash.staticip_reason_required':'State why this client needs a static IP — it’s a deliberate assignment, worth recording why.',
        'flash.staticip_already_assigned':'"{name}" already has a static IP assigned.',
        'flash.staticip_auto_failed':    'Could not assign a static IP automatically: range exhausted or misconfigured.',
        'flash.staticip_assigned':       'Static IP assigned to "{name}": {ip}. It will apply on its next connection.',
        'flash.staticip_not_assigned':   '"{name}" has no static IP assigned.',
        'flash.staticip_released':       'Static IP released from "{name}". It will return to the dynamic pool on its next connection.',
        'flash.maintenance_on_ok':       'Maintenance mode turned on. {n} client(s) blocked.',
        'flash.maintenance_off_ok':      'Maintenance mode turned off. {n} client(s) unblocked.',
        'flash.disconnect_ok':           'Client "{name}" disconnected successfully.',
        'flash.not_connected':           '"{name}" is no longer connected.',
        'flash.mgmt_unavailable':        'OpenVPN management interface unavailable (port 7505). Add "management 127.0.0.1 7505" to /etc/openvpn/server.conf and restart OpenVPN.',
        'flash.disconnect_error':        'Unexpected error disconnecting "{name}". Check the logs.',
        'flash.revoke_failed':           'Error revoking "{name}". Check the system logs.',
        'flash.revoke_ok':               'Client "{name}" revoked successfully.',
        'flash.renew_email_required':    'A valid email is needed for client "{name}" to renew.',
        'flash.renew_revoke_failed':     'Error revoking during renewal. Check the logs.',
        'flash.renew_reissue_failed':    'Error reissuing the certificate. Check the system logs.',
        'flash.renew_ok':                'Client "{name}" renewed successfully ({months} month{plural}).',
        'flash.client_not_found':        '"{name}" does not exist.',
        'flash.ranges_updated':          'Access range for "{name}" updated: {ranges}. It will apply on its next connection (no need to resend the .ovpn).',
        'flash.ranges_removed':          'Access range removed from "{name}" — back to unrestricted access on its next connection.',
        'flash.ovpn_not_found':          'Could not find the .ovpn profile for "{name}".',
        'flash.invalid_panel_username':  'Invalid username: lowercase letters, numbers, "-" or "_", starting with a letter (3-32 characters).',
        'flash.invalid_panel_username_simple': 'Invalid username.',
        'flash.panel_user_exists':       'User "{name}" already exists on the system.',
        'flash.password_no_newlines':    'The password cannot contain line breaks.',
        'flash.password_too_short':      'The password must be at least 8 characters long.',
        'flash.passwords_mismatch':      'The passwords do not match.',
        'flash.panel_user_create_failed':'Error creating the user. Check the system logs.',
        'flash.panel_user_created':      'User "{name}" created. They can log into the panel but have no shell or SSH access.',
        'flash.reset_password_failed':   'Error resetting the password for "{name}": {err}',
        'flash.reset_password_ok':       'Password for "{name}" reset successfully.',
        'flash.delete_user_failed':      'Error deleting "{name}": {err}',
        'flash.delete_user_ok':          'User "{name}" deleted.',
        'flash.check_logs':              'check the system logs',
        'flash.not_panel_user':          'That user does not belong to the panel users group.',
        'flash.staticip_no_range':       'Could not compute this server’s static IP range.',
        'flash.staticip_invalid_ip':     '"{ip}" is not a valid IPv4 address.',
        'flash.staticip_out_of_range':   '{ip} is outside this server’s static IP range ({net}).',
        'flash.staticip_reserved_block': 'That block is reserved and cannot be assigned to a client.',
        'flash.staticip_invalid_offset': '{ip} is not a valid client address within its block. Did you mean {suggested}?',
        'flash.staticip_ip_taken':       '{ip} is already assigned to another client.',

        # --- "Static IP" page (staticip.html) ---
        'sip.card_title':            'This server’s static IP range',
        'sip.range_prefix':          'Reserved range:',
        'sip.range_suffix':          '(contiguous with OpenVPN’s dynamic pool, doesn’t interfere with normally assigned IPs). Each client with a static IP occupies its own block within this range.',
        'sip.range_error':           'Could not compute this server’s static IP range — check that <code>/etc/openvpn/server.conf</code> has a valid <code>server</code> line.',
        'sip.clients_title':         'Clients with a static IP ({assigned} of {total})',
        'sip.th_name':                'Name',
        'sip.th_staticip':            'Static IP',
        'sip.th_reason':              'Reason',
        'sip.th_actions':             'Actions',
        'sip.unassigned_badge':      'Not assigned',
        'sip.no_reason':             '(no reason recorded)',
        'sip.release_confirm':       'Remove the static IP from {name} ({ip})? It will return to the dynamic pool on its next connection.',
        'sip.release_btn':           'Remove',
        'sip.assign_btn':            'Assign static IP',
        'sip.no_clients':            'No active clients yet.',
        'sip.modal_title':           'Assign static IP',
        'sip.modal_client':          'Client:',
        'sip.mode_auto':             'Automatic (next free)',
        'sip.mode_manual':           'Choose IP manually',
        'sip.desired_ip_label':      'Desired IP',
        'sip.desired_ip_optional':   '(client address within the static IP range)',
        'sip.desired_ip_hint':       'Must fall within {net} and not already be assigned to another client. If invalid, the panel suggests the nearest valid address.',
        'sip.range_fallback':        'the static IP range',
        'sip.reason_label':          'Reason',
        'sip.reason_placeholder':    'e.g.: firewall rule on the billing server that identifies this client by static IP',
        'sip.reason_hint':           'Required — a static IP is for specific cases; record why this client needs it.',
        'sip.confirm_assign_btn':    'Confirm assignment',

        # --- "Access Ranges" page (access_ranges.html) ---
        'ar.intro':                  'Access ranges define which networks each client can reach once connected. They’re enforced with a real firewall on the server (not dependent on the client’s .ovpn), so you can change them here without renewing its certificate or resending a new file — the new range applies on its next connection.',
        'ar.clients_title':          'Clients with a restricted range ({restricted} of {total})',
        'ar.th_name':                'Name',
        'ar.th_ranges':              'Access ranges',
        'ar.th_actions':             'Actions',
        'ar.static_ip_title':        'Static IP inside the VPN tunnel',
        'ar.no_restriction':         'No restriction',
        'ar.edit_btn':               'Edit range',
        'ar.no_clients':             'No active clients yet.',
        'ar.modal_title':            'Edit access range',
        'ar.modal_client':           'Client:',
        'ar.ranges_optional':        '(CIDR — empty = no restriction)',
        'ar.ranges_hint':            'Applies on the client’s next connection — doesn’t touch its certificate or .ovpn, no need to resend anything.',
        'ar.save_btn':               'Save range',

        # --- "Connection Log" page (logs.html) ---
        'log.title':                 'Connection Log',
        'log.tab_vpn_tip':           'OpenVPN server events: connections, disconnections, TLS errors…',
        'log.tab_vpn':               'OpenVPN',
        'log.tab_audit_tip':         'Actions taken from this panel: logins, clients created, revoked, blocked…',
        'log.tab_audit':             'Manager Audit',
        'log.quick_filter_label':    'Quick filter:',
        'log.filter_all_tip':        'Show every log line, unfiltered',
        'log.filter_all':            'All',
        'log.filter_events_vpn_tip': 'Show only clients connecting to or disconnecting from the VPN server',
        'log.filter_events_audit_tip':'Show only admin actions: logins, create, revoke, block, etc.',
        'log.filter_events_vpn':     'Connections / Disconnections',
        'log.filter_events_audit':   'Relevant events',
        'log.search_label':          'Search:',
        'log.search_placeholder':    'client, IP, event…',
        'log.search_tip':            'Type a client name, an IP, or any text to search the log. Matches are highlighted in yellow',
        'log.last_label':            'Last:',
        'log.last_tip':              'Maximum number of lines to show. With a filter active, up to 5× more lines are scanned to get enough results',
        'log.lines_option':          '{n} lines',
        'log.filter_btn_tip':        'Apply the text search to the current log',
        'log.filter_btn':            'Filter',
        'log.clear_search_tip':      'Clear the search text and show every line (keeps the active quick filter)',
        'log.clear_search_btn':      'Clear search',
        'log.refresh_tip':           'Reload the log to see the most recent entries. Auto-refreshes every 30s when no search is active',
        'log.refresh_btn':           'Refresh',
        'log.empty_vpn':             'No entries in the OpenVPN log',
        'log.empty_audit':           'No entries in the audit log',
        'log.empty_search_suffix':   ' matching "{search}"',
        'log.lines_shown':           '{n} line(s) shown',

        # --- "Administration" page (admin_users.html) ---
        'adm.create_title':          'Create panel user',
        'adm.create_intro':          'Creates an account that can log into this panel to manage VPN clients, but that <strong>has no access to a system shell or SSH</strong> (it’s created with no shell and in a group explicitly denied in the SSH configuration).',
        'adm.username_label':        'Username',
        'adm.password_label':        'Password',
        'adm.password2_label':       'Repeat password',
        'adm.create_btn':            'Create user',
        'adm.users_title':           'Panel users ({n})',
        'adm.th_user':               'User',
        'adm.th_access':             'Access',
        'adm.th_actions':            'Actions',
        'adm.panel_only_badge':      'Panel only — no shell/SSH',
        'adm.reset_tip':             'You cannot "view" the current password (it’s stored as a hash, not reversible) — it can only be reset to a new one',
        'adm.reset_btn':             'Reset password',
        'adm.delete_confirm':        'Delete user {name}? This action cannot be undone.',
        'adm.delete_btn':            'Delete',
        'adm.no_users':              'No panel users created yet.',
        'adm.reset_modal_title':     'Reset password',
        'adm.reset_modal_user':      'User:',
        'adm.reset_modal_suffix':    '— the current password can’t be viewed, only reset to a new one.',
        'adm.new_password_label':    'New password',
        'adm.new_password2_label':   'Repeat new password',
        'adm.reset_confirm_btn':     'Reset',

        # --- "Help" page (help.html) ---
        'help.page_title':    'User Guide — OpenVPN Manager',
        'help.page_subtitle': 'Click any section to expand it. Click again to collapse it.',

        'help.create.title':    'Add VPN client',
        'help.create.subtitle': 'Create a new certificate and connection profile',
        'help.create.body': """<p>Generates a unique certificate for a user or device. The result is a <strong>.ovpn</strong> file that the client imports into their OpenVPN app.</p>
        <ul>
          <li><strong>Name:</strong> unique client identifier. Letters, numbers, hyphens and underscores only. Cannot be repeated. Example: <code>john-laptop</code>, <code>madrid-office</code>.</li>
          <li><strong>Email:</strong> stored as an internal reference. Never sent anywhere automatically.</li>
          <li><strong>Validity (months):</strong> the certificate’s lifetime. Once it expires, the client can’t connect until it’s renewed. Defaults to 24 months.</li>
          <li><strong>Key password</strong> (optional): encrypts the private key inside the .ovpn. The client will need to enter it every time they import or use the profile.</li>
          <li><strong>Access ranges</strong> (optional, CIDR): internal networks this client’s access is restricted to. Example: <code>192.168.1.0/24</code>. Left empty, the client can reach anything the server allows. Enforced with a <strong>real firewall on the server</strong>, not just a route suggestion to the client — see the "Access Ranges and Firewall" section below for the detail.</li>
        </ul>
        <div class="info-box">&#128161; The .ovpn file contains everything needed: certificates, private key and server configuration. Sharing that single file with the user is enough.</div>""",

        'help.download.title':    'Download .ovpn',
        'help.download.subtitle': 'Get the connection profile for the client',
        'help.download.body': """<p>Downloads the configuration file the user must import into their VPN app (OpenVPN Connect, Tunnelblick, NetworkManager, etc.).</p>
        <ol class="step-list">
          <li>Click the <strong>&#11123; .ovpn</strong> button on the client’s row.</li>
          <li>Send the downloaded file to the user securely (encrypted email, SFTP, etc.).</li>
          <li>The user imports it into their app and connects with their key username/password if it has one.</li>
        </ol>
        <div class="warn-box">&#9888; The .ovpn contains the client’s private key. Treat it like a password: don’t share it over insecure channels like WhatsApp or unencrypted email.</div>""",

        'help.renew.title':    'Renew certificate',
        'help.renew.subtitle': 'Extend a client’s expiry date',
        'help.renew.body': """<p>When a certificate is about to expire or has already expired <span class="badge-demo bd-expired">Expired</span>, it needs to be renewed for the client to keep connecting.</p>
        <p>Renewing does two things automatically:</p>
        <ul>
          <li>Revokes the old certificate (it’s no longer valid).</li>
          <li>Issues a new certificate with the validity you choose.</li>
        </ul>
        <p>The user will need to <strong>download and import the new .ovpn</strong> — the old one will stop working.</p>
        <div class="warn-box">&#9888; Remember to send the new .ovpn to the user after renewing. If the client tries to connect with the old profile, they’ll get a certificate error.</div>""",

        'help.disconnect.title':    'Disconnect',
        'help.disconnect.subtitle': 'Close an active VPN session on demand',
        'help.disconnect.body': """<p>Closes the VPN session of a client that is currently <span class="conn-dot dot-on"></span><strong>Connected</strong>. The client receives a clean shutdown signal and their app will show "disconnected".</p>
        <p><strong>Temporary effect:</strong> the client can reconnect right away with the same .ovpn. To prevent reconnection, use <strong>Block</strong> instead.</p>
        <div class="info-box">&#128161; The disconnect button only appears when the client is actively connected at that moment.</div>""",

        'help.block.title':    'Block / Unblock',
        'help.block.subtitle': 'Temporarily prevent a client from connecting',
        'help.block.body': """<p>Blocking a client does two things at once:</p>
        <ul>
          <li>If connected, disconnects it immediately.</li>
          <li>Writes the <code>disable</code> directive into its individual config file (CCD), preventing any future reconnection while it stays blocked.</li>
        </ul>
        <p>The client will show the <span class="badge-demo bd-blocked">&#128274; Blocked</span> label in the table.</p>
        <p><strong>Unblock</strong> removes that restriction and the client can reconnect with the same .ovpn without needing a new one issued.</p>
        <div class="info-box">&#128161; Useful when an employee is on temporary leave, there’s suspicion of misuse, or you simply want to pause access without permanently revoking the certificate.</div>""",

        'help.revoke.title':    'Revoke certificate',
        'help.revoke.subtitle': 'Permanently invalidate a client’s access',
        'help.revoke.body': """<p>Adds the client’s certificate to the server’s <strong>Certificate Revocation List (CRL)</strong>. From that point on, the server rejects any connection attempt with that certificate, even if the .ovpn is still on the user’s device.</p>
        <p>The client will show as <span class="badge-demo bd-revoked">Revoked</span> in the table and no action can be taken on it except viewing it.</p>
        <div class="danger-box">&#10006; <strong>This action is irreversible.</strong> If the user needs to connect again in the future, you’ll need to create a new client with a different name, or use Renew instead of revoking.</div>
        <div class="warn-box">&#9888; Use this when a user leaves for good, or a device with the .ovpn is lost or stolen.</div>""",

        'help.maintenance.title':    'Maintenance mode',
        'help.maintenance.subtitle': 'Block every client at once',
        'help.maintenance.body': """<p>Blocks every active VPN client at once, except the ones you mark as protected in the dialog. Blocked clients are disconnected and can’t reconnect until maintenance mode is turned off.</p>
        <p>While clients are blocked, a yellow maintenance bar appears at the top of the screen. From there you can turn it off with one click, unblocking everyone at once.</p>
        <div class="warn-box">&#9888; <strong>Always mark your own VPN client as protected</strong> before turning on maintenance mode. If you don’t, you’ll lose remote access and will need to reach the server physically or by another route to turn it off.</div>
        <div class="info-box">&#128161; Ideal for server updates, network configuration changes, or any task that requires nobody being connected to the VPN.</div>""",

        'help.firewall.title':    'Access ranges and firewall',
        'help.firewall.subtitle': 'How each client’s reach is really restricted',
        'help.firewall.body': """<p>"Access ranges" limit which internal networks a given client can reach once connected to the VPN — for example, an external contractor who should only reach one department’s server, not the whole office.</p>
        <p><strong>Enforced with a real firewall on the server itself</strong>, not just a route suggestion to the client. A user who tries to bypass it by adding manual routes on their own computer gets nowhere: the server still rejects any packet toward a destination outside its authorized range.</p>
        <p>A separate process (outside OpenVPN itself) constantly watches who’s connected and with what range, and keeps the firewall rules in sync — so after connecting, there can be a couple of seconds’ lag before the restriction is fully applied.</p>
        <ul>
          <li>Can be set when creating the client or renewing it, in the <strong>Access ranges</strong> field (CIDR format, one or more separated by commas or line breaks).</li>
          <li>Can also be changed at any time from the <strong>Access ranges</strong> tab, without renewing the certificate or resending a new .ovpn to the client — the range is about what it can reach, independent of its certificate, which only says who it is.</li>
          <li>Empty = no restriction, the client reaches everything the server allows (the usual behavior).</li>
          <li>Renewing a client doesn’t erase its configured range — it’s kept unless you change it explicitly.</li>
          <li>The client’s <strong>.ovpn</strong> file is never modified by these rules — it stays exactly as generated. All the control happens on the server, so there’s never a need to resend a new .ovpn just for changing its range.</li>
        </ul>
        <div class="info-box">&#128161; If a restricted client can’t reach something it should, first check that the CIDR range really includes that address — a typo here (e.g. <code>/24</code> instead of <code>/32</code>) is the most common cause.</div>""",

        'help.staticip.title':    'Static IP',
        'help.staticip.subtitle': 'Always give a client the same address inside the VPN tunnel',
        'help.staticip.body': """<p>By default, the IP address a client gets inside the VPN tunnel can change between connections (assigned from a shared pool). A <strong>static IP</strong> always reserves the same address for a given client.</p>
        <p>Useful for very specific cases where something <strong>outside</strong> this panel needs to always identify the same client by its address — for example, a firewall rule on another server, or an external integration that only grants access to one specific IP. Not needed for normal VPN use.</p>
        <p>Managed from the <strong>Static IP</strong> tab, not from the client list:</p>
        <ul>
          <li><strong>Automatic:</strong> the panel picks the next free address within the range reserved for static IPs.</li>
          <li><strong>Manual:</strong> you type the exact address you want — the panel validates it’s correct and free, and if not, suggests the nearest valid one.</li>
          <li><strong>Reason</strong> (required): you must record why it’s being assigned. Since it’s a deliberate assignment and not routine, there’s a record of why each client has it — visible right on the tab.</li>
        </ul>
        <p>The static IP is kept when renewing the client or changing its access range, and is removed with the <strong>Remove</strong> button when no longer needed, freeing that address for another client.</p>
        <div class="info-box">&#128161; Static IP and "Access ranges" are independent and compatible with each other — a client can have both, just one, or neither.</div>""",

        'help.map.title':    'Map',
        'help.map.subtitle': 'Where each client last connected from',
        'help.map.body': """<p>Shows the approximate location (city-level) each client's last connection came from — one point per client, overwritten on every new connection. No history of past locations is kept.</p>
        <p><strong>How it’s computed:</strong> the client’s real IP (the same one the OpenVPN server itself already sees when accepting the connection) is looked up in a geolocation database downloaded and stored on this same server. That IP is <strong>never sent to any external service</strong> — the whole lookup happens locally.</p>
        <p>The only things that leave this server are the periodic (monthly) download of the database itself, and the map tiles the admin’s own browser requests from OpenStreetMap when viewing this page — neither includes any client data.</p>
        <p>A client shows up under <strong>"No location available"</strong> if it has never connected yet, if it connected from a private/local IP (common when testing within the same network), or if that IP has no record in the database.</p>
        <div class="info-box">&#128161; Accuracy is city-level, not an exact address — enough to spot patterns or unexpected access, not for precise tracking.</div>""",

        'help.status.title':    'Client statuses',
        'help.status.subtitle': 'What each label and colored dot means',
        'help.status.body': """<p><strong>Connection column:</strong></p>
        <ul>
          <li><span class="conn-dot dot-on"></span><strong>Connected</strong> — the client has an active VPN session right now. Real-time data queried from the OpenVPN server.</li>
          <li><span class="conn-dot dot-off"></span><strong>Disconnected</strong> — no active session at the moment.</li>
        </ul>
        <p style="margin-top:10px"><strong>Status column:</strong></p>
        <ul>
          <li><span class="badge-demo bd-active">Active</span> — valid certificate, within its expiry date.</li>
          <li><span class="badge-demo bd-expired">Expired</span> — the certificate has expired. The client can’t connect until it’s renewed.</li>
          <li><span class="badge-demo bd-revoked">Revoked</span> — access permanently denied.</li>
          <li><span class="badge-demo bd-blocked">&#128274; Blocked</span> — access temporarily suspended. Can be unblocked.</li>
        </ul>
        <div class="info-box">&#128161; The connection status refreshes automatically every few seconds on "VPN Clients", without reloading the page.</div>""",

        'help.logs.title':    'Connection log',
        'help.logs.subtitle': 'What the two log viewer tabs show',
        'help.logs.body': """<p><strong>&#127760; OpenVPN</strong> — VPN server events: who connects, from what IP, when they disconnect, certificate errors, etc. Source: <code>journalctl -u openvpn@server</code>.</p>
        <p><strong>&#128274; Manager Audit</strong> — actions taken through this web panel: logins, clients created, revoked, blocked, etc. Source: <code>/var/log/openvpn-gui.log</code>.</p>
        <p>Use the <strong>Connections / Disconnections</strong> filter to see only clients coming and going, ignoring system noise.</p>
        <p>The page auto-refreshes every 30 seconds when no search is active.</p>
        <div class="info-box">&#128161; Looking for a specific client’s history? Type its name in the search box. Matches are highlighted in yellow in the results.</div>""",

        'help.concepts.title':    'Key concepts',
        'help.concepts.subtitle': 'PKI, certificates, CRL and CIDR ranges explained',
        'help.concepts.body': """<p><strong>Client certificate:</strong> a unique digital document that identifies each user to the VPN server. Equivalent to a key. Without it, connecting is impossible.</p>
        <p><strong>PKI (Public Key Infrastructure):</strong> the file system on the server that manages every certificate. Lives at <code>/etc/openvpn/easy-rsa/</code>.</p>
        <p><strong>CRL (Certificate Revocation List):</strong> a blacklist of invalidated certificates. The server checks it on every connection attempt. When you revoke a client, its certificate is added here.</p>
        <p><strong>CCD (Client Config Directory):</strong> a folder with one individual config file per client (<code>/etc/openvpn/server.ccd/</code>). Blocking works by writing <code>disable</code> into that file.</p>
        <p><strong>CIDR ranges:</strong> a compact way of writing IP ranges. Examples:</p>
        <ul>
          <li><code>192.168.1.0/24</code> → IPs from 192.168.1.0 to 192.168.1.255 (256 hosts)</li>
          <li><code>10.0.0.0/8</code> → the entire 10.x.x.x network (16 million hosts)</li>
          <li><code>172.16.5.10/32</code> → a single host</li>
        </ul>
        <p><strong>.ovpn file:</strong> an all-in-one configuration profile. Includes the server address, the client’s certificate, its private key and the TLS auth key. This single file is enough to connect.</p>
        <div class="warn-box">&#9888; The .ovpn file is equivalent to a password. Whoever has it can connect to the VPN. Store and share it securely.</div>""",

        # --- "Map" page (map.html) ---
        'map.title':                 'Each client’s last connection',
        'map.intro':                 'Shows the approximate location (city-level) each client last connected from, computed locally on this server from its real IP — that IP is never sent to any external service.',
        'map.db_pending':            'The geolocation database hasn’t been downloaded yet. New clients that connect won’t have a location until the first automatic download completes.',
        'map.no_location_title':     'No location available ({n})',
        'map.th_name':                'Name',
        'map.th_ip':                  'Last IP',
        'map.th_reason':              'Reason',
        'map.never_connected':       'Has never connected yet',
        'map.private_or_unresolved': 'Private/local IP, or no record in the geolocation database',
        'map.history_title':         'Connection history per client',
        'map.history_intro':         'Up to the last 5 distinct IPs each client has connected from — most recent first. If it always connects from the same place, only one shows up.',
        'map.th_history':            'IP history',
        'map.history_no_data':       'No location data',
        'map.popup_last_connection': 'Last connection',
        'map.empty_no_data':         'No location recorded yet.',
    },
}


def get_text(lang, key):
    """Devuelve el texto para `key` en `lang`, con fallback a inglés y,
    si tampoco existe ahí, la propia clave (nunca None/excepción)."""
    table = TRANSLATIONS.get(lang) or TRANSLATIONS[DEFAULT_LANG]
    return table.get(key) or TRANSLATIONS[DEFAULT_LANG].get(key) or key
