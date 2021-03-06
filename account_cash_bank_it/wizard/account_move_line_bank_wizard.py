# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class account_move_line_bank_wizard(osv.TransientModel):
	_name='account.move.line.bank.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	#asientos =  fields.Selection([('posted','Asentados'),('draft','No Asentados'),('both','Ambos')], 'Asientos')
	moneda = fields.Many2one('res.currency','Moneda')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')], 'Mostrar en', required=True)
	cuentas = fields.Many2many('account.account','account_bank_account_rel','id_bank_origen','id_account_destino', string='Cuentas', required=True)



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
			CREATE OR REPLACE view account_move_line_bank as (
				SELECT * 
				FROM get_cajabanco_with_saldoinicial("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")

		if self.cuentas:
			cuentas_list = ["Saldo Inicial"]
			for i in self.cuentas:
				cuentas_list.append(i.code)
			filtro.append( ('cuentacode','in',tuple(cuentas_list)) )
		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_cash_bank_it', 'action_account_moves_bank_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.move.line.bank',
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
			workbook = Workbook( direccion + 'tempo_cajabanco.xlsx')
			worksheet = workbook.add_worksheet("Libro Caja y Banco")
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
			tam_letra = 1
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "Libro Caja y Banco:", bold)
			tam_col[0] = tam_letra* len("Libro Caja y Banco:") if tam_letra* len("Libro Caja y Banco:")> tam_col[0] else tam_col[0]

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
			worksheet.write(3,4, u"Descripción",boldbord)
			tam_col[4] = tam_letra* len(u"Descripción") if tam_letra* len(u"Descripción")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "Concepto",boldbord)
			tam_col[5] = tam_letra* len("Concepto") if tam_letra* len("Concepto")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Ingreso",boldbord)
			tam_col[6] = tam_letra* len("Ingreso") if tam_letra* len("Ingreso")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, "Egreso",boldbord)
			tam_col[7] = tam_letra* len("Egreso") if tam_letra* len("Egreso")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "Saldo",boldbord)
			tam_col[8] = tam_letra* len("Saldo") if tam_letra* len("Saldo")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, "Divisa",boldbord)
			tam_col[9] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Tipo Cambio",boldbord)
			tam_col[10] = tam_letra* len("Tipo Cambio") if tam_letra* len("Tipo Cambio")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, u"Importe Divisa",boldbord)
			tam_col[11] = tam_letra* len(u"Importe Divisa") if tam_letra* len(u"Importe Divisa")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Fecha",boldbord)
			tam_col[12] = tam_letra* len(u"Fecha") if tam_letra* len(u"Fecha")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Medio Pago",boldbord)
			tam_col[13] = tam_letra* len(u"Medio Pago") if tam_letra* len(u"Medio Pago")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, u"Número",boldbord)
			tam_col[14] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, u"RUC",boldbord)
			tam_col[15] = tam_letra* len(u"RUC") if tam_letra* len(u"RUC")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Partner",boldbord)
			tam_col[16] = tam_letra* len(u"Partner") if tam_letra* len(u"Partner")> tam_col[16] else tam_col[16]
			worksheet.write(3,17, u"Entidad Financiera",boldbord)
			tam_col[17] = tam_letra* len(u"Entidad Financiera") if tam_letra* len(u"Entidad Financiera")> tam_col[17] else tam_col[17]
			worksheet.write(3,18, u"Nro. Cuenta",boldbord)
			tam_col[18] = tam_letra* len(u"Nro. Cuenta") if tam_letra* len(u"Nro. Cuenta")> tam_col[18] else tam_col[18]
			worksheet.write(3,19, u"Moneda",boldbord)
			tam_col[19] = tam_letra* len(u"Moneda") if tam_letra* len(u"Moneda")> tam_col[19] else tam_col[19]
			worksheet.write(3,20, u"Partner Entrega Rendir",boldbord)

			for line in self.env['account.move.line.bank'].search([]):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.cuentacode if line.cuentacode  else '',bord)
				worksheet.write(x,4,line.cuentaname if line.cuentaname  else '',bord)
				worksheet.write(x,5,line.glosa if line.glosa  else '',bord)
				worksheet.write(x,6,line.debe ,numberdos)
				worksheet.write(x,7,line.haber ,numberdos)
				worksheet.write(x,8,line.saldo ,numberdos)
				worksheet.write(x,9,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,10,line.tipodecambio ,numbertres)
				worksheet.write(x,11,line.importedivisa ,numberdos)
				worksheet.write(x,12,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,13,line.mediopago if line.mediopago else '',bord)
				worksheet.write(x,14,line.numero if line.numero else '',bord)
				worksheet.write(x,15,line.codigo if line.codigo else '',bord)
				worksheet.write(x,16,line.partner if line.partner else '',bord)
				worksheet.write(x,17,line.entfinan if line.entfinan  else '',bord)				
				worksheet.write(x,18,line.nrocta if line.nrocta  else '',bord)
				worksheet.write(x,19,line.moneda if line.moneda  else '',bord)
				worksheet.write(x,20,line.partner_delivery if line.partner_delivery else '', bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.cuentacode if line.cuentacode  else '') if tam_letra* len(line.cuentacode if line.cuentacode  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len(line.cuentaname if line.cuentaname  else '') if tam_letra* len(line.cuentaname if line.cuentaname  else '')> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len(line.glosa if line.glosa  else '') if tam_letra* len(line.glosa if line.glosa  else '')> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len("%0.2f"%line.debe ) if tam_letra* len("%0.2f"%line.debe )> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len("%0.2f"%line.haber ) if tam_letra* len("%0.2f"%line.haber )> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len("%0.2f"%line.saldo ) if tam_letra* len("%0.2f"%line.saldo )> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len("%0.3f"%line.tipodecambio ) if tam_letra* len("%0.3f"%line.tipodecambio )> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len("%0.2f"%line.importedivisa ) if tam_letra* len("%0.2f"%line.importedivisa )> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len(line.mediopago if line.mediopago else '') if tam_letra* len(line.mediopago if line.mediopago else '')> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len(line.numero if line.numero else '') if tam_letra* len(line.numero if line.numero else '')> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.codigo if line.codigo else '') if tam_letra* len(line.codigo if line.codigo else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.partner if line.partner else '') if tam_letra* len(line.partner if line.partner else '')> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len( str(line.entfinan) if line.entfinan  else '') if tam_letra* len(str(line.entfinan) if line.entfinan  else '')> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len(line.nrocta if line.nrocta  else '') if tam_letra* len(line.nrocta if line.nrocta  else '')> tam_col[18] else tam_col[18]
				tam_col[19] = tam_letra* len(line.moneda if line.moneda  else '') if tam_letra* len(line.moneda if line.moneda  else '')> tam_col[19] else tam_col[19]

				x = x +1



			tam_col = [16.5,7.29,12,7,36,32,11,11,11,9,11,11,14,8,16,16,36,16,16,9]

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
			
			f = open(direccion + 'tempo_cajabanco.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'LibroCajaBanco.xlsx',
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
		tmp += separador+ self.csv_verif(data.cuentacode)
		tmp += separador+ self.csv_verif(data.cuentaname)
		tmp += separador+ self.csv_verif(data.glosa)
		tmp += separador+ self.csv_verif_integer(data.debe)
		tmp += separador+ self.csv_verif_integer(data.haber)
		tmp += separador+ self.csv_verif_integer(data.saldo)
		tmp += separador+ self.csv_verif(data.divisa)
		tmp += separador+ self.csv_verif_integer(data.tipodecambio)
		tmp += separador+ self.csv_verif_integer(data.importedivisa)
		tmp += separador+ self.csv_verif(data.fechaemision)
		tmp += separador+ self.csv_verif(data.mediopago )
		tmp += separador+ self.csv_verif(data.numero)
		tmp += separador+ self.csv_verif(data.codigo)
		tmp += separador+ self.csv_verif(data.partner) 
		tmp += separador+ self.csv_verif(data.entfinan) 
		tmp += separador+ self.csv_verif(data.nrocta) 
		tmp += separador+ self.csv_verif(data.moneda) 
		tmp += separador
		return unicode(tmp)

	@api.multi
	def cabezera_csv(self,separador):
		tmp = separador + self.csv_verif("Periodo")
		tmp += separador+ self.csv_verif("Libro")
		tmp += separador+ self.csv_verif("Voucher")
		tmp += separador+ self.csv_verif("Cuenta")
		tmp += separador+ self.csv_verif("Descripcion")
		tmp += separador+ self.csv_verif("Glosa")
		tmp += separador+ self.csv_verif("Debe")
		tmp += separador+ self.csv_verif("Haber")
		tmp += separador+ self.csv_verif("Saldo")
		tmp += separador+ self.csv_verif("Divisa")
		tmp += separador+ self.csv_verif("Tipo de Cambio")
		tmp += separador+ self.csv_verif("Importe Divisa")
		tmp += separador+ self.csv_verif("Fecha Emision")
		tmp += separador+ self.csv_verif("Fecha Pago")
		tmp += separador+ self.csv_verif("Numero")
		tmp += separador+ self.csv_verif("Codigo")
		tmp += separador+ self.csv_verif("Partner") 
		tmp += separador+ self.csv_verif("Ent. Financiera") 
		tmp += separador+ self.csv_verif("Nro. Cuenta") 
		tmp += separador+ self.csv_verif("Moneda") 
		tmp += separador
		return unicode(tmp)
