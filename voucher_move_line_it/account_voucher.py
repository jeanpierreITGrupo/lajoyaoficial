# -*- coding: utf-8 -*-

import time
from lxml import etree

from openerp import models, fields, api
from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp

		
class account_voucher(models.Model):
	_inherit = 'account.voucher'
	

	"""
	def cancel_voucher(self, cr, uid, ids, context=None):
		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for voucher in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			voucher.refresh()
			for line in voucher.move_ids:
				# refresh to make sure you don't unreconcile an already unreconciled entry
				line.refresh()
				if line.reconcile_id:
					move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
					move_lines.remove(line.id)
					reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
					if len(move_lines) >= 2:
						print "hoho-wtf",move_lines
						# en la funcion de reconcile_partial es donde hay que chekear el que si hay divisa toma el amount_currency  y con ese saca el calculo
						move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)
			if voucher.move_id:
				#move_pool.button_cancel(cr, uid, [voucher.move_id.id])
				#move_pool.unlink(cr, uid, [voucher.move_id.id])
				voucher.move_id.write({'ref':'Asiento anulado'})

				voucher.move_id.refresh()
				for lines_move in voucher.move_id.line_id:
					move_line_pool.unlink(cr,uid,[lines_move.id])
				voucher.move_id.refresh()
				data_new = {
				'name':'Asiento anulado',
				'account_id':voucher.move_id.journal_id.default_debit_account_id.id,
				'debit':0.00,
				'credit':0.00,
				'move_id': voucher.move_id.id,
				}
				ctx = {}
				ctx['journal_id'] = voucher.move_id.journal_id.id
				ctx['period_id'] = voucher.move_id.period_id.id
				ctx['date'] = voucher.move_id.date
				new_id = move_line_pool.create(cr,uid,data_new,context=ctx)
				voucher.move_id.write({'line_id':[(4,new_id)]})
				voucher.write({'move_id' : False})
		return super(account_voucher,self).cancel_voucher(cr,uid,ids,context)
	"""

	def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
		t = super(account_voucher,self).writeoff_move_line_get(cr, uid,voucher_id, line_total, move_id, name, company_currency, current_currency,context=context)
		obj_move = self.pool.get('account.move').browse(cr,uid,move_id,context)
		ids_delete = self.pool.get('account.move').search(cr, uid, [('id','!=',move_id),('ref','=','Asiento anulado'),('name','=',obj_move.name)], context=context)
		move_pool = self.pool.get('account.move')
		move_pool.button_cancel(cr, uid, ids_delete)
		self.pool.get('account.move').unlink(cr, uid, ids_delete , context=context)
		return t


class account_move_line(models.Model):
	_inherit = 'account.move.line'

	def reconcile_partial(self, cr, uid, ids, type='auto', context=None, writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False):
		move_rec_obj = self.pool.get('account.move.reconcile')
		merges = []
		unmerge = []
		total = 0.0
		merges_rec = []
		company_list = []
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			if company_list and not line.company_id.id in company_list:
				raise osv.except_osv(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
			company_list.append(line.company_id.id)

		for line in self.browse(cr, uid, ids, context=context):
			if line.account_id.currency_id:
				currency_id = line.account_id.currency_id
			else:
				currency_id = line.company_id.currency_id
			if line.reconcile_id:
				raise osv.except_osv(_('Warning'), _("Journal Item '%s' (id: %s), Move '%s' is already reconciled!") % (line.name, line.id, line.move_id.name))
			if line.reconcile_partial_id:
				for line2 in line.reconcile_partial_id.line_partial_ids:
					if line2.state != 'valid':
						raise osv.except_osv(_('Warning'), _("Journal Item '%s' (id: %s) cannot be used in a reconciliation as it is not balanced!") % (line2.name, line2.id))
					if not line2.reconcile_id:
						if line2.id not in merges:
							merges.append(line2.id)
						total += (line2.debit or 0.0) - (line2.credit or 0.0)
				merges_rec.append(line.reconcile_partial_id.id)
			else:
				unmerge.append(line.id)
				total += (line.debit or 0.0) - (line.credit or 0.0)
		if self.pool.get('res.currency').is_zero(cr, uid, currency_id, total):
			res = self.reconcile(cr, uid, merges+unmerge, context=context, writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id, writeoff_journal_id=writeoff_journal_id)
			return res
		# marking the lines as reconciled does not change their validity, so there is no need
		# to revalidate their moves completely.
		reconcile_context = dict(context, novalidate=True)
		r_id = move_rec_obj.create(cr, uid, {
			'type': type,
			'line_partial_ids': map(lambda x: (4,x,False), merges+unmerge)
		}, context=reconcile_context)
		move_rec_obj.reconcile_partial_check(cr, uid, [r_id] + merges_rec, context=reconcile_context)
		return r_id