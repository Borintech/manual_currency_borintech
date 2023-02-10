from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('currency_id')
    def _get_currency_rate(self):
        for record in self:
            rate = 1
            if record.currency_id.rate > 0:
                if record.currency_id.name != 'ARS':
                    rate = 1 / record.currency_id.rate
                else:
                    rate = 1
                record.currency_rate = rate

    def _check_balanced(self):
        for rec in self:
            if rec.type == 'in_invoice' or rec.type == 'in_refund':
                if rec.es_manual_rate == True:
                    return True
        res = super(AccountMove, self)._check_balanced()
        return res

    currency_rate = fields.Float(string='Tasa de cambio', readonly=False, compute='_get_currency_rate', store=True)
    es_manual_rate = fields.Boolean(string='Usar TC manual')



    def auto_update(self):
        for rec in self:
            if rec.es_manual_rate:

                for line in rec.line_ids:

                    precio_venta = line.credit
                    precio_deudores = line.debit

                    if line.name == rec.invoice_line_ids.name:
                        precio_venta = 0
                        precio_venta = line.amount_currency * rec.currency_rate
                        precio_venta = precio_venta * -1
                        if line.tax_ids.amount != 0:
                            precio_venta = precio_venta * line.tax_ids.amount / 100

                        #TODO AGREGAR PRECIO A LINEA CREDIT


                    if line.name == False:
                        precio_deudores = 0
                        precio_deudores = line.amount_currency * rec.currency_rate

                        if line.tax_ids.amount != 0:
                            precio_deudores = precio_deudores * line.tax_ids.amount / 100


                    line.with_context(check_move_validity=False).write({
                        'credit': precio_venta,
                        'debit': precio_deudores
                    })



                    #res = super(AccountMove, self.with_context(check_move_validity=False)).write(vals)

                    #WRITE
                    # rec.line_ids.with_context(check_move_validity=False).write({
                    #     'credit': precio_venta,
                    #     'debit': precio_deudores
                    # })


                    #UPDATE
                    # rec.line_ids.update({
                    #     'credit': precio_venta,
                    #     'debit': precio_deudores
                    # })




                    # if line.amount_currency < 0:
                    #     importe_moneda = line.amount_currency * -1
                    #     haber = importe_moneda * rec.currency_rate
                    #     if line.tax_ids.amount != 0:
                    #         haber = haber * line.tax_ids.amount / 100
                    #
                    # else:
                    #     debe += haber
                    #     importe_moneda = line.amount_currency
                    #     debe = importe_moneda * rec.currency_rate
                    #     if line.tax_ids.amount != 0:
                    #         debe = debe * line.tax_ids.amount / 100


                    # rec.line_ids.write({
                    #     'credit': haber,
                    #     'debit': debe
                    # })

                    # rec.line_ids.update({
                    #     'credit': haber,
                    #     'debit': debe
                    # })