# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class hr_cuentas_analiticas(models.Model):
	_name = 'hr.cuentas.analiticas'
	_rec_name = 'name'

	name = fields.Char('Nombre',required=True)
	code = fields.Char('Código',required=True)

	@api.multi
	def name_get(self):
		context = self.env.context
		if context is None:
			context = {}
		result = []
		for cuenta in self:
			result.append((cuenta.id, ' '.join([cuenta.code, cuenta.name])))
		return result

	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search((args + ['|', ('name', 'ilike', name), ('code', 'ilike', name)]),
							   limit=limit)
		if not recs:
			recs = self.search([('name', operator, name)] + args, limit=limit)
		return recs.name_get()