
CREATE OR REPLACE FUNCTION fecha_num(date)
  RETURNS integer AS
$BODY$
    SELECT to_char($1, 'YYYYMMDD')::integer;
$BODY$
  LANGUAGE sql VOLATILE
  COST 100;
ALTER FUNCTION fecha_num(date)
  OWNER TO postgres;




CREATE OR REPLACE FUNCTION getnumber("number" character varying)
  RETURNS character varying AS
$BODY$
DECLARE
number1 ALIAS FOR $1;
res varchar;
BEGIN
   select substring(number1,position('-' in number1)+1) into res;
   return res;  
END;$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION getnumber(character varying)
  OWNER TO postgres;



CREATE OR REPLACE FUNCTION getperiod(move_id integer, date_picking date, special boolean)
  RETURNS character varying AS
$BODY$
DECLARE
move_id1 ALIAS FOR $1;
date_picking1 ALIAS FOR $2;
res varchar;
isspecial alias for special;
BEGIN
    IF move_id1 !=0 THEN
	select account_period.name into res from account_move 
	inner join account_period on account_move.period_id = account_period.id
	where account_move.id=move_id1;
    ELSE 
	select account_period.name into res from account_period
	where date_start<=date_picking1 and date_stop>=date_picking1 and account_period.special=isspecial;
   END IF;
   return res;  
END;$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION getperiod(integer, date, boolean)
  OWNER TO postgres;



CREATE OR REPLACE FUNCTION getperiod(date_picking timestamp without time zone, special boolean)
  RETURNS character varying AS
$BODY$
DECLARE
date_picking1 ALIAS FOR $1;
res varchar;
isspecial alias for $2;
BEGIN
	select account_period.name into res from account_period
	where date_start<=date_picking1 and date_stop>=date_picking1 and account_period.special=isspecial;
   return res;  
END;$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION getperiod(timestamp without time zone, boolean)
  OWNER TO postgres;




CREATE OR REPLACE FUNCTION getperiod(move_id integer, date_picking timestamp without time zone, special boolean)
  RETURNS character varying AS
$BODY$
DECLARE
move_id1 ALIAS FOR $1;
date_picking1 ALIAS FOR $2;
res varchar;
isspecial alias for special;
BEGIN
    IF move_id1 !=0 THEN
	select account_period.name into res from account_move 
	inner join account_period on account_move.period_id = account_period.id
	where account_move.id=move_id1;
    ELSE 
	select account_period.name into res from account_period
	where date_start<=date_picking1 and date_stop>=date_picking1 and account_period.special=isspecial;
   END IF;
   return res;  
END;$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION getperiod(integer, timestamp without time zone, boolean)
  OWNER TO postgres;



CREATE OR REPLACE FUNCTION getserial("number" character varying)
  RETURNS character varying AS
$BODY$
DECLARE
number1 ALIAS FOR $1;
res varchar;
BEGIN
   select substring(number1,0,position('-' in number1)) into res;
   return res;  
END;$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION getserial(character varying)
  OWNER TO postgres;


CREATE OR REPLACE FUNCTION normal_rand(integer, double precision, double precision)
  RETURNS SETOF double precision AS
'$libdir/tablefunc', 'normal_rand'
  LANGUAGE c VOLATILE STRICT
  COST 1
  ROWS 1000;
ALTER FUNCTION normal_rand(integer, double precision, double precision)
  OWNER TO openpg;



CREATE OR REPLACE FUNCTION periodo_num(character varying)
  RETURNS integer AS
$BODY$
    SELECT CASE WHEN substring($1,1,19) = 'Periodo de apertura' THEN (substring($1,21,4) || '00' )::integer ELSE
    (substring( $1,4,4) || substring($1 , 1,2)  )::integer END ;
$BODY$
  LANGUAGE sql VOLATILE
  COST 100;
ALTER FUNCTION periodo_num(character varying)
  OWNER TO postgres;


CREATE OR REPLACE FUNCTION periodo_string(numero integer)
  RETURNS character varying AS
$BODY$
		SELECT CASE WHEN substring(numero::varchar,5,2) = '00' THEN 'Periodo de apertura ' || substring(numero::varchar,1,4) ELSE
		(substring(numero::varchar,5,2) || '/' ||substring(numero::varchar,1,4) )::varchar END;
$BODY$
  LANGUAGE sql VOLATILE
  COST 100;
ALTER FUNCTION periodo_string(integer)
  OWNER TO openpg;











CREATE OR REPLACE VIEW vst_kardex_debitcredit_note AS 
 SELECT stock_location.complete_name, product_category.name AS categoria, 
    product_product.name_template, account_move.date, 
    account_period.name AS getperiod, ''::character varying AS ctanalitica, 
    getserial(account_invoice.supplier_invoice_number) AS serial, 
    getnumber(account_invoice.supplier_invoice_number)::character varying(10) AS getnumber, 
    ''::character varying AS operation_type, res_partner.name, 0 AS ingreso, 
    0 AS salida, account_move_line.debit, account_move_line.credit, 
    'null'::character varying AS type, 
        CASE
            WHEN account_move_line.debit > 0::numeric THEN 'ingreso'::text
            ELSE 'salida'::text
        END AS esingreso, 
    account_move_line.product_id, stock_location.id AS location_id, 
    lpad(account_invoice.type_document_id::text, 2, '0'::text) AS doc_type_ope
   FROM account_invoice_line
   JOIN account_invoice ON account_invoice_line.invoice_id = account_invoice.id
   JOIN account_move ON account_invoice.move_id = account_move.id
   JOIN account_move_line ON account_move.id = account_move_line.move_id
   JOIN res_partner ON account_invoice.partner_id = res_partner.id
   JOIN product_product ON account_move_line.product_id = product_product.id
   JOIN product_template ON product_product.product_tmpl_id = product_template.id
   JOIN product_category ON product_template.categ_id = product_category.id
   JOIN stock_location ON account_invoice_line.location_id = stock_location.id
   JOIN account_period ON account_move.period_id = account_period.id
   JOIN account_journal ON account_move_line.journal_id = account_journal.id
  WHERE account_invoice_line.location_id IS NOT NULL;

ALTER TABLE vst_kardex_debitcredit_note
  OWNER TO postgres;




CREATE OR REPLACE VIEW vst_kardex_fisical AS 
         SELECT DISTINCT sl1.complete_name AS almacen, 
            product_category.name AS categoria, product_product.name_template, 
                CASE
                    WHEN stock_picking.invoice_id IS NOT NULL THEN account_invoice.date_invoice
                    ELSE stock_picking.date::date
                END AS fecha, 
                CASE
                    WHEN stock_move.invoice_id IS NOT NULL THEN account_period.name
                    ELSE getperiod(stock_picking.date::date::timestamp without time zone, true)
                END AS periodo, 
            account_analytic_account.code AS ctanalitica, 
            getserial(account_invoice.supplier_invoice_number) AS serial, 
                CASE
                    WHEN stock_picking.invoice_id IS NOT NULL THEN getnumber(account_invoice.supplier_invoice_number)::character varying(10)
                    ELSE stock_picking.name
                END AS nro, 
            lpad(stock_picking.motivo_guia::text, 2, '0'::text)::character varying AS operation_type, 
            res_partner.name, 
                CASE
                    WHEN sl1.usage::text = 'internal'::text THEN 
                    CASE
                        WHEN stock_move.product_uom = product_template.uom_id THEN stock_move.product_qty
                        ELSE round((stock_move.product_qty::double precision / product_uom.factor::double precision * uomt.factor::double precision)::numeric, length(((abs(uomt.rounding) - floor(abs(uomt.rounding)))::character varying)::text) - 2)
                    END
                    ELSE 0::numeric
                END AS ingreso, 
            0 AS salida, 
                CASE
                    WHEN sl1.usage::text = 'internal'::text THEN 
                    CASE
                        WHEN stock_move.invoice_id IS NULL THEN stock_move.price_unit * round((stock_move.product_qty::double precision / product_uom.factor::double precision * uomt.factor::double precision)::numeric, length(((abs(uomt.rounding) - floor(abs(uomt.rounding)))::character varying)::text) - 2)::double precision
                        ELSE account_move_line.debit::double precision
                    END
                    ELSE 0::numeric::double precision
                END AS debit, 
            0 AS credit, 'in'::text AS type, 'ingreso'::text AS esingreso, 
            stock_move.product_id, sl1.id AS location_id, 
                CASE
                    WHEN stock_move.invoice_id IS NOT NULL THEN ((account_move_line.debit - account_move_line.credit) / account_move_line.quantity)::double precision
                    ELSE stock_move.price_unit
                END AS cadquiere, 
            lpad(account_invoice.type_document_id::text, 2, '0'::text) AS doc_type_ope, 
            stock_move.purchase_line_id, 0 AS sale_line_id
           FROM stock_move
      JOIN product_product ON stock_move.product_id = product_product.id
   JOIN product_template ON product_product.product_tmpl_id = product_template.id
   JOIN product_category ON product_template.categ_id = product_category.id
   JOIN stock_location sl1 ON stock_move.location_dest_id = sl1.id
   JOIN stock_picking ON stock_move.picking_id = stock_picking.id
   JOIN product_uom ON stock_move.product_uom = product_uom.id
   JOIN product_uom uomt ON product_template.uom_id = uomt.id
   LEFT JOIN account_invoice ON stock_move.invoice_id = account_invoice.id
   LEFT JOIN account_journal ON account_invoice.journal_id = account_journal.id
   LEFT JOIN account_analytic_account ON stock_move.analitic_id = account_analytic_account.id
   LEFT JOIN res_partner ON account_invoice.partner_id = res_partner.id
   LEFT JOIN account_period ON account_invoice.period_id = account_period.id
   LEFT JOIN account_move ON account_invoice.move_id = account_move.id
   LEFT JOIN account_move_line ON account_move_line.move_id = account_move.id AND account_move_line.quantity = stock_move.product_qty AND account_move_line.product_id = stock_move.product_id
  WHERE stock_move.state::text = 'done'::text AND sl1.usage::text = 'internal'::text AND product_template.type::text = 'product'::text
UNION ALL 
         SELECT DISTINCT sl1.complete_name AS almacen, 
            product_category.name AS categoria, product_product.name_template, 
                CASE
                    WHEN stock_picking.invoice_id IS NOT NULL THEN account_invoice.date_invoice
                    ELSE stock_picking.date::date
                END AS fecha, 
                CASE
                    WHEN stock_move.invoice_id IS NOT NULL THEN account_period.name
                    ELSE getperiod(stock_picking.date::date::timestamp without time zone, true)
                END AS periodo, 
            account_analytic_account.code AS ctanalitica, 
            getserial(account_invoice.supplier_invoice_number) AS serial, 
                CASE
                    WHEN stock_picking.invoice_id IS NOT NULL THEN getnumber(account_invoice.supplier_invoice_number)::character varying(10)
                    ELSE stock_picking.name
                END AS nro, 
            lpad(stock_picking.motivo_guia::text, 2, '0'::text)::character varying AS operation_type, 
            res_partner.name, 0 AS ingreso, 
                CASE
                    WHEN sl1.usage::text = 'internal'::text THEN 
                    CASE
                        WHEN stock_move.product_uom = product_template.uom_id THEN stock_move.product_qty
                        ELSE round((stock_move.product_qty::double precision / product_uom.factor::double precision * uomt.factor::double precision)::numeric, length(((abs(uomt.rounding) - floor(abs(uomt.rounding)))::character varying)::text) - 2)
                    END
                    ELSE 0::numeric
                END AS salida, 
            0 AS debit, 
                CASE
                    WHEN sl1.usage::text = 'internal'::text THEN 
                    CASE
                        WHEN stock_move.invoice_id IS NULL THEN stock_move.price_unit * round((stock_move.product_qty::double precision / product_uom.factor::double precision * uomt.factor::double precision)::numeric, length(((abs(uomt.rounding) - floor(abs(uomt.rounding)))::character varying)::text) - 2)::double precision
                        ELSE account_move_line.debit::double precision
                    END
                    ELSE 0::numeric::double precision
                END AS credit, 
            'out'::text AS type, 'salida'::text AS esingreso, 
            stock_move.product_id, sl1.id AS location_id, 0 AS cadquiere, 
            lpad(account_invoice.type_document_id::text, 2, '0'::text) AS doc_type_ope, 
            stock_move.purchase_line_id, 0 AS sale_line_id
           FROM stock_move
      JOIN product_product ON stock_move.product_id = product_product.id
   JOIN product_template ON product_product.product_tmpl_id = product_template.id
   JOIN product_category ON product_template.categ_id = product_category.id
   JOIN stock_location sl1 ON stock_move.location_id = sl1.id
   JOIN stock_picking ON stock_move.picking_id = stock_picking.id
   JOIN product_uom ON stock_move.product_uom = product_uom.id
   JOIN product_uom uomt ON product_template.uom_id = uomt.id
   LEFT JOIN account_invoice ON stock_move.invoice_id = account_invoice.id
   LEFT JOIN account_journal ON account_invoice.journal_id = account_journal.id
   LEFT JOIN account_analytic_account ON stock_move.analitic_id = account_analytic_account.id
   LEFT JOIN res_partner ON account_invoice.partner_id = res_partner.id
   LEFT JOIN account_period ON account_invoice.period_id = account_period.id
   LEFT JOIN account_move ON account_invoice.move_id = account_move.id
   LEFT JOIN account_move_line ON account_move_line.move_id = account_move.id AND account_move_line.quantity = stock_move.product_qty AND account_move_line.product_id = stock_move.product_id
  WHERE stock_move.state::text = 'done'::text AND sl1.usage::text = 'internal'::text AND product_template.type::text = 'product'::text;

ALTER TABLE vst_kardex_fisical
  OWNER TO postgres;



CREATE OR REPLACE VIEW vst_kardex_lading AS 
 SELECT stock_location.complete_name, product_category.name AS categoria, 
    product_product.name_template, account_expense_related.date, 
    getperiod(account_invoice.move_id, '2000-01-01'::date, false) AS getperiod, 
    ''::character varying AS ctanalitica, 
    getserial(account_invoice.number) AS serial, 
    getnumber(account_invoice.number)::character varying(10) AS getnumber, 
    ''::character varying AS operation_type, res_partner.name, 0 AS ingreso, 
    0 AS salida, account_expense_related_line.equivalence AS debit, 0 AS credit, 
    'null'::character varying AS type, 'ingreso'::text AS esingreso, 
    account_expense_related_line.product_id, stock_location.id AS location_id, 
    lpad(account_invoice.type_document_id::text, 2, '0'::text) AS doc_type_ope
   FROM account_expense_related_line
   JOIN account_expense_related ON account_expense_related_line.expense_related_id = account_expense_related.id
   JOIN stock_location ON account_expense_related_line.location_id = stock_location.id
   JOIN product_product ON account_expense_related_line.product_id = product_product.id
   JOIN product_template ON product_product.product_tmpl_id = product_template.id
   JOIN product_category ON product_template.categ_id = product_category.id
   JOIN account_invoice ON account_expense_related.invoice_id = account_invoice.id
   JOIN res_partner ON account_invoice.partner_id = res_partner.id
   JOIN account_journal ON account_invoice.journal_id = account_journal.id
  WHERE (account_invoice.state::text = ANY (ARRAY['paid'::character varying::text, 'open'::character varying::text])) AND stock_location.usage::text = 'internal'::text
  ORDER BY product_product.id, account_invoice.date_invoice;

ALTER TABLE vst_kardex_lading
  OWNER TO postgres;




CREATE OR REPLACE VIEW vst_kardex_sunat AS 
 SELECT t.almacen, t.categoria, t.name_template, t.fecha, t.periodo, 
    t.ctanalitica, t.serial, t.nro, t.operation_type, t.name, t.ingreso, 
    t.salida, 0::numeric AS saldof, t.debit::numeric AS debit, 
    t.credit::numeric AS credit, t.cadquiere::numeric AS cadquiere, 
    0::numeric AS saldov, 0::numeric AS cprom, 
    t.type::character varying AS type, t.esingreso, t.product_id, t.location_id, 
    t.doc_type_ope
   FROM (        (         SELECT vst_kardex_fisical.almacen, 
                            vst_kardex_fisical.categoria, 
                            vst_kardex_fisical.name_template, 
                            vst_kardex_fisical.fecha, 
                            vst_kardex_fisical.periodo, 
                            vst_kardex_fisical.ctanalitica, 
                            vst_kardex_fisical.serial, vst_kardex_fisical.nro, 
                            vst_kardex_fisical.operation_type, 
                            vst_kardex_fisical.name, vst_kardex_fisical.ingreso, 
                            vst_kardex_fisical.salida, vst_kardex_fisical.debit, 
                            vst_kardex_fisical.credit, vst_kardex_fisical.type, 
                            vst_kardex_fisical.esingreso, 
                            vst_kardex_fisical.product_id, 
                            vst_kardex_fisical.location_id, 
                            vst_kardex_fisical.cadquiere, 
                            vst_kardex_fisical.doc_type_ope::character varying AS doc_type_ope
                           FROM vst_kardex_fisical
                UNION ALL 
                         SELECT vst_kardex_debitcredit_note.complete_name, 
                            vst_kardex_debitcredit_note.categoria, 
                            vst_kardex_debitcredit_note.name_template, 
                            vst_kardex_debitcredit_note.date, 
                            vst_kardex_debitcredit_note.getperiod, 
                            vst_kardex_debitcredit_note.ctanalitica, 
                            vst_kardex_debitcredit_note.serial, 
                            vst_kardex_debitcredit_note.getnumber, 
                            vst_kardex_debitcredit_note.operation_type, 
                            vst_kardex_debitcredit_note.name, 
                            vst_kardex_debitcredit_note.ingreso, 
                            vst_kardex_debitcredit_note.salida, 
                            vst_kardex_debitcredit_note.debit, 
                            vst_kardex_debitcredit_note.credit, 
                            vst_kardex_debitcredit_note.type, 
                            vst_kardex_debitcredit_note.esingreso, 
                            vst_kardex_debitcredit_note.product_id, 
                            vst_kardex_debitcredit_note.location_id, 
                            0::numeric AS cadquiere, 
                            vst_kardex_debitcredit_note.doc_type_ope::character varying AS doc_type_ope
                           FROM vst_kardex_debitcredit_note)
        UNION ALL 
                 SELECT vst_kardex_lading.complete_name, 
                    vst_kardex_lading.categoria, 
                    vst_kardex_lading.name_template, vst_kardex_lading.date, 
                    vst_kardex_lading.getperiod, vst_kardex_lading.ctanalitica, 
                    vst_kardex_lading.serial, vst_kardex_lading.getnumber, 
                    vst_kardex_lading.operation_type, vst_kardex_lading.name, 
                    vst_kardex_lading.ingreso, vst_kardex_lading.salida, 
                    vst_kardex_lading.debit, vst_kardex_lading.credit, 
                    vst_kardex_lading.type, vst_kardex_lading.esingreso, 
                    vst_kardex_lading.product_id, vst_kardex_lading.location_id, 
                    0::numeric AS cadquiere, 
                    vst_kardex_lading.doc_type_ope::character varying AS doc_type_ope
                   FROM vst_kardex_lading) t
  ORDER BY t.almacen, t.name_template, t.periodo, t.fecha, t.esingreso;

ALTER TABLE vst_kardex_sunat
  OWNER TO postgres;




CREATE OR REPLACE FUNCTION get_kardex(IN date_ini integer, IN date_end integer, IN integer[], IN integer[])
  RETURNS TABLE(almacen character varying, categoria character varying, name_template character varying, fecha date, periodo character varying, ctanalitica character varying, serial character varying, nro character varying, operation_type character varying, name character varying, ingreso numeric, salida numeric, saldof numeric, debit numeric, credit numeric, cadquiere numeric, saldov numeric, cprom numeric, type character varying, esingreso text, product_id integer, location_id integer, doc_type_ope character varying) AS
$BODY$  
BEGIN
return query select * from vst_kardex_sunat where fecha_num(vst_kardex_sunat.fecha) between $1 and $2 and vst_kardex_sunat.product_id = ANY($3) and vst_kardex_sunat.location_id = ANY($4);
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION get_kardex(integer, integer, integer[], integer[])
  OWNER TO postgres;

