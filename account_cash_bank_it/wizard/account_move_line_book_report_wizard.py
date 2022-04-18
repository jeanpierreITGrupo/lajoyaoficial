# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class account_move_line_book_report_wizard(osv.TransientModel):
	_name='account.move.line.book.report.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	moneda = fields.Many2one('res.currency','Moneda')
	



	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini


	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_ini
		fechafin_obj = self.period_end
		filtro = []
		
		t = self.env['account.period'].search([('id','>=',fechaini_obj.id),('id','<=',fechafin_obj.id)]).mapped('name')
		filtro.append( ('periodo','in',tuple(t)) )

		filtro.append( ('statefiltro','=','posted') )
		if self.moneda:
			company_obj = self.env['res.company'].search([]).mapped('currency_id')
			if self.moneda in company_obj:
				print "todo bien"
			else:
				raise osv.except_osv('Alerta','Ese tipo de Moneda aún esta en desarrollo (Por favor comunicarse con ITGrupo).')

		move_obj=self.env['account.move.line.bank.report']

		lstidsmove = move_obj.search(filtro)



		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		result = mod_obj.get_object_reference('account_contable_book_it', 'action_account_moves_all_report_it')
		id = result and result[1] or False
		print id
		
		return {
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line.book.report',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}