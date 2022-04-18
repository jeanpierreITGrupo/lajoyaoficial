# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class pdb_currency_rate(models.Model):
	_name = 'pdb.currency.rate'
	_auto = False
	
	periodo = fields.Char('Periodo', size=50)
	tipo = fields.Char('Tipo', size=50)
	fecha = fields.Date('Fecha')
	compra = fields.Float('Compra', digits=(12,2))
	venta = fields.Float('Venta', digits=(12,2))
	
	
	def init(self,cr):
		cr.execute("""
			DROP FUNCTION IF EXISTS get_currency_rates(integer) CASCADE;
			CREATE OR REPLACE FUNCTION get_currency_rates(IN periodo_ini integer)
			  RETURNS TABLE(
				id bigint, 
				periodo character varying, 
				tipo character varying, 
				fecha character varying, 
				compra numeric, 
				venta numeric
				) 
			AS
			$BODY$
			BEGIN
			RETURN QUERY 

			SELECT row_number() OVER () AS id,* from (

			SELECT 
					''::varchar as name,
					''::varchar as type,
					to_char(rcr.date_sunat  ,'dd/mm/yyyy')::varchar as date_invoice,
					rcr.type_sale,
					rcr.type_purchase
				FROM
					res_currency AS rc  JOIN
					res_currency_rate AS rcr ON rcr.currency_id = rc.id
					inner join (
						select distinct fechaemision from (
select fechaemision from get_compra_1_1_1(false,$1,$1)
union all
select fechaemision from get_venta_1_1_1(false,$1,$1)) X
)  OP on rcr.date_sunat = OP.fechaemision
					
				WHERE
					rc.name = 'USD' order by rcr.date_sunat ) T;

	END;
	$BODY$
	  LANGUAGE plpgsql VOLATILE
	  COST 100
	  ROWS 1000;

  """)
	