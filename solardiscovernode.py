from __future__ import print_function
import re
import requests
from orionsdk import SwisClient
import time

def main(ip,ctrel,pci,province,sbu,sitename):
    npm_server = ''
    username = ''
    password = ''

    target_node_ip = ip
    snmpv3_credential_id = 6
    orion_engine_id = 1

    swis = SwisClient(npm_server, username, password)
    print("Add an SNMP v3 node:")

    corePluginContext = {
    	'BulkList': [{'Address': target_node_ip}],
    	'Credentials': [
    		{
    			'CredentialID': snmpv3_credential_id,
    			'Order': 1
    		}
    	],
    	'WmiRetriesCount': 0,
    	'WmiRetryIntervalMiliseconds': 1000
    }

    corePluginConfig = swis.invoke('Orion.Discovery', 'CreateCorePluginConfiguration', corePluginContext)

    discoveryProfile = {
    	'Name': 'API discovery',
    	'EngineID': orion_engine_id,
    	'JobTimeoutSeconds': 3600,
    	'SearchTimeoutMiliseconds': 5000,
    	'SnmpTimeoutMiliseconds': 5000,
    	'SnmpRetries': 2,
    	'RepeatIntervalMiliseconds': 1800,
    	'SnmpPort': 161,
    	'HopCount': 0,
    	'PreferredSnmpVersion': 'SNMP3',
    	'DisableIcmp': False,
    	'AllowDuplicateNodes': False,
    	'IsAutoImport': True,
    	'IsHidden': True,
    	'PluginConfigurations': [{'PluginConfigurationItem': corePluginConfig}]
    }

    print("Running discovery...")
    discoveryProfileID = swis.invoke('Orion.Discovery', 'StartDiscovery', discoveryProfile)
    print("Returned discovery profile id {}".format(discoveryProfileID))

    running = True
    while running:
	try:
        	query = "SELECT Status FROM Orion.DiscoveryProfiles WHERE ProfileID = " + str(discoveryProfileID)
        	status = swis.query(query)['results'][0]['Status']
		print("##")
	except:
		running = False
    print('Done with discovery')

    batchresults = swis.query("SELECT Result, ResultDescription, ErrorMessage, BatchID FROM Orion.DiscoveryLogs WHERE ProfileID=@id", id=discoveryProfileID)
    batchid= batchresults['results'][0]['BatchID']
    nodeidresults = swis.query("SELECT DisplayName,NetObjectID FROM Orion.DiscoveryLogItems WHERE BatchID=@id", id=batchid)
    netobjectid = nodeidresults['results'][0]['NetObjectID']
    nodeid = netobjectid.split(':')[1]
    print(nodeid)

    #enablehardwarehealth
    hardwarehealth=swis.invoke('Orion.HardwareHealth.HardwareInfoBase', 'EnableHardwareHealth', netobjectid,9)
    #add pollers
    pollers_enabled = {
	'N.Topology_Vlans.SNMP.VtpVlan': True,
	'N.Topology_Layer2.SNMP.Dot1dTpFdbNoVLANs': True,
	'N.Topology_CDP.SNMP.cdpCacheTable': True,
	'N.Topology_STP.SNMP.Dot1dStp':True,
	'N.Topology_PortsMap.SNMP.Dot1dBaseNoVLANs': True,
	'N.Topology_Layer3.SNMP.ipNetToMedia':True,
	'N.VRFRouting.SNMP.MPLSVPNStandard': True,
	
    }

    pollers = []
    for k in pollers_enabled:
        pollers.append(
            {
                'PollerType': k,
                'NetObject': 'N:' + nodeid,
                'NetObjectType': 'N',
                'NetObjectID': nodeid,
                'Enabled': pollers_enabled[k]
            }
        )

    for poller in pollers:
        print("  Adding poller type: {} with status {}... ".format(poller['PollerType'], poller['Enabled']), end="")
        response = swis.create('Orion.Pollers', **poller)
        print("DONE!")
    
    #update custom properties
    customresults = swis.query("SELECT Uri FROM Orion.Nodes WHERE NodeID=@id",id=nodeid)
    uri = customresults['results'][0]['Uri']

    #swis.update(uri + '/CustomProperties', City='Brampton')
    #swis.update(uri + '/CustomProperties', Comments='Test Device')
    swis.update(uri + '/CustomProperties', CTREL_Code=ctrel)
    swis.update(uri + '/CustomProperties', PCI=pci)
    #swis.update(uri + '/CustomProperties', Postal_Code='L7A4B4')
    swis.update(uri + '/CustomProperties', Province=province)
    swis.update(uri + '/CustomProperties', SBU=sbu)
    #swis.update(uri + '/CustomProperties', Site_Contact='Anesh')
    #swis.update(uri + '/CustomProperties', Site_Contact_Number='666-666-666')
    #swis.update(uri + '/CustomProperties', Site_ID='666')
    swis.update(uri + '/CustomProperties', Site_Name=sitename)
    #swis.update(uri + '/CustomProperties', Site_Type='PROD')
    #swis.update(uri + '/CustomProperties', Street_Address='AJ Distrubution')
    swis.update(uri + '/CustomProperties', Support_Team='Corp Network')

    obj = swis.read(uri + '/CustomProperties')
    print (obj)

requests.packages.urllib3.disable_warnings()

if __name__ == '__main__':
    main(ip,ctrel,pci,province,sbu,sitename)
