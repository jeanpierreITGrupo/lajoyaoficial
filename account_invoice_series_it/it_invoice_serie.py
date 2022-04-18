# -*- coding: utf-8 -*-
from openerp import models, fields, api

class it_invoice_serie(models.Model):
	_name = 'it.invoice.serie'
	
	name = fields.Char(string="Serie",size=64)
	type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",index=True)
	sequence_id = fields.Many2one('ir.sequence', string="Secuencia",index=True)
	description = fields.Char(string="Descripción",size=255)

	'''
	@api.onchange('code')
	def _onchange_price(self):
		# set auto-changing field
		if self.code:
			self.description = str(self.code) + ": Descripción"
		# Can optionally return a warning and domains

	def name_get(self, cr, uid, ids, context=None):
		res = []
			
		for record in self.browse(cr, uid, ids, context=context):
			if 'show_code' in context:
				name = record.code
				res.append((record.id, name))
			else:
				name = record.description
				res.append((record.id, name))
		return res
	'''