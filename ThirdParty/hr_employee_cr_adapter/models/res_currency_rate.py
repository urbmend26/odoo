# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from suds.client import Client
from suds.xsd.doctor import Import, ImportDoctor
from xmlrpc.client import ServerProxy
from odoo import api, fields, models
import datetime
import xml.etree.ElementTree


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'
    
    # Change decimal presicion to work with CRC where 1 USD is more de 555 CRC
    rate = fields.Float(string='Selling Rate', digits=(5, 13))

    # Costa Rica uses two exchange rates: 
    #   - Buying exchange rate - used when a financial institutions buy USD from you (rate)
    #   - Selling exchange rate - used when financial institutions sell USD to you (rate_2)
    rate_2 = fields.Float(string='Buying Rate', digits=(5, 12), help='The buying rate of the currency to the currency of rate 1.')

    # Rate as it is get 
    original_rate = fields.Float(string='Selling Rate in Costa Rica', digits=(6, 2), help='The selling exchange rate from CRC to USD as it is send from BCCR')
    # Rate as it is get 
    original_rate_2 = fields.Float(string='Buying Rate in Costa Rica', digits=(6, 2), help='The buying exchange rate from CRC to USD as it is send from BCCR')


    @api.model
    def _cron_update(self):
        # Get current date to get exchange rate for today
        currentDate = datetime.datetime.now().date()
        today = currentDate.strftime('%d/%m/%Y'); #formato requerido por el BCCR dd/mm/yy

        # Get XML Schema for BCCR webservice SOAP
        imp = Import('http://www.w3.org/2001/XMLSchema', location='http://www.w3.org/2001/XMLSchema.xsd')
        imp.filter.add('http://ws.sdde.bccr.fi.cr')

        # Web Service Connection using the XML schema from BCCRR
        client = Client('http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/WebServices/wsIndicadoresEconomicos.asmx?WSDL', doctor=ImportDoctor(imp))

        # Get Selling exchange Rate from BCCR
        # Indicators IDs at https://www.bccr.fi.cr/seccion-indicadores-economicos/servicio-web
        # The response is a string we need to convert it to XML to extract value
        response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='318', tcFechaInicio=today, tcFechaFinal=today, tcNombre='AKUREY', tnSubNiveles='N')
        xmlResponse = xml.etree.ElementTree.fromstring(response)
        rateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")
        sellingRate = 0
        if len(rateNodes) > 0:
            sellingOriginalRate = float(rateNodes[0].text)
            sellingRate = 1/sellingOriginalRate # Odoo utiliza un valor inverso. Es decir a cuantos dólares equivale 1 colón. Por eso se divide 1 colon entre el tipo de cambio. 

        # Get Buying exchange Rate from BCCR
        response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='317', tcFechaInicio=today, tcFechaFinal=today, tcNombre='AKUREY', tnSubNiveles='N')
        xmlResponse = xml.etree.ElementTree.fromstring(response)
        rateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")
        buyingRate = 0
        if len(rateNodes) > 0:
            buyingOriginalRate = float(rateNodes[0].text)
            buyingRate = 1/buyingOriginalRate # Odoo utiliza un valor inverso. Es decir a cuantos dólares equivale 1 colón. Por eso se divide 1 colon entre el tipo de cambio. 

        # Save the exchange rate in database
        newRate = self.create({'name': currentDate.isoformat(),'rate': sellingRate, 'original_rate':sellingOriginalRate, 'rate_2':buyingRate, 'original_rate_2':buyingOriginalRate, 'currency_id': 3})
