# -*- coding: utf-8 -*-
import pprint

from openerp.osv import osv
from openerp import models, fields, api

class account_move_line(models.Model):
	_inherit = 'account.move.line'
	
	small_cash_id = fields.Many2one('small.cash.another', string="Caja Chica ID")
	small_cash_name = fields.Char('Caja Chica', size=64)

	def write(self, cr, uid, ids, vals, context=None, check=False):
		if 'small_cash_id' in vals:
			small_cash = self.pool.get('small.cash.another').browse(cr, uid, vals['small_cash_id'], context)
			vals.update({'small_cash_name': small_cash.name})
		return super(account_move_line, self).write(cr, uid, ids, vals, context, check)
	'''
	def write(self, cr, uid, ids, vals, context=None, check=False):
		print 'Move Data Edit SMALL CASH'
		pprint.pprint(vals)
		for move in self.browse(cr, uid, ids, context):
			journal = vals['journal_id'] if 'journal_id' in vals else move.journal_id
			
			if journal.max_import_cash != 0 or journal.max_import_cash != False:
				cr.execute("""
					SELECT 
						SUM(aml.debit - aml.credit) AS saldo
					FROM 
						account_move_line AS aml JOIN
						account_move AS am ON aml.move_id = am.id JOIN
						account_journal AS aj ON am.journal_id = aj.id JOIN
						account_period AS ap ON am.period_id = ap.id
					WHERE
						am.date <= '""" + move.date +"""' AND
						aml.account_id = """ + str(journal.default_debit_account_id.id) + """ AND
						aj.id = """ + str(journal.id) +"""
					GROUP BY
						aj.name
				""")
				
				dr = cr.dictfetchall()
				pprint.pprint(dr)
				saldo = dr[0]['saldo']
				print 'SALDO', saldo
				for line in move.line_id:
					if line.account_id.id == journal.default_debit_account_id.id:
						if line.debit > 0:
							if (line.debit + saldo) > journal.max_import_cash:
								raise osv.except_osv('Alerta','No se peude exceder el monto limite de la Caja ' + journal.name)
			
		return super(account_move, self).write(cr, uid, ids, vals, context)
		
	'''
	'''
	def write(self, cr, uid, ids, vals, context=None, check=False):
		print 'Move Data Edit SMALL CASH'
		pprint.pprint(vals)
		for line in self.browse(cr, uid, ids, context):
			journal = vals['journal_id'] if 'journal_id' in vals else line.move_id.journal_id
			
			if journal.max_import_cash != 0 or journal.max_import_cash != False:
				print 'DATE', line.move_id.date
				print 'CUENTA', journal.default_debit_account_id.id
				print 'DIARIO', journal.id
				print 'PERIODO', line.move_id.period_id.id
				cr.execute("""
					SELECT 
						aj.name,
						SUM(aml.debit) AS debit,
						SUM(aml.credit) AS credit,
						SUM(aml.debit - aml.credit) AS saldo
					FROM 
						account_move_line AS aml JOIN
						account_move AS am ON aml.move_id = am.id JOIN
						account_journal AS aj ON am.journal_id = aj.id JOIN
						account_period AS ap ON am.period_id = ap.id
					WHERE
						am.date <= '""" + line.move_id.period_id.date_stop +"""' AND
						aml.account_id = """ + str(journal.default_debit_account_id.id) + """ AND
						aj.id = """ + str(journal.id) +""" AND
						ap.id = """ + str(line.move_id.period_id.id) + """
					GROUP BY
						aj.name
				""")
				
				dr = cr.dictfetchall()
				pprint.pprint(dr)
				saldo = dr[0]['saldo']
				print 'SALDO', saldo
				
				#if line.account_id.id == journal.default_debit_account_id.id:
				#	if line.debit > 0:
				
				if saldo > journal.max_import_cash:
					raise osv.except_osv('Alerta','No se peude exceder el monto limite de la Caja ' + journal.name)
			
		return super(account_move_line, self).write(cr, uid, ids, vals, context)
	'''