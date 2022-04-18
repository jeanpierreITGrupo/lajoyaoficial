# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api

class analitica_excel_analisis_wizard(osv.TransientModel):
	_name='analitica.excel.analisis.wizard'
	
	period_ini =fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end =fields.Many2one('account.period','Periodo Final',required=True)

	@api.onchange('period_ini')
	def _onchange_type_account(self):
		if self.period_ini:
			self.period_end = self.period_ini

	@api.multi
	def do_rebuild(self):

		self.env.cr.execute(""" 
			select X1.cuenta,
			aa.name,
			X1.c90,X1.c91,X1.c92,X1.c93,X1.c94,X1.c95,X1.c96,X1.c97,X1.c98,X1.c99,

			X1.c90 + X1.c91 + X1.c92 + X1.c93 + X1.c94 + X1.c95  + X1.c96 + X1.c97 + X1.c98  + X1.c99	 as ctotal
			from (
				select cuenta,
				sum( CASE WHEN left(destinodebe,2) = '90' THEN debe else 0 END ) as c90, 
				sum( CASE WHEN left(destinodebe,2) = '91' THEN debe else 0 END ) as c91, 
				sum( CASE WHEN left(destinodebe,2) = '92' THEN debe else 0 END ) as c92, 
				sum( CASE WHEN left(destinodebe,2) = '93' THEN debe else 0 END ) as c93, 
				sum( CASE WHEN left(destinodebe,2) = '94' THEN debe else 0 END ) as c94, 
				sum( CASE WHEN left(destinodebe,2) = '95' THEN debe else 0 END ) as c95, 
				sum( CASE WHEN left(destinodebe,2) = '96' THEN debe else 0 END ) as c96, 
				sum( CASE WHEN left(destinodebe,2) = '97' THEN debe else 0 END ) as c97, 
				sum( CASE WHEN left(destinodebe,2) = '98' THEN debe else 0 END ) as c98, 
				sum( CASE WHEN left(destinodebe,2) = '99' THEN debe else 0 END ) as c99 
				from account_account_analytic_rep aaar
				where aaar.fecha_ini >= '""" +self.period_ini.date_start+ """' and aaar.fecha_fin <= '""" +self.period_end.date_stop+ """'
				group by cuenta
				order by cuenta
				) as X1
				inner join account_account aa on aa.code = X1.cuenta
		""")

		elementos = self.env.cr.fetchall()

		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'analisis_excel.xlsx')
			worksheet = workbook.add_worksheet("Analisis Analitica")
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

			worksheet.write(0,0, "Analisis Analitica:", bold)
			
			worksheet.write(0,1, self.period_ini.name, normal)
	
			worksheet.write(0,2, self.period_end.name, normal)
				

			worksheet.write(3,0, "Cuenta",boldbord)
			worksheet.write(3,1, "Descripcion",boldbord)
			worksheet.write(3,2, "90",boldbord)
			worksheet.write(3,3, "91",boldbord)
			worksheet.write(3,4, "92",boldbord)
			worksheet.write(3,5, "93",boldbord)
			worksheet.write(3,6, "94",boldbord)
			worksheet.write(3,7, "95",boldbord)
			worksheet.write(3,8, "96",boldbord)
			worksheet.write(3,9, "97",boldbord)
			worksheet.write(3,10, "98",boldbord)
			worksheet.write(3,11, "99",boldbord)
			worksheet.write(3,12, "Total",boldbord)
			

			totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			for line in elementos:
				worksheet.write(x,0,line[0] if line[0] else '' ,bord )
				worksheet.write(x,1,line[1] if line[1] else '' ,bord )
				worksheet.write(x,2,line[2] ,numberdos )
				worksheet.write(x,3,line[3] ,numberdos )
				worksheet.write(x,4,line[4] ,numberdos )
				worksheet.write(x,5,line[5] ,numberdos )
				worksheet.write(x,6,line[6] ,numberdos )
				worksheet.write(x,7,line[7] ,numberdos )
				worksheet.write(x,8,line[8] ,numberdos )
				worksheet.write(x,9,line[9] ,numberdos )
				worksheet.write(x,10,line[10] ,numberdos )
				worksheet.write(x,11,line[11] ,numberdos )
				worksheet.write(x,12,line[12] ,numberdos )

				totales[0] += line[2]
				totales[1] += line[3]
				totales[2] += line[4]
				totales[3] += line[5]
				totales[4] += line[6]
				totales[5] += line[7]
				totales[6] += line[8]
				totales[7] += line[9]
				totales[8] += line[10]
				totales[9] += line[11]
				totales[10] += line[12]
				x += 1


			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10,10]

			worksheet.write(x,0,"TOTALES",boldbord)
			worksheet.write(x,2,totales[0] ,numberdos )
			worksheet.write(x,3,totales[1] ,numberdos )
			worksheet.write(x,4,totales[2] ,numberdos )
			worksheet.write(x,5,totales[3] ,numberdos )
			worksheet.write(x,6,totales[4] ,numberdos )
			worksheet.write(x,7,totales[5] ,numberdos )
			worksheet.write(x,8,totales[6] ,numberdos )
			worksheet.write(x,9,totales[7] ,numberdos )
			worksheet.write(x,10,totales[8] ,numberdos )
			worksheet.write(x,11,totales[9] ,numberdos )
			worksheet.write(x,12,totales[10] ,numberdos )


			#worksheet.set_row(3, 60)
			
			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:Z', tam_col[1])

			workbook.close()
			
			f = open( direccion + 'analisis_excel.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'AnalisisAnalitica.xlsx',
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
