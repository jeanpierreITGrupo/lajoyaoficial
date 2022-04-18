# -*- encoding: utf-8 -*-
{
    'name': 'Liquidation Result in Purchase Order IT',
    'category': 'Purchase',
    'author': 'ITGrupo',
    'depends': ['purchase', 'purchase_liquidation_it'],
    'version': '1.0',
    'description':"""
        Módulo que agrega campo para seleccionar liquidación y muestra el campo de costo total en la orden de compra.
    """,
    'auto_install': False,
    'demo': [],
    'data': ['purchase_order.xml',
            ],
    'installable': True
}