# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class account_bank_report_wizard(osv.TransientModel):
	_name='account.bank.report.wizard'
	
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	#asientos =  fields.Selection([('posted','Asentados'),('draft','No Asentados'),('both','Ambos')], 'Asientos')
	moneda = fields.Many2one('res.currency','Moneda')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')], 'Mostrar en', required=True)
	cuentas = fields.Many2many('account.account','account_bank_report_rel','id_bank_origen','id_account_destino', string='Cuentas', required=True)
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
                        CREATE OR REPLACE view account_bank_report as ( SELECT * 
                                FROM get_report_bank_with_saldoinicial("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code+"""')) )""")

		if self.cuentas:
			cuentas_list = []
			for i in self.cuentas:
				cuentas_list.append(i.id)
			filtro.append( ('aa_id','in',tuple(cuentas_list)) )
		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_cash_bank_it', 'action_account_moves_bank_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.bank.report',
				'view_mode': 'tree',
				'view_type': 'form',
				'res_id': id,
				'views': [(False, 'tree')],
			}


		if self.type_show == 'excel':

			import io
			from xlsxwriter.workbook import Workbook
			from xlsxwriter.utility import xl_rowcol_to_cell

			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_reportcajabanco.xlsx')
			worksheet = workbook.add_worksheet("Libro Auxiliar de Caja y Banco")
			bold = workbook.add_format({'bold': True})

			bold_title = workbook.add_format({'bold': True,'align': 'center','valign': 'vcenter'})
			bold_title.set_font_size(14)
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
			x= 8				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			compania_obj = self.env['res.company'].search([])[0]

			worksheet.write(0,0, compania_obj.partner_id.name, bold)
			worksheet.write(1,0, compania_obj.partner_id.type_number, bold)
			worksheet.merge_range(2,0,2,12, "LIBRO AUXILIAR DE CAJA Y BANCOS", bold_title)
			worksheet.merge_range(3,0,3,12, "(DEL "+ str(self.period_ini.date_start) +" AL " + str(self.period_end.date_stop) +")", bold_title)

			worksheet.write(5,0,"Cuenta Bancaria/Caja:",bold)
			worksheet.write(5,2,self.cuentas[0].name,bold)
			worksheet.write(6,0,"Moneda:",bold)
			worksheet.write(6,2,self.cuentas[0].currency_id.name if self.cuentas[0].currency_id.name else '',bold)


			worksheet.write(7,0, "Fecha",boldbord)
			worksheet.write(7,1, u"Cheque",boldbord)
			worksheet.write(7,2, u"Nombre/Razón Social",boldbord)

			worksheet.write(7,3, u"Documento",boldbord)
			worksheet.write(7,4, u"Glosa",boldbord)
			worksheet.write(7,5, u"Cargo",boldbord)
			worksheet.write(7,6, u"Abono",boldbord)
			worksheet.write(7,7, u"Saldo",boldbord)

			worksheet.merge_range(6,5,6,7, 'Moneda Nacional')

			worksheet.write(7,8, u"T/C",boldbord)

			worksheet.write(7,9, u"Cargo",boldbord)
			worksheet.write(7,10, u"Abono",boldbord)
			worksheet.write(7,11, u"Saldo",boldbord)
			worksheet.merge_range(6,9,6,11, 'Moneda Extranjera')

			worksheet.write(7,12, u"Nro. De Asiento",boldbord)
			worksheet.write(7,13, "Partner Entrega Rendir")

			for line in self.env['account.bank.report'].search(filtro):

				worksheet.write(x,0,line.fecha if line.fecha else '' ,bord )
				worksheet.write(x,1,line.cheque if line.cheque  else '',bord )
				worksheet.write(x,2,line.nombre if line.nombre  else '',bord)
				worksheet.write(x,3,line.documento if line.documento  else '',bord)
				worksheet.write(x,4,line.glosa if line.glosa  else '',bord)
				worksheet.write(x,5,line.cargo_mn ,numberdos)
				worksheet.write(x,6,line.abono_mn ,numberdos)
				worksheet.write(x,7,line.saldo_mn ,numberdos)
				worksheet.write(x,8,line.tipo_cambio ,numberdos)

				worksheet.write(x,9,line.cargo_me ,numberdos)
				worksheet.write(x,10,line.abono_me ,numberdos)
				worksheet.write(x,11,line.saldo_me ,numberdos)

				worksheet.write(x,12,line.nro_asiento.name ,bord)
				worksheet.write(x,13,line.partner_entrega ,bord)

				x = x +1

			worksheet.write(x,2, 'TOTAL', bord)
			worksheet.write_formula(x,5, '=sum(' + xl_rowcol_to_cell(8,5) +':' +xl_rowcol_to_cell(x-1,5) + ')', numberdos)
			worksheet.write_formula(x,6, '=sum(' + xl_rowcol_to_cell(8,6) +':' +xl_rowcol_to_cell(x-1,6) + ')', numberdos)
			worksheet.write_formula(x,9, '=sum(' + xl_rowcol_to_cell(8,9) +':' +xl_rowcol_to_cell(x-1,9) + ')', numberdos)
			worksheet.write_formula(x,10, '=sum(' + xl_rowcol_to_cell(8,10) +':' +xl_rowcol_to_cell(x-1,10) + ')', numberdos)




			tam_col = [14,14,24,12,36,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]

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
			
			f = open(direccion + 'tempo_reportcajabanco.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'LibroAuxiliarCajaBanco.xlsx',
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
		
