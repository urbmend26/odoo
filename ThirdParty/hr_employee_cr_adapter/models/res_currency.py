# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency'

    rate = fields.Float(digits=(5, 12))