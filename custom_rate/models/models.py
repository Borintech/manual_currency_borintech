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

                    company_currency = line.account_id.company_id.currency_id
                    balance = line.amount_currency
                    debe = 0
                    haber = 0
                    if line.currency_id and company_currency and line.currency_id != company_currency:
                        if line.move_id.purchase_currency_rate > 0:

                            debe = balance * rec.currency_rate

                            if line.tax_ids.amount != 0:
                                debe = debe * line.tax_ids.amount / 100

                            debe = line.currency_id._convert(debe, company_currency, line.account_id.company_id,
                                                                line.move_id.date or fields.Date.today(), True,
                                                                line.move_id.purchase_currency_rate)
                        else:

                            haber = balance * rec.currency_rate

                            if line.tax_ids.amount != 0:
                                haber = haber * line.tax_ids.amount / 100

                            haber = line.currency_id._convert(debe, company_currency, line.account_id.company_id,
                                                                line.move_id.date or fields.Date.today(), True,
                                                                line.move_id.purchase_currency_rate)

                        line.debit = debe > 0 and debe or 0.0
                        line.credit = haber < 0 and -haber or 0.0

                    # if line.amount_currency < 0:
                    #     importe_moneda = line.amount_currency * -1
                    #     haber = importe_moneda * rec.currency_rate
                    #     if line.tax_ids.amount != 0:
                    #         haber = haber * line.tax_ids.amount / 100
                    #
                    #     line.credit = haber
                    #
                    # else:
                    #     importe_moneda = line.amount_currency
                    #     debe = importe_moneda * rec.currency_rate
                    #     if line.tax_ids.amount != 0:
                    #         debe = debe * line.tax_ids.amount / 100
                    #
                    #     line.debit = debe
