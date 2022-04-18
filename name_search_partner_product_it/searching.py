# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import expression
import re


class res_partner(models.Model):
	_inherit = 'res.partner'

	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			elems = name.split(' ')
			cadenafinal = []
			for xelem in elems:
				if xelem != None and xelem.strip() != '' and xelem.strip() != None:
					cadenafinal.append( ('name','ilike',xelem.strip()) )

			ids = self.search(cr, user,cadenafinal+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('type_number','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				# Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
				# on a database with thousands of matching products, due to the huge merge+unique needed for the
				# OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
				# Performing a quick memory merge of ids in Python will give much better performance
				ids = set()
				ids.update(self.search(cr, user, args + [('name',operator,name)], limit=limit, context=context))
				if not limit or len(ids) < limit:
					# we may underrun the limit because of dupes in the results, that's fine
					ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					# vivek
					# Purpose  : To filter the product by using part_number
					ids.update(self.search(cr, user, args + [('type_number',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					#End
				ids = list(ids)
			if not ids:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('name','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result

class product_product(models.Model):
	_inherit = 'product.product'

	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
			ids = []

			elems = name.split(' ')
			cadenafinal = []
			for xelem in elems:
				if xelem != None and xelem.strip() != '' and xelem.strip() != None:
					cadenafinal.append( ('name','ilike',xelem.strip()) )

			if operator in positive_operators:
				ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
				if not ids:
					ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, cadenafinal+ args, limit=limit, context=context)
			if not ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
				# Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
				# on a database with thousands of matching products, due to the huge merge+unique needed for the
				# OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
				# Performing a quick memory merge of ids in Python will give much better performance
				ids = self.search(cr, user, args + [('default_code', operator, name)], limit=limit, context=context)
				if not limit or len(ids) < limit:
					# we may underrun the limit because of dupes in the results, that's fine
					limit2 = (limit - len(ids)) if limit else False
					ids += self.search(cr, user, args + [('name', operator, name), ('id', 'not in', ids)], limit=limit2, context=context)
			elif not ids and operator in expression.NEGATIVE_TERM_OPERATORS:
				ids = self.search(cr, user, args + ['&', ('default_code', operator, name), ('name', operator, name)], limit=limit, context=context)
			if not ids and operator in positive_operators:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result