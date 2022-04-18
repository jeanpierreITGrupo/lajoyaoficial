# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import datetime
class get_kardex_saldos(osv.osv_memory):
	_name = "get.kardex.saldos"

	_columns = {
		'date': fields.date('Fecha'),
	}
	
	def date_to_number(self, date):
		splited = date.split('-')
		return ''.join(splited)
	
	def action_procesar_resumen(self, cr, uid, ids, context=None):
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		
		if context is None:
			context = {}
		data = self.read(cr, uid, ids, [], context=context)[0]
		
		date = data['date']
		date = self.date_to_number(date)
		#raise osv.except_osv('Alerta',date)
		
		
		filtro = []
			
		cr.execute("""
		DROP VIEW IF EXISTS kardex_saldos;
			CREATE OR REPLACE view kardex_saldos as (
				SELECT row_number() OVER () AS id,*
				FROM rep_stock_saldo("""+ str(date)+ """)) 
		""")

		result = mod_obj.get_object_reference(cr, uid,'kardex_saldos', 'kardex_saldos_action')
		id = result and result[1] or False
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'kardex.saldos',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}


	def getsaldo_product(self, cr, uid, ids, product_id, fecha_date=None, context=None):
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		
		if context is None:
			context = {}
		
		if fecha_date == None:
			now = datetime.datetime.now()
			date = now.strftime("%Y-%m-%d")
			fecha_date = self.date_to_number(date)
		else:
			fecha_date = self.date_to_number(fecha_date)

		cadsql ="""SELECT row_number() OVER () AS id,*
				FROM rep_stock_saldo("""+ str(fecha_date)+ """)
				where product_id = """+str(product_id)
		# raise osv.except_osv('Alerta',cadsql)
		cr.execute(cadsql)
		d=cr.dictfetchall()
		ret = 0
		if len(d)>0:
			ret = d[0]['saldores']
		return ret
get_kardex_saldos()