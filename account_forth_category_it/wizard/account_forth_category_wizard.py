# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class account_forth_category_wizard(osv.TransientModel):
	_name='account.forth.category.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	moneda = fields.Many2one('res.currency','Moneda')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')], 'Mostrar en', required=True)
	
	
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)



	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'period_end':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'period_ini':[], 'period_end':[]}}

	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini


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
			CREATE OR REPLACE view account_forth_category as (
				SELECT * 
				FROM get_honorarios_1_1_1("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")

		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_forth_category_it', 'action_account_forth_category')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.forth.category',
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
			workbook = Workbook( direccion + 'tempo_cuartacategoria.xlsx')
			worksheet = workbook.add_worksheet("Libro Honorarios")
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
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "Libro Honorarios:", bold)
			tam_col[0] = tam_letra* len("Libro Honorarios:") if tam_letra* len("Libro Honorarios:")> tam_col[0] else tam_col[0]

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
			worksheet.write(3,3, u"Fecha Emisión",boldbord)
			tam_col[3] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[3] else tam_col[3]
			worksheet.write(3,4, u"Fecha Pago",boldbord)
			tam_col[4] = tam_letra* len(u"Fecha Pago") if tam_letra* len(u"Fecha Pago")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "TD.",boldbord)
			tam_col[5] = tam_letra* len("TD.") if tam_letra* len("TD.")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Serie",boldbord)
			tam_col[6] = tam_letra* len("Serie") if tam_letra* len("Serie")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, u"Número",boldbord)
			tam_col[7] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "TDP.",boldbord)
			tam_col[8] = tam_letra* len("TDP.") if tam_letra* len("TDP.")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, "Num. Documento",boldbord)
			tam_col[9] = tam_letra* len("Num. Documento") if tam_letra* len("Num. Documento")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Razon Social",boldbord)
			tam_col[10] = tam_letra* len("Razon Social") if tam_letra* len("Razon Social")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, u"Divisa",boldbord)
			tam_col[11] = tam_letra* len(u"Divisa") if tam_letra* len(u"Divisa")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Monto",boldbord)
			tam_col[12] = tam_letra* len(u"Monto") if tam_letra* len(u"Monto")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Retención",boldbord)
			tam_col[13] = tam_letra* len(u"Retención") if tam_letra* len(u"Retención")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, "Neto Pagado",boldbord)
			tam_col[14] = tam_letra* len("Neto Pagado") if tam_letra* len("Neto Pagado")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, "Estado",boldbord)
			tam_col[15] = tam_letra* len("Estado") if tam_letra* len("Estado")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Periodo Pago",boldbord)
			tam_col[16] = tam_letra* len(u"Periodo Pago") if tam_letra* len(u"Periodo Pago")> tam_col[16] else tam_col[16]
			
			for line in self.env['account.forth.category'].search([]):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.fechaemision if line.fechaemision  else '',bord)
				worksheet.write(x,4,line.fechapago if line.fechapago  else '',bord)
				worksheet.write(x,5,line.tipodocumento if  line.tipodocumento else '',bord)
				worksheet.write(x,6,line.serie if line.serie else '',bord)
				worksheet.write(x,7,line.numero if line.numero else '',bord)
				worksheet.write(x,8,line.tipodoc if line.tipodoc else '',bord)
				worksheet.write(x,9,line.numdoc if line.numdoc else '',bord)
				worksheet.write(x,10,line.partner if line.partner else '',bord)
				worksheet.write(x,11,line.divisa if line.divisa  else '',bord)				
				worksheet.write(x,12,line.monto  ,numberdos)
				worksheet.write(x,13,line.retencion  ,numberdos)
				worksheet.write(x,14,line.neto  ,numberdos)
				worksheet.write(x,15,line.state if line.state else '',bord)
				worksheet.write(x,16,line.periodopago if line.periodopago else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.fechaemision if line.fechaemision  else '') if tam_letra* len(line.fechaemision if line.fechaemision  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len(line.fechapago if line.fechapago  else '') if tam_letra* len(line.fechapago if line.fechapago  else '')> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len(line.tipodocumento if  line.tipodocumento else '') if tam_letra* len(line.tipodocumento if  line.tipodocumento else '')> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len(line.serie if line.serie else '') if tam_letra* len(line.serie if line.serie else '')> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len(line.numero if line.numero else '') if tam_letra* len(line.numero if line.numero else '')> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len(line.tipodoc if line.tipodoc else '') if tam_letra* len(line.tipodoc if line.tipodoc else '')> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.numdoc if line.numdoc else '') if tam_letra* len(line.numdoc if line.numdoc else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len(line.partner if line.partner else '') if tam_letra* len(line.partner if line.partner else '')> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.divisa if line.divisa  else '') if tam_letra* len(line.divisa if line.divisa  else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len("%0.2f"%line.monto  ) if tam_letra* len("%0.2f"%line.monto  )> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len("%0.2f"%line.retencion  ) if tam_letra* len("%0.2f"%line.retencion  )> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len("%0.2f"%line.neto  ) if tam_letra* len("%0.2f"%line.neto  )> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.state if line.state else '') if tam_letra* len(line.state if line.state else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.periodopago if line.periodopago else '') if tam_letra* len(line.periodopago if line.periodopago else '')> tam_col[16] else tam_col[16]

				x = x +1

			tam_col = [15.5,7.14,9,14,14,8,9,11,9,17,26,7,11,11,11,8,12]

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

			workbook.close()
			
			f = open( direccion + 'tempo_cuartacategoria.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'LibroHonorarios.xlsx',
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



	@api.multi
	def csv_verif_integer(self,data):
		if data:
			return '"' + str(data) + '"'
		else:
			return '""'

	@api.multi
	def csv_verif(self,data):
		if data:
			return '"' + data.replace('"','\'') + '"'
		else:
			return '""'
	@api.multi
	def csv_convert(self,data,separador):
		tmp = separador + self.csv_verif(data.periodo)
		tmp += separador+ self.csv_verif(data.libro)
		tmp += separador+ self.csv_verif(data.voucher)
		tmp += separador+ self.csv_verif(data.fechaemision)
		tmp += separador+ self.csv_verif(data.fechapago)
		tmp += separador+ self.csv_verif(data.tipodocumento)
		tmp += separador+ self.csv_verif(data.serie)
		tmp += separador+ self.csv_verif(data.numero)
		tmp += separador+ self.csv_verif(data.tipodoc)
		tmp += separador+ self.csv_verif(data.numdoc)
		tmp += separador+ self.csv_verif(data.partner)
		tmp += separador+ self.csv_verif_integer(data.monto)
		tmp += separador+ self.csv_verif_integer(data.retencion)
		tmp += separador+ self.csv_verif_integer(data.neto)
		tmp += separador+ self.csv_verif(data.state)
		tmp += separador+ self.csv_verif(data.periodopago)
		tmp += separador
		return unicode(tmp)
	
	@api.multi
	def cabezera_csv(self,separador):		
		tmp = separador + self.csv_verif("Periodo")
		tmp += separador+ self.csv_verif("Libro")
		tmp += separador+ self.csv_verif("Voucher")
		tmp += separador+ self.csv_verif("Fecha Emision")
		tmp += separador+ self.csv_verif("Fecha Pago")
		tmp += separador+ self.csv_verif("T.C.")
		tmp += separador+ self.csv_verif("Serie")
		tmp += separador+ self.csv_verif("Número")
		tmp += separador+ self.csv_verif("T.D.P")
		tmp += separador+ self.csv_verif("Num. Documento")
		tmp += separador+ self.csv_verif("Razón Social")
		tmp += separador+ self.csv_verif("Monto")
		tmp += separador+ self.csv_verif("Retención")
		tmp += separador+ self.csv_verif("Neto Pagado")
		tmp += separador+ self.csv_verif("Estado")
		tmp += separador+ self.csv_verif("Periodo Pago")
		tmp += separador
		return tmp