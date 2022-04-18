# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class account_purchase_register_wizard(osv.TransientModel):
	_name='account.purchase.register.wizard'
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
			CREATE OR REPLACE view account_purchase_register as (
				SELECT * 
				FROM get_compra_1_1_1("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")


		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_purchase_register_it', 'action_account_purchase_register_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.purchase.register',
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
			workbook = Workbook(direccion + 'tempo_librocompras.xlsx')
			worksheet = workbook.add_worksheet("Registro Compras")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)


			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,20,"REGISTRO DE COMPRA",title)

			worksheet.write(1,0, "Registro Compras:", bold)
			tam_col[0] = tam_letra* len("Registro Compras:") if tam_letra* len("Registro Compras:")> tam_col[0] else tam_col[0]

			worksheet.write(1,1, self.period_ini.name, normal)
			tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

			worksheet.write(1,2, self.period_end.name, normal)
			tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

			worksheet.write(2,0, "Fecha:",bold)
			tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(2,1, str(datetime.datetime.today())[:10], normal)
			tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
			

			worksheet.write(4,0, "Periodo",boldbord)
			tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
			worksheet.write(4,1, "Libro",boldbord)
			tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
			worksheet.write(4,2, "Voucher",boldbord)
			tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
			worksheet.write(4,3, u"Fecha Emisión",boldbord)
			tam_col[3] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[3] else tam_col[3]
			worksheet.write(4,4, u"Fecha Vencimiento",boldbord)
			tam_col[4] = tam_letra* len(u"Fecha Vencimiento") if tam_letra* len(u"Fecha Vencimiento")> tam_col[4] else tam_col[4]
			worksheet.write(4,5, "TD.",boldbord)
			tam_col[5] = tam_letra* len("TD.") if tam_letra* len("TD.")> tam_col[5] else tam_col[5]
			worksheet.write(4,6, "Serie",boldbord)
			tam_col[6] = tam_letra* len("Serie") if tam_letra* len("Serie")> tam_col[6] else tam_col[6]
			worksheet.write(4,7, u"Año",boldbord)
			tam_col[7] = tam_letra* len(u"Año") if tam_letra* len(u"Año")> tam_col[7] else tam_col[7]
			worksheet.write(4,8, u"Número",boldbord)
			tam_col[8] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[8] else tam_col[8]
			worksheet.write(4,9, "TDP.",boldbord)
			tam_col[9] = tam_letra* len("TDP.") if tam_letra* len("TDP.")> tam_col[9] else tam_col[9]
			worksheet.write(4,10, "RUC/DNI",boldbord)
			tam_col[10] = tam_letra* len("RUC/DNI") if tam_letra* len("RUC/DNI")> tam_col[10] else tam_col[10]
			worksheet.write(4,11, u"Razon Social",boldbord)
			tam_col[11] = tam_letra* len(u"Razon Social") if tam_letra* len(u"Razon Social")> tam_col[11] else tam_col[11]
			worksheet.write(4,12, u"BIOGE",boldbord)
			tam_col[12] = tam_letra* len(u"BIOGE") if tam_letra* len(u"BIOGE")> tam_col[12] else tam_col[12]
			worksheet.write(4,13, u"BIOGENG",boldbord)
			tam_col[13] = tam_letra* len(u"BIOGENG") if tam_letra* len(u"BIOGENG")> tam_col[13] else tam_col[13]
			worksheet.write(4,14, "BIONG",boldbord)
			tam_col[14] = tam_letra* len("BIONG") if tam_letra* len("BIONG")> tam_col[14] else tam_col[14]
			worksheet.write(4,15, "CNG",boldbord)
			tam_col[15] = tam_letra* len("CNG") if tam_letra* len("CNG")> tam_col[15] else tam_col[15]
			worksheet.write(4,16, u"ISC",boldbord)
			tam_col[16] = tam_letra* len(u"ISC") if tam_letra* len(u"ISC")> tam_col[16] else tam_col[16]
			worksheet.write(4,17, u"IGVA",boldbord)
			tam_col[17] = tam_letra* len(u"IGVA") if tam_letra* len(u"IGVA")> tam_col[17] else tam_col[17]
			worksheet.write(4,18, u"IGVB",boldbord)
			tam_col[18] = tam_letra* len(u"IGVB") if tam_letra* len(u"IGVB")> tam_col[18] else tam_col[18]
			worksheet.write(4,19, u"IGBC",boldbord)
			tam_col[19] = tam_letra* len(u"IGBC") if tam_letra* len(u"IGBC")> tam_col[19] else tam_col[19]
			worksheet.write(4,20, u"Otros",boldbord)
			tam_col[20] = tam_letra* len(u"Otros") if tam_letra* len(u"Otros")> tam_col[20] else tam_col[20]
			worksheet.write(4,21, u"Total",boldbord)
			tam_col[21] = tam_letra* len(u"Total") if tam_letra* len(u"Total")> tam_col[21] else tam_col[21]
			worksheet.write(4,22, u"CSND",boldbord)
			tam_col[22] = tam_letra* len(u"CSND") if tam_letra* len(u"CSND")> tam_col[22] else tam_col[22]
			worksheet.write(4,23, u"Moneda",boldbord)
			tam_col[23] = tam_letra* len(u"Moneda") if tam_letra* len(u"Moneda")> tam_col[23] else tam_col[23]
			worksheet.write(4,24, u"TC.",boldbord)
			tam_col[24] = tam_letra* len(u"TC.") if tam_letra* len(u"TC.")> tam_col[24] else tam_col[24]
			worksheet.write(4,25, u"Fecha Doc.",boldbord)
			tam_col[25] = tam_letra* len(u"Fecha Doc.") if tam_letra* len(u"Fecha Doc.")> tam_col[25] else tam_col[25]
			worksheet.write(4,26, u"Número Doc",boldbord)
			tam_col[26] = tam_letra* len(u"Número Doc") if tam_letra* len(u"Número Doc")> tam_col[26] else tam_col[26]
			worksheet.write(4,27, u"F. Doc. M.",boldbord)
			tam_col[27] = tam_letra* len(u"F. Doc. M.") if tam_letra* len(u"F. Doc. M.")> tam_col[27] else tam_col[27]
			worksheet.write(4,28, u"TD Doc.",boldbord)
			tam_col[28] = tam_letra* len(u"TD Doc.") if tam_letra* len(u"TD Doc.")> tam_col[28] else tam_col[28]
			worksheet.write(4,29, u"Serie",boldbord)
			tam_col[29] = tam_letra* len(u"Serie") if tam_letra* len(u"Serie")> tam_col[29] else tam_col[29]
			worksheet.write(4,30, u"Número",boldbord)
			tam_col[30] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[30] else tam_col[30]


			for line in self.env['account.purchase.register'].search([]):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,4,line.fechavencimiento if line.fechavencimiento else '',bord)
				worksheet.write(x,5,line.tipodocumento if line.tipodocumento else '',bord)
				worksheet.write(x,6,line.serie if line.serie else '',bord)
				worksheet.write(x,7,line.anio if line.anio else '',bord)
				worksheet.write(x,8,line.numero if line.numero  else '',bord)
				worksheet.write(x,9,line.tdp if line.tdp  else '',bord)
				worksheet.write(x,10,line.ruc if line.ruc  else '',bord)
				worksheet.write(x,11,line.razonsocial if line.razonsocial  else '',bord)
				worksheet.write(x,12,line.bioge ,numberdos)
				worksheet.write(x,13,line.biogeng ,numberdos)
				worksheet.write(x,14,line.biong ,numberdos)
				worksheet.write(x,15,line.cng ,numberdos)
				worksheet.write(x,16,line.isc ,numberdos)
				worksheet.write(x,17,line.igva ,numberdos)
				worksheet.write(x,18,line.igvb ,numberdos)
				worksheet.write(x,19,line.igvc ,numberdos)
				worksheet.write(x,20,line.otros ,numberdos)
				worksheet.write(x,21,line.total ,numberdos)
				worksheet.write(x,22,line.comprobante if line.comprobante  else '',bord)
				worksheet.write(x,23,line.moneda if  line.moneda else '',bord)
				worksheet.write(x,24,line.tc ,numbertres)
				worksheet.write(x,25,line.fechad if line.fechad else '',bord)
				worksheet.write(x,26,line.numerod if line.numerod else '',bord)
				worksheet.write(x,27,line.fechadm if line.fechadm else '',bord)
				worksheet.write(x,28,line.td if line.td else '',bord)
				worksheet.write(x,29,line.seried if line.seried else '',bord)
				worksheet.write(x,30,line.numerodd if line.numerodd else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len(line.serie if line.serie else '') if tam_letra* len(line.serie if line.serie else '')> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len(line.anio if line.anio else '') if tam_letra* len(line.anio if line.anio else '')> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.tdp if line.tdp  else '') if tam_letra* len(line.tdp if line.tdp  else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len(line.ruc if line.ruc  else '') if tam_letra* len(line.ruc if line.ruc  else '')> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.razonsocial if line.razonsocial  else '') if tam_letra* len(line.razonsocial if line.razonsocial  else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len("%0.2f"%line.bioge ) if tam_letra* len("%0.2f"%line.bioge )> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len("%0.2f"%line.biogeng ) if tam_letra* len("%0.2f"%line.biogeng )> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len("%0.2f"%line.biong ) if tam_letra* len("%0.2f"%line.biong )> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len("%0.2f"%line.cng ) if tam_letra* len("%0.2f"%line.cng )> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len("%0.2f"%line.isc ) if tam_letra* len("%0.2f"%line.isc )> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len("%0.2f"%line.igva ) if tam_letra* len("%0.2f"%line.igva )> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len("%0.2f"%line.igvb ) if tam_letra* len("%0.2f"%line.igvb )> tam_col[18] else tam_col[18]
				tam_col[19] = tam_letra* len("%0.2f"%line.igvc ) if tam_letra* len("%0.2f"%line.igvc )> tam_col[19] else tam_col[19]
				tam_col[20] = tam_letra* len("%0.2f"%line.otros ) if tam_letra* len("%0.2f"%line.otros )> tam_col[20] else tam_col[20]
				tam_col[21] = tam_letra* len("%0.2f"%line.total ) if tam_letra* len("%0.2f"%line.total )> tam_col[21] else tam_col[21]
				tam_col[22] = tam_letra* len(line.comprobante if line.comprobante  else '') if tam_letra* len(line.comprobante if line.comprobante  else '')> tam_col[22] else tam_col[22]
				tam_col[23] = tam_letra* len(line.moneda if  line.moneda else '') if tam_letra* len(line.moneda if  line.moneda else '')> tam_col[23] else tam_col[23]
				tam_col[24] = tam_letra* len("%0.3f"%line.tc ) if tam_letra* len("%0.3f"%line.tc )> tam_col[24] else tam_col[24]
				tam_col[25] = tam_letra* len(line.fechad if line.fechad else '') if tam_letra* len(line.fechad if line.fechad else '')> tam_col[25] else tam_col[25]
				tam_col[26] = tam_letra* len(line.numerod if line.numerod else '') if tam_letra* len(line.numerod if line.numerod else '')> tam_col[26] else tam_col[26]
				tam_col[27] = tam_letra* len(line.fechadm if line.fechadm else '') if tam_letra* len(line.fechadm if line.fechadm else '')> tam_col[27] else tam_col[27]
				tam_col[28] = tam_letra* len(line.td if line.td else '') if tam_letra* len(line.td if line.td else '')> tam_col[28] else tam_col[28]
				tam_col[29] = tam_letra* len(line.seried if line.seried else '') if tam_letra* len(line.seried if line.seried else '')> tam_col[29] else tam_col[29]
				tam_col[30] = tam_letra* len(line.numerodd if line.numerodd else '') if tam_letra* len(line.numerodd if line.numerodd else '')> tam_col[30] else tam_col[30]

				x = x +1


			tam_col = [16.4,7.14,8.5,13,13,3.6,6,4.5,8,4.3,13,32,11,11,11,11,11,11,11,11,11,11,5,6,9,13,13,13,9,7,9]

			worksheet.set_row(0, 30)

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

			worksheet.set_column('U:U', tam_col[20])
			worksheet.set_column('V:V', tam_col[21])
			worksheet.set_column('W:W', tam_col[22])
			worksheet.set_column('X:X', tam_col[23])
			worksheet.set_column('Y:Y', tam_col[24])
			worksheet.set_column('Z:Z', tam_col[25])
			worksheet.set_column('AA:AA', tam_col[26])
			worksheet.set_column('AB:AB', tam_col[27])
			worksheet.set_column('AC:AC', tam_col[28])
			worksheet.set_column('AD:AD', tam_col[29])
			worksheet.set_column('AE:AE', tam_col[30])

			workbook.close()
			
			f = open( direccion + 'tempo_librocompras.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'RegistroCompras.xlsx',
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
		tmp = self.csv_verif(data.periodo)
		tmp += separador+ self.csv_verif(data.libro)
		tmp += separador+ self.csv_verif(data.voucher)
		tmp += separador+ self.csv_verif(data.fechaemision)
		tmp += separador+ self.csv_verif(data.fechavencimiento)
		tmp += separador+ self.csv_verif(data.tipodocumento)
		tmp += separador+ self.csv_verif(data.serie)
		tmp += separador+ self.csv_verif(data.numero)
		tmp += separador+ self.csv_verif(data.anio)
		tmp += separador+ self.csv_verif(data.tdp)
		tmp += separador+ self.csv_verif(data.ruc)
		tmp += separador+ self.csv_verif(data.razonsocial)
		tmp += separador+ self.csv_verif_integer(data.bioge)
		tmp += separador+ self.csv_verif_integer(data.biogeng)
		tmp += separador+ self.csv_verif_integer(data.biong)
		tmp += separador+ self.csv_verif_integer(data.cng)
		tmp += separador+ self.csv_verif_integer(data.isc)
		tmp += separador+ self.csv_verif_integer(data.igva)
		tmp += separador+ self.csv_verif_integer(data.igvb)
		tmp += separador+ self.csv_verif_integer(data.igvc)
		tmp += separador+ self.csv_verif_integer(data.otros)
		tmp += separador+ self.csv_verif_integer(data.total)
		tmp += separador+ self.csv_verif(data.comprobante)
		tmp += separador+ self.csv_verif(data.moneda)
		tmp += separador+ self.csv_verif_integer(data.tc)
		tmp += separador+ self.csv_verif(data.fechad)
		tmp += separador+ self.csv_verif(data.numerod)
		tmp += separador+ self.csv_verif(data.fechadm)
		tmp += separador+ self.csv_verif(data.td)
		tmp += separador+ self.csv_verif(data.seried)
		tmp += separador+ self.csv_verif(data.numerodd)
		tmp += separador
		return unicode(tmp)
	@api.multi
	def cabezera_csv(self,separador):
		tmp = self.csv_verif("Periodo")
		tmp += separador+ self.csv_verif("Libro")
		tmp += separador+ self.csv_verif("Voucher")
		tmp += separador+ self.csv_verif("Fecha Emision")
		tmp += separador+ self.csv_verif("Fecha Vencimiento")
		tmp += separador+ self.csv_verif("Tipo de Documento")
		tmp += separador+ self.csv_verif("Serie")
		tmp += separador+ self.csv_verif("Numero")
		tmp += separador+ self.csv_verif("Año")
		tmp += separador+ self.csv_verif("Tipo Documento")
		tmp += separador+ self.csv_verif("Nro. Documento")
		tmp += separador+ self.csv_verif("Partner")
		tmp += separador+ self.csv_verif("Bioge")
		tmp += separador+ self.csv_verif("Biogeng")
		tmp += separador+ self.csv_verif("Biong")
		tmp += separador+ self.csv_verif("Cng")
		tmp += separador+ self.csv_verif("Isc")
		tmp += separador+ self.csv_verif("IgvA")
		tmp += separador+ self.csv_verif("IgvB")
		tmp += separador+ self.csv_verif("IgvC")
		tmp += separador+ self.csv_verif("Otros")
		tmp += separador+ self.csv_verif("Total")
		tmp += separador+ self.csv_verif("Comprobante Nro. Domicilio")
		tmp += separador+ self.csv_verif("Moneda")
		tmp += separador+ self.csv_verif("T.C.")
		tmp += separador+ self.csv_verif("Fecha D.")
		tmp += separador+ self.csv_verif("Numero D.")
		tmp += separador+ self.csv_verif("Fecha D.M.")
		tmp += separador+ self.csv_verif("T.D.")
		tmp += separador+ self.csv_verif("Serie D.")
		tmp += separador+ self.csv_verif("Numero D.")
		tmp += separador
		return unicode(tmp)