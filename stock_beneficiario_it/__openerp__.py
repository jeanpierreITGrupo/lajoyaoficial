# -*- coding: utf-8 -*-
{
    'name': "BENEFICIARIOS IT",

    'description': """
        Agrega campos de beneficiario en albaranes y facturas de proveedor
    """,

    'author': "ITGrupo",
    'category': 'warehouse',
    'version': '0.1',
    'depends': ['stock_picking_motive','account_invoice_reference_it','hr','stock_picking_audit_it'],
    'data': ['stock_picking_view.xml',
             'account_invoice_view.xml'],
}