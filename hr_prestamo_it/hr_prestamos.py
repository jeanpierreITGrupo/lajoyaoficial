# -*- coding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

import datetime
from datetime import datetime
import decimal
import calendar


class hr_prestamo_header(models.Model):
	_name = 'hr.prestamo.header'
	_rec_name = "employee_id"

	employee_id        = fields.Many2one('hr.employee', "Nombre del Trabajador")
	codigo             = fields.Char('Código', readonly=True, compute="get_codigo")
	departamento       = fields.Char("Departamento", compute="get_departamento")
	fecha_prestamo     = fields.Date('Fecha de Prestamo')
	monto              = fields.Float('Monto de Prestamo')
	cuotas             = fields.Integer('Numero de Cuotas')
	prestamo_lines_ids = fields.One2many('hr.prestamo.lines','prestamo_id', 'prestamo linea')
	state              = fields.Selection([('draft','No Pagado'),('done','Pagado')],'Estado',default="draft")
	texto              = fields.Text('Observaciones')
	prestamo_id        = fields.Many2one('hr.table.prestamo',u'Tipo de Préstamo')

	@api.one
	def get_departamento(self):
		ob = self.env['hr.employee'].search([('department_id','=',self.employee_id.department_id.name),('id','=',self.employee_id.id)])
		self.departamento = ob[0].department_id.name if len(ob) > 0 else False

	@api.one
	def get_cargo(self):
		self.cargo = self.employee_id.job_id.name
	cargo = fields.Char('Cargo que Ocupa', readonly=True, compute="get_cargo")

	@api.one
	def get_codigo(self):
		ob = self.env['hr.employee'].search([('id','=',self.employee_id.id)])
		self.codigo = ob[0].codigo_trabajador if len(ob) > 0 else False

	@api.one
	def paid(self):
		for i in self.prestamo_lines_ids:
			if i.monto == 0:
				i.validacion = '1'
			if i.validacion != '1':
				raise osv.except_osv('Alerta!', 'No fue cancelada la cuota: ' + str(i.cuota))
			self.state = 'done'

	@api.one
	def back_draft(self):
		for i in self.prestamo_lines_ids:
			if i.monto == 0:
				i.validacion = '2'
		self.state = 'draft'

	@api.one
	def calculate(self):
		if len((self.env['hr.prestamo.lines'].search([('prestamo_id','=',self.id)]))) == self.cuotas:
			pass
		else:
			if len((self.env['hr.prestamo.lines'].search([('prestamo_id','=',self.id)]))) != self.cuotas:
				for i in self.prestamo_lines_ids:
					i.unlink()
			fech_pres = self.fecha_prestamo.split('-')
			fech_pres_y = int(fech_pres[0])
			fech_pres_m = int(fech_pres[1])

			for i in range(self.cuotas):

				ult_d = calendar.monthrange(fech_pres_y, fech_pres_m)
				nf = "{0}-{1}-{2}".format(str(fech_pres_y),str(fech_pres_m),str(ult_d[1]))
				fmt = '%Y-%m-%d'
				prox_cuot = datetime.strptime(nf, fmt)

				data = {
							'prestamo_id': self.id,
							'cuota': i+1,
							'fecha_pago': prox_cuot,
							'adelanto': 0,
							'deuda_por_pagar': 0,
						}
				self.env['hr.prestamo.lines'].create(data)
				
				if fech_pres_m > 11:
					fech_pres_m = 1
					fech_pres_y +=1
				else:
					fech_pres_m += 1

			if len(self.prestamo_lines_ids) != self.cuotas:
				pass
			else:
				lin = self.prestamo_lines_ids.sorted(key=lambda r: r.cuota)
				cuota_rst = lin[0].prestamo_id.cuotas 
				monto_tmp = lin[0].prestamo_id.monto
				for i in lin:
					i.monto = monto_tmp / cuota_rst
					monto_tmp -= (monto_tmp / cuota_rst) + i.adelanto
					cuota_rst -= 1

	@api.multi
	def export_excel(self):

		import io
		from xlsxwriter.workbook import Workbook

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")
		workbook = Workbook( direccion + 'prestamos.xlsx')
		worksheet_prestamos = workbook.add_worksheet("Prestamos")
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)	

		x= 6				
		worksheet_prestamos.write(1,2, "CALQUIPA S.A.C.", bold)
		worksheet_prestamos.write(3,2, "PRESTAMOS DE LOS TRABAJADORES", normal)

		nombres = [u"Nº","NOMBRES Y APELLIDOS","CODIGO","DEPARTAMENTO","CARGO","FECHA INICIO DE PRESTAMO","FECHA FIN DE PRESTAMO","MONTO TOTAL","CUOTAS","ADELANTOS/DEVOLUCIONES","ESTADO","OBSERVACION"]
		for i in range(len(nombres)):
			worksheet_prestamos.write(5,i, nombres[i],boldbord)
		cont = 1
		
		for nom in self.env['hr.prestamo.header'].search([]):
			worksheet_prestamos.write(x, 0, str(cont), bord)
			worksheet_prestamos.write(x, 1, nom.employee_id.name, bord)
			worksheet_prestamos.write(x, 2, nom.codigo, bord)
			worksheet_prestamos.write(x, 3, nom.employee_id.department_id.name, bord)
			worksheet_prestamos.write(x, 4, nom.cargo, bord)
			worksheet_prestamos.write(x, 5, nom.fecha_prestamo, bord)
			worksheet_prestamos.write(x, 6, nom.prestamo_lines_ids.sorted(key=lambda r: r.cuota)[len(nom.prestamo_lines_ids)-1].fecha_pago, bord)
			worksheet_prestamos.write(x, 7, nom.monto, numberdos)
			worksheet_prestamos.write(x, 8, nom.cuotas, bord)

			ade = 0
			for j in nom.prestamo_lines_ids:
				ade += j.adelanto
			worksheet_prestamos.write(x, 8, ade if ade > 0 else '', numberdos)

			est = "PAGADO"
			for k in nom.prestamo_lines_ids:
				if k.validacion == "2":
					est = "NO PAGADO"
			worksheet_prestamos.write(x, 9, est, bord)

			worksheet_prestamos.write(x, 10, nom.texto if nom.texto else '', bord)

			cont += 1
			x += 1


		worksheet_prestamos.set_column('A:A', 5.43)
		worksheet_prestamos.set_column('B:B', 38.29)
		worksheet_prestamos.set_column('C:C', 16.71)
		worksheet_prestamos.set_column('D:D', 20.29)
		worksheet_prestamos.set_column('E:E', 25.43)
		worksheet_prestamos.set_column('F:F', 22.71)
		worksheet_prestamos.set_column('G:G', 13.71)
		worksheet_prestamos.set_column('H:H', 8.43)
		worksheet_prestamos.set_column('I:I', 25.71)
		worksheet_prestamos.set_column('J:J', 12.57)
		worksheet_prestamos.set_column('K:K', 70)

		workbook.close()
		
		f = open( direccion + 'prestamos.xlsx', 'rb')
		
		
		vals = {
			'output_name': 'prestamos.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}

	@api.multi
	def single_export_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")
		workbook = Workbook( direccion + 'prestamos.xlsx')
		worksheet_prestamos = workbook.add_worksheet("{0}".format(self.employee_id.name))
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)
		merge_format = workbook.add_format({
										    'border': 1,
										    'align': 'justify',
										    'valign': 'top',})
				
		worksheet_prestamos.write(0,1, "CALQUIPA S.A.C.", bold)
		worksheet_prestamos.write(1,1, "RUC: 20455959943", bold)
		
		x = 5
		worksheet_prestamos.write(x,2, u"Nombre del Trabajador:", bold)
		worksheet_prestamos.write(x,4, u"{0}".format(self.employee_id.name), normal)
		x += 1
		worksheet_prestamos.write(x,2, u"Código del Trabajador:", bold)
		worksheet_prestamos.write(x,4, u"{0}".format(self.codigo), normal)
		x += 1
		worksheet_prestamos.write(x,2, u"Cargo que Ocupa:", bold)
		worksheet_prestamos.write(x,4, u"{0}".format(self.cargo), normal)
		x += 1
		worksheet_prestamos.write(x,2, u"Fecha de Préstamo:", bold)
		worksheet_prestamos.write(x,4, u"{0}".format(self.fecha_prestamo), normal)
		x += 2
		worksheet_prestamos.write(x,2, u"Monto de Préstamo:", bold)
		worksheet_prestamos.write_number(x,4, self.monto, normal)
		worksheet_prestamos.write(x,7, u"Nº de Cuotas:", bold)
		worksheet_prestamos.write_number(x,8, self.cuotas, normal)
		x += 2

		colu = [u"Cuota",u"Monto",u"Fecha de Pago",u"Adelanto / Devolución",u"Fecha de Adelanto",u"Deuda por Pagar",u"Validación",u"Firma"]
		for i in range(len(colu)):
			worksheet_prestamos.write(x,i+2, colu[i], boldbord)
		x += 1
		for i in self.prestamo_lines_ids:
			worksheet_prestamos.write_number(x,2, i.cuota, bord)
			worksheet_prestamos.write_number(x,3, i.monto, numberdos)
			worksheet_prestamos.write(x,4, u"{0}".format(i.fecha_pago), bord)
			worksheet_prestamos.write_number(x,5, i.adelanto, numberdos)
			worksheet_prestamos.write(x,6, u"{0}".format(i.fecha_adelanto) if i.fecha_adelanto else '', bord)
			worksheet_prestamos.write_number(x,7, i.deuda_por_pagar, numberdos)
			if i.validacion == '1':
				worksheet_prestamos.write(x,8, u"PAGADO", bord)
			if i.validacion == '2':
				worksheet_prestamos.write(x,8, u"NO PAGADO", bord)
			worksheet_prestamos.write(x,9, "", bord)
			x += 1

		x += 1
		worksheet_prestamos.write(x,2, u"OBSERVACIONES", bold)
		x += 1
		worksheet_prestamos.merge_range(x,2,x+7,9, self.texto if self.texto else '', merge_format)


		worksheet_prestamos.set_column('C:C', 18.43)
		worksheet_prestamos.set_column('D:D', 13)
		worksheet_prestamos.set_column('E:E', 12.57)
		worksheet_prestamos.set_column('F:F', 21.14)
		worksheet_prestamos.set_column('G:G', 17.71)
		worksheet_prestamos.set_column('H:H', 18)
		worksheet_prestamos.set_column('I:I', 17.71)
		worksheet_prestamos.set_column('J:J', 15)

		workbook.close()
		
		f = open( direccion + 'prestamos.xlsx', 'rb')
		
		
		vals = {
			'output_name': 'prestamos.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}




class hr_prestamo_lines(models.Model):
	_name = 'hr.prestamo.lines'

	prestamo_id = fields.Many2one('hr.prestamo.header','prestamo padre')

	cuota = fields.Integer('Cuota', readonly=True)
	monto = fields.Float('Monto', readonly=False)
	fecha_pago = fields.Date('Fecha de Pago')
	adelanto = fields.Float('Adelanto o Devolucion')
	fecha_adelanto = fields.Date('Fecha de Adelanto o Devolucion')

	@api.multi
	def get_deuda_por_pagar(self):
		ant_state = None
		for i in self[0].prestamo_id.prestamo_lines_ids.sorted(key=lambda r: r.cuota):
			if ant_state == None: 
				i.deuda_por_pagar = i.prestamo_id.monto - i.monto - i.adelanto
			else:
				i.deuda_por_pagar = ant_state.deuda_por_pagar - i.monto - i.adelanto
			ant_state = i

	deuda_por_pagar = fields.Float('Deuda por Pagar', readonly=True, compute="get_deuda_por_pagar")

	validacion = fields.Selection([('1', 'PAGADO'), ('2', 'NO PAGADO')], 'Validacion', default="2")
