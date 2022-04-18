# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import openerp.addons.decimal_precision as dp

import datetime
import decimal

class min_max_view(models.Model):
	_name = 'min.max.view'
	_auto = False

	product_id = fields.Many2one('product.product','Producto')
	uom_id = fields.Many2one('product.uom','Unidad de Medida')
	category = fields.Char('Categoria')
	maximo = fields.Float(u'Máximo')
	minimo = fields.Float(u'Mínimo')
	rotation = fields.Float(u'Rotación')
	saldo = fields.Float('Saldo')
	reponer = fields.Float('Reponer')
	sobrante = fields.Float('Evaluar')
	abastecimiento = fields.Integer(u'Abastecimiento Día(s)')

	@api.model
	def cron_notificar_max(self):
		self.notificar_max()

	@api.multi
	def notificar_max(self):
		wp = self.env['warehouse.parameters'].search([])[0]
		values = {}
		values['subject'] = u"Reporte de Máximos La Joya Minning"
		
		mails = u""
		for i in wp.s_user_ids:
			mails += i.login + ";"
		mails = mails[:-1]
		values['email_to'] = u"dsalinas@itgrupo.net"

		txt = u"""
			<h2>Reporte de Máximos</h2>
			<p>Días de Rotación: """+ str(wp.s_rotation) + u"""</p>
			<p>Almacén: """+ wp.s_warehouse_id.name + u"""</p>
			<p>Evaluación: """+ "Sobrantes" + u"""</p>
			<p>-------------------------------------------------</p>
		"""

		values['body_html'] = txt
		values['res_id'] = False

		mmr = self.env['max.min.report'].display_q(wp.s_rotation, 'sobrantes', [wp.s_warehouse_id.lot_stock_id.id])

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")

		f = open( direccion + u'Reporte_'+'sobrantes'+'.xlsx', 'rb')

		att = {
			'name':u'Reporte_'+'sobrantes'+'.xlsx',
			'type':'binary',
			'datas':base64.encodestring(''.join(f.readlines())),
			'datas_fname':u'Reporte_'+'sobrantes'+'.xlsx',
		}
		att_id=self.pool.get('ir.attachment').create(self.env.cr,self.env.uid,att,self.env.context)

		values['attachment_ids'] = [(6,0,[att_id])]

		msg_id = self.env['mail.mail'].create(values)
		if msg_id:
			msg_id.send()

		f.close()

	@api.model
	def cron_notificar_min(self):
		self.notificar_min()

	@api.multi
	def notificar_min(self):
		wp = self.env['warehouse.parameters'].search([])[0]
		values = {}
		values['subject'] = u"Reporte de Mínimos La Joya Minning"
		
		mails = u""
		for i in wp.s_user_ids:
			mails += i.login + ";"
		mails = mails[:-1]
		print mails
		values['email_to'] = u"dsalinas@itgrupo.net"
		
		txt = u"""
			<h2>Reporte de Mínimos</h2>
			<p>Días de Rotación: """+ str(wp.f_rotation) + u"""</p>
			<p>Almacén: """+ wp.f_warehouse_id.name + u"""</p>
			<p>Evaluación: """+ "Faltantes" + u"""</p>
			<p>-------------------------------------------------</p>
		"""

		values['body_html'] = txt
		values['res_id'] = False

		mmr = self.env['max.min.report'].display_q(wp.f_rotation, 'faltantes', [wp.f_warehouse_id.lot_stock_id.id])

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")

		f = open( direccion + u'Reporte_'+'faltantes'+'.xlsx', 'rb')

		att = {
			'name':u'Reporte_'+'faltantes'+'.xlsx',
			'type':'binary',
			'datas':base64.encodestring(''.join(f.readlines())),
			'datas_fname':u'Reporte_'+'faltantes'+'.xlsx',
		}
		att_id=self.pool.get('ir.attachment').create(self.env.cr,self.env.uid,att,self.env.context)

		values['attachment_ids'] = [(6,0,[att_id])]

		msg_id = self.env['mail.mail'].create(values)
		if msg_id:
			msg_id.send()

	@api.multi
	def display_q(self, rot, eva, wh_ids, shw):

		td = datetime.datetime.today()
		rd = td - datetime.timedelta(days=rot)
		td_str = str(td.year)+'-'+format(td.month,'02')+'-'+format(td.day,'02')
		rd_str = str(rd.year)+'-'+format(rd.month,'02')+'-'+format(rd.day,'02')

		qry = ""
		if eva == 'faltantes':
			qry = "where reponer > 0"
		elif eva == 'sobrantes':
			qry = "where sobrante > 0"

		wh_lst = "array["

		for i in wh_ids:
			wh_lst += str(i) + ","

		wh_lst = wh_lst[:-1]
		wh_lst += "]"

		self.env.cr.execute("""
			CREATE OR REPLACE view min_max_view as (
				SELECT row_number() OVER () AS id,* 
				FROM (

					select * from get_max_min("""+ str(rot) +""", '"""+ str(eva) +"""', '"""+ rd_str +"""', '"""+ td_str +"""',"""+ wh_lst +""")"""+qry+"""

				)T   )

			""")

		if shw == '1':
			return {
				"type": "ir.actions.act_window",
				"res_model": "min.max.view",
				"view_type": "form",
				"view_mode": "tree",
				"target": "current",
			}

		elif shw == '2':
			mmr = self.env['max.min.report'].display_q(rot, eva, wh_ids)

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			if not direccion:
				raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")
			
			f = open( direccion + u'Reporte_'+eva+'.xlsx', 'rb')
				
			vals = {
				'output_name': u'Reporte_'+eva+'.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			sfs_id = self.env['export.file.save'].create(vals)
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}

class max_min_report(models.Model):
	_name = 'max.min.report'

	@api.multi
	def display_q(self, rot, eva, wh_ids):

		td = datetime.datetime.today()
		rd = td - datetime.timedelta(days=rot)
		td_str = str(td.year)+'-'+format(td.month,'02')+'-'+format(td.day,'02')
		rd_str = str(rd.year)+'-'+format(rd.month,'02')+'-'+format(rd.day,'02')

		qry = ""
		if eva == 'faltantes':
			qry = "where reponer > 0"
		elif eva == 'sobrantes':
			qry = "where sobrante > 0"

		wh_lst = "array["

		for i in wh_ids:
			wh_lst += str(i) + ","

		wh_lst = wh_lst[:-1]
		wh_lst += "]"

		self.env.cr.execute("""
			CREATE OR REPLACE view min_max_view as (
				SELECT row_number() OVER () AS id,* 
				FROM (

					select * from get_max_min("""+ str(rot) +""", '"""+ str(eva) +"""', '"""+ rd_str +"""', '"""+ td_str +"""',"""+ wh_lst +""")"""+qry+"""

				)T   )

			""")

		import io
		from xlsxwriter.workbook import Workbook

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")
		workbook = Workbook( direccion + u'Reporte_'+eva+'.xlsx')
		worksheet = workbook.add_worksheet(eva)

		data_format_t = workbook.add_format()
		data_format_t.set_border(style=1)
		data_format_t.set_bold()
		data_format_t.set_italic()
		data_format_t.set_align('center')

		data_format_border = workbook.add_format()
		data_format_border.set_border(style=1)
		data_format_border.set_num_format('#,##0.00')

		data_format_bold = workbook.add_format()
		data_format_bold.set_bold()

		data_format_boldborder = workbook.add_format()
		data_format_boldborder.set_border(style=1)
		data_format_boldborder.set_bold()

		data_format_normal = workbook.add_format()

		worksheet.set_column("A:A", 48.14)
		worksheet.set_column("B:B", 19.29)
		worksheet.set_column("C:C", 56)
		worksheet.set_column("D:J", 15.71)

		header = [u'Producto',
				  u'Unidad de Medida',
				  u'Categoría',
				  u'Máximo',
				  u'Mínimo',
				  u'Rotación',
				  u'Saldo',
				  u'Reponer',
				  u'Evaluar',
				  u'Abastecimiento Día(s)',]

		worksheet.write(0,0, "REPORTE DE "+eva.upper(), data_format_bold)

		x = 2
		for i in range(len(header)):
			worksheet.write(x,i, header[i], data_format_t)

		x += 1

		for i in self.env['min.max.view'].search([]):
			worksheet.write(x,0, i.product_id.name_template if i.product_id.name_template != False else '', data_format_border )
			worksheet.write(x,1, i.uom_id.name if i.uom_id.name != False else '', data_format_border )
			worksheet.write(x,2, i.category if i.category != False else '', data_format_border )
			worksheet.write(x,3, i.maximo if i.maximo != False else 0, data_format_border )
			worksheet.write(x,4, i.minimo if i.minimo != False else 0, data_format_border )
			worksheet.write(x,5, i.rotation if i.rotation != False else 0, data_format_border )
			worksheet.write(x,6, i.saldo if i.saldo != False else 0, data_format_border )
			worksheet.write(x,7, i.reponer if i.reponer != False else 0, data_format_border)
			worksheet.write(x,8, i.sobrante if i.sobrante != False else 0, data_format_border)
			worksheet.write(x,9, i.abastecimiento if i.abastecimiento != False else 0, data_format_border)
			x += 1

		workbook.close()