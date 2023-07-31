# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, SUPERUSER_ID


class AccountMove(models.Model):
    _inherit = "account.move"

    currency_rate = fields.Float(string='Tasa de cambio manual', readonly=False, compute='_get_currency_rate',
                                 store=True)
    es_manual_rate = fields.Boolean(string='Usar TC manual')

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

    @api.onchange('es_manual_rate')
    def _get_currency_rate_false(self, es_manual_rate=None):
        for record in self:
            rate = 1
            if not es_manual_rate:
                if record.currency_id.rate > 0:
                    if record.currency_id.name != 'ARS':
                        rate = 1 / record.currency_id.rate
                    else:
                        rate = 1
                    record.currency_rate = rate
                    record.l10n_ar_currency_rate = record.currency_rate
                for line in record.line_ids:

                    precio_credit = line.credit
                    precio_debit = line.debit

                    if line.amount_currency < 0:
                        precio_credit = 0
                        precio_credit = line.amount_currency * record.currency_rate
                        precio_credit = precio_credit * -1

                    else:
                        precio_debit = 0
                        precio_debit = line.amount_currency * record.currency_rate

                    line.with_context(check_move_validity=False).write({
                        'credit': precio_credit,
                        'debit': precio_debit
                    })

    def _check_balanced(self):
        for rec in self:
            if rec.type == 'in_invoice' or rec.type == 'in_refund':
                if rec.es_manual_rate:
                    return True
        res = super(AccountMove, self)._check_balanced()
        return res

    @api.onchange('currency_rate')
    def auto_update(self):
        for rec in self:
            if rec.es_manual_rate:
                rec.l10n_ar_currency_rate = rec.currency_rate
                for line in rec.line_ids:
                    precio_credit = line.credit
                    precio_debit = line.debit

                    if line.amount_currency < 0:
                        precio_credit = 0
                        precio_credit = line.amount_currency * rec.currency_rate
                        precio_credit = precio_credit * -1
                        limitado = "{:.2f}".format(precio_credit)
                        print("precio credit", precio_credit)
                        print("precio credit", limitado)

                    else:
                        precio_debit = 0
                        precio_debit = line.amount_currency * rec.currency_rate
                        limitado_debit = "{:.2f}".format(precio_debit)
                        print("precio debit", precio_debit)
                        print("precio credit", limitado_debit)

                    line.with_context(check_move_validity=False).write({
                        'credit': precio_credit,
                        'debit': precio_debit
                    })
        # llamo a funcion de ajuste de centavos
        rec.adjust_journal_entries()

    def adjust_journal_entries(move):
        total_debit = sum(line.debit for line in move.line_ids)
        total_credit = sum(line.credit for line in move.line_ids)

        difference = total_credit - total_debit

        if difference != 0:
            if difference > 0:
                # Agrego un débito adicional para equilibrar
                debit_account = \
                    move.line_ids.filtered(lambda line: line.debit > 0).sorted(key=lambda line: line.debit)[1]
                debit_account.write({'debit': debit_account.debit + difference})
            else:
                # Agrego un crédito adicional para equilibrar
                credit_account = \
                    move.line_ids.filtered(lambda line: line.credit > 0).sorted(key=lambda line: line.credit)[1]
                credit_account.write({'credit': credit_account.credit + abs(difference)})
        return move

    def post(self):
        for rec in self:
            if rec.es_manual_rate:
                rec.l10n_ar_currency_rate = rec.currency_rate
                """ recompute debit/credit sending force_rate on context """
                other_curr_ar_invoices = self.filtered(
                    lambda x: x.is_invoice() and
                              x.company_id.country_id == self.env.ref(
                        'base.ar') and x.currency_id != x.company_id.currency_id)
                # llamamos a todos los casos de otra moneda y no solo a los que tienen "l10n_ar_currency_rate" porque odoo
                # tiene una suerte de bug donde solo recomputa los debitos/creditos en ciertas condiciones, pero puede
                # ser que esas condiciones no se cumplan y la cotizacion haya cambiado (por ejemplo la factura tiene fecha y
                # luego se cambia la cotizacion, al validar no se recomputa). Si odoo recomputase en todos los casos seria
                # solo necesario iterar los elementos con l10n_ar_currency_rate y hacer solo el llamado a super
                for record in other_curr_ar_invoices:
                    # si no tiene fecha en realidad en llamando a super ya se recomputa con el llamado a _onchange_invoice_date
                    # también se recomputa con algo de lock dates llamando a _onchange_invoice_date, pero por si no se dan
                    # esas condiciones o si odoo las cambia, llamamos al onchange_currency por las dudas
                    record.with_context(check_move_validity=False,
                                        force_rate=rec.l10n_ar_currency_rate)._onchange_currency()

                    # tambien tenemos que pasar force_rate aca por las dudas de que super entre en onchange_currency en los
                    # mismos casos mencionados recien
                    res = super(AccountMove, record.with_context(force_rate=rec.l10n_ar_currency_rate)).post()
                res = super(AccountMove, self - other_curr_ar_invoices).post()
                return res
            else:
                """ recompute debit/credit sending force_rate on context """
                other_curr_ar_invoices = self.filtered(
                    lambda x: x.is_invoice() and
                              x.company_id.country_id == self.env.ref(
                        'base.ar') and x.currency_id != x.company_id.currency_id)
                # llamamos a todos los casos de otra moneda y no solo a los que tienen "l10n_ar_currency_rate" porque odoo
                # tiene una suerte de bug donde solo recomputa los debitos/creditos en ciertas condiciones, pero puede
                # ser que esas condiciones no se cumplan y la cotizacion haya cambiado (por ejemplo la factura tiene fecha y
                # luego se cambia la cotizacion, al validar no se recomputa). Si odoo recomputase en todos los casos seria
                # solo necesario iterar los elementos con l10n_ar_currency_rate y hacer solo el llamado a super
                for record in other_curr_ar_invoices:
                    # si no tiene fecha en realidad en llamando a super ya se recomputa con el llamado a _onchange_invoice_date
                    # también se recomputa con algo de lock dates llamando a _onchange_invoice_date, pero por si no se dan
                    # esas condiciones o si odoo las cambia, llamamos al onchange_currency por las dudas
                    record.with_context(check_move_validity=False,
                                        force_rate=record.l10n_ar_currency_rate)._onchange_currency()

                    # tambien tenemos que pasar force_rate aca por las dudas de que super entre en onchange_currency en los
                    # mismos casos mencionados recien
                    res = super(AccountMove, record.with_context(force_rate=record.l10n_ar_currency_rate)).post()
                res = super(AccountMove, self - other_curr_ar_invoices).post()
                return res
