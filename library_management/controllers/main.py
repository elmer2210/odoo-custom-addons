from odoo import http
from odoo.http import request
import json
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class SessionAPI(http.Controller):

    
    @http.route('/test/ruta', type='http', auth='public', methods=['GET'])
    def test_route(self):
        return "Ruta de prueba funcionando"

    @http.route('/api/session/start', type='json', auth='public', methods=['POST'], csrf=False)
    def start_session(self, **data):
        """ Recibe `numberID` y `email`, valida y guarda el inicio de sesión """
         # Agregar un print para depuración

        if not data:
            data = request.httprequest.get_json()
            _logger.info("Datos recibidos en la API: %s", json.dumps(data))
        
        student_id = data.get('numberID')
        email = data.get('email')

        if not student_id or not email:
            return {"error": "Faltan datos. Se requiere número de cédula y correo electrónico."}

        student = request.env['student.profile'].sudo().search([
            ('student_id', '=',student_id),
            ('email', '=', email)
        ], limit=1)

        if not student:
            return {"error": "Usuario no encontrado. Verifique su información."}

        session_log = request.env['library.computer'].sudo().create({
            'numberID': student_id,
            'email': email,
            'student_id': student.id,
            'init_time': datetime.now(),
            'finit_time': False  # Se inicializa vacío
        })

        return {
            "success": True,
            "message": "Inicio de sesión registrado exitosamente.",
            "session_id": session_log.id,
            "init_time": session_log.init_time,
        }

    @http.route('/api/session/end', type='json', auth='public', methods=['PUT'], csrf=False)
    def end_session(self, **data):
        """ Actualiza `finit_time` en un registro existente de sesión """

        if not data:
            data = request.httprequest.get_json()

            _logger.info("Datos recibidos en la API: %s", json.dumps(data))

        session_id = data.get('session_id')

        if not session_id:
            return {"error": "Falta el `session_id` para actualizar la sesión."}

        session = request.env['library.computer'].sudo().search([
            ('id', '=', session_id)
        ], limit=1)

        if not session:
            return {"error": "No se encontró la sesión con el ID proporcionado."}

        # Actualizar la sesión con el `end_time`
        session.sudo().write({
            'finit_time': datetime.now()
        })

        return {
            "success": True,
            "message": "Hora de salida registrada exitosamente.",
            "session_id": session.id,
            "init_time": session.init_time,
            "finit_time": session.finit_time
        }
