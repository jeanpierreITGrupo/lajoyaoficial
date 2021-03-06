# -*- coding: utf-8 -*-
import time
from lxml import etree
import pprint
from openerp import models, fields, api
from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp
import base64

class account_account(models.Model):
	_inherit = 'account.account'

	tipo_adquisicion_diario = fields.Selection([('1','Mercaderia'),('2','Activo Fijo'),('3','Otros Activo'),('4','Gastos de Educacion, Recreación, Salud, Mantenimiento de Activos'),('5','Otros no incluidos en 4')],'Tipo de Adquisición')


class account_move_line_book(models.Model):
	_inherit = 'account.move.line.book'
	_auto = False

	tipo_adquisicion_diario = fields.Selection([('1','Mercaderia'),('2','Activo Fijo'),('3','Otros Activo'),('4','Gastos de Educacion, Recreación, Salud, Mantenimiento de Activos'),('5','Otros no incluidos en 4')],'Tipo de Adquisición')


class account_move_line_book_report(models.Model):
	_inherit = 'account.move.line.book.report'
	_auto = False

	tipo_adquisicion_diario = fields.Selection([('1','Mercaderia'),('2','Activo Fijo'),('3','Otros Activo'),('4','Gastos de Educacion, Recreación, Salud, Mantenimiento de Activos'),('5','Otros no incluidos en 4')],'Tipo de Adquisición')




class account_move_line_book_report_wizard(models.TransientModel):
	_inherit ='account.move.line.book.report.wizard'
	

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
				
		self.env.cr.execute("""
			CREATE OR REPLACE view account_move_line_book_report as (
				SELECT X.* , aa.tipo_adquisicion_diario
				FROM get_libro_diario("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) as X
				left join account_account aa on aa.id = X.aa_id
		)""")

		filtro.append( ('statefiltro','=','posted') )
		
		if self.type_show == 'pantalla':

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_contable_book_it', 'action_account_moves_all_report_it')
			id = result and result[1] or False
			print id
			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.move.line.book.report',
				'view_mode': 'tree',
				'view_type': 'form',
				'res_id': id,
				'views': [(False, 'tree')],
			}



		if self.type_show == 'excel':

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_librodiario.xlsx')
			worksheet = workbook.add_worksheet("Libro Diario")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "Libro Diario:", bold)
			tam_col[0] = tam_letra* len("Libro Diario:") if tam_letra* len("Libro Diario:")> tam_col[0] else tam_col[0]

			worksheet.write(0,1, self.period_ini.name, normal)
			tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

			worksheet.write(0,2, self.period_end.name, normal)
			tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

			worksheet.write(1,0, "Fecha:",bold)
			tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
			tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
			

			worksheet.write(3,0, "Periodo",boldbord)
			tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
			worksheet.write(3,1, "Libro",boldbord)
			tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
			worksheet.write(3,2, "Voucher",boldbord)
			tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
			worksheet.write(3,3, "Cuenta",boldbord)
			tam_col[3] = tam_letra* len("Cuenta") if tam_letra* len("Cuenta")> tam_col[3] else tam_col[3]
			worksheet.write(3,4, "Debe",boldbord)
			tam_col[4] = tam_letra* len("Debe") if tam_letra* len("Debe")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "Haber",boldbord)
			tam_col[5] = tam_letra* len("Haber") if tam_letra* len("Haber")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Divisa",boldbord)
			tam_col[6] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, "Tipo Cambio",boldbord)
			tam_col[7] = tam_letra* len("Tipo Cambio") if tam_letra* len("Tipo Cambio")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "Importe Divisa",boldbord)
			tam_col[8] = tam_letra* len("Importe Divisa") if tam_letra* len("Importe Divisa")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, u"Código",boldbord)
			tam_col[9] = tam_letra* len(u"Código") if tam_letra* len(u"Código")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Partner",boldbord)
			tam_col[10] = tam_letra* len("Partner") if tam_letra* len("Partner")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, "Tipo Documento",boldbord)
			tam_col[11] = tam_letra* len("Tipo Documento") if tam_letra* len("Tipo Documento")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Número",boldbord)
			tam_col[12] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Fecha Emisión",boldbord)
			tam_col[13] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, "Fecha Vencimiento",boldbord)
			tam_col[14] = tam_letra* len("Fecha Vencimiento") if tam_letra* len("Fecha Vencimiento")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, "Glosa",boldbord)
			tam_col[15] = tam_letra* len("Glosa") if tam_letra* len("Glosa")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Cta. Analítica",boldbord)
			tam_col[16] = tam_letra* len(u"Cta. Analítica") if tam_letra* len(u"Cta. Analítica")> tam_col[16] else tam_col[16]
			worksheet.write(3,17, u"Referencia Conciliación",boldbord)
			tam_col[17] = tam_letra* len(u"Referencia Conciliación") if tam_letra* len(u"Referencia Conciliación")> tam_col[17] else tam_col[17]

			worksheet.write(3,18, u"Estado",boldbord)
			tam_col[18] = tam_letra* len(u"Estado") if tam_letra* len(u"Estado")> tam_col[18] else tam_col[18]

			worksheet.write(3,19, u"Flujo Caja",boldbord)
			worksheet.write(3,20, u"Tipo de Adquisición",boldbord)
			

			for line in self.env['account.move.line.book.report'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,4,line.debe ,numberdos)
				worksheet.write(x,5,line.haber ,numberdos)
				worksheet.write(x,6,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,7,line.tipodecambio ,numbertres)
				worksheet.write(x,8,line.importedivisa ,numberdos)
				worksheet.write(x,9,line.codigo if line.codigo else '',bord)
				worksheet.write(x,10,line.partner if line.partner else '',bord)
				worksheet.write(x,11,line.tipodocumento if line.tipodocumento else '',bord)
				worksheet.write(x,12,line.numero if line.numero  else '',bord)
				worksheet.write(x,13,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,14,line.fechavencimiento if line.fechavencimiento else '',bord)
				worksheet.write(x,15,line.glosa if line.glosa else '',bord)
				worksheet.write(x,16,line.ctaanalitica if line.ctaanalitica  else '',bord)
				worksheet.write(x,17,line.refconcil if line.refconcil  else '',bord)
				worksheet.write(x,18,line.state if line.state  else '',bord)
				worksheet.write(x,19,(line.flujo_caja_id.name + '-' + line.flujo_caja_id.concepto) if line.flujo_caja_id.name  else '',bord)
				worksheet.write(x,20,line.tipo_adquisicion_diario if line.tipo_adquisicion_diario  else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.cuenta if line.cuenta  else '') if tam_letra* len(line.cuenta if line.cuenta  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len("%0.2f"%line.debe ) if tam_letra* len("%0.2f"%line.debe )> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len("%0.2f"%line.haber ) if tam_letra* len("%0.2f"%line.haber )> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len("%0.3f"%line.tipodecambio ) if tam_letra* len("%0.3f"%line.tipodecambio )> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len("%0.2f"%line.importedivisa ) if tam_letra* len("%0.2f"%line.importedivisa )> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.codigo if line.codigo else '') if tam_letra* len(line.codigo if line.codigo else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len(line.partner if line.partner else '') if tam_letra* len(line.partner if line.partner else '')> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '') if tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '')> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len(line.refconcil if line.refconcil  else '') if tam_letra* len(line.refconcil if line.refconcil  else '')> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len(line.state if line.state  else '') if tam_letra* len(line.state if line.state  else '')> tam_col[18] else tam_col[18]
				x = x +1


			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10,10]

			worksheet.set_row(3, 60)
			
			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			worksheet.set_column('G:G', tam_col[6])
			worksheet.set_column('H:H', tam_col[7])
			worksheet.set_column('I:I', tam_col[8])
			worksheet.set_column('J:J', tam_col[9])
			worksheet.set_column('K:K', tam_col[10])
			worksheet.set_column('L:L', tam_col[11])
			worksheet.set_column('M:M', tam_col[12])
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:T', tam_col[19])

			workbook.close()
			
			f = open( direccion + 'tempo_librodiario.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'LibroDiario.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			print sfs_id
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}



class account_move_line_book_wizard(models.TransientModel):
	_inherit='account.move.line.book.wizard'
	

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
			
		self.env.cr.execute("""
			CREATE OR REPLACE view account_move_line_book as (
				SELECT X.* , aa.tipo_adquisicion_diario
				FROM get_libro_diario("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) as X
				left join account_account aa on aa.id = X.aa_id
		)""")

		if self.asientos:
			if self.asientos == 'posted':
				filtro.append( ('statefiltro','=','posted') )
			if self.asientos == 'draft':
				filtro.append( ('statefiltro','=','draft') )
		
		if self.libros:
			libros_list = []
			for i in  self.libros:
				libros_list.append(i.code)
			filtro.append( ('libro','in',tuple(libros_list)) )
		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_contable_book_it', 'action_account_moves_all_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.move.line.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'res_id': id,
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_librodiario.xlsx')
			worksheet = workbook.add_worksheet("Libro Diario")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "Libro Diario:", bold)
			tam_col[0] = tam_letra* len("Libro Diario:") if tam_letra* len("Libro Diario:")> tam_col[0] else tam_col[0]

			worksheet.write(0,1, self.period_ini.name, normal)
			tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

			worksheet.write(0,2, self.period_end.name, normal)
			tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

			worksheet.write(1,0, "Fecha:",bold)
			tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
			tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
			

			worksheet.write(3,0, "Periodo",boldbord)
			tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
			worksheet.write(3,1, "Libro",boldbord)
			tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
			worksheet.write(3,2, "Voucher",boldbord)
			tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
			worksheet.write(3,3, "Cuenta",boldbord)
			tam_col[3] = tam_letra* len("Cuenta") if tam_letra* len("Cuenta")> tam_col[3] else tam_col[3]
			worksheet.write(3,4, "Debe",boldbord)
			tam_col[4] = tam_letra* len("Debe") if tam_letra* len("Debe")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "Haber",boldbord)
			tam_col[5] = tam_letra* len("Haber") if tam_letra* len("Haber")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Divisa",boldbord)
			tam_col[6] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, "Tipo Cambio",boldbord)
			tam_col[7] = tam_letra* len("Tipo Cambio") if tam_letra* len("Tipo Cambio")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "Importe Divisa",boldbord)
			tam_col[8] = tam_letra* len("Importe Divisa") if tam_letra* len("Importe Divisa")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, u"Código",boldbord)
			tam_col[9] = tam_letra* len(u"Código") if tam_letra* len(u"Código")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Partner",boldbord)
			tam_col[10] = tam_letra* len("Partner") if tam_letra* len("Partner")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, "Tipo Documento",boldbord)
			tam_col[11] = tam_letra* len("Tipo Documento") if tam_letra* len("Tipo Documento")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Número",boldbord)
			tam_col[12] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Fecha Emisión",boldbord)
			tam_col[13] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, "Fecha Vencimiento",boldbord)
			tam_col[14] = tam_letra* len("Fecha Vencimiento") if tam_letra* len("Fecha Vencimiento")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, "Glosa",boldbord)
			tam_col[15] = tam_letra* len("Glosa") if tam_letra* len("Glosa")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Cta. Analítica",boldbord)
			tam_col[16] = tam_letra* len(u"Cta. Analítica") if tam_letra* len(u"Cta. Analítica")> tam_col[16] else tam_col[16]
			worksheet.write(3,17, u"Referencia Conciliación",boldbord)
			tam_col[17] = tam_letra* len(u"Referencia Conciliación") if tam_letra* len(u"Referencia Conciliación")> tam_col[17] else tam_col[17]

			worksheet.write(3,18, u"Estado",boldbord)
			tam_col[18] = tam_letra* len(u"Estado") if tam_letra* len(u"Estado")> tam_col[18] else tam_col[18]
			worksheet.write(3,19, u"Flujo Caja",boldbord)
			worksheet.write(3,20, u"Tipo de Adquisición",boldbord)
			
			for line in self.env['account.move.line.book'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,4,line.debe ,numberdos)
				worksheet.write(x,5,line.haber ,numberdos)
				worksheet.write(x,6,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,7,line.tipodecambio ,numbertres)
				worksheet.write(x,8,line.importedivisa ,numberdos)
				worksheet.write(x,9,line.codigo if line.codigo else '',bord)
				worksheet.write(x,10,line.partner if line.partner else '',bord)
				worksheet.write(x,11,line.tipodocumento if line.tipodocumento else '',bord)
				worksheet.write(x,12,line.numero if line.numero  else '',bord)
				worksheet.write(x,13,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,14,line.fechavencimiento if line.fechavencimiento else '',bord)
				worksheet.write(x,15,line.glosa if line.glosa else '',bord)
				worksheet.write(x,16,line.ctaanalitica if line.ctaanalitica  else '',bord)
				worksheet.write(x,17,line.refconcil if line.refconcil  else '',bord)
				worksheet.write(x,18,line.state if line.state  else '',bord)
				worksheet.write(x,19,(line.flujo_caja_id.name + '-' + line.flujo_caja_id.concepto) if line.flujo_caja_id.name  else '',bord)
				worksheet.write(x,20,line.tipo_adquisicion_diario if line.tipo_adquisicion_diario  else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.cuenta if line.cuenta  else '') if tam_letra* len(line.cuenta if line.cuenta  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len("%0.2f"%line.debe ) if tam_letra* len("%0.2f"%line.debe )> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len("%0.2f"%line.haber ) if tam_letra* len("%0.2f"%line.haber )> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len("%0.3f"%line.tipodecambio ) if tam_letra* len("%0.3f"%line.tipodecambio )> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len("%0.2f"%line.importedivisa ) if tam_letra* len("%0.2f"%line.importedivisa )> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.codigo if line.codigo else '') if tam_letra* len(line.codigo if line.codigo else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len(line.partner if line.partner else '') if tam_letra* len(line.partner if line.partner else '')> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '') if tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '')> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len(line.refconcil if line.refconcil  else '') if tam_letra* len(line.refconcil if line.refconcil  else '')> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len(line.state if line.state  else '') if tam_letra* len(line.state if line.state  else '')> tam_col[18] else tam_col[18]
				x = x +1


			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10,10]

			worksheet.set_row(3, 60)
			
			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			worksheet.set_column('G:G', tam_col[6])
			worksheet.set_column('H:H', tam_col[7])
			worksheet.set_column('I:I', tam_col[8])
			worksheet.set_column('J:J', tam_col[9])
			worksheet.set_column('K:K', tam_col[10])
			worksheet.set_column('L:L', tam_col[11])
			worksheet.set_column('M:M', tam_col[12])
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:T', tam_col[19])

			workbook.close()
			
			f = open( direccion + 'tempo_librodiario.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'LibroDiario.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			print sfs_id
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}


