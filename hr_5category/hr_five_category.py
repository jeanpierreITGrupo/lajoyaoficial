# -*- coding: utf-8 -*-
from openerp     import models, fields, api
from openerp.osv import osv, expression
import pprint

from xlsxwriter.workbook import Workbook
import base64
import io
import os
import sys

class hr_five_category(models.Model):
	_name     = 'hr.five.category'
	_rec_name = 'period_id'
	
	period_id = fields.Many2one('account.period','Periodo', required=True)

	five_lines = fields.One2many('hr.five.category.lines','five_category_id','Lineas',copy=True)

	@api.model
	def create(self, vals):
		t = super(hr_five_category,self).create(vals)
		# he = self.env['hr.employee'].search([('fecha_cese','=',False)])
		# huh = self.env['hr.uit.historical'].search([('fiscalyear_id','=',t.period_id.fiscalyear_id.id)])
		# if not len(huh):
		# 	raise osv.except_osv("Alerta!", u"No existe un histórico de UIT para el año " + line.five_category_id.period_id.fiscalyear_id.code + ".")
		# for i in he:
		# 	if ((i.basica*14) - (huh[0].amount*7)) > 0:
		# 		l_vals = {}
		# 		l_vals['five_category_id'] = t.id
		# 		l_vals['employee_id']      = i.id
		# 		n_l = self.env['hr.five.category.lines'].create(l_vals)
		return t

	@api.one
	def copy(self,default):
		t = super(hr_five_category, self).copy(default)
		for i in range(len(self.five_lines)):
			to_write = self.five_lines[i].calculo_lines[0].read()[0]
			no_considerar = ['__last_update','create_date','create_uid','display_name','five_line_id','id','write_date','write_uid']
			for nc in no_considerar:
				to_write.pop(nc,None)
			t.five_lines[i].calculo_lines[0].write(to_write)

			to_write = self.five_lines[i].remuneracion_lines[0].read()[0]
			no_considerar = ['__last_update','create_date','create_uid','display_name','five_line_id','id','write_date','write_uid']
			for nc in no_considerar:
				to_write.pop(nc,None)
			t.five_lines[i].remuneracion_lines[0].write(to_write)

			to_write = self.five_lines[i].descuento_lines[0].read()[0]
			no_considerar = ['__last_update','create_date','create_uid','display_name','five_line_id','id','write_date','write_uid']
			for nc in no_considerar:
				to_write.pop(nc,None)
			t.five_lines[i].descuento_lines[0].write(to_write)

			to_write = self.five_lines[i].manual_lines[0].read()[0]
			no_considerar = ['__last_update','create_date','create_uid','display_name','five_line_id','id','write_date','write_uid']
			for nc in no_considerar:
				to_write.pop(nc,None)
			t.five_lines[i].manual_lines[0].write(to_write)
		return t

	@api.one
	def unlink(self):
		for i in self.five_lines:
			for j in i.calculo_lines:
				j.unlink()
			for k in i.remuneracion_lines:
				k.unlink()
			for l in i.descuento_lines:
				l.unlink()
			for l in i.manual_lines:
				l.unlink()
		return super(hr_five_category,self).unlink()

	@api.one
	def procesar(self):
		hp_essalud = self.env['hr.parameters'].search([('num_tipo','=',4)])[0]
		hp_eps_essalud = self.env['hr.parameters'].search([('num_tipo','=',99)])[0]
		for line in self.five_lines:
			line.calculo_lines[0].sueldo_anual   = line.remuneracion_lines[0].total
			line.calculo_lines[0].bonificacion_j = line.calculo_lines[0].gratificacion_j * (hp_eps_essalud.monto if line.employee_id.use_eps else hp_essalud.monto)/100.00
			line.calculo_lines[0].bonificacion_d = line.calculo_lines[0].gratificacion_d * (hp_eps_essalud.monto if line.employee_id.use_eps else hp_essalud.monto)/100.00
			
			meses = ['01','02','03','04','05','06','07','08','09','10','11','12']
			meses_eval = meses[:meses.index(line.five_category_id.period_id.code.split('/')[0])]
			b_ex = 0
			for i in meses_eval:
				five_ant = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=',i+'/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				b_ex += (five_ant[0].calculo_lines[0].bon_extra_per if len(five_ant) else 0)
			line.calculo_lines[0].bonificacion_ex = b_ex

			line.calculo_lines[0].renta_bruta  = line.calculo_lines[0].sueldo_anual + line.calculo_lines[0].gratificacion_j + line.calculo_lines[0].bonificacion_j + line.calculo_lines[0].gratificacion_d + line.calculo_lines[0].bonificacion_d + line.calculo_lines[0].bonificacion_ex
			line.calculo_lines[0].total_rentas = line.calculo_lines[0].renta_bruta + line.calculo_lines[0].otras_rentas

			huh = self.env['hr.uit.historical'].search([('fiscalyear_id','=',line.five_category_id.period_id.fiscalyear_id.id)])
			if not len(huh):
				raise osv.except_osv("Alerta!", u"No existe un histórico de UIT para el año " + line.five_category_id.period_id.fiscalyear_id.code + ".")
			huh = huh[0]
			if huh.amount*7 > line.calculo_lines[0].total_rentas:
				line.calculo_lines[0].deduccion_uit = line.calculo_lines[0].total_rentas
			else:
				line.calculo_lines[0].deduccion_uit = huh.amount*7
			line.calculo_lines[0].renta_neta = line.calculo_lines[0].total_rentas - line.calculo_lines[0].deduccion_uit
			
			if not len(self.env['hr.5percent'].search([])):
				raise osv.except_osv("Alerta!", u"No existen parámetros de quinta categoría.")
			uit_year    = self.env['hr.uit.historical'].search([('fiscalyear_id','=',self.period_id.fiscalyear_id.id)])
			h5          = self.env['hr.5percent'].search([('type_element','=','hasta'),('uit_id','=',uit_year.id)]).sorted(key=lambda r: r.id)
			h5_ex       = self.env['hr.5percent'].search([])[-1]
			uit_qty_all = [i.uit_qty*huh.amount for i in h5]
			tramos      = []
			aux         = 0
			tmp 		= line.calculo_lines[0].renta_neta
			tmp2		= line.calculo_lines[0].renta_neta + line.calculo_lines[0].bon_extra_per
			if line.calculo_lines[0].bon_extra_per == 0:
				tmp2 = 0
			for i in uit_qty_all:
				tramos.append(i-aux)
				aux = i
			distrib = []
			distrib2 = []
			for i in tramos:
				if tmp >= i:
					distrib.append(i)
					tmp -= i
				else:
					distrib.append(tmp)
					tmp = 0
					break
			for i in tramos:
				if tmp2 >= i:
					distrib2.append(i)
					tmp2 -= i
				else:
					distrib2.append(tmp2)
					tmp2 = 0
					break
			res = []
			for i in range(len(distrib)):
				res.append(distrib[i]*(h5[i].tasa/100.00))
			if tmp:
				res.append(tmp*(h5_ex.tasa/100.00))
			res2 = []
			for i in range(len(distrib2)):
				res2.append(distrib2[i]*(h5[i].tasa/100.00))
			if tmp2:
				res2.append(tmp2*(h5_ex.tasa/100.00))
			line.calculo_lines[0].impuesto_anual = sum(res)



			desc_enero_marzo           = 0
			desc_abril                 = 0
			desc_mayo_julio            = 0
			desc_agosto                = 0
			desc_septiembre_noviembre  = 0
			desc_diciembre             = 0
			desc_enero_marzo2          = 0
			desc_abril2                = 0
			desc_mayo_julio2           = 0
			desc_agosto2               = 0
			desc_septiembre_noviembre2 = 0
			desc_diciembre2            = 0
			# -line.calculo_lines[0].otras_retencion
			#ENERO
			if self.period_id.code.split('/')[0] == '01':
				impuesto_renta = sum(res)
				five_enero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				desc_enero      = (impuesto_renta-five_enero.calculo_lines[0].otras_retencion)/12.00
				desc_febrero    = (impuesto_renta)/12.00
				desc_marzo      = (impuesto_renta)/12.00

				desc_abril      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo)/9.00
				desc_mayo       = (impuesto_renta - desc_enero - desc_febrero - desc_marzo-desc_abril)/8.00
				desc_junio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo-desc_abril)/8.00
				desc_julio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo-desc_abril)/8.00
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio-desc_julio)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#FEBRERO
			if self.period_id.code.split('/')[0] == '02':
				five_enero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = (impuesto_renta-line.calculo_lines[0].otras_retencion)/12.00
				desc_marzo      = (impuesto_renta)/12.00
				desc_abril      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo)/9.00
				desc_mayo       = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_junio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_julio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#MARZO
			if self.period_id.code.split('/')[0] == '03':
				five_enero   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = (impuesto_renta-line.calculo_lines[0].otras_retencion)/12.00
				desc_abril      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo)/9.00
				desc_mayo       = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_junio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_julio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#ABRIL
			if self.period_id.code.split('/')[0] == '04':
				five_enero   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo-line.calculo_lines[0].otras_retencion)/9.00
				desc_mayo       = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_junio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_julio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
				print line.employee_id.last_name_father,'desc_abril',desc_abril
			#MAYO
			if self.period_id.code.split('/')[0] == '05':
				five_enero   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril-line.calculo_lines[0].otras_retencion)/8.00
				desc_junio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_julio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
				print line.employee_id.last_name_father,'desc_mayo',desc_mayo
			#JUNIO
			if self.period_id.code.split('/')[0] == '06':
				five_enero   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_mayo    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','05/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = five_mayo[0].calculo_lines[0].total_imponible if len(five_mayo) else 0
				desc_junio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril-line.calculo_lines[0].otras_retencion)/8.00
				desc_julio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril)/8.00
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#JULIO
			if self.period_id.code.split('/')[0] == '07':
				five_enero   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_mayo    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','05/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_junio   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','06/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = five_mayo[0].calculo_lines[0].total_imponible if len(five_mayo) else 0
				desc_junio      = five_junio[0].calculo_lines[0].total_imponible if len(five_junio) else 0
				desc_julio      = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril-line.calculo_lines[0].otras_retencion)/8.00
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#AGOSTO
			if self.period_id.code.split('/')[0] == '08':
				five_enero   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_mayo    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','05/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_junio   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','06/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_julio   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','07/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = five_mayo[0].calculo_lines[0].total_imponible if len(five_mayo) else 0
				desc_junio      = five_junio[0].calculo_lines[0].total_imponible if len(five_junio) else 0
				desc_julio      = five_julio[0].calculo_lines[0].total_imponible if len(five_julio) else 0
				desc_agosto     = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio-line.calculo_lines[0].otras_retencion)/5.00
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#SEPTIEMBRE
			if self.period_id.code.split('/')[0] == '09':
				five_enero   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_mayo    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','05/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_junio   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','06/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_julio   = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','07/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_agosto  = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','08/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = five_mayo[0].calculo_lines[0].total_imponible if len(five_mayo) else 0
				desc_junio      = five_junio[0].calculo_lines[0].total_imponible if len(five_junio) else 0
				desc_julio      = five_julio[0].calculo_lines[0].total_imponible if len(five_julio) else 0
				desc_agosto     = five_agosto[0].calculo_lines[0].total_imponible if len(five_agosto) else 0
				desc_septiembre = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto-line.calculo_lines[0].otras_retencion)/4.00
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#OCTUBRE
			if self.period_id.code.split('/')[0] == '10':
				five_enero      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_mayo       = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','05/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_junio      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','06/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_julio      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','07/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_agosto     = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','08/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_septiembre = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','09/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = five_mayo[0].calculo_lines[0].total_imponible if len(five_mayo) else 0
				desc_junio      = five_junio[0].calculo_lines[0].total_imponible if len(five_junio) else 0
				desc_julio      = five_julio[0].calculo_lines[0].total_imponible if len(five_julio) else 0
				desc_agosto     = five_agosto[0].calculo_lines[0].total_imponible if len(five_agosto) else 0
				desc_septiembre = five_septiembre[0].calculo_lines[0].total_imponible if len(five_septiembre) else 0
				desc_octubre    = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto-line.calculo_lines[0].otras_retencion)/4.00
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#NOVIEMBRE
			if self.period_id.code.split('/')[0] == '11':
				five_enero      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_mayo       = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','05/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_junio      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','06/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_julio      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','07/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_agosto     = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','08/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_septiembre = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','09/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_octubre    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','10/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)

				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = five_mayo[0].calculo_lines[0].total_imponible if len(five_mayo) else 0
				desc_junio      = five_junio[0].calculo_lines[0].total_imponible if len(five_junio) else 0
				desc_julio      = five_julio[0].calculo_lines[0].total_imponible if len(five_julio) else 0
				desc_agosto     = five_agosto[0].calculo_lines[0].total_imponible if len(five_agosto) else 0
				desc_septiembre = five_septiembre[0].calculo_lines[0].total_imponible if len(five_septiembre) else 0
				desc_octubre    = five_octubre[0].calculo_lines[0].total_imponible if len(five_octubre) else 0
				desc_noviembre  = (impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto-line.calculo_lines[0].otras_retencion)/4.00
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre
			#DICIEMBRE
			if self.period_id.code.split('/')[0] == '12':
				five_enero      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','01/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_febrero    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','02/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_marzo      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','03/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_abril      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','04/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_mayo       = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','05/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_junio      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','06/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_julio      = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','07/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_agosto     = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','08/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_septiembre = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','09/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_octubre    = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','10/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				five_noviembre  = self.env['hr.five.category.lines'].search([('five_category_id.period_id.code','=','11/'+self.period_id.fiscalyear_id.code),('employee_id','=',line.employee_id.id)])
				impuesto_renta = sum(res)
				desc_enero      = five_enero[0].calculo_lines[0].total_imponible if len(five_enero) else 0
				desc_febrero    = five_febrero[0].calculo_lines[0].total_imponible if len(five_febrero) else 0
				desc_marzo      = five_marzo[0].calculo_lines[0].total_imponible if len(five_marzo) else 0
				desc_abril      = five_abril[0].calculo_lines[0].total_imponible if len(five_abril) else 0
				desc_mayo       = five_mayo[0].calculo_lines[0].total_imponible if len(five_mayo) else 0
				desc_junio      = five_junio[0].calculo_lines[0].total_imponible if len(five_junio) else 0
				desc_julio      = five_julio[0].calculo_lines[0].total_imponible if len(five_julio) else 0
				desc_agosto     = five_agosto[0].calculo_lines[0].total_imponible if len(five_agosto) else 0
				desc_septiembre = five_septiembre[0].calculo_lines[0].total_imponible if len(five_septiembre) else 0
				desc_octubre    = five_octubre[0].calculo_lines[0].total_imponible if len(five_octubre) else 0
				desc_noviembre  = five_noviembre[0].calculo_lines[0].total_imponible if len(five_noviembre) else 0
				desc_diciembre  = impuesto_renta - desc_enero - desc_febrero - desc_marzo - desc_abril - desc_mayo - desc_junio - desc_julio - desc_agosto - desc_septiembre - desc_octubre - desc_noviembre-line.calculo_lines[0].otras_retencion

			impuesto_renta2 = sum(res2)
			desc_enero2      = (impuesto_renta2/12.00)
			desc_febrero2    = (impuesto_renta2/12.00)
			desc_marzo2      = (impuesto_renta2/12.00)
			desc_abril2      = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2)/9.00
			desc_mayo2       = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2)/8.00
			desc_junio2      = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2)/8.00
			desc_julio2      = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2)/8.00
			desc_agosto2     = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2 - desc_mayo2 - desc_junio2 - desc_julio2)/5.00
			desc_septiembre2 = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2 - desc_mayo2 - desc_junio2 - desc_julio2 - desc_agosto2)/4.00
			desc_octubre2    = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2 - desc_mayo2 - desc_junio2 - desc_julio2 - desc_agosto2)/4.00
			desc_noviembre2  = (impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2 - desc_mayo2 - desc_junio2 - desc_julio2 - desc_agosto2)/4.00
			desc_diciembre2  = impuesto_renta2 - desc_enero2 - desc_febrero2 - desc_marzo2 - desc_abril2 - desc_mayo2 - desc_junio2 - desc_julio2 - desc_agosto2 - desc_septiembre2 - desc_octubre2 - desc_noviembre2	




			if not line.monto_man:
				line.descuento_lines[0].enero      = desc_enero
				line.descuento_lines[0].febrero    = desc_febrero
				line.descuento_lines[0].marzo      = desc_marzo				
				line.descuento_lines[0].abril      = desc_abril
				line.descuento_lines[0].mayo       = desc_mayo
				line.descuento_lines[0].junio      = desc_junio
				line.descuento_lines[0].julio      = desc_julio
				line.descuento_lines[0].agosto     = desc_agosto
				line.descuento_lines[0].septiembre = desc_septiembre
				line.descuento_lines[0].octubre    = desc_octubre
				line.descuento_lines[0].noviembre  = desc_noviembre
				line.descuento_lines[0].diciembre  = desc_diciembre

				if self.period_id.code.split("/")[0] == '01':
					line.calculo_lines[0].retencion_men   = desc_enero
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '02':
					line.calculo_lines[0].retencion_men   = desc_febrero
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '03':
					line.calculo_lines[0].retencion_men   = desc_marzo
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '04':
					line.calculo_lines[0].retencion_men   = desc_abril
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '05':
					line.calculo_lines[0].retencion_men   = desc_mayo
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '06':
					line.calculo_lines[0].retencion_men   = desc_junio
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '07':
					line.calculo_lines[0].retencion_men   = desc_julio
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '08':
					line.calculo_lines[0].retencion_men   = desc_agosto
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '09':
					line.calculo_lines[0].retencion_men   = desc_septiembre
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '10':
					line.calculo_lines[0].retencion_men   = desc_octubre
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '11':
					line.calculo_lines[0].retencion_men   = desc_noviembre
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta
				if self.period_id.code.split("/")[0] == '12':
					line.calculo_lines[0].retencion_men   = desc_diciembre
					if line.calculo_lines[0].bon_extra_per == 0:
						line.calculo_lines[0].ret_por_bon_ext = 0
					else:
						line.calculo_lines[0].ret_por_bon_ext = impuesto_renta2 - impuesto_renta

				line.calculo_lines[0].total_imponible = line.calculo_lines[0].retencion_men + line.calculo_lines[0].ret_por_bon_ext
				line.monto = line.calculo_lines[0].total_imponible
			else:
				if self.period_id.code.split("/")[0] == '01':
					line.monto = line.manual_lines[0].enero
				if self.period_id.code.split("/")[0] == '02':
					line.monto = line.manual_lines[0].febrero
				if self.period_id.code.split("/")[0] == '03':
					line.monto = line.manual_lines[0].marzo
				if self.period_id.code.split("/")[0] == '04':
					line.monto = line.manual_lines[0].abril
				if self.period_id.code.split("/")[0] == '05':
					line.monto = line.manual_lines[0].mayo
				if self.period_id.code.split("/")[0] == '06':
					line.monto = line.manual_lines[0].junio
				if self.period_id.code.split("/")[0] == '07':
					line.monto = line.manual_lines[0].julio
				if self.period_id.code.split("/")[0] == '08':
					line.monto = line.manual_lines[0].agosto
				if self.period_id.code.split("/")[0] == '09':
					line.monto = line.manual_lines[0].septiembre
				if self.period_id.code.split("/")[0] == '10':
					line.monto = line.manual_lines[0].octubre
				if self.period_id.code.split("/")[0] == '11':
					line.monto = line.manual_lines[0].noviembre
				if self.period_id.code.split("/")[0] == '12':
					line.monto = line.manual_lines[0].diciembre
	
class hr_five_category_lines(models.Model):
	_name     = 'hr.five.category.lines'
	_rec_name = 'employee_id'
	
	five_category_id = fields.Many2one('hr.five.category','Main')

	employee_id = fields.Many2one('hr.employee', 'Trabajador', required=True)
	monto_man	= fields.Boolean(u'Empleado nuevo')
	monto		= fields.Float('Monto')

	calculo_lines      = fields.One2many('hr.five.category.calculo','five_line_id','calculo')
	remuneracion_lines = fields.One2many('hr.five.category.remuneracion','five_line_id','remuneracion')
	descuento_lines    = fields.One2many('hr.five.category.descuento','five_line_id','descuento')
	manual_lines  	   = fields.One2many('hr.five.category.manual','five_line_id','manual')

	@api.model
	def create(self,vals):
		hfclr = self.env['hr.five.category.lines'].search([('employee_id','=',vals['employee_id']),('five_category_id','=',vals['five_category_id'])])
		if len(hfclr):
			raise osv.except_osv("Alerta!", u"El empleado " + hfclr[0].employee_id.name_related + " ya existe.")
		t = super(hr_five_category_lines,self).create(vals)

		vals_c = {}
		vals_c['five_line_id']    = t.id
		vals_c['sueldo_anual']    = 0
		vals_c['gratificacion_j'] = 0
		vals_c['bonificacion_j']  = 0
		vals_c['gratificacion_d'] = 0
		vals_c['bonificacion_d']  = 0
		vals_c['renta_bruta']     = 0
		vals_c['otras_rentas']    = 0
		vals_c['total_rentas']    = 0
		vals_c['deduccion_uit']   = 0
		vals_c['bonificacion_ex'] = 0
		vals_c['renta_neta']      = 0
		vals_c['retencion_men']   = 0
		vals_c['bon_extra_per']   = 0
		vals_c['ret_por_bon_ext'] = 0
		vals_c['total_imponible'] = 0
		self.env['hr.five.category.calculo'].create(vals_c)

		vals_rd = {}
		vals_rd['five_line_id'] = t.id
		vals_rd['enero']        = 0
		vals_rd['febrero']      = 0
		vals_rd['marzo']        = 0
		vals_rd['abril']        = 0
		vals_rd['mayo']         = 0
		vals_rd['junio']        = 0
		vals_rd['julio']        = 0
		vals_rd['agosto']       = 0
		vals_rd['septiembre']   = 0
		vals_rd['octubre']      = 0
		vals_rd['noviembre']    = 0
		vals_rd['diciembre']    = 0
		vals_rd['total']        = 0
		self.env['hr.five.category.remuneracion'].create(vals_rd)
		self.env['hr.five.category.descuento'].create(vals_rd)
		self.env['hr.five.category.manual'].create(vals_rd)
		return t

	@api.one
	def write(self,vals):
		if 'employee_id' in vals:
			hfclr = self.env['hr.five.category.lines'].search([('employee_id','=',vals['employee_id']),('five_category_id','=',self.five_category_id.id),('id','!=',self.id)])
			if len(hfclr):
				raise osv.except_osv("Alerta!", u"El empleado " + hfclr[0].employee_id.name_related + " ya existe.")
		t = super(hr_five_category_lines,self).write(vals)
		return t

	@api.multi
	def make_excel(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		basic = {
			'align'		: 'left',
			'valign'	: 'vcenter',
			'text_wrap'	: 1,
			'font_size'	: 9,
			'font_name'	: 'Calibri'
		}

		numeric = basic.copy()
		numeric['align'] = 'right'
		numeric['num_format'] = '#,##0.00'

		numeric_int = basic.copy()
		numeric_int['align'] = 'right'

		numeric_int_bold = numeric.copy()
		numeric_int_bold['bold'] = 1

		numeric_bold = numeric.copy()
		numeric_bold['bold'] = 1
		numeric_bold['num_format'] = '#,##0.00'

		bold = basic.copy()
		bold['bold'] = 1

		header = bold.copy()
		header['bg_color'] = '#A9D0F5'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 15

		highlight_line = basic.copy()
		highlight_line['bold'] = 1
		highlight_line['bg_color'] = '#C1E1FF'

		highlight_numeric_line = highlight_line.copy()
		highlight_numeric_line['num_format'] = '#,##0.00'
		highlight_numeric_line['align'] = 'right'		

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Reporte_5ta_categoria'
		workbook  = Workbook(direccion + titulo + '.xlsx')

		worksheet = workbook.add_worksheet(self.employee_id.name_related[:31] if self.employee_id.name_related else "Empleado")
		
		basic_format                  = workbook.add_format(basic)
		bold_format                   = workbook.add_format(bold)
		numeric_int_format            = workbook.add_format(numeric_int)
		numeric_int_bold_format       = workbook.add_format(numeric_int_bold)
		numeric_format                = workbook.add_format(numeric)
		numeric_bold_format           = workbook.add_format(numeric_bold)
		title_format                  = workbook.add_format(title)
		header_format                 = workbook.add_format(header)
		highlight_line_format         = workbook.add_format(highlight_line)
		highlight_numeric_line_format = workbook.add_format(highlight_numeric_line)

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', "RUC: "+rc.partner_id.type_number if rc.partner_id.type_number else 'RUC: ', title_format)
		worksheet.merge_range('A3:D3', ("Trabajador: "+self.employee_id.name_related) if self.employee_id.name_related else "Trabajador", title_format)

		row = 3
		col = 0

		headers = [u'Sueldo Anual a Percibir',
				   u'Gratificación Julio',
				   u'Bonificación Extraordinaria Julio',
				   u'Gratificación Diciembre',
				   u'Bonificación Extraordinaria Diciembre',
				   u'Bonificación ext. de meses anteriores',
				   u'Renta bruta',
				   u'Otras Rentas de Quinta Categoría',
				   u'Total Rentas de Quinta Categoría',
				   u'Deducción de 7 UIT',
				   u'Renta neta anual',
				   u'Impuesto anual',
				   u'Retención mensual R1',
				   u'Bon extra del periodo',
				   u'Ret por bon ext R2',
				   u'Retención del periodo',]

		row += 1
		for pos in range(len(headers)):
			worksheet.write(row,pos, headers[pos], header_format)

		row += 1
		col = 0
		worksheet.write(row,col, self.calculo_lines[0].sueldo_anual, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].gratificacion_j, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].bonificacion_j, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].gratificacion_d, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].bonificacion_d, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].bonificacion_ex, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].renta_bruta, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].otras_rentas, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].total_rentas, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].deduccion_uit, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].renta_neta, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].impuesto_anual, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].retencion_men, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].bon_extra_per, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].ret_por_bon_ext, numeric_format)
		col += 1
		worksheet.write(row,col, self.calculo_lines[0].total_imponible, numeric_format)
		col += 1


		col_sizes = [10.43, 24.71, 41.43]
		worksheet.set_column('A:O', col_sizes[0])

		workbook.close()

		f = open(direccion + titulo + '.xlsx', 'rb')
		
		vals = {
			'output_name': titulo + '.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id  = self.env['export.file.save'].create(vals)

		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}

class hr_five_category_calculo(models.Model):
	_name = 'hr.five.category.calculo'

	five_line_id = fields.Many2one('hr.five.category.lines','padre')

	sueldo_anual    = fields.Float(u'Sueldo Anual a Percibir')
	gratificacion_j = fields.Float(u'Gratificación Julio')
	bonificacion_j  = fields.Float(u'Bonificación Extraordinaria Julio')
	gratificacion_d = fields.Float(u'Gratificación Diciembre')
	bonificacion_d  = fields.Float(u'Bonificación Extraordinaria Diciembre')
	bonificacion_ex = fields.Float(u'Bonificación ext. de meses anteriores')
	renta_bruta     = fields.Float(u'Renta bruta')
	otras_rentas    = fields.Float(u'Otras Rentas de Quinta Categoría')
	total_rentas    = fields.Float(u'Total Rentas de Quinta Categoría')
	deduccion_uit   = fields.Float(u'Deducción de 7 UIT')
	renta_neta      = fields.Float(u'Renta neta anual')
	impuesto_anual  = fields.Float(u'Impuesto anual')

	otras_retencion = fields.Float(u'Otras retenciones de 5ta')

	retencion_men   = fields.Float(u'Retención mensual R1')
	bon_extra_per   = fields.Float(u'Bon extra del periodo')
	ret_por_bon_ext = fields.Float(u'Ret por bon ext R2')
	total_imponible = fields.Float(u'Retención del periodo')

class hr_five_category_remuneracion(models.Model):
	_name = 'hr.five.category.remuneracion'

	five_line_id = fields.Many2one('hr.five.category.lines','padre')

	enero      = fields.Float(u'Enero')
	febrero    = fields.Float(u'Febrero')
	marzo      = fields.Float(u'Marzo')
	abril      = fields.Float(u'Abril')
	mayo       = fields.Float(u'Mayo')
	junio      = fields.Float(u'Junio')
	julio      = fields.Float(u'Julio')
	agosto     = fields.Float(u'Agosto')
	septiembre = fields.Float(u'Septiembre')
	octubre    = fields.Float(u'Octubre')
	noviembre  = fields.Float(u'Noviembre')
	diciembre  = fields.Float(u'Diciembre')
	total      = fields.Float(u'Total', compute="compute_total")

	@api.onchange('enero')
	def onchange_enero(self):
		self.febrero    = self.enero
		self.marzo      = self.enero
		self.abril      = self.enero
		self.mayo       = self.enero
		self.junio      = self.enero
		self.julio      = self.enero
		self.agosto     = self.enero
		self.septiembre = self.enero
		self.octubre    = self.enero
		self.noviembre  = self.enero
		self.diciembre  = self.enero

	@api.onchange('febrero')
	def onchange_febrero(self):
		self.marzo      = self.febrero
		self.abril      = self.febrero
		self.mayo       = self.febrero
		self.junio      = self.febrero
		self.julio      = self.febrero
		self.agosto     = self.febrero
		self.septiembre = self.febrero
		self.octubre    = self.febrero
		self.noviembre  = self.febrero
		self.diciembre  = self.febrero

	@api.onchange('marzo')
	def onchange_marzo(self):
		self.abril      = self.marzo
		self.mayo       = self.marzo
		self.junio      = self.marzo
		self.julio      = self.marzo
		self.agosto     = self.marzo
		self.septiembre = self.marzo
		self.octubre    = self.marzo
		self.noviembre  = self.marzo
		self.diciembre  = self.marzo

	@api.onchange('abril')
	def onchange_abril(self):
		self.mayo       = self.abril
		self.junio      = self.abril
		self.julio      = self.abril
		self.agosto     = self.abril
		self.septiembre = self.abril
		self.octubre    = self.abril
		self.noviembre  = self.abril
		self.diciembre  = self.abril

	@api.onchange('mayo')
	def onchange_mayo(self):
		self.junio      = self.mayo
		self.julio      = self.mayo
		self.agosto     = self.mayo
		self.septiembre = self.mayo
		self.octubre    = self.mayo
		self.noviembre  = self.mayo
		self.diciembre  = self.mayo

	@api.onchange('junio')
	def onchange_junio(self):
		self.julio      = self.junio
		self.agosto     = self.junio
		self.septiembre = self.junio
		self.octubre    = self.junio
		self.noviembre  = self.junio
		self.diciembre  = self.junio

	@api.onchange('julio')
	def onchange_julio(self):
		self.agosto     = self.julio
		self.septiembre = self.julio
		self.octubre    = self.julio
		self.noviembre  = self.julio
		self.diciembre  = self.julio

	@api.onchange('agosto')
	def onchange_agosto(self):
		self.septiembre = self.agosto
		self.octubre    = self.agosto
		self.noviembre  = self.agosto
		self.diciembre  = self.agosto

	@api.onchange('septiembre')
	def onchange_septiembre(self):
		self.octubre    = self.septiembre
		self.noviembre  = self.septiembre
		self.diciembre  = self.septiembre

	@api.onchange('octubre')
	def onchange_octubre(self):
		self.noviembre  = self.octubre
		self.diciembre  = self.octubre

	@api.onchange('noviembre')
	def onchange_noviembre(self):
		self.diciembre  = self.noviembre

	@api.one
	def compute_total(self):
		self.total = self.enero + self.febrero + self.marzo + self.abril + self.mayo + self.junio + self.julio + self.agosto + self.septiembre + self.octubre + self.noviembre + self.diciembre

class hr_five_category_descuento(models.Model):
	_name = 'hr.five.category.descuento'

	five_line_id = fields.Many2one('hr.five.category.lines','padre')

	enero      = fields.Float(u'Enero')
	febrero    = fields.Float(u'Febrero')
	marzo      = fields.Float(u'Marzo')
	abril      = fields.Float(u'Abril')
	mayo       = fields.Float(u'Mayo')
	junio      = fields.Float(u'Junio')
	julio      = fields.Float(u'Julio')
	agosto     = fields.Float(u'Agosto')
	septiembre = fields.Float(u'Septiembre')
	octubre    = fields.Float(u'Octubre')
	noviembre  = fields.Float(u'Noviembre')
	diciembre  = fields.Float(u'Diciembre')
	total      = fields.Float(u'Total', compute="compute_total")

	@api.one
	def compute_total(self):
		self.total = self.enero + self.febrero + self.marzo + self.abril + self.mayo + self.junio + self.julio + self.agosto + self.septiembre + self.octubre + self.noviembre + self.diciembre

class hr_five_category_manual(models.Model):
	_name = 'hr.five.category.manual'

	five_line_id = fields.Many2one('hr.five.category.lines','padre')

	enero      = fields.Float(u'Enero')
	febrero    = fields.Float(u'Febrero')
	marzo      = fields.Float(u'Marzo')
	abril      = fields.Float(u'Abril')
	mayo       = fields.Float(u'Mayo')
	junio      = fields.Float(u'Junio')
	julio      = fields.Float(u'Julio')
	agosto     = fields.Float(u'Agosto')
	septiembre = fields.Float(u'Septiembre')
	octubre    = fields.Float(u'Octubre')
	noviembre  = fields.Float(u'Noviembre')
	diciembre  = fields.Float(u'Diciembre')


#DEVOLUCION DE RENTA
class hr_five_category_devolucion(models.Model):
	_name     = 'hr.five.category.devolucion'
	_rec_name = 'period_id'

	period_id = fields.Many2one('account.period',u'Periodo', required=True)

	devolucion_lines = fields.One2many('hr.five.category.devolucion.lines','devolucion_id',u'Lineas')

	@api.one
	def unlink(self):
		for i in self.devolucion_lines:
			i.unlink()
		return super(hr_five_category_devolucion,self).unlink()

class hr_five_category_devolucion_lines(models.Model):
	_name = 'hr.five.category.devolucion.lines'

	devolucion_id = fields.Many2one('hr.five.category.devolucion',u'Padre')

	employee_id 		= fields.Many2one('hr.employee','Empleado', domain=[('fecha_cese','!=',False)], required=True)
	fecha_cese 			= fields.Date(u'Fecha de Cese')
	fecha_ingreso		= fields.Date(u'Fecha de Ingreso')
	ingresos_afectos    = fields.Float(u'Ingresos Afectos a 5ta', compute="compute_ingresos_afectos")

	otras_rentas        = fields.Float(u'Otras Rentas de 5ta Categoría')
	total_ingresos      = fields.Float(u'Total Ingresos Afectos a 5ta', compute="compute_tot_ingresos_afectos")

	deduccion_uit       = fields.Float(u'Deducción 7 UIT', compute="compute_deduccion_uit")
	renta_neta          = fields.Float(u'Renta Neta Anual', compute="compute_renta_neta")
	impuesto_anual      = fields.Float(u'Impuesto Anual Real', compute="compute_impuesto_anual")
	retencion_efectuada = fields.Float(u'Retenciones Efectuadas', compute="compute_retencion_efectuada")
	monto_devolver      = fields.Float(u'Monto a Devolver/Retener', compute="compute_monto_devolver")



	@api.model
	def create(self, vals):
		if 'employee_id' in vals:
			he = self.env['hr.employee'].search([('id','=',vals['employee_id'])])[0]
			vals['fecha_cese'] = he.fecha_cese
			vals['fecha_ingreso'] = he.fecha_ingreso

		t = super(hr_five_category_devolucion_lines,self).create(vals)
		return t

	@api.one
	def write(self, vals):
		# if 'employee_id' in vals:
		# 	he = self.env['hr.employee'].search([('id','=',vals['employee_id'])])[0]
		# 	vals['fecha_cese'] = he.fecha_cese
		# 	vals['fecha_ingreso'] = he.fecha_ingreso
		t = super(hr_five_category_devolucion_lines,self).write(vals)
		return t

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.fecha_cese = self.employee_id.fecha_cese
			self.fecha_ingreso = self.employee_id.fecha_ingreso

	@api.one
	def compute_ingresos_afectos(self):
		if self.fecha_cese and self.fecha_ingreso:
			ran_l = self.fecha_cese.split('-')
			rang_meses = self.get_range()
			res = 0
			for mes in rang_meses:
				per = mes+"/"+ran_l[0]
				ht = self.env['hr.tareo'].search([('periodo','=',per)])
				if len(ht):
					ht = ht[0]
					htl = self.env['hr.tareo.line'].search([('employee_id','=',self.employee_id.id),('tareo_id','=',ht.id)])
					if len(htl):
						htl = htl[0]						
						for con_in in htl.conceptos_ingresos_lines:
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',con_in.concepto_id.id)])
							if len(hcrl):
								hcrl = hcrl[0]
								if hcrl.quinta_categ:
									res += con_in.monto
						for con_de in htl.conceptos_descuentos_base_lines:
							res -= con_de.monto
			self.ingresos_afectos = res

	@api.one
	def compute_deduccion_uit(self):
		if self.fecha_cese:
			ran_l = self.fecha_cese.split('-')
			huh = self.env['hr.uit.historical'].search([('fiscalyear_id.code','=',ran_l[0])])
			res = 0
			if len(huh):
				huh = huh[0]
				res = huh.amount
			self.deduccion_uit = res*7

	@api.one
	def compute_renta_neta(self):
		if self.fecha_cese:
			self.renta_neta = self.total_ingresos - self.deduccion_uit

	@api.one
	def compute_tot_ingresos_afectos(self):
		self.total_ingresos = self.ingresos_afectos+self.otras_rentas


	@api.one
	def compute_impuesto_anual(self):
		if self.fecha_cese and self.fecha_ingreso:
			ran_l = self.fecha_cese.split('-')
			huh = self.env['hr.uit.historical'].search([('fiscalyear_id.code','=',ran_l[0])])

			if len(huh):
				huh = huh[0]
				h5          = self.env['hr.5percent'].search([('type_element','=','hasta'),('uit_id','=',huh.id)]).sorted(key=lambda r: r.id)
				h5_ex       = self.env['hr.5percent'].search([('uit_id','=',huh.id)])[-1]
				if len(h5) and len(h5_ex):
					uit_qty_all = [i.uit_qty*huh.amount for i in h5]
					tramos      = []
					aux         = 0
					tmp 		= self.renta_neta

					for i in uit_qty_all:
						tramos.append(i-aux)
						aux = i
					distrib = []
					for i in tramos:
						if tmp >= i:
							distrib.append(i)
							tmp -= i
						else:
							distrib.append(tmp)
							tmp = 0
							break				
					res = []
					for i in range(len(distrib)):
						res.append(distrib[i]*h5[i].tasa/100.00)
					if tmp:
						res.append(tmp*h5_ex.tasa/100.00)
					if sum(res)>0:
						self.impuesto_anual = sum(res)
					else:
						self.impuesto_anual = 0
	@api.one
	def compute_retencion_efectuada(self):
		if self.fecha_cese and self.fecha_ingreso:
			ran_l = self.fecha_cese.split('-')
			rang_meses = self.get_range()

			print 1, rang_meses
			res = 0
			for mes in rang_meses:
				print ran_l
				print mes,"/",ran_l[0]
				per = mes+"/"+ran_l[0]
				ht = self.env['hr.tareo'].search([('periodo','=',per)])
				if len(ht):
					ht = ht[0]
					htl = self.env['hr.tareo.line'].search([('employee_id','=',self.employee_id.id),('tareo_id','=',ht.id)])
					if len(htl):
						htl = htl[0]
						qc = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','033')])
						if len(qc):
							qc = qc[0]
							res += qc.monto						
			self.retencion_efectuada = res

	@api.one
	def compute_monto_devolver(self):
		self.monto_devolver = self.impuesto_anual - self.retencion_efectuada


	@api.model
	def get_range(self):
		meses = ['01','02','03','04','05','06','07','08','09','10','11','12']
		ran_l = self.fecha_cese.split('-')
		ran_l2 = self.fecha_ingreso.split('-')
		print self.fecha_cese
		print self.fecha_ingreso
		desde =0
		print ran_l2
		print int(ran_l2[0]),int(self.devolucion_id.period_id.code.split('/')[1])
		if int(ran_l2[0])<int(self.devolucion_id.period_id.code.split('/')[1]):
			desde='01'
		else:
			desde=meses[int(ran_l2[1])-1]
		print desde,
		rang_meses = meses[meses.index(desde):meses.index(ran_l[1])+1]
		return rang_meses
