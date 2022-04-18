# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs


class account_sheet_work_wizard(osv.TransientModel):
	_name='account.sheet.work.wizard'
	_inherit= 'account.sheet.work.wizard'


	check_comparative = fields.Boolean('Mostrar Comparativo')
	period_ini_c = fields.Many2one('account.period','Periodo Inicio')
	period_end_c = fields.Many2one('account.period','Periodo Fin')
	fiscalyear_c_id = fields.Many2one('account.fiscalyear','Año Fiscal')


	@api.onchange('fiscalyear_c_id')
	def onchange_fiscalyear_c(self):
		if self.fiscalyear_c_id:
			return {'domain':{'period_ini_c':[('fiscalyear_id','=',self.fiscalyear_c_id.id )], 'period_fin_c':[('fiscalyear_id','=',self.fiscalyear_c_id.id )]}}
		else:
			return {'domain':{'period_ini_c':[], 'period_end_c':[]}}


	@api.onchange('period_ini_c')
	def _change_periodo_ini_c(self):
		if self.period_ini_c:
			self.period_end_c= self.period_ini_c


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
			DROP VIEW IF EXISTS account_sheet_work_simple;
			CREATE OR REPLACE view account_sheet_work_simple as (
				select *, 0 as debec, 0 as haberc, 0 as saldodeudorc, 0 as saldoacredorc from get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				0 as debec, 0 as haberc, 0 as saldodeudorc, 0 as saldoacredorc
				from 
				get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))

				 
			)""")	
		else:
			self.env.cr.execute("""
				
			DROP VIEW IF EXISTS account_sheet_work_simple;
			CREATE OR REPLACE view account_sheet_work_simple as (
				select *,0 as debec, 0 as haberc, 0 as saldodeudorc, 0 as saldoacredorc from get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				0 as debec, 0 as haberc, 0 as saldodeudorc, 0 as saldoacredorc
				from 
				get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))

				 
			)""")	

		

				
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		result = mod_obj.get_object_reference('account_sheet_work', 'action_account_sheet_work_simple')
		
		id = result and result[1] or False
		print id
		return {
			'context': {'tree_view_ref':'account_sheet_work.view_account_sheet_work_simple_tree'},
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.sheet.work.simple',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}
	


	@api.multi
	def do_rebuild_C(self):
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
				
select row_number() OVER () AS id,* from ( 
 select coalesce(A1.cuenta,A2.cuenta) as cuenta, coalesce(A1.descripcion,A2.descripcion) as descripcion, A1.debe, A1.haber, A1.saldodeudor, A1.saldoacredor, A2.debe as debec, A2.haber as haberc , A2.saldodeudor as saldodeudorc , A2.saldoacredor as saldoacredorc  from get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
 AS A1
FULL JOIN get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + self.period_ini_c.code + """'),periodo_num('""" + self.period_end_c.code +"""'))
AS A2 on (A1.cuenta = A2.cuenta and A1.descripcion = A2.descripcion)
) AS T
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				0 as debec, 0 as haberc, 0 as saldodeudorc, 0 as saldoacredorc
				from 
				(
				select row_number() OVER () AS id,* from ( 
 select coalesce(A1.cuenta,A2.cuenta) as cuenta, coalesce(A1.descripcion,A2.descripcion) as descripcion , A1.debe, A1.haber, A1.saldodeudor, A1.saldoacredor, A2.debe as debec, A2.haber as haberc , A2.saldodeudor as saldodeudorc , A2.saldoacredor as saldoacredorc  from get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
 AS A1
FULL JOIN get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + self.period_ini_c.code + """'),periodo_num('""" + self.period_end_c.code +"""'))
AS A2 on (A1.cuenta = A2.cuenta and A1.descripcion = A2.descripcion)
) AS T
					)AS X 
	
	

				 
			)""")	
		else:
			self.env.cr.execute("""
				
			DROP VIEW IF EXISTS account_sheet_work_simple cascade;
			CREATE OR REPLACE view account_sheet_work_simple as (


select row_number() OVER () AS id,* from ( 
 select coalesce(A1.cuenta,A2.cuenta) as cuenta, coalesce(A1.descripcion,A2.descripcion) as descripcion, A1.debe, A1.haber, A1.saldodeudor, A1.saldoacredor, A2.debe as debec, A2.haber as haberc , A2.saldodeudor as saldodeudorc , A2.saldoacredor as saldoacredorc  from get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
 AS A1
FULL JOIN get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + self.period_ini_c.code + """'),periodo_num('""" + self.period_end_c.code +"""'))
AS A2 on (A1.cuenta = A2.cuenta and A1.descripcion = A2.descripcion)
) AS T
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				0 as debec, 0 as haberc, 0 as saldodeudorc, 0 as saldoacredorc
				from 
				(
				select row_number() OVER () AS id,* from ( 
 select coalesce(A1.cuenta,A2.cuenta) as cuenta, coalesce(A1.descripcion,A2.descripcion) as descripcion , A1.debe, A1.haber, A1.saldodeudor, A1.saldoacredor, A2.debe as debec, A2.haber as haberc , A2.saldodeudor as saldodeudorc , A2.saldoacredor as saldoacredorc  from get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
 AS A1
FULL JOIN get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + self.period_ini_c.code + """'),periodo_num('""" + self.period_end_c.code +"""'))
AS A2 on (A1.cuenta = A2.cuenta and A1.descripcion = A2.descripcion)
) AS T
					)AS X 
				 
			)""")	

		

				
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		result = mod_obj.get_object_reference('account_sheet_work', 'action_account_sheet_work_simple')
		
		id = result and result[1] or False
		print id
		return {
			'context': {'tree_view_ref':'account_sheet_work.view_account_sheet_work_simple_c_tree'},
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.sheet.work.simple',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}
	