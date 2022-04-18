# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs


class account_sheet_work_wizard(osv.TransientModel):
	_name='account.sheet.work.wizard'
	
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	wizrd_level_sheet = fields.Selection((('1','Cuentas de Balance'),
									('2','Cuentas de Registro')						
									),'Nivel',required=True)

	moneda = fields.Many2one('res.currency','Moneda', required=False)
	
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)



	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'period_end':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'period_ini':[], 'period_end':[]}}



	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini


	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		has_currency = self.moneda
		
		filtro = []
		
		currency = False
		if has_currency.id != False:
			user = self.env['res.users'].browse(self.env.uid)
			if user.company_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una compañia configurada para el usuario actual.")
			if user.company_id.currency_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una moneda configurada para la compañia del usuario actual.")
			
			if has_currency.id != user.company_id.currency_id.id:
				currency = True
			
		
		if self.wizrd_level_sheet == '1':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_sheet_work_simple cascade;
			CREATE OR REPLACE view account_sheet_work_simple as (
				select * from get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor
				from 
				get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))

				 
			)""")	
		else:
			self.env.cr.execute("""
				
			DROP VIEW IF EXISTS account_sheet_work_simple cascade;
			CREATE OR REPLACE view account_sheet_work_simple as (
				select * from get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor
				from 
				get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))

				 
			)""")	

		

				
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		result = mod_obj.get_object_reference('account_sheet_work', 'action_account_sheet_work_simple')
		
		id = result and result[1] or False
		print id
		return {
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.sheet.work.simple',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}
	