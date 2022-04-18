# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
from openerp.tools.translate import _

import pprint

class account_move_line(osv.osv):
	_name='account.move.line'
	_inherit='account.move.line'
	
	_columns = {
		'debit_me': fields.float('Debe M.E', digits=(12,2)),
		'credit_me': fields.float('Haber M.E', digits=(12,2)),
		'square_flag': fields.boolean('Cuadre'),
	}

	_defaults={
		'debit_me':0,
		'credit_me':0,
		'square_flag': False,
	}
	
	def update_me_fields(self, cr, uid, context):
		period_id = context['period_id']
		parameters_ids = self.pool.get('main.parameter').search(cr, uid, [])
		if len(parameters_ids) == 0:
			raise osv.except_osv('Alerta!', 'No existe el objeto Parametros Generales en su sistema! Contacte a su administrador!')
		currency_id = self.pool.get('main.parameter').browse(cr, uid, parameters_ids[0], context).currency_id
		print 'UPDATE START'
		moves_ids = self.pool.get('account.move').search(cr, uid, [('period_id','=',period_id)])
		lines_ids = self.search(cr, uid, [('move_id','in',moves_ids)])
		maxl = len(lines_ids)
		print 'TOTAL A PROCESAR', maxl
		i = 1
		for line in self.browse(cr, uid, lines_ids, context):
			print i
			if line.square_flag:
				cr.execute("""
					DELETE FROM account_move_line WHERE id = """ + str(line.id)+ """
				""")
			else:
				vals = {}
				currency = line.currency_id
				currency_rate_it = line.currency_rate_it
				amount_currency = line.amount_currency
				date = line.date
				debit = line.debit
				credit = line.credit
				
				if currency_rate_it == False or currency_rate_it == 0.00:
					rate_ids = self.pool.get('res.currency.rate').search(cr, uid,[('currency_id','=',currency_id.id),('name','=',date)])
					if len(rate_ids) == 0:
						currency_rate_it = 0.00
						#raise osv.except_osv('Alerta!', 'No existe un tipo de cambio para la fecha indicada.')
					else:
						rate = self.pool.get('res.currency.rate').browse(cr, uid, rate_ids, context)
						currency_rate_it = rate[0].type_sale

				
				debit_me = 0.00
				credit_me = 0.00
				
				if amount_currency == False or amount_currency == 0:
					user = self.pool.get('res.users').browse(cr, uid, uid, context)
					debit_me = debit/currency_rate_it if currency_rate_it != 0.00 else 0.00
					credit_me = credit/currency_rate_it if currency_rate_it != 0.00 else 0.00
				else:
					debit_me = amount_currency if debit != 0.00 else 0.00
					credit_me = abs(amount_currency) if credit != 0.00 else 0.00
				#vals.update({'rate': currency_rate_it, 'debit_me': debit_me, 'credit_me': credit_me, 'amount_currency': amount_currency,'currency_id' : currency.id})
				#pprint.pprint(vals)
				#self.pool.get('account.move.line').write(cr, uid, [line.id], vals, context)
				cr.execute(""" UPDATE account_move_line 
							SET debit_me = round(""" + str(debit_me)+""",2), credit_me = round(""" + str(credit_me)+""",2), currency_rate_it = """ + str(currency_rate_it)+"""

							WHERE id = """ +str(line.id)+"""
					""")
			i+=1
		
		#self.pool.get('account.move.line').write(cr, uid, lines_ids, {'update_flag':True}, context)
	
account_move_line()