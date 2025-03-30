from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    especialidad_ids = fields.Many2many(
        "res.partner.especialidad",
        column1="partner_id",
        column2="especialidad_id",
        string="Especialidad",
    )
    nro_colegiado = fields.Char(string="Nro. Colegiado")
