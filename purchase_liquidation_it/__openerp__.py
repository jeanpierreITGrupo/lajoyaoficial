# -*- encoding: utf-8 -*-
{
    'name': 'Purchase Liquidation IT',
    'category': 'Purchase',
    'author': 'ITGrupo',
    'depends': ['web','purchase_parameters_it'],
    'version': '1.0',
    'description':"""
        Módulo que crea menú Liquidación de Compra que permite ingresar datos para la negociación a las distintas áreas 
        involucradas. Luego de ingresados los datos se crean 3 líneas para el historial de la negociación.
    """,
    'auto_install': False,
    'demo': [],
    'data': ['security/liquidation_groups.xml',
            'wizard/purchase_negotiation.xml',
            'purchase_liquidation_data.xml',
            'purchase_liquidation.xml',
            ],
    'installable': True
}