# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class expenses_without_record_line(models.Model):
	_name = 'expenses.without.record.line'

	expedient_id = fields.Many2one('purchase.costing', "Expediente")
	gold_espectative = fields.Float('Expectativa del Oro', digits=(12,2))
	porcentaje_gastos = fields.Float('Porcentaje Gastos',digits=(12,6))
	monto_proporcional = fields.Float('Monto Proporcional',digits=(12,2))

	padre = fields.Many2one('expenses.without.record','Padre')

class expenses_without_record(models.Model):
	_name = 'expenses.without.record'

	period_id = fields.Many2one('account.period','Periodo',required=True)
	amount = fields.Float('Monto',digits=(12,2),required=False,readonly=True)
	warehouse_id = fields.Many2one('stock.location','Almacen',required=True)
	analytic_id = fields.Many2one('account.analytic.account','Cuenta Analítica G.S.E.',required=True)

	lines = fields.One2many('expenses.without.record.line','padre','Lineas')
	
	_rec_name = 'period_id'

	@api.one
	def actualizar(self):


		self.env.cr.execute(""" 
			select sum(debit-credit) from account_move am 
			inner join account_move_line aml on aml.move_id = am.id
			inner join account_period ap on ap.id = am.period_id
			where ap.id = """+ str(self.period_id.id)  +"""
			and aml.analytic_account_id = """ + str(self.analytic_id.id) + """
			""")
		cant = 0

		for i in self.env.cr.fetchall():
			cant = i[0] if i[0] else 0
		
		self.write({'amount': cant})
		self.amount = cant
		self.refresh()

		for i in self.lines:
			i.unlink()
			
		self.env.cr.execute(""" 
			select  pc.id,sum(coalesce(sm.gold_expected,0))  from  purchase_costing pc
			inner join purchase_costing_detalles pcd on pcd.padre = pc.id
			inner join purchase_liquidation pl on pl.id = pcd.nro_lote
			left join stock_move sm on sm.lot_num = pl.id and sm.location_dest_id = """ + str(self.warehouse_id.id) + """
			left join stock_picking sp on sp.id = sm.picking_id and sp.state != 'draft' 
			group by pc.id
			""")

		t_e = 0
		for i in self.env.cr.fetchall():
			self.env['expenses.without.record.line'].create({'expedient_id':i[0],'gold_espectative':i[1],'padre':self.id})
			t_e += i[1]

		self.refresh()
		for i in self.lines:
			i.porcentaje_gastos = (i.gold_espectative / t_e) if t_e != 0 else 0
			i.monto_proporcional = ((i.gold_espectative / t_e) if t_e != 0 else 0) * self.amount