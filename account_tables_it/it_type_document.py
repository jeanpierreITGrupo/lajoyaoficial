# -*- coding: utf-8 -*-

from openerp import models, fields, api
import re

class it_type_document(models.Model):
	_name = 'it.type.document'
	code = fields.Char(required=True, string="Código",size=3)
	description = fields.Char(required=True, string="Descripción",size=100)

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
			name = record.code

			if 'type' in context:
				if context['type']== 'in_invoice' or context['type']== 'out_invoice':
					name = record.description

			
			if 'td_description' in context:
				name = record.description
				
			res.append((record.id, name))
		return res



	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			ids = self.search(cr, user, [('code','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('description','=',name)]+ args, limit=limit, context=context)
			if not ids:
				# Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
				# on a database with thousands of matching products, due to the huge merge+unique needed for the
				# OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
				# Performing a quick memory merge of ids in Python will give much better performance
				ids = set()
				ids.update(self.search(cr, user, args + [('code',operator,name)], limit=limit, context=context))
				if not limit or len(ids) < limit:
					# we may underrun the limit because of dupes in the results, that's fine
					ids.update(self.search(cr, user, args + [('code',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					# vivek
					# Purpose  : To filter the product by using part_number
					ids.update(self.search(cr, user, args + [('description',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					#End
				ids = list(ids)
			if not ids:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('code','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result
