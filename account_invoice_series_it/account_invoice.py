# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class account_invoice(models.Model):
	_inherit = 'account.invoice'
	
	serie_id = fields.Many2one('it.invoice.serie', string="Serie",index=True)
	serie_id_internal = fields.Many2one('it.invoice.serie', string="Serie",index=True,copy=False)
	nro_internal = fields.Char('Internal Number',copy=False)




	@api.one
	def write(self,vals):
		t = super(account_invoice,self).write(vals)
		if 'currency_id' in vals:
			self.button_reset_taxes()
		return t

	@api.onchange('type_document_id')
	def _onchange_type_account(self):
		self.serie_id=""
		if self.type_document_id:
			return {'domain':{'serie_id':[('type_document_id','=',self.type_document_id.id)]}}
		else:
			self.serie_id = ""


	@api.one
	def copy(self,default=None):
		t =super(account_invoice,self).copy(default)
		if default == None:
			default = {}
		t.type_document_id = False
		t.serie_id = False
		return t
	
	@api.onchange('serie_id')
	def _onchange_serie_id(self):
		if self.serie_id:
			next_number = self.serie_id.sequence_id.number_next_actual
			print 'prefix', self.serie_id.sequence_id.prefix
			if self.serie_id.sequence_id.prefix == False:
				raise osv.except_osv('Alerta!', "No existe un prefijo configurado en la secuencia de la serie.")
			prefix = self.serie_id.sequence_id.prefix
			padding = self.serie_id.sequence_id.padding
			self.supplier_invoice_number = prefix + "0"*(padding - len(str(next_number))) + str(next_number)
		else:
			self.supplier_invoice_number = ""
	"""	
	@api.one
	def action_date_assign(self):
		t = super(account_invoice,self).action_date_assign()
		self.write({})
		for inv in self:
			print 'number', inv.supplier_invoice_number
			#inv.write({'number': inv.supplier_invoice_number})
			if inv.serie_id.id != False:
				name=self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, inv.serie_id.sequence_id.id, self.env.context)	
		return True
		
	@api.multi
	def action_number(self):
		t = super(account_invoice,self).action_number()
		self.write({})
		for inv in self:
			print 'number', inv.supplier_invoice_number
			inv.write({'number': inv.supplier_invoice_number})
			print 'new_number', inv.number
		return t
	
	"""

	@api.multi
	def invoice_validate(self):
		for i in self:
			if i.serie_id.id and i.serie_id_internal.id and i.serie_id.id == i.serie_id_internal.id:
				i.number = i.nro_internal
				i.supplier_invoice_number=i.nro_internal
			elif i.serie_id.id and i.serie_id_internal.id != i.serie_id.id:
				i.serie_id_internal = i.serie_id.id
				i.nro_internal = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, i.serie_id.sequence_id.id, self.env.context)
				i.number = i.nro_internal
				i.supplier_invoice_number=i.nro_internal
		return super(account_invoice,self).invoice_validate()
