# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv


class res_currency_wizard(models.Model):
	_name="res.currency.wizard"

	fecha_ini = fields.Date("Fecha Inicio")
	fecha_fin = fields.Date("Fecha Final")

	@api.onchange('fecha_ini')
	def _onchange_type_account(self):
		if self.fecha_ini:
			self.fecha_fin = self.fecha_ini

	@api.multi
	def do_rebuild(self):

		import urllib, urllib2
		import datetime
		import pprint
		fecha_inicial = datetime.datetime.strptime(self.fecha_ini, '%Y-%m-%d')
		fecha_final = datetime.datetime.strptime(self.fecha_fin, '%Y-%m-%d')

		mesini = fecha_inicial.month -1
		aoini = fecha_inicial.year
		if mesini == 0:
			mesini = 12
			aoini += -1
		mes_ini = datetime.datetime(year=aoini,month = mesini,day=1)
		mes_fin = datetime.datetime(year=fecha_final.year,month = fecha_final.month,day=1)
		rango_mes = []

		while mes_ini!=mes_fin:
			rango_mes.append( [str(mes_ini.month),str(mes_ini.year)] )
			mes_ini = datetime.datetime(year=mes_ini.year +((mes_ini.month+1)/12),month = (mes_ini.month+1)%12,day=1)

		rango_mes.append([str(mes_ini.month),str(mes_ini.year)])
			
		saldos = []
		dato_sal = [0,0,0]
		cont = 0
		diaanterior = None
		for meses in rango_mes:
			mes = meses[0]
			anho = meses[1]
			datos = urllib.urlencode({'mes':mes, 'anho':anho})
			url = "http://www.sunat.gob.pe/cl-at-ittipcam/tcS01Alias?"
			try:
				res = urllib2.urlopen(url + datos)
			except:
				raise osv.except_osv('Error!', 'No se puede conectar a la página de Sunat!')
			from BeautifulSoup import BeautifulSoup
			soup = BeautifulSoup(res.read())
			table = soup.findAll('table')[1]

			for i in table.findAll("tr")[1:]:
				for j in i.findAll("td"):
					dato_sal[cont]=j.text
					if cont == 2:
						dia_actual = datetime.datetime(year=int(anho),month=int(mes),day=int(dato_sal[0]))
						while (diaanterior and diaanterior + datetime.timedelta(days=1) != dia_actual):
							diaanterior = diaanterior + datetime.timedelta(days=1)
							saldos.append( [diaanterior,diaanterior.day,saldos[-1][2],saldos[-1][3] ] )
							
						saldos.append([dia_actual,dato_sal[0],dato_sal[1],dato_sal[2]])
						diaanterior = dia_actual
					cont = (cont+1)%3

		dic_sal = {}
		for i in saldos:
			dic_sal[i[0]] = [i[2],i[3]]

		final = []
		while fecha_inicial<=fecha_final:
			if fecha_inicial in dic_sal:
				final.append([fecha_inicial,dic_sal[fecha_inicial][0],dic_sal[fecha_inicial][1] ])
			else:
				dic_sal[fecha_inicial] = dic_sal[fecha_inicial - datetime.timedelta(days=1)]
				final.append([fecha_inicial,dic_sal[fecha_inicial][0],dic_sal[fecha_inicial][1] ])
			fecha_inicial = fecha_inicial + datetime.timedelta(days= 1)
		

		currency_extra = self.env['main.parameter'].search([])[0].currency_id
		for fn in final:
			tmp_fn = self.env['res.currency.rate'].search([('currency_id','=',currency_extra.id),('date_sunat','=',str(fn[0]))])
			if len(tmp_fn)>0:
				tmp_fn.type_purchase =  float(fn[1])
				tmp_fn.type_sale = float(fn[2])
				tmp_fn.rate = 1 /float(fn[2])
			else:
				data = {
				'date_sunat':fn[0],
				'name':fn[0],
				'type_purchase' :  float(fn[1]),
				'type_sale' : float(fn[2]),
				'rate' : 1 /float(fn[2]),
				}
				new_rate= self.env['res.currency.rate'].create(data)
				currency_extra.write({'rate_ids':[(4,new_rate.id)]})

class res_currency(models.Model):
	_inherit = 'res.currency'

	@api.one
	def get_flag_currency_param(self):
		t = self.env['main.parameter'].search([])[0].currency_id.id
		if t == self.id:
			self.flag_currency_param = True
		else:
			self.flag_currency_param = False




	flag_currency_param = fields.Boolean("Currency Flag", compute="get_flag_currency_param")

	@api.multi
	def update_rate_price(self):
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'res.currency.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'views': [(False, 'form')],
			'target':'new',
		}
