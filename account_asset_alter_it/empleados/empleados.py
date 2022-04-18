# -*- coding: utf-8 -*-

from openerp import models, fields, api
import re

class empleados_css(models.Model):
	_name = 'empleados'
	
	codigo=fields.Char(required=True, string="Código",size=3)
	Nombres=fields.Char(required=True, string="Nombres",size=40)
	Edad=fields.Char(required=True, string="Edad",size=40)
	Sueldo=fields.Char(required=False, string="Sueldo")
	
	_order = 'codigo'

	
