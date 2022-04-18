# -*- coding: utf-8 -*-

from openerp import models, fields, api

class it_type_document_partner(models.Model):
	_name = 'it.type.document.partner'
	code = fields.Char(required=True, string="Código",size=3)
	description = fields.Char(required=True, string="Descripción",size=70)

	_order = 'code'

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