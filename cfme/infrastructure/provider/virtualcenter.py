from navmazing import NavigateToSibling
from wrapanapi.virtualcenter import VMWareSystem

from cfme.common.provider import DefaultEndpoint, DefaultEndpointForm
from cfme.common.provider_views import ProviderNodesView
from cfme.exceptions import DestinationNotFound
from utils.appliance.implementations.ui import CFMENavigateStep, navigator
from . import InfraProvider
from cfme.exceptions import ItemNotFound


class VirtualCenterEndpoint(DefaultEndpoint):
    pass


class VirtualCenterEndpointForm(DefaultEndpointForm):
    pass


class VMwareProvider(InfraProvider):
    type_name = "virtualcenter"
    mgmt_class = VMWareSystem
    db_types = ["Vmware::InfraManager"]
    endpoints_form = VirtualCenterEndpointForm
    discover_dict = {"vmware": True}
    # xpath locators for elements, to be used by selenium
    _console_connection_status_element = '//*[@id="connection-status"]'
    _canvas_element = '//*[@id="remote-console"]/canvas'
    _ctrl_alt_del_xpath = '//*[@id="ctrlaltdel"]'
    _fullscreen_xpath = '//*[@id="fullscreen"]'

    def __init__(self, name=None, endpoints=None, key=None, zone=None, hostname=None,
                 ip_address=None, start_ip=None, end_ip=None, provider_data=None, appliance=None):
        super(VMwareProvider, self).__init__(
            name=name, endpoints=endpoints, zone=zone, key=key, provider_data=provider_data,
            appliance=appliance)
        self.hostname = hostname
        self.start_ip = start_ip
        self.end_ip = end_ip
        if ip_address:
            self.ip_address = ip_address

    def deployment_helper(self, deploy_args):
        """ Used in utils.virtual_machines """
        # Called within a dictionary update. Since we want to remove key/value pairs, return the
        # entire dictionary
        deploy_args.pop('username', None)
        deploy_args.pop('password', None)
        if "allowed_datastores" not in deploy_args and "allowed_datastores" in self.data:
            deploy_args['allowed_datastores'] = self.data['allowed_datastores']

        return deploy_args

    @classmethod
    def from_config(cls, prov_config, prov_key, appliance=None):
        endpoint = VirtualCenterEndpoint(**prov_config['endpoints']['default'])

        if prov_config.get('discovery_range'):
            start_ip = prov_config['discovery_range']['start']
            end_ip = prov_config['discovery_range']['end']
        else:
            start_ip = end_ip = prov_config.get('ipaddress')
        return cls(name=prov_config['name'],
                   endpoints={endpoint.name: endpoint},
                   zone=prov_config['server_zone'],
                   key=prov_key,
                   start_ip=start_ip,
                   end_ip=end_ip,
                   appliance=appliance)

    @property
    def view_value_mapping(self):
        return {'name': self.name,
                'prov_type': 'VMware vCenter'
                }

    # Following methods will only work if the remote console window is open
    # and if selenium focused on it. These will not work if the selenium is
    # focused on Appliance window.
    def get_console_connection_status(self):
        try:
            return self.appliance.browser.widgetastic.selenium.find_element_by_xpath(
                self._console_connection_status_element).text
        except:
            raise ItemNotFound("Element not found on screen, is current focus on console window?")

    def get_remote_console_canvas(self):
        try:
            return self.appliance.browser.widgetastic.selenium.find_element_by_xpath(
                self._canvas_element)
        except:
            raise ItemNotFound("Element not found on screen, is current focus on console window?")

    def get_console_ctrl_alt_del_btn(self):
        try:
            return self.appliance.browser.widgetastic.selenium.find_element_by_xpath(
                self._ctrl_alt_del_xpath)
        except:
            raise ItemNotFound("Element not found on screen, is current focus on console window?")

    def get_console_fullscreen_btn(self):
        try:
            return self.appliance.browser.widgetastic.selenium.find_element_by_xpath(
                self._fullscreen_xpath)
        except:
            raise ItemNotFound("Element not found on screen, is current focus on console window?")


@navigator.register(VMwareProvider, 'ProviderNodes')  # matching other infra class destinations
class ProviderNodes(CFMENavigateStep):
    VIEW = ProviderNodesView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        try:
            self.prerequisite_view.contents.relationships.click_at('Hosts')
        except NameError:
            raise DestinationNotFound("Hosts aren't present on details page of this provider")
