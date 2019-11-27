import os
import boto3
import re
import time
import netaddr
import utils
from botocore.config import Config
from botocore.exceptions import ClientError
from utils import Global

logger = utils.get_logger()

class EC2:

    def __init__(self, aws, region):

        self.aws = aws
        self.region = region
        config = Config(retries = dict(max_attempts = 20))
        self.resource = boto3.resource('ec2', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, region_name = region, config = config)
        self.client = boto3.client('ec2', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, region_name = region, config = config)

        self.resource_types = ['TGW_VPC_ATTACHMENT', 'TGW', 'LAUNCH_TEMPLATE', 'INSTANCE', 'KEY_PAIR', 'NETWORK_INTERFACE', 'SUBNET', 'SECURITY_GROUP', 'PEERING_CONNECTION',
                                    'NETWORK_ACL', 'INTERNET_GATEWAY', 'ELASTIC_IP', 'ROUTE_TABEL', 'VPN_CONNECTION',
                                        'VIRTUAL_PRIVATE_GATEWAY', 'CUSTOMER_GATEWAY', 'TGW_ROUTE_TABLE', 'VPC'] # Don't change order

    def get_ResourceTypes(self):
        skip_resources = ['KEY_PAIR']
        return [k for k in self.resource_types if k not in skip_resources]

    def get_Resource_Data(self, resource_type, filters = None):

        if not filters:
            filters = []

        if not resource_type in self.resource_types:
            raise invalidResourceType('Invalid EC2 Resource')

        if resource_type is 'LAUNCH_TEMPLATE':
            return [k for k in self.client.describe_launch_templates(Filters = filters)['LaunchTemplates']]

        if resource_type is 'INSTANCE':
            if not filters:
                return [k for k in self.resource.instances.all()]
            return [k for k in self.resource.instances.filter(Filters = filters)]

        if resource_type is 'VPC':
            if not filters:
                return [k for k in self.resource.vpcs.all()]
            return [k for k in self.resource.vpcs.filter(Filters = filters)]

        if resource_type is 'SUBNET':
            if not filters:
                return [k for k in self.resource.subnets.all()]
            return [k for k in self.resource.subnets.filter(Filters = filters)]

        if resource_type is 'INTERNET_GATEWAY':
            if not filters:
                return [k for k in self.resource.internet_gateways.all()]
            return [k for k in self.resource.internet_gateways.filter(Filters = filters)]

        if resource_type is 'SECURITY_GROUP':
            if not filters:
                return [k for k in self.resource.security_groups.all()]
            return [k for k in self.resource.security_groups.filter(Filters = filters)]

        if resource_type is 'ROUTE_TABEL':
            if not filters:
                return [k for k in self.resource.route_tables.all()]
            return [k for k in self.resource.route_tables.filter(Filters = filters)]

        if resource_type is 'NETWORK_INTERFACE':
            if not filters:
                return [k for k in self.resource.network_interfaces.all()]
            return [k for k in self.resource.network_interfaces.filter(Filters = filters)]

        if resource_type is 'ELASTIC_IP':
            return [k for k in self.client.describe_addresses(Filters = filters)['Addresses']]

        if resource_type is 'PEERING_CONNECTION':
            if not filters:
                return [k for k in self.resource.vpc_peering_connections.all()]
            return [k for k in self.resource.vpc_peering_connections.filter(Filters = filters)]

        if resource_type is 'NETWORK_ACL':
            if not filters:
                return [k for k in self.resource.network_acls.all()]
            return [k for k in self.resource.network_acls.filter(Filters = filters)]

        if resource_type is 'CUSTOMER_GATEWAY':
            return [k for k in self.client.describe_customer_gateways(Filters = filters)['CustomerGateways']]

        if resource_type is 'VIRTUAL_PRIVATE_GATEWAY':
            return [k for k in self.client.describe_vpn_gateways(Filters = filters)['VpnGateways']]

        if resource_type is 'VPN_CONNECTION':
            return [k for k in self.client.describe_vpn_connections(Filters = filters)['VpnConnections']]

        if resource_type is 'KEY_PAIR':
            return [k for k in self.client.describe_key_pairs(Filters = filters)['KeyPairs']]

        if resource_type is 'TGW':
            try:
                return [k for k in self.client.describe_transit_gateways(Filters = filters)['TransitGateways']]
            except Exception as e:
                logger.debug('Exception while retrieving TGW for:'+self.region+':'+str(e), To_Screen=False)
                return []
            
        if resource_type is 'TGW_ROUTE_TABLE':
            try:
                return [k for k in self.client.describe_transit_gateway_route_tables(Filters = filters)['TransitGatewayRouteTables']]
            except Exception as e:
                logger.debug('Exception while retrieving TGW_ROUTE_TABLE for:'+self.region+':'+str(e), To_Screen=False)
                return []

        if resource_type is 'TGW_VPC_ATTACHMENT':
            try:
                return [k for k in self.client.describe_transit_gateway_vpc_attachments(Filters = filters)['TransitGatewayVpcAttachments']]
            except Exception as e:
                logger.debug('Exception while retrieving TGW_VPC_ATTACHMENT for:'+self.region+':'+str(e), To_Screen=False)
                return []

        return None

    def get_Resource_List(self, resource_type, filters = None):

        if not filters:
            filters = []

        if not resource_type in self.resource_types:
            raise invalidResourceType('Invalid EC2 Resource')

        data = self.get_Resource_Data(resource_type, filters)

        if resource_type in ['INSTANCE', 'VPC', 'SUBNET', 'INTERNET_GATEWAY',
                                'SECURITY_GROUP', 'ROUTE_TABEL', 'NETWORK_INTERFACE',
                                    'NETWORK_ACL', 'PEERING_CONNECTION']:
            return [k.id for k in data]

        if resource_type is 'LAUNCH_TEMPLATE':
            return [k['LaunchTemplateId'] for k in data]

        if resource_type is 'ELASTIC_IP':
            return [k['PublicIp'] for k in data]

        if resource_type is 'CUSTOMER_GATEWAY':
            return [k['CustomerGatewayId'] for k in data]

        if resource_type is 'VIRTUAL_PRIVATE_GATEWAY':
            return [k['VpnGatewayId'] for k in data]

        if resource_type is 'VPN_CONNECTION':
            return [k['VpnConnectionId'] for k in data]

        if resource_type is 'KEY_PAIR':
            return [k['KeyName'] for k in data]

        if resource_type is 'TGW':
            return [k['TransitGatewayId'] for k in data]

        if resource_type is 'TGW_ROUTE_TABLE':
            return [k['TransitGatewayRouteTableId'] for k in data]

        if resource_type is 'TGW_VPC_ATTACHMENT':
            return [k['TransitGatewayAttachmentId'] for k in data]

        return None

    def get_Resource_Handel(self, resource_type, resource_id, all_data = True):

        if not resource_type in self.resource_types:
            raise invalidResourceType('Invalid EC2 Resource')

        if resource_type is 'LAUNCH_TEMPLATE':
            return Launch_Template(self, resource_id)

        if resource_type is 'INSTANCE':
            return Instace(self, resource_id, all_data)

        if resource_type is 'VPC':
            return Vpc(self, resource_id)

        if resource_type is 'SUBNET':
            return Subnet(self, resource_id)

        if resource_type is 'INTERNET_GATEWAY':
            return Internet_Gateway(self, resource_id)

        if resource_type is 'SECURITY_GROUP':
            return Security_Group(self, resource_id)

        if resource_type is 'ROUTE_TABEL':
            return Route_Tabel(self, resource_id)

        if resource_type is 'NETWORK_INTERFACE':
            return Network_Interface(self, resource_id)

        if resource_type is 'PEERING_CONNECTION':
            return Peering_Connection(self, resource_id)

        if resource_type is 'NETWORK_ACL':
            return Network_Acl(self, resource_id)

        if resource_type is 'CUSTOMER_GATEWAY':
            return Customer_Gateway(self, resource_id)

        if resource_type is 'ELASTIC_IP':
            return Elastic_Ip(self, resource_id)

        if resource_type is 'VPN_CONNECTION':
            return Vpn_Connection(self, resource_id)

        if resource_type is 'VIRTUAL_PRIVATE_GATEWAY':
            return Virtual_Private_Gateway(self, resource_id)

        if resource_type is 'KEY_PAIR':
            return Key_Pair(self, resource_id)

        if resource_type is 'TGW':
            return Tgw(self, resource_id)

        if resource_type is 'TGW_VPC_ATTACHMENT':
            return Tgw_Vpc_Attachment(self, resource_id)

        if resource_type is 'TGW_ROUTE_TABLE':
            return Tgw_Route_Table(self, resource_id)

        return None


    def is_Resource_Alive(self, resource_type, resource_id):

        if not resource_type in self.resource_types:
            raise invalidResourceType('Invalid EC2 Resource')

        h = self.get_Resource_Handel(resource_type, resource_id)

        if resource_type is 'LAUNCH_TEMPLATE':
            return (True, h.state)

        if resource_type is 'INSTANCE':
            return (h.state not in ['shutting-down', 'terminated'], h.state)

        if resource_type is 'VPC':
            return (True, h.state)

        if resource_type is 'SUBNET':
            return (True, h.state)

        if resource_type is 'INTERNET_GATEWAY':
            return (True, h.state)

        if resource_type is 'SECURITY_GROUP':
            return (True, h.state)

        if resource_type is 'ROUTE_TABEL':
            return (True, h.state)

        if resource_type is 'NETWORK_INTERFACE':
            return (True, h.state)

        if resource_type is 'ELASTIC_IP':
            return (True, h.state)

        if resource_type is 'PEERING_CONNECTION':
            return (True, h.state)

        if resource_type is 'NETWORK_ACL':
            return (True, h.state)

        if resource_type is 'CUSTOMER_GATEWAY':
            return (True, h.state)

        if resource_type is 'VIRTUAL_PRIVATE_GATEWAY':
            return (h.state != 'deleted', h.state)

        if resource_type is 'VPN_CONNECTION':
            return (h.state != 'deleted', h.state)

        if resource_type is 'KEY_PAIR':
            return (True, h.state)

        if resource_type is 'TGW':
            return (h.state != 'deleted', h.state)

        if resource_type is 'TGW_VPC_ATTACHMENT':
            return (h.state != 'deleted', h.state)

        if resource_type is 'TGW_ROUTE_TABLE':
            return (True, h.state)

        return None

    def resource_cleanup(self, resources):

        for resource_type in self.resource_types:
            logger.info('Account: {} Region: {} - Cleaning {}'.format(self.aws.account, self.region, resource_type), To_Screen = True)
            all_names = self.get_Resource_List(resource_type)
            name_list = all_names if resources else []
            if not resources.get('all'):
                name_list = [k for k in all_names if k in resources.get('name', [])]
                resource_filter = resources.get('filter', {})
                for fltr in resource_filter.get('name', []):
                    if not resource_filter.get('ignore_case'):
                        name_list.extend([k for k in all_names if fltr in k])
                    else:
                        name_list.extend([k for k in all_names if fltr.lower() in k.lower()])
                name_list = list(set(name_list))
                name_list = [k for k in name_list if k not in resources.get('exclude_name', [])]

            resource_handle_list = [self.get_Resource_Handel(resource_type, k) for k in name_list]

            if resource_type is 'SECURITY_GROUP':
                for resource in resource_handle_list:
                    resource.delete_rules()

            for resource in resource_handle_list:
                resource.delete()

            if resource_type is 'INSTANCE':
                for resource in resource_handle_list:
                    resource.wait_until_deleted()

        return True

    def get_LaunchTemplate(self, id = None):
        return self.get_Resource_Handel('LAUNCH_TEMPLATE', id)

    def get_Instance(self, id = None, all_data = True):
        return self.get_Resource_Handel('INSTANCE', id, all_data)

    def get_KeyPair(self, id = None):
        return self.get_Resource_Handel('KEY_PAIR', id)

    def get_AvailibilityZones(self):
        response = self.client.describe_availability_zones()
        return response['AvailabilityZones']

    def get_InstanceList(self, filters = None):
        return self.get_Resource_List('INSTANCE', filters)

    def get_RunningInstanceList(self, filters = None):
        if not filters:
            filters = []
        filters.append({'Name': 'instance-state-name', 'Values': ['running']})
        return self.get_Resource_List('INSTANCE', filters)

    def get_VpcList(self, filters = None):
        return self.get_Resource_List('VPC', filters)

    def get_Vpc(self, id = None):
        return self.get_Resource_Handel('VPC', id)

    def is_Vpc_Alive(self, id):
        if id in self.get_VpcList():
            return self.is_Resource_Alive('VPC', id)[0]
        return False

    def get_VirtualPrivateGatewayList(self, filters = None):
        return self.get_Resource_List('VIRTUAL_PRIVATE_GATEWAY', filters)

    def get_VirtualPrivateGateway(self, id):
        return self.get_Resource_Handel('VIRTUAL_PRIVATE_GATEWAY', id)

    def is_VirtualPrivateGateway_Alive(self, id):
        if id in self.get_VirtualPrivateGatewayList():
            return self.is_Resource_Alive('VIRTUAL_PRIVATE_GATEWAY', id)[0]
        return False

    def get_VpnConnectionList(self, filters = None):
        return self.get_Resource_List('VPN_CONNECTION', filters)

    def get_VpnConnection(self, id):
        return self.get_Resource_Handel('VPN_CONNECTION', id)

    def is_VpnConnection_Alive(self, id):
        if id in self.get_VpnConnectionList():
            return self.is_Resource_Alive('VPN_CONNECTION', id)[0]
        return False

    def get_SubnetList(self, filters = None):
        return self.get_Resource_List('SUBNET', filters)

    def get_Subnet(self, id):
        return self.get_Resource_Handel('SUBNET', id)

    def is_Subnet_Alive(self, id):
        if id in self.get_SubnetList():
            return self.is_Resource_Alive('SUBNET', id)[0]
        return False

    def get_InternetGatewayList(self, filters = None):
        return self.get_Resource_List('INTERNET_GATEWAY', filters)

    def get_InternetGateway(self, id = None):
        return self.get_Resource_Handel('INTERNET_GATEWAY', id)

    def get_SecurityGroupList(self, filters = None):
        return self.get_Resource_List('SECURITY_GROUP', filters)

    def get_SecurityGroup(self, id):
        return self.get_Resource_Handel('SECURITY_GROUP', id)

    def is_SecurityGroup_Alive(self, id):
        if id in self.get_SecurityGroupList():
            return self.is_Resource_Alive('SECURITY_GROUP', id)[0]
        return False

    def get_RouteTableList(self, filters = None):
        return self.get_Resource_List('ROUTE_TABEL', filters)

    def get_RouteTable(self, id):
        return self.get_Resource_Handel('ROUTE_TABEL', id)

    def is_RouteTable_Alive(self, id):
        if id in self.get_RouteTableList():
            return self.is_Resource_Alive('ROUTE_TABEL', id)[0]
        return False

    def terminate_Instances(self, ids = None, filters = None):

        if not ids:
            ids = self.get_Resource_List('INSTANCE', filters)
        if type(ids) == str:
            ids = [ids]
        if type(ids) != list:
            raise Exception('Only list or string is allowed, Found: {}'.format(type(ids)))

        for instance_id in ids:
            instance = self.resource.Instance(id = instance_id)
            instance.terminate()

        return True

    def verify_terminated_Instances(self, ids = None, filters = None):

        if not ids:
            ids = self.get_Resource_List('INSTANCE', filters)
        if type(ids) == str:
            ids = [ids]
        if type(ids) != list:
            raise Exception('Only list or string is allowed, Found: {}'.format(type(ids)))

        logger.info('Waiting until all Instances are Terminated...', To_Screen = True)
        for instance_id in ids:
            instance = self.resource.Instance(id = instance_id)
            instance.wait_until_terminated()

        running_instances = self.get_RunningInstanceList(filters)
        if any([k in running_instances for k in ids]):
            logger.error('Not all instances are terminated', To_Screen = True)
            logger.info('Running Instances: {}'.format(running_instances), To_Screen = True)
            return False

        logger.info('All Instances are Terminated', To_Screen = True)
        return True


class Launch_Template:

    def __init__(self, ec2, id = None):

        self.ec2 = ec2
        self.id = id
        self.state = None

    def create(self, name, subnet_id, image_id, instance_type, key_pair, selector_type, selector_val, public = True):

        if name in [k.get('LaunchTemplateName') for k in self.ec2.client.describe_launch_templates()['LaunchTemplates']]:
            self.delete(name)

        data = {}
        data['NetworkInterfaces'] = [{'SubnetId': subnet_id, 'AssociatePublicIpAddress': public, 'DeleteOnTermination': True, 'DeviceIndex': 0}]
        data['ImageId'] = image_id
        data['InstanceType'] = instance_type
        data['KeyName'] = key_pair
        if selector_type.lower() == 'tag_value':
            data['TagSpecifications'] = [{'ResourceType': 'instance', 'Tags': [{'Key': selector_val[0], 'Value': selector_val[1]}]}]
        elif selector_type.lower() == 'ip':
            pass
        elif selector_type.lower() == 'region':
            subnet = self.ec2.get_Subnet(subnet_id)
            subnet_region = subnet.availability_zone[:-1]
            # logger.info('SRegion: {}, Subnet Region: {}'.format(selector_val, subnet_region), To_Screen = True)
            if selector_val != subnet_region:
                return 0
        elif selector_type.lower() == 'zone':
            subnet = self.ec2.get_Subnet(subnet_id)
            # logger.info('SZone: {}, Subnet Zone: {}'.format(selector_val, subnet.availability_zone), To_Screen = True)
            if selector_val != subnet.availability_zone:
                return 0
            data['Placement'] = {'AvailabilityZone': selector_val}
        else:
            raise Exception('Invalid Selector Type: {}'.format(selector_type))

        response = self.ec2.client.create_launch_template(LaunchTemplateName = name, LaunchTemplateData = data)
        return response['LaunchTemplate']['LaunchTemplateId']

    def delete(self, name = None):
        if name:
            self.ec2.client.delete_launch_template(LaunchTemplateName = name)
        else:
            self.ec2.client.delete_launch_template(LaunchTemplateId = self.id)

class Instace:

    def __init__(self, ec2, id = None, all_data = True):

        self.ec2 = ec2
        self.id = id
        if not self.id:
            return
        self.instance = ec2.resource.Instance(id = self.id)
        self.state = None
        if not all_data:
            return
        try:
            self.state = self.instance.state['Name'] # Valid Values: pending | running | shutting-down | terminated | stopping | stopped
            self.vpc = self.instance.vpc_id if self.instance.vpc else None
            self.subnet = self.instance.subnet_id
            self.public_ip = self.instance.public_ip_address
            self.private_ip = self.instance.private_ip_address
            self.instance_type = self.instance.instance_type
            self.ami_id = self.instance.image_id
            self.launch_time = self.instance.launch_time
            self.network_interfaces = [k.id for k in self.instance.network_interfaces]
            self.security_groups = [k['GroupId'] for k in self.instance.security_groups]
            self.key_name = self.instance.key_name
            self.tags = self.instance.tags
            self.describe_addresses = self.instance.describe_addresses
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def delete(self):
        try:
            self.instance.terminate()
            return True
        except Exception as e:
            logger.error("Error when instance.terminate(): %s"%(str(e)), To_Screen = True)
            return False

    def reboot(self):
        try:
            self.instance.reboot()
            time.sleep(10)
            return True
        except Exception as e:
            logger.error("Error when instance.reboot(): %s"%(str(e)), To_Screen = True)
            return False

    def stop(self):
        try:
            self.instance.stop()
            time.sleep(10)
            return True
        except Exception as e:
            logger.error("Error when instance.stop(): %s"%(str(e)), To_Screen = True)
            return False

    def start(self):
        try:
            self.instance.start()
            time.sleep(10)
            return True
        except Exception as e:
            logger.error("Error when instance.start(): %s"%(str(e)), To_Screen = True)
            return False

    def wait_until_running(self):
        try:
            self.instance.wait_until_running()
            return True
        except Exception as e:
            logger.error("Error when wait_til_running(): %s"%(str(e)), To_Screen = True)
            return False

    def wait_until_stopped(self):
        try:
            self.instance.wait_until_stopped()
            return True
        except Exception as e:
            logger.error("Error when wait_until_stopped(): %s"%(str(e)), To_Screen = True)
            return False

    def wait_until_deleted(self):
        try:
            self.instance.wait_until_terminated()
            return True
        except Exception as e:
            logger.error("Error when wait_until_terminated(): %s"%(str(e)), To_Screen = True)
            return False

    def wait_until_exists(self):
        self.instance.wait_until_exists()

    def create(self, template_id = None, data = None, count = 1, ips = None):

        if not any([template_id, data]):
            raise Exception('Need template or data to create Instances')

        # data = {'SubnetId': '', 'ImageId': '', 'InstanceType': '', 'KeyName': '', 'SelectorType': '', 'SelectorVal': ''}

        if template_id and not ips:
            instances = self.ec2.resource.create_instances(LaunchTemplate = {'LaunchTemplateId': template_id}, MaxCount = count, MinCount = count)
            return [k.id for k in instances]

        TagSpecifications = []
        Placement = {}
        SelectorType = data.get('SelectorType', '')
        SelectorVal = data.get('SelectorVal', '')
        SubnetId = data.get('SubnetId', '')
        ImageId = data.get('ImageId', '')
        KeyName = data.get('KeyName', '')
        InstanceType = data.get('InstanceType', '')
        if SelectorType and SelectorVal:
            if SelectorType.lower() == 'tag_value':
                TagSpecifications = [{'ResourceType': 'instance', 'Tags': [{'Key': SelectorVal[0], 'Value': SelectorVal[1]}]}]
            elif SelectorType.lower() == 'ip':
                pass
            elif SelectorType.lower() == 'region':
                subnet = self.ec2.get_Subnet(SubnetId)
                subnet_region = subnet.availability_zone[:-1]
                if SelectorVal != subnet_region:
                    logger.info('Skipping Instance Creation if region not matching.', To_Screen = True)
                    return 0
            elif SelectorType.lower() == 'zone':
                subnet = self.ec2.get_Subnet(SubnetId)
                if SelectorVal != subnet.availability_zone:
                    logger.info('Skipping Instance Creation if zone not matching.', To_Screen = True)
                    return 0
                Placement = {'AvailabilityZone': SelectorVal}
            else:
                raise Exception('Invalid Selector Type: {}'.format(SelectorType))

        if not ips:
            instances = self.ec2.resource.create_instances(SubnetId = SubnetId, ImageId = ImageId,
                        KeyName = KeyName, TagSpecifications = TagSpecifications, InstanceType = InstanceType,
                        Placement = Placement, MaxCount = count, MinCount = count)
            return [k.id for k in instances]

        instances = []
        if type(ips) == str:
            ips = [ips]
        if type(ips) != list:
            raise Exception('Only string and list allowed as Private Ips to create Instance')

        i = 0
        for ip in ips:
            if i == count:
                break
            try:
                if not template_id:
                    NetworkInterfaces = [{'PrivateIpAddress': ip, 'SubnetId': SubnetId, 'AssociatePublicIpAddress': True, 'DeleteOnTermination': True, 'DeviceIndex': 0}]
                    new_instances = self.ec2.resource.create_instances(
                            ImageId = ImageId, KeyName = KeyName, TagSpecifications = TagSpecifications,
                            NetworkInterfaces = NetworkInterfaces, InstanceType = InstanceType,
                            Placement = Placement, MaxCount = 1, MinCount = 1)
                else:
                    NetworkInterfaces = [{'PrivateIpAddress': ip, 'DeviceIndex': 0}]
                    new_instances = self.ec2.resource.create_instances(
                            LaunchTemplate = {'LaunchTemplateId': template_id},
                            NetworkInterfaces = NetworkInterfaces,
                            MaxCount = 1, MinCount = 1)
                instances.extend(new_instances)
                i += 1
            except Exception as e:
                # logger.info('Exception while creating Instance: {}'.format(e), To_Screen = True)
                # logger.info('Trying with Different Ip', To_Screen = True)
                pass

        return [k.id for k in instances]

class Vpc:

    def __init__(self, ec2, id):

        self.ec2 = ec2
        if not id:
            return
        self.id = id
        self.vpc = ec2.resource.Vpc(id = id)
        self.state = None
        try:
            self.state = self.vpc.state # Valid Values: pending | available
            self.subnets = [k.id for k in self.vpc.subnets.all()]
            self.security_groups = [k.id for k in self.vpc.security_groups.all()]
            self.internet_gateways = [k.id for k in self.vpc.internet_gateways.all()]
            self.route_tables = [k.id for k in self.vpc.route_tables.all()]
            self.cidr_block = self.vpc.cidr_block
            self.cidr = [k['CidrBlock'] for k in self.vpc.cidr_block_association_set if k['CidrBlockState']['State'] == 'associated']
            self.dhcp = self.vpc.dhcp_options_id
            self.tags = self.vpc.tags
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def get_vgw(self):
        vgw_list= self.ec2.get_Resource_List('VIRTUAL_PRIVATE_GATEWAY')
        if not vgw_list:
            return False
        for vgw_id in vgw_list:
            vgw = self.ec2.get_Resource_Handel('VIRTUAL_PRIVATE_GATEWAY', vgw_id)
            if self.id in vgw.vpcs:
                return vgw_id

        return False

    def delete(self):
        for i in range(30):
            try:
                self.vpc.delete()
                break
            except Exception as e:
                logger.info('Waiting for VPC to be deleted...', To_Screen = True)
                time.sleep(10)
                continue
        else:
            logger.error('Failed to delete Vpc for Account: {}, Region: {}'.format(self.ec2.aws.account, self.ec2.region), To_Screen = True)
            raise Exception(e)

    def create(self, cidr):
        try:
            response = self.ec2.client.create_vpc(CidrBlock = cidr)
        except Exception as e:
            logger.error('Failed to create VPC Exception: {}'.format(e), To_Screen = True)
            return False

        return response['Vpc']['VpcId']

    def attach_igw(self, igw_id):
        try:
            self.vpc.attach_internet_gateway(InternetGatewayId = igw_id)
        except Exception as e:
            logger.error('Failed to attach IGW {} to VPC {}, Exception: {}'.format(igw_id, self.id, e), To_Screen = True)

class Subnet:

    def __init__(self, ec2, id):

        self.subnet = ec2.resource.Subnet(id = id)
        self.state = None
        try:
            self.state = self.subnet.state # Valid Values: pending | available
            self.vpc = self.subnet.vpc_id
            self.availability_zone = self.subnet.availability_zone
            self.cidr = self.subnet.cidr_block
            self.tags = self.subnet.tags
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def delete(self):
        self.subnet.delete()

    def get_ips(self, cidr = None, count = None):

        if not cidr:
            cidr = self.cidr
        if netaddr.IPNetwork(cidr) not in netaddr.IPNetwork(self.cidr):
            return []

        ip_list = [str(k) for k in netaddr.IPNetwork(cidr)]
        if count:
            return ip_list[:count]
        return ip_list

class Internet_Gateway:

    def __init__(self, ec2, id):

        self.ec2 = ec2
        if not id:
            return
        self.id = id
        self.igw = ec2.resource.InternetGateway(id = id)
        self.state = None # Valid Values: attaching | attached | detaching | detached
        try:
            self.vpcs = [k['VpcId'] for k in self.igw.attachments]
            self.tags = self.igw.tags
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def delete(self):
        for entry in self.igw.attachments:
            self.igw.detach_from_vpc(VpcId = entry['VpcId'])
        self.igw.delete()

    def create(self):
        try:
            response = self.ec2.client.create_internet_gateway()
        except Exception as e:
            logger.error('Failed to Create IGW, Exception: {}'.format(e), To_Screen = True)
            return False

        return response['InternetGateway']['InternetGatewayId']

    def attach_to_vpc(self, vpc_id):
        try:
            self.igw.attach_to_vpc(VpcId = vpc_id)
        except Exception as e:
            logger.error('Failed to attach IGW {} to VPC {}, Exception: {}'.format(self.id, vpc_id, e), To_Screen = True)
            return False

        return True

class Security_Group:

    def __init__(self, ec2, id):

        self.sg = ec2.resource.SecurityGroup(id = id)
        self.state = None
        try:
            self.group_name = self.sg.group_name
            self.description = self.sg.description
            self.vpc = self.sg.vpc_id
            self.tags = self.sg.tags
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def add_rule_ingress(self, data = None):

        if not data:
            data = [{
                        'FromPort': 0,
                        'ToPort': 65535,
                        'IpProtocol': 'tcp',
                        'IpRanges': [{
                                        'CidrIp': '0.0.0.0/0'
                                    }]
                    }]

        self.sg.authorize_ingress(IpPermissions = data)

    def add_rule_egress(self, data = None):

        if not data:
            data = [{
                        'FromPort': 0,
                        'ToPort': 65535,
                        'IpProtocol': 'tcp',
                        'IpRanges': [{
                                        'CidrIp': '0.0.0.0/0'
                                    }]
                    }]

        self.sg.authorize_egress(IpPermissions = data)

    def delete_rules(self):
        if self.group_name == 'default':
            return
        if self.sg.ip_permissions:
            self.sg.revoke_ingress(IpPermissions = self.sg.ip_permissions)
        if self.sg.ip_permissions_egress:
            self.sg.revoke_egress(IpPermissions = self.sg.ip_permissions_egress)

    def delete(self):
        if self.group_name == 'default':
            return
        self.sg.delete()

class Route_Tabel:

    def __init__(self, ec2, id):

        self.rt = ec2.resource.RouteTable(id = id)
        self.state = None
        try:
            self.subnets = [k.get('SubnetId') for k in self.rt.associations_attribute]
            self.subnets = [k for k in self.subnets if k]
            self.accociation_id = [k['RouteTableAssociationId'] for k in self.rt.associations_attribute]
            self.cidrs = [k.destination_cidr_block for k in self.rt.routes]
            self.vpc = self.rt.vpc_id
            self.tags = self.rt.tags
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def add_route(self, data = None):

        if not data:
            data = {
                        'DestinationCidrBlock': 'string',
                        'GatewayId': 'string',
                        'InstanceId': 'string',
                        'NatGatewayId': 'string',
                        'TransitGatewayId':'string',
                        'NetworkInterfaceId': 'string',
                        'VpcPeeringConnectionId': 'string'
                   }

        self.rt.create_route(
                                DestinationCidrBlock = data.get('DestinationCidrBlock', ''),
                                GatewayId = data.get('GatewayId', ''),
                                InstanceId = data.get('InstanceId', ''),
                                NatGatewayId = data.get('NatGatewayId', ''),
                                TransitGatewayId = data.get('TransitGatewayId', ''),
                                NetworkInterfaceId = data.get('NetworkInterfaceId', ''),
                                VpcPeeringConnectionId = data.get('VpcPeeringConnectionId', '')
                            )

    def delete(self):
        if not self.accociation_id:
            self.rt.delete()

class Network_Interface:

    def __init__(self, ec2, id):

        self.ni = ec2.resource.NetworkInterface(id = id)
        self.state = None
        try:
            self.state = self.ni.status
            self.vpc = self.ni.vpc_id
            self.subnet = self.ni.subnet_id
            self.private_ip = self.ni.private_ip_address
            self.instance = None
            if self.ni.attachment:
                self.instance = self.ni.attachment.get('InstanceId')
            self.availability_zone = self.ni.availability_zone
            self.security_groups = [k['GroupId'] for k in self.ni.groups]
            self.tags = self.ni.tag_set
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def delete(self):
        self.ni.delete()

class Peering_Connection:

    def __init__(self, ec2, id):

        self.pc = ec2.resource.VpcPeeringConnection(id = id)
        self.state = None
        try:
            self.state = self.pc.status['Message']
            self.vpc = self.pc.accepter_vpc.id
            self.tags = self.pc.tags
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def delete(self):
        self.pc.delete()

class Network_Acl:

    def __init__(self, ec2, id):

        self.acl = ec2.resource.NetworkAcl(id = id)
        self.state = None
        try:
            self.vpc = self.acl.vpc_id
            self.tags = self.acl.tags
        except Exception as e:
            logger.debug('Exception: {}'.format(e))

    def delete(self):
        if self.acl.is_default:
            return
        for entry in self.acl.entries:
            if not entry['RuleNumber'] in range(1, 32766):
                continue
            self.acl.delete_entry(Egress = entry['Egress'], RuleNumber = entry['RuleNumber'])

        self.acl.delete()

class Customer_Gateway:

    def __init__(self, ec2, id):

        self.ec2 = ec2
        self.id = id
        self.state = None

    def delete(self):

        for i in range(30):
            try:
                self.ec2.client.delete_customer_gateway(CustomerGatewayId = self.id)
                break
            except Exception as e:
                logger.info('Waiting for CGW to be deleted...', To_Screen = True)
                time.sleep(10)
                continue
        else:
            logger.error('Failed to delete Customer Gateway for Account: {}, Region: {}'.format(self.ec2.aws.account, self.ec2.region), To_Screen = True)
            raise Exception(e)

class Elastic_Ip:

    def __init__(self, ec2, ip):

        self.ec2 = ec2
        self.ip = ip
        self.state = None
        self.allocation_id = ec2.client.describe_addresses(PublicIps = [self.ip])['Addresses'][0]['AllocationId']

    def delete(self):
        self.ec2.client.release_address(AllocationId = self.allocation_id)

class Vpn_Connection:

    def __init__(self, ec2, id):

        self.ec2 = ec2
        self.id = id
        self.vpn = self.ec2.client.describe_vpn_connections(VpnConnectionIds = [self.id])['VpnConnections'][0]
        self.state = self.vpn.get('State')
        self.vgw = self.vpn.get('VpnGatewayId')
        self.cgw = self.vpn.get('CustomerGatewayId')
        self.tunnels = self.vpn.get('VgwTelemetry', [])

    def delete(self):
        self.ec2.client.delete_vpn_connection(VpnConnectionId = self.id)

class Virtual_Private_Gateway:

    def __init__(self, ec2, id):

        self.ec2 = ec2
        self.id = id
        self.vgw = self.ec2.client.describe_vpn_gateways(VpnGatewayIds = [self.id])['VpnGateways'][0]
        self.vpcs = [k['VpcId'] for k in self.vgw['VpcAttachments']]
        self.vpc_status = [k['State'] for k in self.vgw['VpcAttachments']]
        self.state = self.vgw['State']

    def get_connection_list(self):

        vpn_list = self.ec2.get_Resource_List('VPN_CONNECTION')
        if not vpn_list:
            return False

        vpn_ids = []
        vpn_states = []
        for vpn_id in vpn_list:
            vpn = self.ec2.get_Resource_Handel('VPN_CONNECTION', vpn_id)
            if (self.id == vpn.vgw) and (vpn.state != 'deleted'):
                vpn_ids.append(vpn_id)
                vpn_states.append(vpn.state)

        return zip(vpn_ids, vpn_states)

    def delete(self):
        for (vpc_id, status) in zip(self.vpcs, self.vpc_status):
            if status != 'detached':
                self.ec2.client.detach_vpn_gateway(VpcId = vpc_id, VpnGatewayId = self.id)

        for i in range(30):
            try:
                self.ec2.client.delete_vpn_gateway(VpnGatewayId = self.id)
                break
            except Exception as e:
                logger.info('Waiting for VGW to be deleted...', To_Screen = True)
                time.sleep(10)
                continue
        else:
            logger.error('Failed to delete Virtual Private Gateway for Account: {}, Region: {}'.format(self.ec2.aws.account, self.ec2.region), To_Screen = True)
            raise Exception(e)

class Key_Pair:

    def __init__(self, ec2, id = None):
        self.ec2 = ec2
        self.id = id
        if not self.id:
            return
        self.keypair = self.ec2.client.describe_key_pairs(KeyNames = [self.id])['KeyPairs']
        self.state = None

    def create(self, name):
        if name in [k.get('KeyName') for k in self.ec2.client.describe_key_pairs()['KeyPairs']]:
            return True
        key_file = os.path.join(Global.test_path, '{}.pem'.format(name))
        response = self.ec2.client.create_key_pair(KeyName = name)
        with open(key_file, 'w') as fw:
            fw.write(response['KeyMaterial'])
        os.chmod(key_file, 256)
        return True

    def delete(self):
        if not self.id:
            raise resourceIdMissing('Key Name is missing')

        self.ec2.client.delete_key_pair(KeyName = self.id)

class Tgw:
    def __init__(self, ec2, id=None):
        self.ec2 = ec2
        self.id = id
        if not self.id:
            return
        self.tgw = self.ec2.client.describe_transit_gateways(TransitGatewayIds=[self.id])['TransitGateways'][0]
        self.state = self.tgw.get('State')

    def delete(self):
        for i in range(30):
            try:
                self.ec2.client.delete_transit_gateway(TransitGatewayId=self.id)
                break
            except Exception as e:
                logger.info('Waiting for Transit Gateway to be deleted...', To_Screen = True)
                time.sleep(10)
                continue
        else:
            logger.error('Failed to delete Transit Gateway for Account: {}, Region: {}'.format(self.ec2.aws.account, self.ec2.region), To_Screen = True)
            raise Exception(e)

class Tgw_Vpc_Attachment:
    def __init__(self, ec2, id=None):
        self.ec2 = ec2
        self.id = id
        if not self.id:
            return
        self.tgw_vpc_attachment = self.ec2.client.describe_transit_gateway_vpc_attachments(TransitGatewayAttachmentIds=[self.id])['TransitGatewayVpcAttachments'][0]
        self.state = self.tgw_vpc_attachment.get('State')

    def delete(self):
        for i in range(30):
            try:
                self.ec2.client.delete_transit_gateway_vpc_attachment(TransitGatewayAttachmentId=self.id)
                break
            except Exception as e:
                logger.info('Waiting for Transit Gateway Attachment to be deleted...', To_Screen = True)
                time.sleep(10)
                continue
        else:
            logger.error('Failed to delete Transit Gateway Attachment for Account: {}, Region: {}'.format(self.ec2.aws.account, self.ec2.region), To_Screen = True)
            raise Exception(e)

class Tgw_Route_Table:
    def __init__(self, ec2, id=None):
        self.ec2 = ec2
        self.id = id
        if not self.id:
            return
        self.tgw_route_table = self.ec2.client.describe_transit_gateway_route_tables(TransitGatewayRouteTableIds=[self.id])['TransitGatewayRouteTables'][0]
        self.state = self.tgw_route_table.get('State')

    def delete(self):
        if not self.id:
            raise resourceIdMissing('Route Table is missing')
        self.ec2.client.delete_transit_gateway_route_table(TransitGatewayRouteTableId=self.id)

 
