# -*- coding: utf-8 -*-

from openerp import models, fields, api  , exceptions , _

class account_invoice(models.Model):
	_inherit = 'account.invoice'
	type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",index=True ,ondelete='restrict')
	journal_code = fields.Char(string="Libro",store=True, related='journal_id.code')
	type_document_code = fields.Char(string="Tipo",store=True, related='type_document_id.code')
	default_description = fields.Char(string="Descripción")

	def copy(self, cr, uid, id, default=None, context=None):
		default['supplier_invoice_number']= ''
		return super(account_invoice,self).copy( cr, uid, id, default, context)

	@api.one
	def action_number(self):
		t = super(account_invoice,self).action_number()
		self.write({'number':self.supplier_invoice_number,})
		self.move_id.write({'ref':self.number,})

		for inv in self:
			if inv.type_document_id:
				self._cr.execute(""" UPDATE account_move_line SET type_document_id=%s WHERE move_id=%s """,(inv.type_document_id.id, inv.move_id.id))
			if inv.supplier_invoice_number:
				self._cr.execute(""" UPDATE account_move_line SET nro_comprobante=%s WHERE move_id=%s """,(inv.supplier_invoice_number, inv.move_id.id))
			if inv.default_description:
				self._cr.execute(""" UPDATE account_move_line SET name=%s WHERE move_id=%s """,(inv.default_description, inv.move_id.id))
		return t


	def invoice_pay_customer(self, cr, uid, ids, context=None):
		t = super(account_invoice,self).invoice_pay_customer(cr, uid, ids, context)

		if not ids: return []
		inv = self.browse(cr, uid, ids[0], context=context)		
		if inv.type_document_id:
			t['context']['type_document_id'] = inv.type_document_id.id
		if inv.supplier_invoice_number:
			t['context']['nro_comprobante'] = inv.supplier_invoice_number
		return t
		"""
	@api.onchange('supplier_invoice_number')
	def onchange_suplier_invoice_number_it(self):
		if self.supplier_invoice_number:
			if self.type_document_id.id and ( int(self.type_document_id.code) == 1 or int(self.type_document_id.code) == 2 or int(self.type_document_id.code) == 3  ):
				self.supplier_invoice_number = str(self.supplier_invoice_number).replace(' ','')
				self.write({'supplier_invoice_number':str(self.supplier_invoice_number).replace(' ','')})
				self.refresh()
				t = self.supplier_invoice_number.split('-')
				if len(t) == 2:
					parte1= t[0]
					if len(t[0]) < 4:
						for i in range(0,4-len(t[0])):
							parte1 = '0'+parte1
					parte2= t[1]
					if len(t[1]) < 7:
						for i in range(0,7-len(t[1])):
							parte2 = '0'+parte2
					self.supplier_invoice_number = parte1 + '-' + parte2
					self.write({'supplier_invoice_number': parte1 + '-' + parte2})
					print  parte1 + '-' + parte2
					print "llegue onchange"
				else:
					pass
		"""
	
	@api.onchange('supplier_invoice_number','type_document_id')
	def onchange_suplier_invoice_number_it(self):
		if self.supplier_invoice_number:
			self.supplier_invoice_number = str(self.supplier_invoice_number).replace(' ','')
			#self.write({'supplier_invoice_number':str(self.supplier_invoice_number).replace(' ','')})
			
			if self.type_document_id.id and ( (self.type_document_id.code) == '01' or (self.type_document_id.code) == '02' or (self.type_document_id.code) == '03' or (self.type_document_id.code) == '04' or (self.type_document_id.code) == '06' or (self.type_document_id.code) == '07' or (self.type_document_id.code) == '08' or (self.type_document_id.code) == '12' or (self.type_document_id.code) == '13' or (self.type_document_id.code) == '15' or (self.type_document_id.code) == '00' or (self.type_document_id.code) == 'PM' or (self.type_document_id.code) == '07' ):
				self.supplier_invoice_number = str(self.supplier_invoice_number).replace(' ','')
				#self.write({'supplier_invoice_number':str(self.supplier_invoice_number).replace(' ','')})
				t = self.supplier_invoice_number.split('-')
				if len(t) == 2:
					parte1= t[0]
					if len(t[0]) < 4:
						for i in range(0,4-len(t[0])):
							parte1 = '0'+parte1
					parte2= t[1]
					if len(t[1]) < 7:
						for i in range(0,7-len(t[1])):
							parte2 = '0'+parte2
					self.supplier_invoice_number = parte1 + '-' + parte2
					#self.write({'supplier_invoice_number': parte1 + '-' + parte2})
					print  parte1 + '-' + parte2
					print "llegue onchange"
				elif len(t) == 1:
					parte2= t[0]
					if len(t[0]) < 7:
						for i in range(0,7-len(t[0])):
							parte2 = '0'+parte2
					self.supplier_invoice_number = parte2
					#self.write({'supplier_invoice_number':  parte2})
					print "llegue onchange"
				else:
					pass

	@api.one
	@api.constrains('supplier_invoice_number','partner_id','type_document_id','journal_id','state')
	def constrains_suplier_invoice_number(self):
		"""if self.supplier_invoice_number:
			filtro = []
			filtro.append( ('state','not in',('draft','cancel')) )
			filtro.append( ('id','!=',self.id) )
			if self.partner_id:
				filtro.append( ('partner_id','=',self.partner_id.id) )
			if self.type_document_id:
				filtro.append( ('type_document_id','=',self.type_document_id.id) )
			filtro.append( ('supplier_invoice_number','=',str(self.supplier_invoice_number).replace(' ','')) )
			if self.journal_id:
				filtro.append( ('journal_id.type','=', self.journal_id.type) )
			print filtro
			m = self.env['account.invoice'].search( filtro )
			if len(m) > 0:
				t = str(self.supplier_invoice_number).replace(' ','')
				raise exceptions.Warning(_("Número de Documento Duplicado ("+t+").")) """
		
		if self.supplier_invoice_number:
			filtro = []
			filtro.append( ('state','not in',('draft','cancel')) )
			filtro.append( ('id','!=',self.id) )
			if self.partner_id:
				filtro.append( ('partner_id','=',self.partner_id.id) )
			if self.type_document_id:
				filtro.append( ('type_document_id','=',self.type_document_id.id) )
			#filtro.append( ('supplier_invoice_number','=',str(self.supplier_invoice_number).replace(' ','')) )
			if self.journal_id:
				filtro.append( ('journal_id.type','=', self.journal_id.type) )
			print filtro
			m = self.env['account.invoice'].search( filtro )
			for elem in m:
				t = str(self.supplier_invoice_number).replace(' ','')
				t_t = t.split('-')
				r_t = ''
				pos = 0
				for t_elem in t_t:
					pos=0
					for t_char in t_elem:
						if t_char == '0':
							pos += 1
						else:
							r_t += t_elem[pos:] + '-'
							pos= 0
							break
				r_t = r_t[:-1]

				t = str(elem.supplier_invoice_number).replace(' ','')
				t_t = t.split('-')
				r_t2 = ''
				pos = 0
				for t_elem in t_t:
					pos=0
					for t_char in t_elem:
						if t_char == '0':
							pos += 1
						else:
							r_t2 += t_elem[pos:] + '-'
							pos= 0
							break
				r_t2 = r_t2[:-1]

				if r_t == r_t2:				
					raise exceptions.Warning( (u"Número de Documento Duplicado ("+elem.supplier_invoice_number+u")."))  