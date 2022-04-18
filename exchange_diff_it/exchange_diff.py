# -*- coding: utf-8 -*-
from openerp.osv import osv, fields


class exchange_diff_line(osv.osv):
	_name='exchange.diff.line'
	_columns={
		'account_id': fields.many2one('account.account', 'Cuenta'),
		'account_code': fields.related('account_id','code', type="char", relation="account.account", string="Cuenta", store=True),
		'invoice': fields.char('Factura', size=64),
		'partner_id': fields.many2one('res.partner', 'Partner'),
		'type_document_id': fields.many2one('it.type.document', 'Partner'),
		'currency_id': fields.many2one('res.currency', 'Divisa'),
		'debit': fields.float('Debe', digits=(12,2)),
		'credit': fields.float('Haber', digits=(12,2)),
		'saldo': fields.float('Saldo M.N.', digits=(12,2)),
		'amount_currency': fields.float('Monto Act', digits=(12,2)),
		'exchange': fields.float('Tipo Cambio Cierre', digits=(12,3)),
		'amount': fields.float('Monto Act', digits=(12,2)),
		'diff': fields.float('Diferencia', digits=(12,2)),
		'period_id': fields.many2one('account.period', 'Periodo'),
		'current_type': fields.char('Tipo', size=64),
		'exchange_account_id': fields.many2one('account.account', 'Cuenta Ajuste'),
		'exchange_account_code': fields.related('exchange_account_id','code', type="char", relation="account.account", string="Cuenta Ajuste", store=True),
		#'line_id': fields.many2one('exchange.diff', 'Header'),
	}
	
	def make_calculate_differences(self, cr, uid, ids, context):
		#raise osv.except_osv('Alerta','Listo para implemetar el asiento de cambio')
		journal_id = context['journal_id']
		has_extorno = context['has_extorno']
		#Configuracion
		config_obj_id = self.pool.get('exchange.diff.config').search(cr, uid, [])
		if len(config_obj_id) == 0:
			raise osv.except_osv('Alerta','Debe configurar las diferencias de cambio en el menu Contabilidad/Miscelaneous')
		config_obj = self.pool.get('exchange.diff.config').browse(cr, uid, config_obj_id[0], context)
		if config_obj.earn_account_id.id == False:
			raise osv.except_osv('Alerta','Debe configurar una cuenta para las ganancias')
		if config_obj.lose_account_id.id == False:
			raise osv.except_osv('Alerta','Debe configurar una cuenta para las perdidas')
		periodo = None
		periodo_next = None
		total_earn = 0.00	
		total_lose = 0.00	

		cc_earn = []
		cc_earn_ext = []
		cc_lose = []
		cc_lose_ext = []

		for item in self.browse(cr, uid, ids, context):
			if periodo is None:
				periodo = self.pool.get('account.period').browse(cr, uid, item.period_id.id, context)
				periodo_next_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '>', periodo.date_stop)])
				if len(periodo_next_ids) == 0:
					raise osv.except_osv('Alerta','No existe el periodo siguiente a ' + periodo.code)
				periodo_next = self.pool.get('account.period').browse(cr, uid, periodo_next_ids[0], context)
				
			if item.exchange_account_id.id != False:
				if item.exchange_account_id.id == config_obj.lose_account_id.id:
					refund_cc = (0,0,{
							'tax_amount': 0.0, 
							'name': 'Diferencia de Cambio Mensual', 
							'ref': False, 
							'currency_id': item.currency_id.id,
							'debit': 0.00,
							'credit': abs(item.diff), 
							'date_maturity': False, 
							'date': periodo.date_stop,
							'amount_currency':0.00, 
							'account_id': item.account_id.id,
							'partner_id': item.partner_id.id,
							'type_document_id': item.type_document_id.id,
							'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo.code,
							})
					if has_extorno:
						refund_cc_2 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'Extorno Diferencia de Cambio Mensual', 
								'ref': False, 
								'currency_id': item.currency_id.id,
								'debit': abs(item.diff),
								'credit': 0.00,
								'date_maturity': False, 
								'date': periodo_next.date_start,
								'amount_currency':0.00, 
								'account_id': item.account_id.id,
								'partner_id': item.partner_id.id,
								'type_document_id': item.type_document_id.id,
								'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo_next.code,
								})
						cc_lose_ext.append(refund_cc_2)
					cc_lose.append(refund_cc)
					total_lose += abs(item.diff)
				if item.exchange_account_id.id == config_obj.earn_account_id.id:
					#parcho al empleado
					refund_cc = (0,0,{
							'tax_amount': 0.0, 
							'name': 'Diferencia de Cambio Mensual', 
							'ref': False, 
							'currency_id': item.currency_id.id,
							'debit': abs(item.diff),
							'credit': 0.00, 
							'date_maturity': False, 
							'date': periodo.date_stop,
							'amount_currency':0.00, 
							'account_id': item.account_id.id,
							'partner_id': item.partner_id.id,
							'type_document_id': item.type_document_id.id,
							'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo.code,
							})
					if has_extorno:	
						refund_cc_2 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'Diferencia de Cambio Mensual', 
								'ref': False, 
								'currency_id': item.currency_id.id,
								'debit': 0.00,
								'credit': abs(item.diff), 
								'date_maturity': False, 
								'date': periodo_next.date_start,
								'amount_currency':0.00, 
								'account_id': item.account_id.id,
								'partner_id': item.partner_id.id,
								'type_document_id': item.type_document_id.id,
								'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo_next.code,
								})
						cc_earn_ext.append(refund_cc_2)
					cc_earn.append(refund_cc)
					total_earn += abs(item.diff) 

		if len(cc_lose) > 0:
			lose_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': 'Diferencia de Cambio Mensual', 
					'ref': False, 
					'currency_id': False,
					'debit': total_lose,
					'credit': 0.00, 
					'date_maturity': False, 
					'date': periodo.date_stop,
					'amount_currency':0.00, 
					'account_id': config_obj.lose_account_id.id,
					'partner_id': False,
					'type_document_id': False,
					'nro_comprobante': 'DIF. CAM. ' + periodo.code,
					})
			if has_extorno:	
				lose_cc_2 = (0,0,{
						'tax_amount': 0.0, 
						'name': 'Diferencia de Cambio Mensual', 
						'ref': False, 
						'currency_id': False,
						'debit': 0.00,
						'credit': total_lose, 
						'date_maturity': False, 
						'date': periodo_next.date_start,
						'amount_currency':0.00, 
						'account_id': config_obj.lose_account_id.id,
						'partner_id': False,
						'type_document_id': False,
						'nro_comprobante': 'DIF. CAM. ' + periodo_next.code,
						})
				cc_lose_ext.append(lose_cc_2)		
			cc_lose.append(lose_cc)		

		if len(cc_earn) > 0:
			earn_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': 'Diferencia de Cambio Mensual', 
					'ref': False, 
					'currency_id': False,
					'debit': 0.00,
					'credit': total_earn, 
					'date_maturity': False, 
					'date': periodo.date_stop,
					'amount_currency':0.00, 
					'account_id': config_obj.earn_account_id.id,
					'partner_id': False,
					'type_document_id': False,
					'nro_comprobante': 'DIF. CAM. ' + periodo.code,
					})
			if has_extorno:	
				earn_cc_2 = (0,0,{
						'tax_amount': 0.0, 
						'name': 'Diferencia de Cambio Mensual', 
						'ref': False, 
						'currency_id': False,
						'debit': total_earn,
						'credit': 0.00, 
						'date_maturity': False, 
						'date': periodo_next.date_start,
						'amount_currency':0.00, 
						'account_id': config_obj.earn_account_id.id,
						'partner_id': False,
						'type_document_id': False,
						'nro_comprobante': 'DIF. CAM. ' + periodo_next.code,
						})
				cc_earn_ext.append(earn_cc_2)
			cc_earn.append(earn_cc)

		#lst = self.pool.get('account.period').search(cr,uid,[('date_start','<=',fixer.done_date),('date_stop','>=',fixer.done_date)])
		#period_id=lst[0]

		user = self.pool.get('res.users').browse(cr, uid, uid, context)
		journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context)
		# raise osv.except_osv('Alerta', cc)					
		obj_sequence = self.pool.get('ir.sequence')
		id_seq = journal.sequence_id.id

		#Creo el asiento de Ganancias
		if len(cc_earn) > 0:
			name=obj_sequence.next_by_id(cr, uid, id_seq, context)					
			move = {
					'name':name,
					'ref': 'AJUSTE DIF. CAM. ' + periodo.code,
					'line_id': cc_earn,
					'date': periodo.date_stop,
					'journal_id': journal.id,
					'period_id':periodo.id,
					'company_id': user.company_id.id,
				}
			move_obj = self.pool.get('account.move')
			move_id1 = move_obj.create(cr, uid, move, context=None)
			move_id_act=move_id1
			move_obj.post(cr, uid, [move_id1], context=None)
			#ids_move.append(move_id_act)
			if has_extorno:
				name=obj_sequence.next_by_id(cr, uid, id_seq, context)					
				move = {
						'name':name,
						'ref': 'EXTORNO DIF. CAM. ' + periodo_next.code,
						'line_id': cc_earn_ext,
						'date': periodo.date_start,
						'journal_id': journal.id,
						'period_id':periodo_next.id,
						'company_id': user.company_id.id,
					}
				move_obj = self.pool.get('account.move')
				move_id1 = move_obj.create(cr, uid, move, context=None)
				move_id_act=move_id1
				move_obj.post(cr, uid, [move_id1], context=None)

		#Creo el asiento de Perdidas
		if len(cc_lose) > 0:
			name2=obj_sequence.next_by_id(cr, uid, id_seq, context)					
			move2 = {
					'name':name2,
					'ref': 'DIF. CAM. ' + periodo.code,
					'line_id': cc_lose,
					'date': periodo.date_stop,
					'journal_id': journal.id,
					'period_id':periodo.id,
					'company_id': user.company_id.id,
				}
			move_obj2 = self.pool.get('account.move')
			move_id12 = move_obj2.create(cr, uid, move2, context=None)
			move_id_act2=move_id12
			move_obj2.post(cr, uid, [move_id12], context=None)	
			#XD
			if has_extorno:
				name2=obj_sequence.next_by_id(cr, uid, id_seq, context)					
				move2 = {
						'name':name2,
						'ref': 'EXTORNO DIF. CAM. ' + periodo.code,
						'line_id': cc_lose_ext,
						'date': periodo_next.date_start,
						'journal_id': journal.id,
						'period_id':periodo_next.id,
						'company_id': user.company_id.id,
					}
				move_obj2 = self.pool.get('account.move')
				move_id12 = move_obj2.create(cr, uid, move2, context=None)
				move_id_act2=move_id12
				move_obj2.post(cr, uid, [move_id12], context=None)
		return ids

			
	def make_process_records(self, cr, uid, context):
		fiscalyear_id = context['fiscalyear_id']
		period_id = context['period_id']
		tipo = context['type']
		res = []
		#Configuracion
		config_obj_id = self.pool.get('exchange.diff.config').search(cr, uid, [])
		if len(config_obj_id) == 0:
			raise osv.except_osv('Alerta','Debe configurar las diferencias de cambio en el menu Contabilidad/Miscelaneous')

		config_obj = self.pool.get('exchange.diff.config').browse(cr, uid, config_obj_id[0], context)
		#self.current_type = tipo
		#self.period_id = period_id
		if tipo == 'payable':
			periodo = self.pool.get('account.period').browse(cr, uid, period_id, context)
			periods_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<', periodo.date_stop),('fiscalyear_id','=',fiscalyear_id)])
			
			
			account_ids = self.pool.get('account.account').search(cr, uid, [('type','=',tipo),('active','=',True),('currency_id', '!=', False)])
			
			moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('move_id.period_id','in',periods_ids),('move_id.state','!=','draft')])
			
			
			'''
			moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_partial_id', '!=', False),('period_id','in',periods_ids)])
			pay_moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_id', '!=', False),('period_id','in',periods_ids)])
			not_pay_moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_partial_id', '=', False), ('reconcile_id', '=', False), ('period_id','in',periods_ids)])
			'''
			
			#Configuracion
			if config_obj.earn_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las ganancias')
			if config_obj.lose_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las perdidas')
			
			if len(moves_ids) > 0:
				print 'moves'
				fact = {}
				for line in self.pool.get('account.move.line').browse(cr, uid, moves_ids, context):
					'''
					period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', line.date),('date_stop', '>=', line.date)])
					if len(period_ids) == 0:
						raise osv.except_osv('Alerta','No existe un periodo definido para la fecha ' + str(line.date))
					period_obj = self.pool.get('account.period').browse(cr, uid, period_ids[0], context)
					'''
					rate = 0.00
					for dato in config_obj.lines_id:
						if dato.period_id.id == periodo.id:
							rate = dato.venta
							break
					
					print 'o_line', line.partner_id.id
					partner = str(line.partner_id.id) if line.partner_id.id != False else 'NONE_PARTNER'
					print 'partner', partner
					
					print 'o_voucher', line.nro_comprobante 
					voucher = line.nro_comprobante if line.nro_comprobante != False else 'NONE_VOUCHER'
					print 'voucher', voucher
					
					print 'line_doc_type', line.type_document_id
					doc_type = str(line.type_document_id.id) if line.type_document_id.id != False else 'NONE_TYPE'
					print 'doc_type', doc_type

					print 'line_doc_type', line.account_id.id
					accindex = str(line.account_id.id) if line.account_id.id != False else 'NONE_TYPE'
					print 'accindex', accindex
					
					index = voucher + '|' + partner + '|' + doc_type + '|' + accindex
					
					if index in fact:
						if line.credit > 0:
							fact[index]['invoice'] = line.nro_comprobante	
						fact[index]['debit'] += line.debit
						fact[index]['credit'] += line.credit
						fact[index]['saldo'] = fact[index]['credit'] - fact[index]['debit']
						fact[index]['amount_currency'] += line.amount_currency
						fact[index]['amount'] = round(fact[index]['amount_currency'] * fact[index]['exchange'],2)
						fact[index]['diff'] = fact[index]['amount'] - fact[index]['saldo']
						fact[index]['exchange_account_id'] = config_obj.earn_account_id.id if fact[index]['diff'] >= 0 else config_obj.lose_account_id.id,
					else:
						fact.update({index : {
							'account_id': line.account_id.id,
							'invoice': line.nro_comprobante,
							'partner_id': line.partner_id.id,
							'type_document_id': line.type_document_id.id,
							'currency_id': line.currency_id.id,
							'debit': line.debit,
							'credit': line.credit,
							'saldo': line.credit - line.debit,
							'amount_currency': line.amount_currency,
							'exchange': rate,
							'amount': round((line.amount_currency) * rate,2),
							'diff': ((line.amount_currency) * rate) - (line.credit - line.debit),
							'period_id': periodo.id,
							'current_type': tipo,
							'exchange_account_id': config_obj.earn_account_id.id if (((line.amount_currency) * rate) - (line.credit - line.debit)) >= 0 else config_obj.lose_account_id.id,
							#'line_id': obj.id,
						}})
					
				for key, value in fact.items():
					#value['amount_currency'] = abs(value['amount_currency'])
					value['amount'] = -1 * round((value['amount_currency'] * value['exchange']),2)
					value['diff'] = value['amount'] - value['saldo']
					if round(value['diff'],2) != 0:
						value['exchange_account_id'] = config_obj.earn_account_id.id if value['amount'] < value['saldo'] else config_obj.lose_account_id.id
					else:
						value['exchange_account_id'] = False
					ex_line = self.pool.get('exchange.diff.line').create(cr, uid, value, context)
					res.append(ex_line)

			exc = open('/home/manager/reportes/verificar_exchanfe_diff.txt','w')
			exc.write( str(len(res)))
			exc.close()
			
		if tipo == 'receivable':
			periodo = self.pool.get('account.period').browse(cr, uid, period_id, context)
			periods_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<', periodo.date_stop),('fiscalyear_id','=',fiscalyear_id)])
			print 'periodos', periods_ids
			account_ids = self.pool.get('account.account').search(cr, uid, [('type','=',tipo),('currency_id','!=',False),('active','=',True)])
			
			account_ids = self.pool.get('account.account').search(cr, uid, [('type','=',tipo),('active','=',True),('currency_id', '!=', False)])
			moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('move_id.period_id','in',periods_ids),('move_id.state','!=','draft')])
			'''
			moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_partial_id', '!=', False), ('period_id','in',periods_ids)])
			pay_moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_id', '!=', False), ('period_id','in',periods_ids)])
			not_pay_moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_partial_id', '=', False), ('reconcile_id', '=', False), ('period_id','in',periods_ids)])
			'''
			#Configuracion
			if config_obj.earn_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las ganancias')
			if config_obj.lose_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las perdidas')
			
			#raise osv.except_osv('Alerta',moves_ids)
			if len(moves_ids) > 0:
				fact = {}
				for line in self.pool.get('account.move.line').browse(cr, uid, moves_ids, context):
					'''
					period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', line.date),('date_stop', '>=', line.date)])
					if len(period_ids) == 0:
						raise osv.except_osv('Alerta','No existe un periodo definido para la fecha ' + str(line.date))
					period_obj = self.pool.get('account.period').browse(cr, uid, period_ids[0], context)
					'''
					rate = 0.00
					for dato in config_obj.lines_id:
						if dato.period_id.id == periodo.id:
							rate = dato.compra
							break
					
					print 'o_line', line.partner_id.id
					partner = str(line.partner_id.id) if line.partner_id.id != False else 'NONE_PARTNER'
					print 'partner', partner
					
					print 'o_voucher', line.nro_comprobante 
					voucher = line.nro_comprobante if line.nro_comprobante != False else 'NONE_VOUCHER'
					print 'voucher', voucher
					
					print 'line_doc_type', line.type_document_id
					doc_type = str(line.type_document_id.id) if line.type_document_id.id != False else 'NONE_TYPE'
					print 'doc_type', doc_type
					
					print 'line_doc_type', line.account_id.id
					accindex = str(line.account_id.id) if line.account_id.id != False else 'NONE_TYPE'
					print 'accindex', accindex
					
					index = voucher + '|' + partner + '|' + doc_type + '|' + accindex
					
					if index in fact:
						if line.credit > 0:
							fact[index]['invoice'] = line.nro_comprobante	
						fact[index]['debit'] += line.debit
						fact[index]['credit'] += line.credit
						fact[index]['saldo'] = fact[index]['debit'] - fact[index]['credit']
						fact[index]['amount_currency'] += line.amount_currency
						fact[index]['amount'] = round(fact[index]['amount_currency'] * fact[index]['exchange'],2)
						fact[index]['diff'] = fact[index]['amount'] - fact[index]['saldo']
						fact[index]['exchange_account_id'] = config_obj.earn_account_id.id if fact[index]['diff'] >= 0 else config_obj.lose_account_id.id,
					else:
						fact.update({index : {
							'account_id': line.account_id.id,
							'invoice': line.nro_comprobante,
							'partner_id': line.partner_id.id,
							'type_document_id': line.type_document_id.id,
							'currency_id': line.currency_id.id,
							'debit': line.debit,
							'credit': line.credit,
							'saldo': line.debit - line.credit,
							'amount_currency': line.amount_currency,
							'exchange': rate,
							'amount': round((line.amount_currency) * rate,2),
							'diff': ((line.amount_currency) * rate) - (line.debit - line.credit),
							'period_id': periodo.id,
							'current_type': tipo,
							'exchange_account_id': config_obj.earn_account_id.id if (((line.amount_currency) * rate) - (line.debit - line.credit)) >= 0 else config_obj.lose_account_id.id,
							#'line_id': obj.id,
						}})
					
				for key, value in fact.items():
					#value['amount_currency'] = abs(value['amount_currency'])
					value['amount'] = value['amount_currency'] * value['exchange']
					value['diff'] = value['amount'] - value['saldo']
					if round(value['diff'],2) != 0:
						value['exchange_account_id'] = config_obj.lose_account_id.id if value['amount'] < value['saldo'] else config_obj.earn_account_id.id,
					else:
						value['exchange_account_id'] = False
					ex_line = self.pool.get('exchange.diff.line').create(cr, uid, value, context)
					res.append(ex_line)

		if tipo == 'asset':
			periodo = self.pool.get('account.period').browse(cr, uid, period_id, context)
			periods_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<', periodo.date_stop),('fiscalyear_id','=',fiscalyear_id)])
			print 'periodos', periods_ids
			
			type_ids = self.pool.get('account.account.type').search(cr, uid, [('report_type','=',tipo)])
			account_ids = self.pool.get('account.account').search(cr, uid, [('user_type','in',type_ids),('active','=',True), ('currency_id','!=',False), ('type','!=','receivable')])
			moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids),('move_id.period_id','in',periods_ids),('move_id.state','!=','draft')])
			'''
			moves_ids += self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_partial_id', '=', False), ('reconcile_id', '=', False), ('period_id','in',periods_ids)])
			'''
			
			#Configuracion
			if config_obj.earn_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las ganancias')
			if config_obj.lose_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las perdidas')
			
			#raise osv.except_osv('Alerta',moves_ids)
			if len(moves_ids) > 0:
				fact = {}
				for line in self.pool.get('account.move.line').browse(cr, uid, moves_ids, context):
					'''
					period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', line.date),('date_stop', '>=', line.date)])
					if len(period_ids) == 0:
						raise osv.except_osv('Alerta','No existe un periodo definido para la fecha ' + str(line.date))
					period_obj = self.pool.get('account.period').browse(cr, uid, period_ids[0], context)
					'''
					rate = 0.00
					for dato in config_obj.lines_id:
						if dato.period_id.id == periodo.id:
							rate = dato.compra
							break
					
					if line.account_id.id in fact:
						if line.credit > 0:
							fact[line.account_id.id]['invoice'] = line.nro_comprobante	
						fact[line.account_id.id]['debit'] += line.debit
						fact[line.account_id.id]['credit'] += line.credit
						fact[line.account_id.id]['saldo'] = fact[line.account_id.id]['debit'] - fact[line.account_id.id]['credit']
						fact[line.account_id.id]['amount_currency'] += line.amount_currency
						fact[line.account_id.id]['amount'] = fact[line.account_id.id]['amount_currency'] * fact[line.account_id.id]['exchange']
						fact[line.account_id.id]['diff'] = fact[line.account_id.id]['amount'] - fact[line.account_id.id]['saldo']
						fact[line.account_id.id]['exchange_account_id'] = config_obj.earn_account_id.id if fact[line.account_id.id]['diff'] >= 0 else config_obj.lose_account_id.id,
					else:
						fact.update({line.account_id.id : {
							'account_id': line.account_id.id,
							'invoice': line.nro_comprobante,
							'partner_id': line.partner_id.id,
							'type_document_id': line.type_document_id.id,
							'currency_id': line.currency_id.id,
							'debit': line.debit,
							'credit': line.credit,
							'saldo': line.debit - line.credit,
							'amount_currency': line.amount_currency,
							'exchange': rate,
							'amount': (line.amount_currency) * rate,
							'diff': ((line.amount_currency) * rate) - (line.debit - line.credit),
							'period_id': periodo.id,
							'current_type': tipo,
							'exchange_account_id': config_obj.earn_account_id.id if (((line.amount_currency) * rate) - (line.debit - line.credit)) >= 0 else config_obj.lose_account_id.id,
							#'line_id': obj.id,
						}})
					
				for key, value in fact.items():
					#value['amount_currency'] = abs(value['amount_currency'])
					value['amount'] = value['amount_currency'] * value['exchange']
					value['diff'] = value['amount'] - value['saldo']
					if round(value['diff'],2) != 0:
						value['exchange_account_id'] = config_obj.lose_account_id.id if value['amount'] < value['saldo'] else config_obj.earn_account_id.id,
					else:
						value['exchange_account_id'] = False
					ex_line = self.pool.get('exchange.diff.line').create(cr, uid, value, context)
					res.append(ex_line)
					
		if tipo == 'liability':
			periodo = self.pool.get('account.period').browse(cr, uid, period_id, context)
			periods_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<', periodo.date_stop),('fiscalyear_id','=',fiscalyear_id)])
			print 'periodos', periods_ids
			
			type_ids = self.pool.get('account.account.type').search(cr, uid, [('report_type','=',tipo)])
			account_ids = self.pool.get('account.account').search(cr, uid, [('user_type','in',type_ids),('type','!=','payable'), ('active','=',True), ('currency_id','!=',False)])
			moves_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('move_id.period_id','in',periods_ids),('move_id.state','!=','draft')])
			'''
			moves_ids += self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids), ('currency_id', '!=', False), ('reconcile_partial_id', '=', False), ('reconcile_id', '=', False), ('period_id','in',periods_ids)])
			'''
			#Configuracion
			if config_obj.earn_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las ganancias')
			if config_obj.lose_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las perdidas')
			
			#raise osv.except_osv('Alerta',moves_ids)
			if len(moves_ids) > 0:
				fact = {}
				for line in self.pool.get('account.move.line').browse(cr, uid, moves_ids, context):
					'''
					period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', line.date),('date_stop', '>=', line.date)])
					if len(period_ids) == 0:
						raise osv.except_osv('Alerta','No existe un periodo definido para la fecha ' + str(line.date))
					period_obj = self.pool.get('account.period').browse(cr, uid, period_ids[0], context)
					'''
					rate = 0.00
					for dato in config_obj.lines_id:
						if dato.period_id.id == periodo.id:
							rate = dato.venta
							break
					
					if line.account_id.id in fact:
						if line.credit > 0:
							fact[line.account_id.id]['invoice'] = line.nro_comprobante	
						fact[line.account_id.id]['debit'] += line.debit
						fact[line.account_id.id]['credit'] += line.credit
						fact[line.account_id.id]['saldo'] = fact[line.account_id.id]['debit'] - fact[line.account_id.id]['credit']
						fact[line.account_id.id]['amount_currency'] += line.amount_currency
						fact[line.account_id.id]['amount'] = fact[line.account_id.id]['amount_currency'] * fact[line.account_id.id]['exchange']
						fact[line.account_id.id]['diff'] = fact[line.account_id.id]['amount'] - fact[line.account_id.id]['saldo']
						fact[line.account_id.id]['exchange_account_id'] = config_obj.earn_account_id.id if fact[line.account_id.id]['diff'] >= 0 else config_obj.lose_account_id.id,
					else:
						fact.update({line.account_id.id : {
							'account_id': line.account_id.id,
							'invoice': line.nro_comprobante,
							'partner_id': line.partner_id.id,
							'type_document_id': line.type_document_id.id,
							'currency_id': line.currency_id.id,
							'debit': line.debit,
							'credit': line.credit,
							'saldo': line.debit - line.credit,
							'amount_currency': line.amount_currency,
							'exchange': rate,
							'amount': round((line.amount_currency) * rate,2),
							'diff': ((line.amount_currency) * rate) - (line.debit - line.credit),
							'period_id': periodo.id,
							'current_type': tipo,
							'exchange_account_id': config_obj.earn_account_id.id if (((line.amount_currency) * rate) - (line.debit - line.credit)) >= 0 else config_obj.lose_account_id.id,
							#'line_id': obj.id,
						}})
					
				for key, value in fact.items():
					#value['amount_currency'] = abs(value['amount_currency'])
					value['amount'] = -1 * round((value['amount_currency'] * value['exchange']),2)
					value['diff'] = value['amount'] - value['saldo']
					if round(value['diff'],2) != 0:
						value['exchange_account_id'] = config_obj.earn_account_id.id if value['amount'] < value['saldo'] else config_obj.lose_account_id.id,
					else:
						value['exchange_account_id'] = False
					ex_line = self.pool.get('exchange.diff.line').create(cr, uid, value, context)
					res.append(ex_line)
			
		return res

