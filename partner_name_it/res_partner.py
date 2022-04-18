# -*- coding: utf-8 -*-

from openerp import models, fields, api,exceptions , _

import re

class res_partner(models.Model):
	_inherit = 'res.partner'

	type_document_id = fields.Many2one('it.type.document.partner', string="Tipo de Documento",index=True,ondelete='restrict')
	type_number = fields.Char('Número de Documento',size=20)

	first_name = fields.Char('Nombre',size=50)
	last_name_f = fields.Char('Apellido Paterno',size=50)
	last_name_m = fields.Char('Apellido Materno',size=50)
	
	@api.model
	def create(self,vals):
		t =super(res_partner,self).create(vals)
		if t.type_document_id.id and t.type_document_id.code == '6':
			t.write({'vat':'PE'+t.type_number})
		return t

	@api.one
	def write(self,vals):
		t =super(res_partner,self).write(vals)
		self.refresh()
		if self.type_document_id.id and self.type_document_id.code == '6':
			if self.vat != 'PE' + self.type_number:
				self.vat = 'PE' + self.type_number
		return t


	@api.onchange('first_name','last_name_f','last_name_m')
	def _onchange_price(self):
		# set auto-changing field
		fn = ""
		if self.first_name:
			fn = self.first_name
		lnf = ""
		if self.last_name_f:
			lnf = self.last_name_f
		lnm = ""
		if self.last_name_m:
			lnm = self.last_name_m
		self.name = (fn + " " + lnf + " " + lnm).strip()
		# Can optionally return a warning and domains

	@api.one
	@api.constrains('type_number','type_document_id')
	def constrains_suplier_invoice_number(self):
		if self.type_number:
			if self.type_document_id:
				filtro = []
				filtro.append( ('id','!=',self.id) )
				if self.type_document_id:
					filtro.append( ('type_document_id','=',self.type_document_id.id) )
				filtro.append( ('type_number','=', self.type_number) )
				
				m = self.env['res.partner'].search( filtro )
				if len(m) > 0:
					raise exceptions.Warning(_("Número de Documento Duplicado ("+str(self.type_document_id.code)+" - "+str(self.type_number)+")."))

				t = self.env['main.parameter'].search([])[0]
				if self.type_document_id.id == t.sunat_type_document_ruc_id.id:
					if t.l_ruc!= len(self.type_number):
						raise exceptions.Warning(_("Número Invalido RUC"))						

				if self.type_document_id.id == t.sunat_type_document_dni_id.id:
					if t.l_dni!= len(self.type_number):
						raise exceptions.Warning(_("Número Invalido DNI"))						



	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('type_number','=',name)]+ args, limit=limit, context=context)
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