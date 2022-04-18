# -*- encoding: utf-8 -*-
import base64
from openerp     import models, fields, api
from openerp.osv import osv, expression

class hr_quincenales(models.TransientModel):
	_name = 'hr.quincenales'

	fecha = fields.Date('Fecha', required=True)

	@api.multi
	def do_rebuild(self):
		he = self.env['hr.employee'].search([('fecha_cese','=',False)])
		not_found = []
		to_create = []
		error_msg = ""
		for employee in he:
			hp  = self.env['hr.parameters'].search([('num_tipo','=',10001)])
			hta = self.env['hr.table.adelanto'].search([('code','in',['001'])])

			fch = self.fecha.split('-')
			fch = fch[1] + "/" + fch[0]
			hml = self.env['hr.membership.line'].search([('periodo.code','=',fch),('membership','=',employee.afiliacion.id)])

			if len(hml) > 0:
				hml = hml[0]

				ad = False
				for i in hta:
					if employee.tipo_trabajador.id == i.tipo_trabajador.id:
						ad = i.id
						break

				monto     = (employee.basica + (hp[0].monto if employee.children_number > 0 else 0))
				base_dsct = (employee.basica + (hp[0].monto if employee.children_number > 0 else 0))
				
				monto -= (base_dsct * hml.tasa_pensiones/100.00)
				if employee.afiliacion.code != 'ONP':
					monto -= (base_dsct * hml.prima/100.00)
					if employee.c_mixta:
						monto -= (base_dsct * hml.c_mixta/100.00)
					else:
						monto -= (base_dsct * hml.c_variable/100.00)

				vals = {
					'fecha'            : self.fecha,
					'monto'            : monto/2.00,
					'employee'         : employee.id,
					'codigo_trabajador': employee.codigo_trabajador,
					'adelanto_id'      : ad,
				}
				to_create.append(vals)

			else:
				error_msg += "- " + employee.name_related + " / " + (employee.afiliacion.name if employee.afiliacion.name else '') + "\n"

		if len(error_msg) > 0:
			raise osv.except_osv("Alerta!", u"No se econtró afiliación con la fecha indicada para los siguientes empleados.\n"+error_msg)
		
		for v in to_create:
			n_ha = self.env['hr.adelanto'].create(v)

class hr_adelanto(models.Model):
	_name = 'hr.adelanto'
	_rec_name = 'employee'

	fecha             = fields.Date('Fecha Adelanto')
	monto             = fields.Float('Monto',digits=(12,2))
	employee          = fields.Many2one('hr.employee','Trabajador')
	codigo_trabajador = fields.Char(u'Código',store=True,related='employee.codigo_trabajador')
	adelanto_id		  = fields.Many2one('hr.table.adelanto', 'Tipo de Adelanto')