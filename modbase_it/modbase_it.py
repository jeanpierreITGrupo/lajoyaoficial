# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp.http import Controller
from openerp.http import request, route

import decimal

import openerp.http as http

class very_permision(http.Controller):

	@http.route('/verify_controller', type='http')
	def index(self, **kw):
		user_obj = request.env['res.users'].search([('id','=',request.uid)])
		for i in user_obj.groups_id:
			if i.name == 'Modo Administrador':
				return "true"
		return "false"