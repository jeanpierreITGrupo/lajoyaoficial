# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class saldo_comprobante_empresa_wizard(osv.TransientModel):
	_name='saldo.comprobante.empresa.wizard'

	fiscal_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	periodo_ini = fields.Many2one('account.period','Periodo Inicio',required=True)
	periodo_fin = fields.Many2one('account.period','Periodo Final',required=True)
	mostrar = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],'Mostrar',required=True)
	check = fields.Boolean('Solo pendientes')
	empresa = fields.Many2one('res.partner','Empresa')
	cuenta = fields.Many2one('account.account','Cuenta')
	tipo = fields.Selection( [('A pagar','A pagar'),('A cobrar','A cobrar')], 'Tipo')




	@api.onchange('tipo')
	def _onchange_type_account(self):
		if self.tipo:
			if str(self.tipo) == "A pagar":
				return {'domain':{'cuenta':[('type','=','payable')]}}
			elif str(self.tipo) == "A cobrar":
				return {'domain':{'cuenta':[('type','=','receivable')]}}
		else:
			return {'domain':{'cuenta':[('type','in',('payable','receivable'))]}}

	@api.multi
	def do_rebuild(self):		

		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante_empresa;
			create or replace view saldo_comprobante_empresa as (

select t1.id as id, ap.name as periodo,t3.type_number as ruc,t3.name as empresa,t4.code as code,t4.name as descripcion,
CASE WHEN t4.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta
,t_debe as debe,t_haber as haber,t_debe-t_haber as saldo  from ( 
select min(aml.id) as id, concat(aml.partner_id,aml.account_id) as identificador,sum(aml.debit) as t_debe,sum(aml.credit) as t_haber from account_move_line aml
inner join account_move am on am.id = aml.move_id
inner join account_period api on api.id = am.period_id
inner join account_account aa on aa.id = aml.account_id
where aa.es_analisis = true and periodo_num(api.code) >= periodo_num('""" + str(self.periodo_ini.code) + """') and periodo_num(api.code) <= periodo_num('""" + str(self.periodo_fin.code) + """')
and am.state != 'draft'
group by identificador) t1

left join account_move_line t2 on t2.id=t1.id
left join account_move am on am.id = t2.move_id
left join account_period ap on ap.id = am.period_id
left join res_partner t3 on t3.id=t2.partner_id
left join account_account t4 on t4.id=t2.account_id


order by code,empresa

						)""")
		filtro = []
		if self.check== True:
			filtro.append( ('saldo','!=',0) )
		if self.cuenta.id:
			filtro.append( ('code','=', self.cuenta.code ) )

		if self.empresa.id:
			filtro.append( ('empresa','=', self.empresa.name ) )

		if self.tipo:
			filtro.append( ('tipo_cuenta','=',self.tipo) )

		move_obj = self.env['saldo.comprobante.empresa']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		if self.mostrar == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'saldo.comprobante.empresa',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

			
		if self.mostrar == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'saldoperiodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Saldo x Empresa")
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


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)

			x= 9				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,8, u"Análisis de Saldos x Empresa", title)

			worksheet.write(1,0, u"Año Fiscal", bold)
			worksheet.write(1,1, self.fiscal_id.name, normal)

			worksheet.write(2,0, u"Periodo Inicial", bold)
			worksheet.write(2,1, self.periodo_ini.name, normal)

			worksheet.write(3,0, u"Periodo Final", bold)
			worksheet.write(3,1, self.periodo_fin.name, normal)

			worksheet.write(4,0, u"Solo Pendientes", bold)
			worksheet.write(4,1, 'Si' if self.check else 'No', normal)

			worksheet.write(5,0, u"Empresa", bold)
			worksheet.write(5,1, self.empresa.name if self.empresa.name else '', normal)

			worksheet.write(6,0, u"Cuenta", bold)
			worksheet.write(6,1, self.cuenta.name if self.cuenta.name else '', normal)


			worksheet.write(8,0, "Periodo",boldbord)
			worksheet.write(8,1, "Empresa",boldbord)
			worksheet.write(8,2, "RUC",boldbord)
			worksheet.write(8,3, "Tipo Cuenta",boldbord)
			worksheet.write(8,4, u"Cuenta",boldbord)
			worksheet.write(8,5, u"Descripción",boldbord)
			worksheet.write(8,6, "Debe",boldbord)
			worksheet.write(8,7, "Haber",boldbord)
			worksheet.write(8,8, "Saldo",boldbord)




			for line in self.env['saldo.comprobante.empresa'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.empresa if line.empresa  else '',bord )
				worksheet.write(x,2,line.ruc if line.ruc  else '',bord)
				worksheet.write(x,3,line.tipo_cuenta if line.tipo_cuenta  else '',bord)
				worksheet.write(x,4,line.code if line.code  else '',bord)
				worksheet.write(x,5,line.descripcion if line.descripcion  else '',bord)
				worksheet.write(x,6,line.debe ,numberdos)
				worksheet.write(x,7,line.haber ,numberdos)
				worksheet.write(x,8,line.saldo ,numberdos)

				x = x +1

			tam_col = [11,6,8.8,7.14,38,11,11,11,10,11,14,10,11,14,14,10,16,16,20,36]


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
			
			f = open(direccion + 'saldoperiodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'SaldoEmpresa.xlsx',
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

			#import os
			#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}


		