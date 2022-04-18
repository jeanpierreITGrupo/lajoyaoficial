# -*- coding: utf-8 -*-
import logging

from openerp import SUPERUSER_ID
from openerp import tools, fields , api
from openerp.modules.module import get_module_resource
from openerp.osv import osv
from openerp.tools.translate import _

class hr_employee(osv.osv):
	_inherit = "hr.employee"
	
	last_name_father = fields.Char('Apellido Paterno')
	last_name_mother = fields.Char('Apellido Materno')
	first_name_complete = fields.Char('Nombres') 
	children_number = fields.Integer('Nro. de Hijos')

	zona_contab = fields.Char('Zona')
	tipo_contab = fields.Selection([
		('operario','Operario'),
		('mantenimiento','Mantenimiento'),
		('administracion','Administración'),
		('ventas','Ventas')],'Tipo')

	fecha_ingreso = fields.Date('Fecha Ingreso')
	fecha_afiliacion = fields.Date('Fecha Afiliación')

	@api.onchange('last_name_father','last_name_mother','first_name_complete')
	def onchange_name_last_fp(self):
		self.name = ( (self.first_name_complete if self.first_name_complete else '' ).upper() + " " + (self.last_name_father if self.last_name_father else '').upper() + " " + (self.last_name_mother if self.last_name_mother else '' ).upper()).strip()