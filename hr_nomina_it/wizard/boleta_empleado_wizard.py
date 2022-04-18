# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class boleta_empleado_wizard(models.TransientModel):
	_name = 'boleta.empleado.wizard'

	forma       = fields.Selection([('1','Todos'),('2','Uno')],'Imprimir',required=True,default='1')
	employee_id = fields.Many2one('hr.employee','Empleado')
	digital_sgn = fields.Binary('Firma', filename="may")

	@api.multi
	def do_rebuild(self):
		if 'comes_from' in self.env.context:
			ht = self.env['hr.tareo'].search([('id','=',self.env.context['active_id'])])[0]
			htl = self.env['hr.tareo.line'].search([('tareo_id','=',self.env.context['active_id']),('employee_id','=',self.employee_id.id)])
			if self.env.context['comes_from'] == 'generar_pdf':
				if self.forma == '1':
					return ht.make_pdf(ht.detalle.ids, self.digital_sgn)
				if self.forma == '2':
					if len(htl) == 0:
						raise osv.except_osv("Alerta!", u"No existe el empleado en el tareo.")
					else:
						return ht.make_pdf(htl.id, self.digital_sgn)
			if self.env.context['comes_from'] == 'generar_email':
				if self.forma == '1':
					return ht.make_email(ht.detalle.ids, self.digital_sgn)
				if self.forma == '2':
					if len(htl) == 0:
						raise osv.except_osv("Alerta!", u"No existe el empleado en el tareo.")
					else:
						return ht.make_email(htl.id, self.digital_sgn)
		return True