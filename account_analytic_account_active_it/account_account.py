# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_analytic_account(models.Model):
	_inherit = 'account.analytic.account'

	active = fields.Boolean('Activo',default=True)
	
	
	def _debit_credit_bal_qtty(self, cr, uid, ids, fields, arg, context=None):
		return
		cr.execute(""" select id from account_analytic_account where coalesce(active,false) = false """)
		tol = cr.fetchall()
		elem = [-1,-1,-1]
		for i in tol:
			elem.append(i[0])

		cr.execute(""" update account_analytic_account set active = true """)
		t = super(account_analytic_account,self)._debit_credit_bal_qtty(cr, uid, ids, fields, arg, context)		
		cr.execute(""" update account_analytic_account set active = false where id in """ + str( tuple(elem) ) )
		return t