# -*- encoding: utf-8 -*-
{
    'name': 'Purchase Costing IT',
    'category': 'Purchase',
    'author': 'ITGrupo',
    'depends': ['account','purchase','stock', 'parameters_expedient','purchase_parameters_it','purchase_liquidation_it'],
    'version': '1.0',
    'description':"""
        Módulo que permite hacer el costeo de compra de material.
    """,
    'auto_install': False,
    'demo': [],
    'data': ['purchase_costing_data.xml',
            'expedient_trace.xml',
            'purchase_costing.xml',
            'expenses_without_record.xml'],
    'installable': True
}