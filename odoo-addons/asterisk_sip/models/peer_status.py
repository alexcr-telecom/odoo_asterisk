import humanize
import logging
from odoo import models, fields, api, _


DEFAULT_SIP_PEER_STATUS_KEEP_DAYS = 7 # The number of days to keep statuses


_logger = logging.getLogger(__name__)


class SipPeerStatus(models.Model):
    _name = 'asterisk.sip_peer_status'
    _order = 'create_date desc'
    _rec_name = 'status'

    peer = fields.Many2one(comodel_name='asterisk.sip_peer', required=True,
                           ondelete='cascade')
    peer_name = fields.Char()
    status = fields.Selection(selection=(
        ('Registered', 'Registered'),
        ('Unregistered', 'Unregistered'),
        ('Unreachable', 'Unreachable'),
        ('Reachable', 'Reachable')
    ), index=True, required=True)
    cause = fields.Char(index=True)
    address = fields.Char(index=True)
    created = fields.Char(compute='_get_created')


    @api.model
    def log_status(self, values):
        if values.get('Event') != 'PeerStatus' or values.get('ChannelType') != 'SIP':
            logger.error('Wrong event for Asterisk SIP peer status: {}'.format(
                values))
            return False

        channel, peer_name = values.get('Peer', '/').split('/')
        peer = self.env['asterisk.sip_peer'].search([('name', '=', peer_name)])
        if not peer:
            logger.warning('Did not find peer {} to update status.'.format(
                peer_name
            ))
            return False

        self.create({
            'peer': peer.id,
            'peer_name': peer_name,
            'status': values.get('PeerStatus', False),
            'cause': values.get('Cause', False),
            'address': values.get('Address', False)
        })
        return True



    @api.model
    def delete_expired(self, days=DEFAULT_SIP_PEER_STATUS_KEEP_DAYS):
        records = self.search([('create_date', '<', fields.Datetime.to_string(
            datetime.now() - timedelta(days=days)))])
        if records:
            logger.info('Deleting {} peer statuses.'.format(len(records)))
            records.unlink()



    @api.multi
    def _get_created(self):
        for rec in self:
            to_translate = self.env.context.get('lang', 'en_US')
            if to_translate != 'en_US':
                humanize.i18n.activate(to_translate)
            rec.created = humanize.naturaltime(
                fields.Datetime.from_string(rec.create_date))
