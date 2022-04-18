# -*- encoding: utf-8 -*-
import pprint

from openerp import models, fields, api, _
from openerp.osv import osv


class account_move_reversed(osv.osv_memory):
	_name='account.move.reversed'

	period_id = fields.Many2one('account.period','Periodo')
	date = fields.Date('Fecha')
	journal_id = fields.Many2one('account.journal','Diario')
	
	
	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		record_id = context and context.get('active_id', False)
		return False

	def reverse_account_move(self, cr, uid, ids, context=None):
		line_obj = self.pool.get('account.move')
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')


		if context is None:
			context = {}


		data = self.read(cr, uid, ids, context=context)[0]
		context.update( {'period_id': data['period_id'][0] , 'journal_id': data['journal_id'][0] ,'date': data['date'] } )
		# for install_act in picking_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
			# if install_act.state == 'draft':
			# 	raise osv.except_osv('Alerta', 'No es posible procesar notas en borrador')
		print 'active_ids', context.get(('active_ids'), [])
		ids2=line_obj.reverse_account_move(cr, uid, context.get(('active_ids'), []), context)
		if ids2==[]:
			raise osv.except_osv('Alerta','No se revirtio el archivo')
		result={}
		
		mod_obj = self.pool.get('ir.model.data')
		res = mod_obj.get_object_reference(cr, uid, 'account', 'view_move_form')
		return {
				   'name': 'Control Forms',
					'view_type': 'form',
					'view_mode': 'form',
					'view_id': [res and res[1] or False],
					'res_model': 'account.move',
					'context': "{}",
					'type': 'ir.actions.act_window',
					'nodestroy': True,
					'res_id': ids2[0] or False,
			   }
account_move_reversed()

class account_move(models.Model):
	_inherit='account.move'
	
	def reverse_account_move(self, cr, uid, ids, context=None):
		#pprint.pprint(self.read())
		period_id = context['period_id']
  		journal_id = context['journal_id']
  		date = context['date']

		moves_ids = []
		for periodo in self.browse(cr, uid, ids, context):
			lines = []

			#periodo_next_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '>', periodo.period_id.date_stop)])
			#periodo_next_id = periodo_next_ids[0] if len(periodo_next_ids) != 0 else periodo.period_id.id

			#periodo_next = self.pool.get('account.period').browse(cr, uid, periodo_next_id, context)
			
			for line in periodo.line_id:
				line_cc = (0,0,{
					'account_id': line.account_id.id,
					'account_tax_id': line.account_tax_id.id,
					'amount_currency': abs(line.amount_currency) if line.amount_currency < 0 else -1 * line.amount_currency,
					'amount_residual': line.amount_residual,
					'amount_residual_currency': line.amount_residual_currency,
					'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False,
					#'analytic_lines': line.analytic_account_id,
					'credit': line.debit,
					'currency_id': line.currency_id.id,
					'currency_rate_it': line.currency_rate_it,
					'date': date,
					'date_maturity': date,
					'debit': line.credit,
					'invoice': line.invoice,
					'means_payment_id': line.means_payment_id.id,
					'name': line.name, 
					'nro_comprobante': line.nro_comprobante,
					'partner_id': line.partner_id.id,
					'product_id': line.product_id.id,
					'product_uom_id': line.product_uom_id.id,
					'quantity': line.quantity,
					'ref': line.ref,
					'rendicion_id': line.rendicion_id.id,
					'tax_amount': abs(line.tax_amount) if line.tax_amount < 0 else -1 *line.tax_amount,
					'tax_code_id': line.tax_code_id.id,
					'type_document_id': line.type_document_id.id,
				})
				lines.append(line_cc)
			move = {
					'name':'/',
					'ref': periodo.ref,
					'line_id': lines,
					'date': date,
					'journal_id': journal_id,
					'period_id': period_id,
					'company_id': periodo.company_id.id,
					'partner_id': periodo.partner_id.id,
				}
			move_obj = self.pool.get('account.move')

			move_id1 = move_obj.create(cr, uid, move, context)
			moves_ids.append(move_id1)
			#move_id_act=move_id1
			#move_obj.post(cr, uid, [move_id1], context=None)
		return moves_ids
	
	@api.one
	def reverse_account_move_1(self):
		#pprint.pprint(self.read())
		lines = []
		
		periodo_next_ids = self.env['account.period'].search([('date_start', '>', self.period_id.date_stop)])
		periodo_next = periodo_next_ids[0] if len(periodo_next_ids) != 0 else self.period_id
		
		for line in self.line_id:
			line_cc = (0,0,{
				'account_id': line.account_id.id,
				'account_tax_id': line.account_tax_id.id,
				'amount_currency': abs(line.amount_currency) if line.amount_currency < 0 else -1 * line.amount_currency,
				'amount_residual': line.amount_residual,
				'amount_residual_currency': line.amount_residual_currency,
				'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False,
				#'analytic_lines': line.analytic_account_id,
				'credit': line.debit,
				'currency_id': line.currency_id.id,
				'currency_rate_it': line.currency_rate_it,
				'date': line.date,
				'date_maturity': line.date_maturity,
				'debit': line.credit,
				'invoice': line.invoice,
				'means_payment_id': line.means_payment_id.id,
				'name': line.name, 
				'nro_comprobante': line.nro_comprobante,
				'partner_id': line.partner_id.id,
				'product_id': line.product_id.id,
				'product_uom_id': line.product_uom_id.id,
				'quantity': line.quantity,
				'ref': line.ref,
				'rendicion_id': line.rendicion_id.id,
				'tax_amount': abs(line.tax_amount) if line.tax_amount < 0 else -1 *line.tax_amount,
				'tax_code_id': line.tax_code_id.id,
				'type_document_id': line.type_document_id.id,
			})
			lines.append(line_cc)
		move = {
				'name':'/',
				'ref': self.ref,
				'line_id': lines,
				'date': self.date,
				'journal_id': self.journal_id.id,
				'period_id': periodo_next.id,
				'company_id': self.company_id.id,
				'partner_id': self.partner_id.id,
			}
		move_obj = self.env['account.move']
		move_id1 = move_obj.create(move)
		#move_id_act=move_id1
		#move_obj.post(cr, uid, [move_id1], context=None)
		return move_id1
		"""
		return {
			"type": "ir.actions.act_window",
			"res_model": "account.move",
			"views": [[False, "form"]],
			"res_id": move_id1.id,
			"target": "current",
		}
		"""