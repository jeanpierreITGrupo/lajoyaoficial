# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
import pprint

class production_cost_journal_wizard(models.TransientModel):
	_name = 'production.cost.journal.wizard'

	period_id = fields.Many2one('account.period', "Periodo", required=1)

	@api.multi
	def get_lines(self):
		locations = self.env['stock.location'].search([('usage','=','internal')])
		products = self.env['product.product'].search([])
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

		cadf = "select * from get_moves_cost("+self.period_id.date_start.replace('-','') + "," + self.period_id.date_stop.replace('-','') + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[], 'internal', 'production')"
		self.env.cr.execute(cadf)
		ds = self.env.cr.dictfetchall()
		journal_line_obj = self.env['production.cost.journal']
		lines = journal_line_obj.search([])
		for line in lines:
			line.unlink()

		for line in ds:
			analytic_id = None
			if line['analytic_account']:
				analytic_id = self.env['account.analytic.account'].search([('code','=',line['analytic_account'])])
			else:
				if not analytic_id.account_account_moorage_id:
					raise osv.except_osv('Alerta','No ha configurado la cuenta de amarre al debe del Centro de Costo ' + analytic_id.name)
				if not analytic_id.account_account_moorage_credit_id:
					raise osv.except_osv('Alerta','No ha configurado la cuenta de amarre al haber del Centro de Costo ' + analytic_id.name)
				raise osv.except_osv('Alerta','No se puede crear el asiento debido a que existen movimientos sin Centro de Costo')
			vals = {
				'product_id'		: line['producto'],
				'analytic_account'	: analytic_id.id if analytic_id else None,
				'a_debit'			: analytic_id.account_account_moorage_id.id if analytic_id and analytic_id.account_account_moorage_id else None,
				'a_credit'			: analytic_id.account_account_moorage_credit_id.id if analytic_id and analytic_id.account_account_moorage_credit_id else None,
				'valued_rest'		: line['saldov'],
				'period_id'			: self.period_id.id,
			}
			journal_line_obj.create(vals)
		return {
			"type"		: "ir.actions.act_window",
			"res_model"	: "production.cost.journal",
			"view_type"	: "form",
			"view_mode"	: "tree",
			"target"	: "current",
		}