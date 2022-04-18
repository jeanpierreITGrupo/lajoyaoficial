# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from openerp.osv import osv
import base64
from zipfile import ZipFile


class costo_venta_it(models.Model):
	_name = 'costo.venta.it'

	periodo = fields.Many2one('account.period','Periodo')
	fecha  = fields.Date('Fecha de Asiento')

	@api.multi
	def do_rebuild(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		file_path = direccion + 'categorias_sin_cuenta.txt'

		t = "'{"
		for i in self.env['product.product'].search([]):
			t += str(i.id) + ','

		t=t[:-1] + "}'"

		fecha_inianio = str(self.periodo.date_start).replace('-','')
		fechafin = str(self.periodo.date_stop).replace('-','')

		m = "'{"
		origen = [0,0,0]
		for i in self.env['stock.location'].search([]):
			if i.usage == 'internal':
				origen.append(i.id)
				m += str(i.id) + ','

				
		destino = [0,0,0]
		for i in self.env['stock.location'].search([]):
			if i.usage == 'customer':
				destino.append(i.id)
				m += str(i.id) + ','
		m=m[:-1] + "}'"

		self.env.cr.execute("""
			select aa5.id, sum(credit) as credit from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """::INT[],""" + m + """::INT[]) as X
			inner join product_product pp on pp.id = X.product_id

left outer join product_template on product_template.id = pp.product_tmpl_id
left outer join product_category on product_category.id = product_template.categ_id
left outer join ir_property ip1 on (ip1.res_id = 'product.template,' || COALESCE(product_template.id,-1) ) and ip1.name = 'property_account_income'
left outer join account_account aa1 on aa1.id = COALESCE( substring(ip1.value_reference from 17)::int8 , -1)
left outer join ir_property ip2 on (ip2.res_id = 'product.template,' || COALESCE(product_template.id,-1) ) and ip2.name = 'property_account_expense'
left outer join account_account aa2 on aa2.id = COALESCE( substring(ip2.value_reference from 17)::int8, -1)
left outer join ir_property ip3 on (ip3.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip3.name = 'property_stock_account_input_categ' 
left outer join account_account aa3 on aa3.id = COALESCE( substring(ip3.value_reference from 17)::int8, -1)
left outer join ir_property ip4 on (ip4.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip4.name = 'property_stock_account_output_categ'
left outer join account_account aa4 on aa4.id = COALESCE( substring(ip4.value_reference from 17)::int8, -1)
left outer join ir_property ip5 on (ip5.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip5.name = 'property_stock_valuation_account_id'
left outer join account_account aa5 on aa5.id = COALESCE( substring(ip5.value_reference from 17)::int8, -1)
left outer join ir_property ip7 on (ip7.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip7.name = 'property_account_income_categ'
left outer join account_account aa7 on aa7.id = COALESCE( substring(ip7.value_reference from 17)::int8, -1)
left outer join ir_property ip8 on (ip8.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip8.name = 'property_account_expense_categ'
left outer join account_account aa8 on aa8.id = COALESCE( substring(ip8.value_reference from 17)::int8, -1) 
where product_template.active = true

			and (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
			group by aa5.id
			   """)
		
		linea_valoracion = []

		for i in self.env.cr.fetchall():
			if i[0]:
				linea_valoracion.append( (i[0],i[1]) )


		self.env.cr.execute("""
			select aa4.id, sum(credit) as credit from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """,""" + m + """) as X
			inner join product_product pp on pp.id = X.product_id

left outer join product_template on product_template.id = pp.product_tmpl_id
left outer join product_category on product_category.id = product_template.categ_id
left outer join ir_property ip1 on (ip1.res_id = 'product.template,' || COALESCE(product_template.id,-1) ) and ip1.name = 'property_account_income'
left outer join account_account aa1 on aa1.id = COALESCE( substring(ip1.value_reference from 17)::int8 , -1)
left outer join ir_property ip2 on (ip2.res_id = 'product.template,' || COALESCE(product_template.id,-1) ) and ip2.name = 'property_account_expense'
left outer join account_account aa2 on aa2.id = COALESCE( substring(ip2.value_reference from 17)::int8, -1)
left outer join ir_property ip3 on (ip3.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip3.name = 'property_stock_account_input_categ' 
left outer join account_account aa3 on aa3.id = COALESCE( substring(ip3.value_reference from 17)::int8, -1)
left outer join ir_property ip4 on (ip4.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip4.name = 'property_stock_account_output_categ'
left outer join account_account aa4 on aa4.id = COALESCE( substring(ip4.value_reference from 17)::int8, -1)
left outer join ir_property ip5 on (ip5.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip5.name = 'property_stock_valuation_account_id'
left outer join account_account aa5 on aa5.id = COALESCE( substring(ip5.value_reference from 17)::int8, -1)
left outer join ir_property ip7 on (ip7.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip7.name = 'property_account_income_categ'
left outer join account_account aa7 on aa7.id = COALESCE( substring(ip7.value_reference from 17)::int8, -1)
left outer join ir_property ip8 on (ip8.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip8.name = 'property_account_expense_categ'
left outer join account_account aa8 on aa8.id = COALESCE( substring(ip8.value_reference from 17)::int8, -1) 
where product_template.active = true
			and (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
			group by aa4.id
			   """)

		linea_salida = []

		for i in self.env.cr.fetchall():
			if i[0]:
				linea_salida.append( (i[0],i[1]) )


		parametros = self.env['main.parameter'].search([])[0]

		valsC = {
			'period_id':self.periodo.id,
			'journal_id':parametros.diario_destino.id,
			'ref':'CV-'+ self.periodo.code.replace('/','-'),
			'date':self.fecha,
		}
		asiento = self.env['account.move'].create(valsC)

		for i in linea_salida:
			dataL = {
				'name':'COSTO DE VENTAS '+ self.periodo.code.replace('/','-'),
				'account_id':i[0],
				'nro_comprobante':'CV-'+ self.periodo.code.replace('/','-'),
				'debit': i[1] ,
				'credit': 0,
				'move_id': asiento.id,
			}
			self.env['account.move.line'].create(dataL)

		for i in linea_valoracion:
			dataL = {
				'name':'COSTO DE VENTAS '+ self.periodo.code.replace('/','-'),
				'account_id':i[0],
				'nro_comprobante':'CV-'+ self.periodo.code.replace('/','-'),
				'debit': 0,
				'credit': i[1],
				'move_id': asiento.id,
			}
			self.env['account.move.line'].create(dataL)




		fo = open(file_path, "w")
		fo.write('Categoría' + "\r\n");
		fo.write('----------------------------------' + "\r\n");

		self.env.cr.execute("""
			select distinct product_category.name from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """::INT[],""" + m + """::INT[]) as X
			inner join product_product pp on pp.id = X.product_id

left outer join product_template on product_template.id = pp.product_tmpl_id
left outer join product_category on product_category.id = product_template.categ_id
left outer join ir_property ip1 on (ip1.res_id = 'product.template,' || COALESCE(product_template.id,-1) ) and ip1.name = 'property_account_income'
left outer join account_account aa1 on aa1.id = COALESCE( substring(ip1.value_reference from 17)::int8 , -1)
left outer join ir_property ip2 on (ip2.res_id = 'product.template,' || COALESCE(product_template.id,-1) ) and ip2.name = 'property_account_expense'
left outer join account_account aa2 on aa2.id = COALESCE( substring(ip2.value_reference from 17)::int8, -1)
left outer join ir_property ip3 on (ip3.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip3.name = 'property_stock_account_input_categ' 
left outer join account_account aa3 on aa3.id = COALESCE( substring(ip3.value_reference from 17)::int8, -1)
left outer join ir_property ip4 on (ip4.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip4.name = 'property_stock_account_output_categ'
left outer join account_account aa4 on aa4.id = COALESCE( substring(ip4.value_reference from 17)::int8, -1)
left outer join ir_property ip5 on (ip5.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip5.name = 'property_stock_valuation_account_id'
left outer join account_account aa5 on aa5.id = COALESCE( substring(ip5.value_reference from 17)::int8, -1)
left outer join ir_property ip7 on (ip7.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip7.name = 'property_account_income_categ'
left outer join account_account aa7 on aa7.id = COALESCE( substring(ip7.value_reference from 17)::int8, -1)
left outer join ir_property ip8 on (ip8.res_id = 'product.category,' || COALESCE(product_category.id,-1) ) and ip8.name = 'property_account_expense_categ'
left outer join account_account aa8 on aa8.id = COALESCE( substring(ip8.value_reference from 17)::int8, -1) 
where product_template.active = true

			and (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
			and ( aa5.id is null or aa4.id is null )
			   """)

		for i in self.env.cr.fetchall():
			fo.write('-- '+i[0].upper() + "\r\n");

		fo.close()
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
		    "res_id": sfs_id.id,
		    "target": "new",
		}