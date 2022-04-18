# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp     import models, fields, api
import base64
import codecs

class armado_ruma(models.Model):
	_inherit = 'armado.ruma'

	categoria_id = fields.Many2one('mrp.plantas',u'Categoría')

	@api.model
	def default_get(self, fields):
		res = super(armado_ruma, self).default_get(fields)
		mp  = self.env['mrp.plantas'].search([('default_value','=',True)])
		if len(mp) > 0:
			mp = mp[0]
			res['categoria_id'] = mp.id
		return res

	@api.model
	def create(self, vals):
		isq  = self.env['ir.sequence'].search([('name','=','Build Ruma')])

		if len(isq) == 0:
			raise osv.except_osv('Alerta!', u"No se Encontró la secuencia por defecto de la orden de producción")

		isq = isq[0]
		current_default_sequence = isq.number_next
		t = super(armado_ruma,self).create(vals)

		if t.categoria_id.id == False:
			raise osv.except_osv('Alerta!', u"Debe seleccionar una planta antes de confirmar la producción")

		if t.categoria_id.id != isq.id:
			isq.number_next = current_default_sequence
			t.name          = self.env['ir.sequence'].next_by_id(t.categoria_id.secuencia.id)
		return t