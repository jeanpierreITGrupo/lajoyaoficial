# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp import http
from openerp.osv import osv

class checkera_sequence(models.Model):
	_name = 'checkera.sequence'

	sequence_id = fields.Many2one('ir.sequence','Secuencia')
	journal_id = fields.Many2one('account.journal','Diario')
	_rec_name='sequence_id'



class girar_checkera(models.TransientModel):
	_name = 'girar.checkera'

	@api.one
	def do_rebuild(self):
		if self.env.context['origen']=='transferencia':
			trans = self.env['account.transfer'].browse(self.env.context['id_origen'])
			trans.girar_checke()
		elif self.env.context['origen']== 'delivery':
			pago = self.env['deliveries.to.pay'].search([('id','=',self.env.context['id_origen'])])[0]
			pago.girar_checke()
		elif self.env.context['origen']== 'pago':
			pago = self.env['account.voucher'].search([('id','=',self.env.context['id_origen'])])[0]
			pago.girar_checke()
		else:
			asiento = self.env['account.move'].search([('id','=',self.env.context['id_origen'])])[0]
			asiento.girar_checke()


class account_voucher(models.Model):
	_inherit = 'account.voucher'
	
	checkera_sequence_id = fields.Many2one('checkera.sequence','Secuencia de Chequera')
	type_journal = fields.Selection(string='Tipo Journal', related='journal_id.type')

	@api.multi
	def girar_chequera(self):
		return {            
			'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'girar.checkera',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'origen':'pago','id_origen':self.id},
        }


	@api.multi
	def girar_chequera2(self):
		self.girar_checke()
		i_id = self.env['account.invoice'].search([('id','=',self.env.context['invoice_id'])])[0]
		t = i_id.invoice_pay_customer()
		t['res_id']=self.id
		return t



	@api.one
	def girar_checke(self):
		flag = False
		if self.checkera_sequence_id.id and self.state == 'draft':
			if self.checkera_sequence_id.sequence_id.id:
				if self.journal_id.type == 'bank':
					flag = True
		if flag == True:
			self.reference = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, self.checkera_sequence_id.sequence_id.id, self.env.context)
		else:
			raise osv.except_osv('Alerta','No se pudo girar la chequera, verifique si la chequera tiene su sequencia.') 

	@api.one
	def action_move_line_create(self):
		t = super(account_voucher,self).action_move_line_create()
		if self.checkera_sequence_id.id:
			if self.checkera_sequence_id.sequence_id.id:
				if self.journal_id.type == 'bank':
					self.move_id.write({'checkera_sequence_id':self.checkera_sequence_id.id})
		return t

class account_move(models.Model):
	_inherit='account.move'
	
	checkera_sequence_id = fields.Many2one('checkera.sequence','Secuencia de Chequera')
	type_journal = fields.Selection(string='Tipo Journal', related='journal_id.type')


	@api.multi
	def girar_chequera(self):
		return {            
			'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'girar.checkera',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'origen':'asiento','id_origen':self.id},
        }
	@api.one
	def girar_checke(self):
		flag = False
		if self.checkera_sequence_id.id and self.state == 'draft':
			if self.checkera_sequence_id.sequence_id.id:
				if self.journal_id.type == 'bank':
					flag = True
		if flag == True:
			self.ref = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, self.checkera_sequence_id.sequence_id.id, self.env.context)
		else:
			raise osv.except_osv('Alerta','No se pudo girar la chequera, verifique si la chequera tiene su sequencia.') 




class account_transfer(models.Model):
	_inherit='account.transfer'
	
	checkera_sequence_id = fields.Many2one('checkera.sequence','Secuencia de Chequera')
	type_journal = fields.Selection(string='Tipo Journal', related='origen_journal_id.type')


	@api.multi
	def girar_chequera(self):
		return {            
			'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'girar.checkera',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'origen':'transferencia','id_origen':self.id},
        }
	@api.one
	def girar_checke(self):
		flag = False
		if self.checkera_sequence_id.id and self.state == 'draft':
			if self.checkera_sequence_id.sequence_id.id:
				if self.origen_journal_id.type == 'bank':
					flag = True
		if flag == True:
			self.doc_origen = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, self.checkera_sequence_id.sequence_id.id, self.env.context)
		else:
			raise osv.except_osv('Alerta','No se pudo girar la chequera, verifique si la chequera tiene su sequencia.') 





class deliveries_to_pay(models.Model):
	_inherit='deliveries.to.pay'
	
	checkera_sequence_id = fields.Many2one('checkera.sequence','Secuencia de Chequera')
	type_journal = fields.Selection(string='Tipo Journal', related='deliver_journal_id.type')


	@api.multi
	def girar_chequera(self):
		return {            
			'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'girar.checkera',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'origen':'delivery','id_origen':self.id},
        }
	@api.one
	def girar_checke(self):
		flag = False
		if self.checkera_sequence_id.id and self.state == 'draft':
			if self.checkera_sequence_id.sequence_id.id:
				if self.deliver_journal_id.type == 'bank':
					flag = True
		if flag == True:
			self.invoice_number = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, self.checkera_sequence_id.sequence_id.id, self.env.context)
		else:
			raise osv.except_osv('Alerta','No se pudo girar la chequera, verifique si la chequera tiene su sequencia.') 




		""" @api.onchange('checkera_sequence_id')
	def onchange_checkera_sequence_id(self):
		if self.checkera_sequence_id.id:
			next_number = self.checkera_sequence_id.sequence_id.number_next_actual

			prefix = self.checkera_sequence_id.sequence_id.prefix if self.checkera_sequence_id.sequence_id.prefix else ''
			padding = self.checkera_sequence_id.sequence_id.padding
			self.ref = prefix + "0"*(padding - len(str(next_number))) + str(next_number)


	@api.one
	def button_validate(self):
		t = super(account_move,self).button_validate()
		if self.checkera_sequence_id.id:
			if self.checkera_sequence_id.sequence_id.id:
				if self.journal_id.type == 'bank':
					name=self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, self.checkera_sequence_id.sequence_id.id, self.env.context)
		return t




class account_voucher(models.Model):
	_inherit = 'account.voucher'
	
	checkera_sequence_id = fields.Many2one('checkera.sequence','Secuencia de Chequera')
	type_journal = fields.Selection(string='Tipo Journal', related='journal_id.type')


	@api.onchange('checkera_sequence_id')
	def onchange_checkera_sequence_id(self):
		if self.checkera_sequence_id.id:
			next_number = self.checkera_sequence_id.sequence_id.number_next_actual

			prefix = self.checkera_sequence_id.sequence_id.prefix if self.checkera_sequence_id.sequence_id.prefix else ''
			padding = self.checkera_sequence_id.sequence_id.padding
			self.reference = prefix + "0"*(padding - len(str(next_number))) + str(next_number)


	@api.one
	def action_move_line_create(self):
		t = super(account_voucher,self).action_move_line_create()
		if self.checkera_sequence_id.id:
			if self.checkera_sequence_id.sequence_id.id:
				if self.journal_id.type == 'bank':
					name=self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, self.checkera_sequence_id.sequence_id.id, self.env.context)
					self.move_id.write({'checkera_sequence_id':self.checkera_sequence_id.id})
		return t"""

		
		"""@api.model
		def create(self,vals):
			t = super(account_voucher,self).create(vals)
			if t.checkera_sequence_id.id:
				jm = self.env['account.voucher'].search([('journal_id','=',t.journal_id.id),('reference','=',t.reference),('id','!=',t.id)])
				if len(jm)> 0:
					raise osv.except_osv('Alerta','Existe otro cheque con el mismo número')
			return t"""