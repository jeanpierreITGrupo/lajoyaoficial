# -*- encoding: utf-8 -*-
from openerp     import models, fields, api, exceptions , _
from openerp.osv import osv
import base64

import decimal
import datetime

class listado_propuestas_wizard(models.TransientModel):
	_name = 'listado.propuestas.wizard'

	start_date = fields.Date(u'Fecha inicio', required=True)
	end_date   = fields.Date(u'Fecha fin', required=True)

	@api.model
	def default_get(self, fields):
		res = super(listado_propuestas_wizard,self).default_get(fields)
		res['start_date'] = datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d")
		res['end_date']   = datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d")
		return res

	@api.multi
	def do_rebuild(self):
		self.env.cr.execute("""

			CREATE OR REPLACE view listado_propuestas as (
				SELECT row_number() OVER () AS id,* 
					FROM (
					SELECT
					name, 
					fecha_rec, 
					state, 
					origen, 
					ruc_proveedor, 
					rs_proveedor, 
					material, 
					sacos, 
					tmh, 
					h2o, 
					p_recup, 
					ley_oz_oro, 
					MAX(ley_oz_au_comer) AS ley_oz_au_comer, 
					ley_oz_plata, 
					MAX(ley_oz_ag_comer) AS ley_oz_ag_comer, 
					soda, 
					cianuro, 
					consumo_q_valorado, 
					fecha_retiro, 
					fletero, 
					nro_placa, 
					guia_t, 
					guia_r, 
					cod_comp, 
					cod_conces, 
					nom_conces
					FROM
						(SELECT
						pl.lot || '-' || pl.name AS name,
						pl.in_date AS fecha_rec,
						pl.state AS state,
						tz.name AS origen,
						rp.type_number AS ruc_proveedor,
						rp.name AS rs_proveedor,
						pp.name_template AS material,
						pl.qty AS sacos,
						pl.tmh AS tmh,
						pl.h2o AS h2o,
						pl.percentage_recovery AS p_recup,
						pl.ley_oz_au AS ley_oz_oro,
						CASE WHEN pll.mineral = 'oro' THEN pll.ley_oz ELSE 0.00 END AS ley_oz_au_comer,
						pl.ley_oz_ag AS ley_oz_plata,
						CASE WHEN pll.mineral = 'plata' THEN pll.ley_oz ELSE 0.00 END AS ley_oz_ag_comer,
						pl.soda AS soda,
						pl.cianuro AS cianuro,
						pl.value_consumed AS consumo_q_valorado,
						pl.fecha_retiro AS fecha_retiro,
						pl.fletero AS fletero,
						pl.nro_placa AS nro_placa,
						pl.guia_transp AS guia_t,
						pl.guia_remitente AS guia_r,
						pl.cod_compro AS cod_comp,
						pl.cod_conces AS cod_conces,
						pl.nombre_conces AS nom_conces
						FROM purchase_liquidation pl
						LEFT JOIN table_zone tz ON pl.source_zone = tz.id
						LEFT JOIN res_partner rp ON pl.supplier_id = rp.id
						LEFT JOIN product_product pp ON pl.material = pp.id
						LEFT JOIN purchase_liquidation_line pll ON pll.parent = pl.id
						WHERE pl.in_date BETWEEN '"""+str(self.start_date)+"""'::date AND '"""+str(self.end_date)+"""'::date AND pll.line_type = 'Propuesta') TB
					GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,14,16,17,18,19,20,21,22,23,24,25,26
				)T
			)
			 
		""")

		return {
			'type'          : 'ir.actions.act_window',
			'res_model'     : 'listado.propuestas',
			'view_type'     : 'form',
			'view_mode'     : 'tree',
			'target'		: 'current',
		}

class listado_propuestas(models.Model):
	_name = 'listado.propuestas'
	_auto = False
	
	name               = fields.Char(u'Lote')
	fecha_rec          = fields.Date(u'Fecha de Recepción')
	state              = fields.Selection([('draft','Dato'),('proposal','Propuesta'),('negotiated','Negociado'),('done','Renegociado'),('to_pay','Solic. Presupuesto')], "Estado")
	origen             = fields.Char(u'Origen')
	ruc_proveedor      = fields.Char(u'RUC Proveedor')
	rs_proveedor       = fields.Char(u'Proveedor Mineral')
	material           = fields.Char(u'Material')
	sacos              = fields.Integer(u'N° Sacos')
	tmh                = fields.Float(u'TMH')
	h2o                = fields.Float(u'% H2O')
	p_recup            = fields.Float(u'% RCPLAB')
	ley_oz_oro         = fields.Float(u'Ley Au Oz/tc')
	ley_oz_au_comer    = fields.Float(u'Ley Au (Comercial)')
	ley_oz_plata       = fields.Float(u'Ley Ag Oz/tc')
	ley_oz_ag_comer    = fields.Float(u'Ley Ag (Comercial)')
	soda               = fields.Float(u'NaOH(Kg/Tn)')
	cianuro            = fields.Float(u'NaCN(Kg/Tn)')
	consumo_q_valorado = fields.Float(u'Penalidad ($/tms)')
	fecha_retiro       = fields.Date(u'Fecha Retiro')
	fletero            = fields.Char(u'Nombre del Fletero')
	nro_placa          = fields.Char(u'Nro. Placa')
	guia_t             = fields.Char(u'Guía Transport')
	guia_r             = fields.Char(u'Guía Remitente')
	cod_comp           = fields.Char(u'Código Compromiso')
	cod_conces         = fields.Char(u'Código Concesión')
	nom_conces         = fields.Char(u'Nombre Concesión')