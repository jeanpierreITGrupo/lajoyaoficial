# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class production_cost_journal(models.TransientModel):
	_name = "production.cost.journal"

	product_id = fields.Many2one('product.product', "Producto")
	analytic_account = fields.Many2one('account.analytic.account', "Centro de Costo")
	valued_rest = fields.Float("Saldo Valorado")
	a_debit = fields.Many2one('account.account', "A_Debit")
	a_credit = fields.Many2one('account.account', "A_Credit")
	period_id = fields.Many2one('account.period', "Periodo")

	@api.multi
	def make_production_journal(self):
		locations = self.env['stock.location'].search([('usage','=','internal')])
		products = self.env['product.product'].search([])
		period_id = self.env['production.cost.journal'].search([])[0].period_id
		lst_locations = []
		lst_products = []
		for location in locations:
			lst_locations.append(location.id)
		for product in products:
			lst_products.append(product.id)
		productos='{'
		almacenes='{'
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'

		#Obteniendo líneas 
		cadf = "select analytic_account, sum(saldov) as saldo from get_moves_cost("+period_id.date_start.replace('-','') + "," + period_id.date_stop.replace('-','') + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[], 'internal', 'production') group by analytic_account"
		self.env.cr.execute(cadf)
		lines = self.env.cr.dictfetchall()

		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		journal_id = self.env['main.parameter'].search([]).diario_destino
		name = period_id.name.replace('/','-')
		vals = {
			'journal_id'	: journal_id.id,
			'period_id'		: period_id.id,
			'ref'			: 'CP-' + name,
			'date'			: period_id.date_stop,
		}
		move_id = move_obj.create(vals)

		import pprint
		pprint.pprint(lines)
		
		#Creando lineas de credit
		for line in lines:
			analytic_id = self.env['account.analytic.account'].search([('code','=',line['analytic_account'])])
			vals = {
				'move_id'			: move_id.id,
				'name'				: u'ASIENTO DE COSTO DE PRODUCCIÓN ' + name,
				'nro_comprobante'	: 'CP-' + name,
				'account_id'		: analytic_id.account_account_moorage_credit_id.id,
				'debit'				: 0.0,
				'credit'			: line['saldo'],	
			}
			move_line_obj.create(vals)

		#Creando lineas de debit
		for line in lines:
			vals = {
				'move_id'			: move_id.id,
				'name'				: 'ASIENTO DE COSTO DE PRODUCCIÓN ' + name,
				'nro_comprobante'	: 'CP-' + name,
				'account_id'		: analytic_id.account_account_moorage_id.id,
				'debit'				: line['saldo'],	
				'credit'			: 0.0,
			}
			move_line_obj.create(vals)

		return {
			"type"		: "ir.actions.act_window",
			"res_model"	: "account.move",
			"view_type"	: "form",
			"view_mode"	: "form",
			"res_id"	: move_id.id,
			"target"	: "current",
		}
