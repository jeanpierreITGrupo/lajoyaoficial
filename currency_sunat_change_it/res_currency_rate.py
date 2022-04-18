# -*- coding: utf-8 -*-

from openerp import models, fields, api

class res_currency_rate(models.Model):
	_inherit = 'res.currency.rate'

	name = fields.Date('Fecha',required=True,selected=True)
	type_sale = fields.Float('Tipo de Venta', digits=(16,3))
	type_purchase = fields.Float('Tipo de Compra', digits=(16,3))
	date_sunat = fields.Date('Fecha Sunat')

	@api.onchange('type_sale','rate')
	def _onchange_price(self):
		# set auto-changing field
		if self.type_sale == 0.00:
			self.rate = 0
			self.write({'rate': (0.0)})
		else:
			self.rate = 1.0 / (self.type_sale)
			self.write({'rate': (1.0 / (self.type_sale))})
	
		if self.rate == 0.00:
			self.type_sale = 0
		else:
			self.type_sale = 1.0 / (self.rate)
		# Can optionally return a warning and domains



	@api.onchange('date_sunat')
	def _onchange_date_sunat(self):
		if self.date_sunat:
			self.name = self.date_sunat

	@api.onchange('name')
	def _onchange_date_name(self):
		if self.name:
			from datetime import datetime , timedelta
			date_name = datetime.strptime(str(self.name)[:10],'%Y-%m-%d')
			print date_name
			date_sunat_obj = date_name
			self.date_sunat = str(date_sunat_obj)


