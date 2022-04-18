# -*- coding: utf-8 -*-
from openerp     import tools
from openerp     import models, fields, api
from openerp.osv import osv, expression
import pprint 

class hr_actualizar_proyecciones_wizard(models.TransientModel):
	_name = 'hr.actualizar.proyecciones.wizard'

	month = fields.Selection([('1',u'Enero'),
							  ('2',u'Febrero'),
							  ('3',u'Marzo'),
							  ('4',u'Abril'),
							  ('5',u'Mayo'),
							  ('6',u'Junio'),
							  ('7',u'Julio'),
							  ('8',u'Agosto'),
							  ('9',u'Septiembre'),
							  ('10',u'Octubre'),
							  ('11',u'Noviembre'),
							  ('12',u'Diciembre'),], u'Mes', required=True)

	lines = fields.One2many('hr.actualizar.proyecciones.lines.wizard','actualizar_id','lineas')

	@api.multi
	def do_rebuild(self):
		hfcl  = self.env['hr.five.category.lines'].search([('id','=',self.env.context['active_id'])])[0]
		for i in self.lines:
			hfcp = self.env['hr.five.category.proy'].search([('five_line_id','=',hfcl.id),('concepto_id','=',i.concept_id.id)])
			if int(self.month) <= 1:
				hfcp.january = i.monto
			if int(self.month) <= 2:
				hfcp.february = i.monto
			if int(self.month) <= 3:
				hfcp.march = i.monto
			if int(self.month) <= 4:
				hfcp.april = i.monto
			if int(self.month) <= 5:
				hfcp.may = i.monto
			if int(self.month) <= 6:
				hfcp.june = i.monto
			if int(self.month) <= 7:
				hfcp.july = i.monto
			if int(self.month) <= 8:
				hfcp.august = i.monto
			if int(self.month) <= 9:
				hfcp.september = i.monto
			if int(self.month) <= 10:
				hfcp.october = i.monto
			if int(self.month) <= 11:
				hfcp.november = i.monto
			if int(self.month) <= 12:
				hfcp.december = i.monto

class hr_actualizar_proyecciones_lines_wizard(models.TransientModel):
	_name = 'hr.actualizar.proyecciones.lines.wizard'

	actualizar_id = fields.Many2one('hr.actualizar.proyecciones.wizard','padre')

	concept_id = fields.Many2one('hr.lista.conceptos', u'Concepto', required=True)
	monto	   = fields.Float(u'Monto')

	@api.onchange('concept_id')
	def onchange_concept_id(self):
		if self.concept_id.id:
			hfcl = self.env['hr.five.category.lines'].search([('id','=',self.env.context['active_id'])])[0]
			if self.concept_id.code == '001':
				self.monto = hfcl.employee_id.basica
			elif self.concept_id.code == '002':
				hp = self.env['hr.parameters'].search([('num_tipo','=',10001)])[0]
				self.monto = hp.monto if hfcl.employee_id.children_number else 0
			else:
				self.monto = 0