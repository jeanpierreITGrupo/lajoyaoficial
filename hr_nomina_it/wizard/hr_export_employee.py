# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class hr_export_employee(models.TransientModel):
	_name = 'hr.export.employee'

	# noactivos = fields.Boolean('Incluir no activos')

	@api.multi
	def export_employee(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		lstp=self.env['main.parameter'].search([])
		if lstp==[]:
			raise osv.except_osv('Error!',"No se ha ingresado los parametros")
		parameters = lstp[0]
		if not parameters.dir_create_file:
			raise osv.except_osv('Error!',"No se ha ingresado los parametros para secuencia de planillas")

		workbook = Workbook(parameters.dir_create_file+'listado_empleados.xlsx')
		worksheet = workbook.add_worksheet("Trabajadores")

		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 4				
		tam_letra = 1.2
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		import datetime

		
		# worksheet.write(2,0,'Nro',bold)
		worksheet.write(2,1,'COD',boldbord)
		worksheet.write(2,2,'APELLIDO PATERNO',boldbord)
		worksheet.write(2,3,'APELLIDO MATERNO',boldbord)
		worksheet.write(2,4,'NOMBRES',boldbord)
		worksheet.write(2,5,'FECHA DE NACIMIENTO',boldbord)
		worksheet.write(2,6,'NACIONALIDAD',boldbord)
		worksheet.write(2,7,'TIPO DOCUMENTO',boldbord)
		worksheet.write(2,8,'Nro DOCUMENTO',boldbord)
		worksheet.write(2,9,'DEPARTAMENTO',boldbord)
		worksheet.write(2,10,'TITULO DEL TRABAJO',boldbord)
		worksheet.write(2,11,'TIPO DE TRABAJADOR',boldbord)
		worksheet.write(2,12,'Nro PASAPORTE',boldbord)
		worksheet.write(2,13,'SEXO',boldbord)
		worksheet.write(2,14,'ESTADO CIVIL',boldbord)
		worksheet.write(2,15,'Nro DE HIJOS',boldbord)
		worksheet.write(2,16,'DIRECCION',boldbord)
		worksheet.write(2,17,'FECHA DE INGRESO',boldbord)
		worksheet.write(2,18,'FECHA DE CESE',boldbord)
		worksheet.write(2,19,'BASICO',boldbord)
		worksheet.write(2,20,'ASIGNACION FAMILIAR',boldbord)
		worksheet.write(2,21,'DIST. CC',boldbord)
		worksheet.write(2,22,'EPS',boldbord)
		worksheet.write(2,23,'AFILIACIO',boldbord)
		worksheet.write(2,24,'COMISION MIXTA',boldbord)
		worksheet.write(2,25,'FECHA DE AFILIACION',boldbord)
		worksheet.write(2,26,'CUSSPP',boldbord)
		worksheet.write(2,27,'BANCO CTS',boldbord)
		worksheet.write(2,28,'Nro CTA CTS',boldbord)
		worksheet.write(2,29,'BANCO REM',boldbord)
		worksheet.write(2,30,'Nro CTA REM',boldbord)
		worksheet.write(2,31,'FIN CONTRATO',boldbord)

		n=3
		x=0

		for empleado in self.env['hr.employee'].search([],order ='last_name_father,last_name_mother,first_name_complete'):
			if not empleado.last_name_father:
				continue
			sexo = 'Masculino' if empleado.gender == 'male' else 'Femenino'
			estadoc= 'Soltero' if empleado.marital == 'single' else 'Casado'
			# worksheet.write(n,0,'0',bold)
			worksheet.write(n,1,empleado.codigo_trabajador,normal)
			worksheet.write(n,2,empleado.last_name_father,normal)
			worksheet.write(n,3,empleado.last_name_mother,normal)
			worksheet.write(n,4,empleado.first_name_complete,normal)
			worksheet.write(n,5,empleado.birthday,normal)
			worksheet.write(n,6,empleado.country_id.name,normal)
			worksheet.write(n,7,empleado.type_document_id.description,normal)
			worksheet.write(n,8,empleado.identification_id,normal)
			worksheet.write(n,9,empleado.department_id.name,normal)
			worksheet.write(n,10,empleado.job_id.name,normal)
			worksheet.write(n,11,empleado.tipo_trabajador.name,normal)
			worksheet.write(n,12,empleado.passport_id if empleado.passport_id else '',normal)
			worksheet.write(n,13,sexo,normal)
			worksheet.write(n,14,estadoc,normal)
			worksheet.write(n,15,empleado.children_number,normal)
			worksheet.write(n,16,empleado.direccion_text if empleado.direccion_text else '',normal)
			worksheet.write(n,17,empleado.fecha_ingreso,normal)
			worksheet.write(n,18,empleado.fecha_cese if empleado.fecha_cese else '',normal)
			worksheet.write(n,19,empleado.basica,normal)
			hp = self.env['hr.parameters'].search([('num_tipo','=',10001)])[0]
			worksheet.write(n,20,hp.monto if hp.monto and empleado.children_number > 0 else 0.00,normal)
			worksheet.write(n,21,empleado.dist_c.codigo if empleado.dist_c.codigo else '',normal)
			worksheet.write(n,22,'SI' if empleado.use_eps else 'NO',normal)
			worksheet.write(n,23,empleado.afiliacion.name,normal)
			worksheet.write(n,24,'SI'  if empleado.c_mixta else 'NO',normal)
			worksheet.write(n,25,empleado.fecha_afiliacion,normal)
			worksheet.write(n,26,empleado.cusspp if empleado.cusspp else '',normal)
			worksheet.write(n,27,empleado.banco_cts if empleado.banco_cts else '',normal)
			worksheet.write(n,28,empleado.cta_cts if empleado.cta_cts else '',normal)
			worksheet.write(n,29,empleado.banco_rem if empleado.banco_rem else '',normal)
			worksheet.write(n,30,empleado.cta_rem if empleado.cta_rem else '',normal)	
			worksheet.write(n,31,empleado.end_contract_date if empleado.end_contract_date else '',normal)	
			n=n+1

		workbook.close()
		
		f = open(parameters.dir_create_file+'listado_empleados.xlsx','rb')
		namefile = 'Listado de trabajadores.xlsx'
		vals = {
			'output_name': namefile,
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		print 0,view_ref
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print 1,view_id
		print 2,result
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}