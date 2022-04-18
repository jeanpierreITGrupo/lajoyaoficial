# -*- coding: utf-8 -*-
import base64
from openerp.osv import osv
from openerp     import models, fields, api

from datetime import datetime

class reporte_empleado_wizard(models.TransientModel):
	_name = 'reporte.empleado.wizard'

	forma       = fields.Selection([('1','Todos'),('2','Uno')],'Imprimir',required=True,default='1')
	employee_id = fields.Many2one('hr.employee','Empleado')

	@api.multi
	def do_rebuild(self):
		hl = self.env['hr.liquidaciones'].search([('id','=',self.env.context['active_id'])])[0]
		hllc = self.env['hr.liquidaciones.lines.cts'].search([('liquidacion_id','=',hl.id),('employee_id','=',self.employee_id.id)])
		
		if self.forma == '1':
			return hl.export_pdf(self.env.context['employees'])
		if self.forma == '2':
			if not len(hllc):
				raise osv.except_osv("Alerta!", u"No existe el empleado seleccionado en liquidaciones.")
			else:
				return hl.export_pdf(self.employee_id.id)
		return True