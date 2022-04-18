# -*- coding: utf-8 -*-
import pprint

from openerp.osv import osv
from openerp import models, fields, api


class account_journal(models.Model):
	_inherit='account.journal'

	sequence_transference = fields.Many2one('ir.sequence','Recibo interno Caja')
	

class account_transfer(models.Model):
	_name = 'account.transfer'

	STATE_SELECTION = [
		('draft', 'Borrador'),
		('done', 'Transferido'),
		('cancel', 'Cancelado')
	]

	#@api.depends('origen_amount', 'origen_journal_id', 'destiny_journal_id', 'destiny_exchange', 'date')
	
	'''
	@api.onchange('origen_journal_id')
	def _onchange_origen_journal_id(self):
		if self.origen_journal_id:
			if self.origen_journal_id.currency.id != False:
				if deliver.destiny_journal_id.currency.id != False:
					self.currency_id.id = deliver.origen_journal_id.currency.id
				else:
					self.currency_id.id = deliver.origen_journal_id.currency.id
			else:
				if deliver.destiny_journal_id.currency.id != False:
					self.currency_id.id = deliver.destiny_journal_id.currency.id
				else:
					self.currency_id.id = deliver.origen_journal_id.currency.id
					
	@api.onchange('destiny_journal_id')
	def _onchange_destiny_journal_id(self):
		if self.origen_journal_id:
			if self.origen_journal_id.currency.id != False:
				if deliver.destiny_journal_id.currency.id != False:
					self.currency_id.id = deliver.origen_journal_id.currency.id
				else:
					self.currency_id.id = deliver.origen_journal_id.currency.id
			else:
				if deliver.destiny_journal_id.currency.id != False:
					self.currency_id.id = deliver.destiny_journal_id.currency.id
				else:
					self.currency_id.id = deliver.origen_journal_id.currency.id
	
	'''
		
	@api.multi
	def _refund_amount(self):
		if self.origen_journal_id.currency.id != False:
			if self.destiny_journal_id.currency.id != False:
				self.destiny_amount = self.origen_amount
			else:
				if self.destiny_exchange == 0:
					self.destiny_amount = self.origen_amount * self.origen_exchange
				else:
					self.destiny_amount = self.origen_amount * self.destiny_exchange
		else:
			if self.destiny_journal_id.currency.id != False:
				if self.destiny_exchange == 0:
					self.destiny_amount = self.origen_amount / self.origen_exchange
				else:
					self.destiny_amount = self.origen_amount / self.destiny_exchange
			else:
				self.destiny_amount = self.origen_amount

	
	@api.onchange('origen_amount', 'origen_journal_id', 'destiny_journal_id', 'destiny_exchange', 'date')
	def _refund_amount(self):
		if self.origen_journal_id.id:
			if self.origen_journal_id.sequence_transference.id:
				t = self.origen_journal_id.sequence_transference
				self.doc_origen = t.prefix + (str(t.number_next_actual)).rjust(t.padding,'0')


		if self.origen_journal_id.id:
			if self.origen_journal_id.sequence_transference.id:
				t = self.origen_journal_id.sequence_transference
				self.doc_origen = t.prefix + (str(t.number_next_actual)).rjust(t.padding,'0')

		for deliver in self:
			if deliver.origen_journal_id.currency.id != False:
				if deliver.destiny_journal_id.currency.id != False:
					self.destiny_amount = self.origen_amount
					#self.currency_id = deliver.origen_journal_id.currency
					if self.destiny_exchange == 0:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',self.date), ('currency_id','=', self.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						rate = currency_rate[0].type_sale
						self.origen_exchange = rate
					else:
						rate = self.destiny_exchange
						self.origen_exchange = 0.00
				else:
					if self.destiny_exchange == 0:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',self.date), ('currency_id','=', self.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						rate = currency_rate[0].type_sale
						self.origen_exchange = rate
						self.destiny_exchange = 0.00
						self.destiny_amount = self.origen_amount * self.origen_exchange
						self.currency_id = deliver.origen_journal_id.currency
					else:
						rate = self.destiny_exchange
						self.origen_exchange = 0.00
						self.destiny_amount = self.origen_amount * self.destiny_exchange
						self.currency_id = deliver.origen_journal_id.currency
			else:
				if deliver.destiny_journal_id.currency.id != False:
					if self.destiny_exchange == 0:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',self.date), ('currency_id','=', self.destiny_journal_id.currency.id)])
						if len(currency_rate) == 0:
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						rate = currency_rate[0].type_sale
						self.origen_exchange = rate
						self.destiny_amount = self.origen_amount / self.origen_exchange
						self.currency_id = deliver.destiny_journal_id.currency
					else:
						rate = self.destiny_exchange
						self.origen_exchange = 0.00
						self.destiny_amount = self.origen_amount / self.destiny_exchange
						self.currency_id = deliver.destiny_journal_id.currency
				else:
					self.destiny_amount = self.origen_amount
					self.currency_id = False
	
	name = fields.Char('Nombre',size=50, default='Transferencia Borrador')
	date = fields.Date('Fecha de Entrega')
	company_id = fields.Many2one('res.company','Compania')
	currency_id = fields.Many2one('res.currency','Moneda', default=False)
	doc_origen = fields.Char('Doc. Origen',size=30)
	doc_destiny = fields.Char('Doc. Destino',size=30)
	glosa = fields.Char('Glosa',size=50)
	origen_journal_id = fields.Many2one('account.journal','Caja Origen')
	origen_amount = fields.Float('Monto Origen', digits=(12,2))
	origen_exchange = fields.Float('T.C. Oficial', digits=(12,3))
	destiny_journal_id = fields.Many2one('account.journal','Caja Destino')
	destiny_amount = fields.Float('Monto Destino', digits=(12,2), compute='_refund_amount')
	destiny_exchange = fields.Float('T.C. Personalizado', digits=(12,4))
	done_move = fields.Many2many('account.move', 'transfer_account_move_rel', 'transfer_id', 'account_move_id', string="Asiento de Transferencia", readonly=True)
	state = fields.Selection(STATE_SELECTION, 'Status', readonly=True, select=True, default='draft')


	name_move_1 = fields.Char('Name Move 1',copy=False)
	move_move_1_id = fields.Many2one('account.move','Asiento 1',copy=False)
	name_move_2 = fields.Char('Name Move 2',copy=False)
	move_move_2_id = fields.Many2one('account.move','Asiento 2',copy=False)
	period_id_move_id = fields.Many2one('account.period','Periodo',copy=False)



	@api.multi
	def unlink(self):
		if self.name_move_1 or self.name_move_2:
			raise osv.except_osv('Acción Inválida!', 'No se puede eliminar una transferencia ya validada.')
		return super(account_transfer,self).unlink()

	@api.multi
	def action_cancel(self):

		if self.origen_journal_id.id:
			if self.origen_journal_id.sequence_transference.id:
				t = self.origen_journal_id.sequence_transference
				self.doc_origen = t.next()


		for transfer in self:
			if transfer.state == 'done':
				self.write({'state': 'draft'})
				for move in transfer.done_move:
					self.pool.get('account.move').write(self.env.cr,self.env.uid,[move.id],{'state': 'draft'},self.env.context)
					move.unlink()
					#lines_ids = self.pool.get('account.move.line').search(self.env.cr, self.env.uid, [('move_id', '=', move.id)])
					#self.pool.get('account.move.line').unlink(self.env.cr,self.env.uid,lines_ids,self.env.context)
					"""
					print 'TO_DELETE_ID', move.id
					vals = {
						'tax_amount': 0.0, 
						'name': 'ANULADO', 
						'ref': False,
						'nro_comprobante': False,
						'currency_id': move.journal_id.currency.id, 
						'debit': 0,
						'credit': 0, 
						'date_maturity': False, 
						'date': move.date,
						'amount_currency': 0, 
						'account_id': move.journal_id.default_debit_account_id.id,
						'partner_id': False,
						'move_id': move.id,
					}
					new_line = self.pool.get('account.move.line').create(self.env.cr, self.env.uid, vals, self.env.context)
					print 'New Line', new_line
					self.pool.get('account.move').post(self.env.cr, self.env.uid, [move.id], context=None)
					
					self.env.cr.execute(""delete from transfer_account_move_rel where account_move_id ='"" + str(move.id) + ""'"")
					"""
				return True
	
	@api.multi
	def aprove(self):
		ids_move = []
		for transfer in self:

			name_tmp= 'None'
			if transfer.name == 'Transferencia Borrador':
				name_tmp = self.pool.get('ir.sequence').get(self.env.cr, self.env.uid, 'account.transfer') or '/'
			else:
				name_tmp = transfer.name

			transfer.write({'name':name_tmp})
			transfer.refresh()
			#Validate debit and internal account
			if transfer.origen_journal_id.default_debit_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Origen debe tener configurada una cuenta de Debito por defecto.')
			if transfer.origen_journal_id.internal_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Origen debe tener configurada una cuenta de Transferencias.')
			if transfer.destiny_journal_id.default_debit_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Destino debe tener configurada una cuenta de Debito por defecto.')
			if transfer.destiny_journal_id.internal_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Destino debe tener configurada una cuenta de Transferencias.')
			
			user = self.env['res.users'].browse(self.env.uid)
			
			amount_origin = 0.00
			amount_currency_origin = 0.00
			currency_rate_origin = 0.00
			
			amount_destiny = 0.00
			amount_currency_destiny = 0.00
			currency_rate_destiny = 0.00
			
			res_currency_id = self.env['main.parameter'].search([])[0].currency_id
			
			#Si el origen es en dolares
			if transfer.origen_journal_id.currency.id != False:
				if transfer.destiny_journal_id.currency.id != False:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = transfer.origen_amount
					amount_currency_destiny = transfer.destiny_amount
					amount_origin = transfer.origen_amount * currency_rate_origin
					amount_destiny = transfer.destiny_amount * currency_rate_destiny
				else:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = transfer.origen_amount
					amount_currency_destiny = 0.00
					amount_origin = transfer.origen_amount * currency_rate_origin
					amount_destiny = transfer.destiny_amount
			#Si el origen es en soles
			else:
				if transfer.destiny_journal_id.currency.id != False:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = 0.00
					amount_currency_destiny = transfer.destiny_amount
					amount_origin = transfer.origen_amount
					amount_destiny = transfer.origen_amount
				else:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = 0.00
					amount_currency_destiny = 0.00
					amount_origin = transfer.origen_amount
					amount_destiny = transfer.destiny_amount
			
			
			'''
			amount_origin = transfer.origen_amount
			amount_currency_origin = 0.00
			currency_rate_origin = 0.00
			if transfer.origen_journal_id.currency.id != False:
				currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
				if len(currency_rate) == 0:
					raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
				currency_rate_origin = currency_rate[0].type_sale
				if transfer.destiny_exchange != 0:
					currency_rate_origin = transfer.destiny_exchange
				amount_currency_origin = amount_origin
				amount_origin = transfer.origen_amount * currency_rate_origin 
			
			amount_destiny = transfer.destiny_amount
			amount_currency_destiny = 0.00
			currency_rate_destiny = 0.00
			if transfer.destiny_journal_id.currency.id != False:
				currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.destiny_journal_id.currency.id)])
				if len(currency_rate) == 0:
					raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
				currency_rate_destiny = currency_rate[0].type_sale
				if transfer.destiny_exchange != 0:
					currency_rate_destiny = transfer.destiny_exchange
				amount_currency_destiny = amount_destiny
				amount_destiny = transfer.destiny_amount * currency_rate_destiny 
			'''	
			cc = []
			#Ingreso la devolucion
			refund_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False,
					'nro_comprobante': transfer.doc_origen,
					'currency_id': transfer.origen_journal_id.currency.id, 
					'debit': 0.00,
					'credit': amount_origin, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': -1 * amount_currency_origin,
					'account_id': transfer.origen_journal_id.default_debit_account_id.id,
					'currency_rate_it': currency_rate_origin,
					})
			cc.append(refund_cc)

			#parcho al empleado
			employee_fix_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False, 
					'nro_comprobante': transfer.doc_origen,
					'currency_id': False, 
					'debit': amount_origin,
					'credit': 0.00, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': 0.00, 
					'account_id': transfer.origen_journal_id.internal_account_id.id,
					'currency_rate_it': currency_rate_origin,
					})
			cc.append(employee_fix_cc)
			lst = self.env['account.period'].search([('date_start','<=',transfer.date),('date_stop','>=',transfer.date)])
			period_id=lst[0]
			# raise osv.except_osv('Alerta', cc)					
			obj_sequence = self.pool.get('ir.sequence')
			id_seq = transfer.origen_journal_id.sequence_id.id


			name = None
			if transfer.period_id_move_id.id != period_id.id:
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
				self.write({'name_move_1': name, 'period_id_move_id':period_id.id})
			else:
									
				if transfer.name_move_1 == False:
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
					self.write({'name_move_1': name})
				else:
					name = transfer.name_move_1

			"""
			context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
			name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)					
			"""

			move = {
					'name':name,
					'ref': transfer.name,
					'line_id': cc,
					'date': transfer.date,
					'journal_id': transfer.origen_journal_id.id,
					'period_id':period_id.id,
					'company_id': user.company_id.id,
				}
			move_obj = self.pool.get('account.move')
			move_id1 = move_obj.create(self.env.cr, self.env.uid, move, context=None)

			self.write({'move_move_1_id':move_id1})

			move_id_act=move_id1
			move_obj.post(self.env.cr, self.env.uid, [move_id1], context=None)
			ids_move.append(move_id_act)

			#Asiento de vuelta
			cc2 = []
			#Ingreso la devolucion
			refund_cc2 = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False,
					'nro_comprobante': transfer.doc_destiny,
					'currency_id': transfer.destiny_journal_id.currency.id, 
					'debit': amount_destiny,
					'credit': 0, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': amount_currency_destiny, 
					'account_id': transfer.destiny_journal_id.default_debit_account_id.id,
					'currency_rate_it': currency_rate_destiny,
					})
			cc2.append(refund_cc2)

			#parcho al empleado
			employee_fix_cc2 = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False, 
					'nro_comprobante': transfer.doc_destiny,
					'currency_id': False, 
					'debit': 0,
					'credit': amount_destiny, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': 0.00, 
					'account_id': transfer.destiny_journal_id.internal_account_id.id,
					'currency_rate_it': currency_rate_destiny,
					})
			cc2.append(employee_fix_cc2)
			#lst2 = self.env['account.period'].search([('date_start','<=',transfer.date),('date_stop','>=',transfer.date)])
			#period_id=lst2[0]
			# raise osv.except_osv('Alerta', cc)					
			obj_sequence = self.pool.get('ir.sequence')
			id_seq2 = transfer.destiny_journal_id.sequence_id.id
			context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}


			name2 = None
			if transfer.period_id_move_id.id != period_id.id:
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
				self.write({'name_move_2': name2, 'period_id_move_id':period_id.id})
			else:
									
				if transfer.name_move_2 == False:
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
					self.write({'name_move_2': name2})
				else:
					name2 = transfer.name_move_2

			"""
			name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
			"""

			move2 = {
					'name':name2,
					'ref': transfer.name,
					'line_id': cc2,
					'date': transfer.date,
					'journal_id': transfer.destiny_journal_id.id,
					'period_id':period_id.id,
					'company_id': user.company_id.id,
				}
			move_obj2 = self.pool.get('account.move')
			move_id12 = move_obj.create(self.env.cr, self.env.uid, move2, context=None)


			self.write({'move_move_2_id':move_id12})
			move_id_act2=move_id12
			move_obj2.post(self.env.cr, self.env.uid, [move_id12], context=None)
			ids_move.append(move_id_act2)
			
			self.write({'state' : 'done', 'done_move': [(6, 0, ids_move)]})	