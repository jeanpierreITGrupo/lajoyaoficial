# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class analisis_cuenta_wizard(osv.TransientModel):
	_name='analisis.cuenta.wizard'

	fiscalyear_id = fields.Many2one	('account.fiscalyear',u'Año',required=True)
	period_ini =fields.Many2one('account.period','Periodo Inicial',required=True)
	period_fin =fields.Many2one('account.period','Periodo Final',required=True)
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')], 'Mostrar en', required=True)


	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )],'period_fin':[('fiscalyear_id','=',self.fiscalyear_id.id )] }}
		else:
			return {'domain':{'period_ini':[],'period_fin':[]}}


	@api.multi
	def do_rebuild(self):		
		
		inicial_a = int(self.period_ini.code.split('/')[0])
		inicial_b = int(self.period_ini.code.split('/')[1])
		final_a = int(self.period_fin.code.split('/')[0])
		final_b = int(self.period_fin.code.split('/')[1])

		tmp = []
		while str(inicial_b) + ('0'+str(inicial_a) if inicial_a <10 else str(inicial_a)) <= str(final_b) + ('0'+str(final_a) if final_a <10 else str(final_a)) :
			tmp.append( ('0'+str(inicial_a) if inicial_a <10 else str(inicial_a)) + '/' + str(inicial_b))
			if inicial_a ==13:
				inicial_a = 0
				inicial_b +=1
			else:
				inicial_a +=1


		filtro = [('period_code','in', tmp )]

		move_obj = self.env['analisis.cuenta']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		if self.type_show == 'pantalla':

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'analisis.cuenta',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		else:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_cuentacorriente.xlsx')
			worksheet = workbook.add_worksheet("Cuenta Corriente")
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


			worksheet.merge_range(0,0,0,7,u"Análisis Cuenta",title)

			worksheet.write(1,0, u"Análisis de Cuenta:", bold)
			
			worksheet.write(1,1, self.period_ini.name, normal)
			
			worksheet.write(1,2, self.period_fin.name, normal)
			
			worksheet.write(2,0, "Fecha:",bold)
			
			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(2,1, str(datetime.datetime.today())[:10], normal)
			



			worksheet.write(4,0, "Periodo",boldbord)
			
			worksheet.write(4,1, "Diario",boldbord)
			worksheet.write(4,2, "Voucher",boldbord)
			worksheet.write(4,3, u"Rubro",boldbord)

			worksheet.write(4,4, u"Cuenta",boldbord)
			worksheet.write(4,5, "Debe",boldbord)

			worksheet.write(4,6, "Haber",boldbord)
			worksheet.write(4,7, u"Saldo",boldbord)


			for line in lstidsmove:
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.diario if line.diario  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.rubro if line.rubro else '',bord)
				worksheet.write(x,4,line.cuenta if line.cuenta else '',bord)
				worksheet.write(x,5,line.debe ,numberdos)
				worksheet.write(x,6,line.haber ,numberdos)
				worksheet.write(x,7,line.saldo ,numberdos)

				x = x +1

			tam_col = [16.14,7,22.2,13.5,38,3.5,15,15,15,15,15,15,15,15,15,15]
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

			workbook.close()
			
			f = open(direccion + 'tempo_cuentacorriente.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'AnalisisCuenta.xlsx',
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

		