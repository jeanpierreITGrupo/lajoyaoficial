# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_sheet_work_f2_visual(models.Model):
	_name = 'account.sheet.work.f2.visual'
	_auto = False


	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)

	debeinicial = fields.Float('SI Debe', digits=(12,2))
	haberinicial = fields.Float('SI Haber', digits=(12,2))
	
	debe = fields.Float('MP Debe', digits=(12,2))
	haber = fields.Float('MP Haber', digits=(12,2))

	debesa = fields.Float('SA Debe', digits=(12,2))
	habersa = fields.Float('SA Haber', digits=(12,2))

	saldodeudor = fields.Float('Deudo', digits=(12,2))
	saldoacredor = fields.Float('Acreedor', digits=(12,2))
	activo = fields.Float('Activo', digits=(12,2))
	pasivo = fields.Float('Pasivo', digits=(12,2))
	perdidasnat = fields.Float('Perdidas NAT', digits=(12,2))
	ganancianat = fields.Float('Ganacias NAT', digits=(12,2))
	perdidasfun = fields.Float('Perdidas FUN', digits=(12,2))
	gananciafun = fields.Float('Ganancia FUN', digits=(12,2))

	def init(self,cr):
		cr.execute("""

DROP FUNCTION IF EXISTS get_reporte_hoja_balance(boolean, integer, integer);

CREATE OR REPLACE FUNCTION get_reporte_hoja_balance(IN has_currency boolean, IN periodo_ini integer, IN periodo_fin integer)
  RETURNS TABLE(id bigint, cuenta character varying, descripcion character varying, debe numeric, haber numeric, saldodeudor numeric, saldoacredor numeric, activo numeric, pasivo numeric, perdidasnat numeric, ganancianat numeric, perdidasfun numeric, gananciafun numeric, cuentaf character varying, totaldebe numeric, totalhaber numeric, finaldeudor numeric, finalacreedor numeric) AS
$BODY$
BEGIN

IF $3 is Null THEN
		$3 := $2;
END IF;

RETURN QUERY 
select X.id,X.cuenta,X.descripcion,X.debe,X.haber,X.saldodeudor,X.saldoacredor,
CASE WHEN ((X.activo >0 or X.pasivo >0) or (X.ver_pas=1) ) and X.finaldeudor>0 THEN X.finaldeudor ELSE 0 end activo,
CASE WHEN ((X.pasivo >0 or X.activo >0) or (X.ver_pas=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end pasivo,
CASE WHEN ((X.perdidasnat >0 or X.ganancianat >0) or (X.ver_nat=1) ) and X.finaldeudor>0 THEN X.finaldeudor  ELSE 0 end perdidasnat,
CASE WHEN ((X.ganancianat >0 or X.perdidasnat >0) or (X.ver_nat=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end ganancianat,
CASE WHEN ((X.perdidasfun >0 or X.gananciafun >0) or (X.ver_fun=1) ) and X.finaldeudor >0 THEN X.finaldeudor ELSE 0 end perdidasfun,
CASE WHEN ((X.gananciafun >0 or X.perdidasfun >0) or (X.ver_fun=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end gananciafun,
X.cuentaf,X.totaldebe,X.totalhaber,X.finaldeudor,X.finalacreedor

 from (select row_number() OVER () AS id,RES.* from 
  (select  CASE WHEN M.cuenta IS NOT NULL THEN M.cuenta ELSE aa_f.code END as cuenta, CASE WHEN M.descripcion IS NOT NULL THEN M.descripcion ELSE aa_f.name END as descripcion, M.debe, M.haber, M.saldodeudor, M.saldoacredor, M.activo, M.pasivo, M.perdidasnat, M.ganancianat, M.perdidasfun, M.gananciafun,T.cuentaF, T.totaldebe,T.totalhaber ,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) >0 THEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) ELSE 0 END as finaldeudor,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) <0 THEN -1 * (coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0)) ELSE 0 END as finalacreedor,
T.ver_pas, T.ver_nat, T.ver_fun
from get_hoja_trabajo_detalle_balance($1,(substring($2::varchar,0,5)||'01')::integer,$3) AS M 
FULL JOIN (select O1.cuenta as cuentaF,
--sum(O1.saldodeudor) as totaldebe,
--sum(O1.saldoacredor) as totalhaber   from get_hoja_trabajo_detalle_balance($1,(substring($2::varchar,0,5)||'00')::integer,(substring($2::varchar,0,5)||'00')::integer ) as O1
sum(O1.debe) as totaldebe,
sum(O1.haber) as totalhaber,
CASE WHEN sum(O1.activo)> 0 or sum(O1.pasivo) >0 THEN 1 ELSE 0 END as ver_pas,
CASE WHEN sum(O1.perdidasnat)> 0 or sum(O1.ganancianat) >0 THEN 1 ELSE 0 END as ver_nat,
CASE WHEN sum(O1.perdidasfun)> 0 or sum(O1.gananciafun) >0 THEN 1 ELSE 0 END as ver_fun
   from get_hoja_trabajo_detalle_balance($1,(substring($2::varchar,0,5)||'00')::integer,(substring($2::varchar,0,5)||'00')::integer ) as O1
group by O1.cuenta) AS T on T.cuentaF = M.cuenta
left join account_account aa_f on aa_f.code = T.cuentaF order by cuenta) RES ) AS X;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;





  DROP FUNCTION IF EXISTS get_reporte_hoja_registro(boolean, integer, integer);

CREATE OR REPLACE FUNCTION get_reporte_hoja_registro(IN has_currency boolean, IN periodo_ini integer, IN periodo_fin integer)
  RETURNS TABLE(id bigint, cuenta character varying, descripcion character varying, debe numeric, haber numeric, saldodeudor numeric, saldoacredor numeric, activo numeric, pasivo numeric, perdidasnat numeric, ganancianat numeric, perdidasfun numeric, gananciafun numeric, cuentaf character varying, totaldebe numeric, totalhaber numeric, finaldeudor numeric, finalacreedor numeric) AS
$BODY$
BEGIN

IF $3 is Null THEN
		$3 := $2;
END IF;

RETURN QUERY 
select X.id,X.cuenta,X.descripcion,X.debe,X.haber,X.saldodeudor,X.saldoacredor,
CASE WHEN ((X.activo >0 or X.pasivo >0) or (X.ver_pas=1) ) and X.finaldeudor>0 THEN X.finaldeudor ELSE 0 end activo,
CASE WHEN ((X.pasivo >0 or X.activo >0) or (X.ver_pas=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end pasivo,
CASE WHEN ((X.perdidasnat >0 or X.ganancianat >0) or (X.ver_nat=1) ) and X.finaldeudor>0 THEN X.finaldeudor  ELSE 0 end perdidasnat,
CASE WHEN ((X.ganancianat >0 or X.perdidasnat >0) or (X.ver_nat=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end ganancianat,
CASE WHEN ((X.perdidasfun >0 or X.gananciafun >0) or (X.ver_fun=1) ) and X.finaldeudor >0 THEN X.finaldeudor ELSE 0 end perdidasfun,
CASE WHEN ((X.gananciafun >0 or X.perdidasfun >0) or (X.ver_fun=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end gananciafun,
X.cuentaf,X.totaldebe,X.totalhaber,X.finaldeudor,X.finalacreedor

 from (select row_number() OVER () AS id,RES.* from 
  (select  CASE WHEN M.cuenta IS NOT NULL THEN M.cuenta ELSE aa_f.code END as cuenta, CASE WHEN M.descripcion IS NOT NULL THEN M.descripcion ELSE aa_f.name END as descripcion, M.debe, M.haber, M.saldodeudor, M.saldoacredor, M.activo, M.pasivo, M.perdidasnat, M.ganancianat, M.perdidasfun, M.gananciafun,T.cuentaF, T.totaldebe,T.totalhaber ,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) >0 THEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) ELSE 0 END as finaldeudor,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) <0 THEN -1 * (coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0)) ELSE 0 END as finalacreedor,
T.ver_pas, T.ver_nat, T.ver_fun
from get_hoja_trabajo_detalle_registro($1,(substring($2::varchar,0,5)||'01')::integer,$3) AS M 
FULL JOIN (select O1.cuenta as cuentaF,
--sum(O1.saldodeudor) as totaldebe,
--sum(O1.saldoacredor) as totalhaber   from get_hoja_trabajo_detalle_registro($1,(substring($2::varchar,0,5)||'00')::integer,(substring($2::varchar,0,5)||'00')::integer ) as O1
sum(O1.debe) as totaldebe,
sum(O1.haber) as totalhaber,
CASE WHEN sum(O1.activo)> 0 or sum(O1.pasivo) >0 THEN 1 ELSE 0 END as ver_pas,
CASE WHEN sum(O1.perdidasnat)> 0 or sum(O1.ganancianat) >0 THEN 1 ELSE 0 END as ver_nat,
CASE WHEN sum(O1.perdidasfun)> 0 or sum(O1.gananciafun) >0 THEN 1 ELSE 0 END as ver_fun

   from get_hoja_trabajo_detalle_registro($1,(substring($2::varchar,0,5)||'00')::integer,(substring($2::varchar,0,5)||'00')::integer ) as O1
group by O1.cuenta) AS T on T.cuentaF = M.cuenta 
left join account_account aa_f on aa_f.code = T.cuentaF order by cuenta) RES) AS X;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

			""")