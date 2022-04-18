# -*- encoding: utf-8 -*-
{
    'name': 'Reporte Cuenta Corriente Comericla IT',
    'category': 'Purchase',
    'author': 'ITGrupo',
    'depends': ['web','purchase_parameters_it'],
    'version': '1.0',
    'description':"""
        crea reporte de cuentas corriente comercial IT
    """,
    'auto_install': False,
    'demo': [],
    'data': [        'purchase_liquidation.xml',
            ],
    'installable': True
}