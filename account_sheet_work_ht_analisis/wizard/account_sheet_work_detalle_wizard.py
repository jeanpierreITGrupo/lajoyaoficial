# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs


class account_sheet_work_analisis_ht_wizard(osv.TransientModel):
	_name='account.sheet.work.analisis.ht.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	#wizrd_level_sheet = fields.Selection((('1','Cuentas de Balance'),
	#								('2','Cuentas de Registro')						
	#								),'Nivel',required=True)

	moneda = fields.Many2one('res.currency','Moneda', required=False)
	
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)


	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],'Mostrar',required=True)

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

		DROP TABLE IF EXISTS tmp_pre_hojadetalle cascade;
		create TABLE tmp_pre_hojadetalle as (

		select * from get_hoja_trabajo_detalle_registro_analisis_ht("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')
			) ) ;

			
		DROP VIEW IF EXISTS account_sheet_work_detalle cascade;
		CREATE OR REPLACE view account_sheet_work_analisis_ht as (
			
			select * from tmp_pre_hojadetalle
			union all 
			select  
			1000001 as id,
			''::varchar as ee_ff_peru,
			''::varchar as nivel1,
			''::varchar as nivel2,
			''::varchar as nivel3,
			''::varchar as nivel4,

			Null::varchar as cuenta,
			'Total' as descripcion,
			sum(debe) as debe,
			sum(haber) as haber,
			sum(saldodeudor) as saldodeudor,
			sum(saldoacredor) as saldoacredor,
			sum(activo) as activo,
			sum(pasivo) as pasivo,
			sum(perdidasnat) as perdidasnat,
			sum(ganancianat) as ganancianat,
			sum(perdidasfun) as perdidasfun,
			sum(gananciafun) as gananciafun
			from 
			tmp_pre_hojadetalle
			union all 
			select  
			1000002 as id,
			''::varchar as ee_ff_peru,
			''::varchar as nivel1,
			''::varchar as nivel2,
			''::varchar as nivel3,
			''::varchar as nivel4,
			Null::varchar as cuenta,
			'Resultado del Periodo' as descripcion,
			
			0 as debe,
			0 as haber,
			0 as saldodedudor,
			0 as saldoacredor,
			
			CASE WHEN sum(activo) > sum(pasivo) THEN  0 ELSE sum(pasivo)- sum(activo) END as activo,
			CASE WHEN sum(pasivo) > sum(activo) THEN  0 ELSE sum(activo)- sum(pasivo) END as pasivo,
			CASE WHEN sum(perdidasnat) > sum(ganancianat) THEN 0 ELSE sum(ganancianat)- sum(perdidasnat) END as perdidasnat,
			CASE WHEN sum(ganancianat) > sum(perdidasnat) THEN 0 ELSE sum(perdidasnat)- sum(ganancianat) END as ganancianat,
			CASE WHEN sum(perdidasfun) > sum(gananciafun) THEN 0 ELSE sum(gananciafun)- sum(perdidasfun) END as perdidasfun,
			CASE WHEN sum(gananciafun) > sum(perdidasfun) THEN 0 ELSE sum(perdidasfun)- sum(gananciafun) END as gananciafun
			
			from 
			tmp_pre_hojadetalle
			 
			union all

			select 1000003 as id,
			''::varchar as ee_ff_peru,
			''::varchar as nivel1,
			''::varchar as nivel2,
			''::varchar as nivel3,
			''::varchar as nivel4,
			Null::varchar as cuenta,
			'Gran Total' as descripcion,
			sum(debe) as debe,
			sum(haber) as haber,
			sum(saldodeudor) as saldodeudor,
			sum(saldoacredor) as saldoacredor,
			sum(activo) as activo,
			sum(pasivo) as pasivo,
			sum(perdidasnat) as perdidasnat,
			sum(ganancianat) as ganancianat,
			sum(perdidasfun) as perdidasfun,
			sum(gananciafun) as gananciafun

			from (select  
			1000001 as id,
			Null::varchar as cuenta,
			'Total' as descripcion,
			sum(debe) as debe,
			sum(haber) as haber,
			sum(saldodeudor) as saldodeudor,
			sum(saldoacredor) as saldoacredor,
			sum(activo) as activo,
			sum(pasivo) as pasivo,
			sum(perdidasnat) as perdidasnat,
			sum(ganancianat) as ganancianat,
			sum(perdidasfun) as perdidasfun,
			sum(gananciafun) as gananciafun
			from 
			tmp_pre_hojadetalle
			union all 
			select  
			1000002 as id,
			Null::varchar as cuenta,
			'Resultado del Periodo' as descripcion,
			
			0 as debe,
			0 as haber,
			0 as saldodedudor,
			0 as saldoacredor,
			
			CASE WHEN sum(activo) > sum(pasivo) THEN  0 ELSE sum(pasivo)- sum(activo) END as activo,
			CASE WHEN sum(pasivo) > sum(activo) THEN  0 ELSE sum(activo)- sum(pasivo) END as pasivo,
			CASE WHEN sum(perdidasnat) > sum(ganancianat) THEN 0 ELSE sum(ganancianat)- sum(perdidasnat) END as perdidasnat,
			CASE WHEN sum(ganancianat) > sum(perdidasnat) THEN 0 ELSE sum(perdidasnat)- sum(ganancianat) END as ganancianat,
			CASE WHEN sum(perdidasfun) > sum(gananciafun) THEN 0 ELSE sum(gananciafun)- sum(perdidasfun) END as perdidasfun,
			CASE WHEN sum(gananciafun) > sum(perdidasfun) THEN 0 ELSE sum(perdidasfun)- sum(gananciafun) END as gananciafun
			
			from 
			tmp_pre_hojadetalle
			 
			) AS T
		)""")	

		
		if self.type_show == 'pantalla':

				
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			
			return {
				'domain': filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.sheet.work.analisis.ht',
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

			workbook = Workbook(direccion +'tempo_hojatrabajo.xlsx')
			worksheet = workbook.add_worksheet("Hoja Trabajo")

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
			
			numberdosbold = workbook.add_format({'num_format':'0.00','bold': True})
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

			worksheet.write(0,0, u"Año Fiscal:", bold)
			worksheet.write(0,1, self.fiscalyear_id.name, normal)
			worksheet.write(1,0, u"Periodo:", bold)
			worksheet.write(1,1, self.period_ini.name+ ' - '+ self.period_end.name, normal)
			
			worksheet.write(3,0, "EE FF PERU",boldbord)
			#worksheet.write(3,1, "Nivel 1",boldbord)
			#worksheet.write(3,2, "Nivel 2",boldbord)
			#worksheet.write(3,3, "Nivel 3",boldbord)
			#worksheet.write(3,4, "Nivel 4",boldbord)
			worksheet.write(3,1, "Cuenta",boldbord)
			worksheet.write(3,2, u"Descripción",boldbord)
			worksheet.write(3,3, "Debe",boldbord)
			worksheet.write(3,4, "Haber",boldbord)
			worksheet.write(3,5, u"Saldo Deudo",boldbord)
			worksheet.write(3,6, "Saldo Acreedor",boldbord)
			worksheet.write(3,7, "Activo",boldbord)
			worksheet.write(3,8, "Pasivo",boldbord)
			worksheet.write(3,9, "Perdidas Nat.",boldbord)
			worksheet.write(3,10, "Ganancia Nat.",boldbord)
			worksheet.write(3,11, "Perdidas Fun.",boldbord)
			worksheet.write(3,12, u"Ganancia Fun.",boldbord)

			for i in self.env['account.sheet.work.analisis.ht'].search(filtro):
				worksheet.write(x,0, i.ee_ff_peru if i.ee_ff_peru else '',bord)
				#worksheet.write(x,1, i.nivel1 if i.nivel1 else '',bord)
				#worksheet.write(x,2, i.nivel2 if i.nivel2 else '',bord)
				#worksheet.write(x,3, i.nivel3 if i.nivel3 else '',bord)
				#worksheet.write(x,4, i.nivel4 if i.nivel4 else '',bord)

				worksheet.write(x,1, i.cuenta if i.cuenta else '',bord)
				worksheet.write(x,2, i.descripcion ,bord)
				worksheet.write(x,3, i.debe ,numberdos)
				worksheet.write(x,4, i.haber ,numberdos)

				worksheet.write(x,5, i.saldodeudor ,numberdos)
				worksheet.write(x,6, i.saldoacredor ,numberdos)
				worksheet.write(x,7, i.activo ,numberdos)
				worksheet.write(x,8, i.pasivo ,numberdos)
				worksheet.write(x,9, i.perdidasnat ,numberdos)
				worksheet.write(x,10, i.ganancianat ,numberdos)
				worksheet.write(x,11, i.perdidasfun ,numberdos)
				worksheet.write(x,12, i.gananciafun ,numberdos)

				x = x+1


			tam_col = [14,14,14,14,14,14,18,25,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]


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
			
			f = open(direccion + 'tempo_hojatrabajo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'AnalisisHT.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),     
			}

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			#import os
			#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}

