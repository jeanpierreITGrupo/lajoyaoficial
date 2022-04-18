# -*- coding: utf-8 -*-
from openerp     import models, fields, api
from openerp.osv import osv, expression
import pprint

from xlsxwriter.workbook import Workbook
import base64
import io
import os
import sys

from tempfile import TemporaryFile
import csv

class hr_five_cat_update(models.Model):
	_name     = 'hr.five.cat.update'
	_rec_name = 'five_file_txt'

	#IMPORTACION
	five_file     = fields.Binary('Archivo (CSV)')
	five_file_txt = fields.Char(u'Archivo (CSV) texto')
	delimiter       = fields.Char('Delimitador', size=1, required=True, default=",")

	five_no_imp_lines = fields.One2many('hr.five.cat.update.no.importado','importador_id','lineas no importadas')

	def string2float(self, s):
		try:
			float(s)
			return True
		except:
			return False

	@api.one
	def unlink(self):
		for i in self.five_no_imp_lines:
			i.unlink()
		t = super(hr_five_cat_update,self).unlink()
		return t

	@api.one
	def importar(self):
		if self.five_file == None:
			raise osv.except_osv('Alerta!', 'Debe cargar un archivo csv.')
		elif not self.delimiter:
			raise osv.except_osv('Alerta!', 'Debe indicar un delimitador.')
		else:
			self.env.cr.execute("set client_encoding ='UTF8';")
			data    = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(data['five_file']))
			fileobj.seek(0)
			fic = csv.reader(fileobj,delimiter=str(self.delimiter),quotechar='"')

			skip_titles = True
			for row in fic:
				if skip_titles:
					skip_titles = False
					continue
				detalle = ""

				# VALIDACIONES
				if not len(row[0].strip()) or not len(self.env['account.period'].search([('code','=',row[0].strip())])): #periodo
					detalle += u"- periodo incorrecto\n"
				if not len(row[1].strip()) or not len(self.env['hr.employee'].search([('identification_id','=',row[1].strip())])): #dni
					detalle += u"- dni incorrecto\n"
				if not self.string2float(row[2].strip()): #bonificación extra del periodo
					detalle += u"- bonificación extra del periodo incorrecto\n"
				if not self.string2float(row[3].strip()): #retención del periodo
					detalle += u"- retención del periodo incorrecto\n"

				ap = self.env['account.period'].search([('code','=',row[0].strip())])
				if len(ap):
					ap = ap[0]
					if not len(self.env['hr.five.category.lines'].search([('five_category_id.period_id','=',ap.id)])):
						detalle += u"- no existe 5ta cat. con este periodo\n"
					
					he = self.env['hr.employee'].search([('identification_id','=',row[1].strip())])
					if len(he):
						he = he[0]
						if not len(self.env['hr.five.category.lines'].search([('employee_id','=',he.id),('five_category_id.period_id','=',ap.id)])):
							detalle += u"- no existe el empleado en 5ta cat. para este periodo\n"

				if len(detalle):
					vals = {
						'importador_id': self.id,
						
						'period'      : row[0].strip(),
						'dni'         : row[1].strip(),
						'bonificacion': row[2].strip(),
						'retencion'   : row[3].strip(),
						'detalle'     : detalle,
					}
					self.env['hr.five.cat.update.no.importado'].create(vals)
				else:
					ap   = self.env['account.period'].search([('code','=',row[0].strip())])[0]
					he   = self.env['hr.employee'].search([('identification_id','=',row[1].strip())])[0]
					hfcl = self.env['hr.five.category.lines'].search([('employee_id','=',he.id),('five_category_id.period_id','=',ap.id)])[0]
					
					hfcl.calculo_lines[0].bon_extra_per   = float(row[2].strip())
					hfcl.calculo_lines[0].total_imponible = float(row[3].strip())
					hfcl.monto                            = hfcl.calculo_lines[0].total_imponible

	@api.one
	def importar_errores(self):
		for line in self.five_no_imp_lines:
			detalle = ""

			# VALIDACIONES
			if not len(line.period.strip()) or not len(self.env['account.period'].search([('code','=',line.period.strip())])): #periodo
				detalle += u"- periodo incorrecto\n"
			if not len(line.dni.strip()) or not len(self.env['hr.employee'].search([('identification_id','=',line.dni.strip())])): #dni
				detalle += u"- dni incorrecto\n"
			if not self.string2float(line.bonificacion.strip()): #bonificación extra del periodo
				detalle += u"- bonificación extra del periodo incorrecto\n"
			if not self.string2float(line.retencion.strip()): #retención del periodo
				detalle += u"- retención del periodo incorrecto\n"

			ap = self.env['account.period'].search([('code','=',line.period.strip())])
			if len(ap):
				ap = ap[0]
				if not len(self.env['hr.five.category.lines'].search([('five_category_id.period_id','=',ap.id)])):
					detalle += u"- no existe 5ta cat. con este periodo\n"
				
				he = self.env['hr.employee'].search([('identification_id','=',line.dni.strip())])
				if len(he):
					he = he[0]
					if not len(self.env['hr.five.category.lines'].search([('employee_id','=',he.id),('five_category_id.period_id','=',ap.id)])):
						detalle += u"- no existe el empleado en 5ta cat. para este periodo\n"

			if len(detalle):
				line.detalle = detalle
			else:
				ap   = self.env['account.period'].search([('code','=',line.period.strip())])[0]
				he   = self.env['hr.employee'].search([('identification_id','=',line.dni.strip())])[0]
				hfcl = self.env['hr.five.category.lines'].search([('employee_id','=',he.id),('five_category_id.period_id','=',ap.id)])[0]
				
				hfcl.calculo_lines[0].bon_extra_per   = float(line.bonificacion.strip())
				hfcl.calculo_lines[0].total_imponible = float(line.retencion.strip())
				hfcl.monto                            = hfcl.calculo_lines[0].total_imponible
				line.unlink()

	@api.one
	def limpiar_errores(self):
		for i in self.five_no_imp_lines:
			i.unlink()

class hr_five_cat_update_no_importado(models.Model):
	_name = 'hr.five.cat.update.no.importado'

	importador_id = fields.Many2one('hr.five.cat.update','padre')

	period       = fields.Char(u'Periodo')
	dni          = fields.Char(u'DNI')
	bonificacion = fields.Char(u'Bonificación')
	retencion    = fields.Char(u'Retención')
	detalle      = fields.Char(u'Detalle')