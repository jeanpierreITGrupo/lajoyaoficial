# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
import pprint
import os.path
import os
import base64

class sale_cost_journal_wizard(models.TransientModel):
	_name = 'sale.cost.journal.wizard'

	period_id = fields.Many2one('account.period', "Periodo", required=1)

	@api.multi
	def get_lines(self):
		locations = self.env['stock.location'].search([('usage','=','internal')])
		products = self.env['product.product'].search([])
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
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

		cadf = "select * from get_moves_cost("+self.period_id.date_start.replace('-','') + "," + self.period_id.date_stop.replace('-','') + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[], 'internal', 'customer')"
		self.env.cr.execute(cadf)
		ds = self.env.cr.dictfetchall()
		journal_line_obj = self.env['sale.cost.journal']
		lines = journal_line_obj.search([])
		
		for line in lines:
			line.unlink()

		categories = []
		values = []
		file_path = direccion + 'categorias_sin_cuenta.txt'
		if os.path.exists(file_path):
			os.remove(file_path)
		fo = None
		for line in ds:
			if (not line['out_account'] or not line['valued_account']) and line['category'] not in categories:
				if not os.path.exists(file_path):
					fo = open(direccion +"categorias_sin_cuenta.txt", "w")
					fo.write('Categoría' + "\r\n");
					fo.write('----------------------------------' + "\r\n");
				categories.append(line['category'])
				fo.write('-- '+line['category'].upper() + "\r\n");
			vals = {
				'out_account'		: int(line['out_account'].split(',')[1]) if line['out_account'] else None,
				'valued_account'	: int(line['valued_account'].split(',')[1]) if line['valued_account'] else None,
				'product_id'		: line['producto'],
				'valued_rest'		: line['saldov'],
				'period_id'			: self.period_id.id,
			}
			values.append(vals)
		#Existen Excepciones
		if fo:
			fo.close()
			dummy, view_id = self.pool.get('ir.model.data').get_object_reference(self.env.cr, self.env.uid, 'journal_sale_cost_it', 'export_file')
			f = open(file_path, 'r')
			vals = {
				'output_name': 'categorias_sin_cuenta.txt',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			sfs_id = self.env['export.file.save'].create(vals)

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    'view_mode': 'form',
			    "view_type": "form",
			    "view_id" : view_id,
			    "res_id": sfs_id.id,
			    "target": "new",
			}
		#Todo bien
		else:
			for vals in values:
				journal_line_obj.create(vals)
			return {
				"type"		: "ir.actions.act_window",
				"res_model"	: "sale.cost.journal",
				"view_type"	: "form",
				"view_mode"	: "tree",
				"target"	: "current",
			}