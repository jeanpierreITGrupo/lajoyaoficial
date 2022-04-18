# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api

class account_voucher(models.Model):
	_inherit = 'account.voucher'
	fefectivo_id = fields.Many2one('account.config.efective',string ="F. Efectivo")
	
	def account_move_get(self, cr, uid, voucher_id, context=None):
		seq_obj = self.pool.get('ir.sequence')
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		
		if not voucher.number:
			c = dict(context)
			c.update({'fiscalyear_id': voucher.period_id.fiscalyear_id.id,'period': voucher.period_id})
			name = seq_obj.next_by_id(cr, uid, voucher.journal_id.sequence_id.id, context=c)
			self.pool.get('account.voucher').write(cr, uid, [voucher.id], {'number': name})

		elif voucher.journal_id.sequence_id:
			if not voucher.journal_id.sequence_id.active:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please activate the sequence of selected journal !'))
		else:
			raise osv.except_osv(_('Error!'),
						_('Please define a sequence on the journal.'))
		
		return super(account_voucher,self).account_move_get(cr, uid, voucher_id, context)
		

class account_sequence_journal_wizard(osv.TransientModel):
	_name='account.sequence.journal.wizard'
	
	journal_ids =fields.Many2many('account.journal','account_journal_sequence_wizard_rel','sequence_wizard_id','journal_id','Diarios',required=True)
	fiscal_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	period_ini =fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end =fields.Many2one('account.period','Periodo Final',required=True)



	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini


	@api.multi
	def do_rebuild(self):
		self.env.cr.execute(" select id from account_period where periodo_num(code) >= periodo_num('"+ self.period_ini.code +"') and periodo_num(code) <= periodo_num('"+ self.period_end.code +"')")
		print " select id from account_period where periodo_num(code) >= periodo_num('"+ self.period_ini.code +"') and periodo_num(code) <= periodo_num('"+ self.period_end.code +"')"
		periodos_ids = [id for (id,) in self.env.cr.fetchall()] 
		print periodos_ids
		periodos = self.env['account.period'].search([('id','in',periodos_ids)])
		for i in self.journal_ids:
			for j in periodos:
				filtro = []
				filtro.append( ('fiscalyear_id','=',self.fiscal_id.id) )
				filtro.append( ('period_id','=',j.id) )
				filtro.append( ('sequence_main_id','=',i.sequence_id.id) )
				check_tmp = self.env['account.sequence.fiscalyear'].search(filtro)
				if len(check_tmp)> 0:
					pass
				else:
					dic_new_seq = {
					'name': i.name + '-' + j.code[:2],
					'padding': 6,
					'number_next_actual': 1,
					'number_increment': 1,
					'implementation': 'no_gap',
					'prefix': '',
					}
					new_sequence= self.env['ir.sequence'].create(dic_new_seq)

					dic_new_seq_fiscal = {
					'fiscalyear_id': self.fiscal_id.id,
					'period_id': j.id,
					'sequence_id': new_sequence.id,
					'sequence_main_id': i.sequence_id.id,
					}
					new_sequence_fiscal= self.env['account.sequence.fiscalyear'].create(dic_new_seq_fiscal)
					i.sequence_id.write({'fiscal_ids': [(4,new_sequence_fiscal.id)]})


		obj_id = self.env['warning'].create({'title': 'Generar Secuencias', 'message': 'Secuencias generadas exitosamente', 'type': 'info'})

		res = {
			'name': 'Generar Asientos Unicos',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'warning',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': obj_id.id
		}
		print res
		return res
