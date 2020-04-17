import requests
import json
requests.packages.urllib3.disable_warnings() 
import re
from bs4 import BeautifulSoup
import urlparse
from orionsdk import SwisClient
from solardiscovernode import main

user = ''
pwd = ''
npm_server = ''
username = ''
password = ''


swis = SwisClient(npm_server, username, password)

querystring = {"_max_results":"10","_paging":"1","_return_as_object":"1"}


url = "https://10.2.61.100/wapi/v2.7/record:host?zone=ns.ctc&view=Internal"
exturl= "https://10.2.61.100/wapi/v2.7/ipv4address"
networkurl="https://10.2.61.100/wapi/v2.7/network"
response = requests.request("GET", url, auth=(user,pwd),params=querystring,verify=False)
next_page_id = response.json()['next_page_id']

while next_page_id:
	query = {"_page_id":next_page_id}
	query = {"_return_fields":"extattrs,name,ipv4addrs"}
	newresponse = requests.request("GET", url, auth=(user,pwd), params=query,verify=False)
	values= newresponse.text
	jsonv = json.loads(values)
	
	for val in jsonv:
		try:
			#print val['ipv4addrs'][0]['host']+" "+val['ipv4addrs'][0]['ipv4addr']+val['extattrs']['device']['value']
			ipval = val['ipv4addrs'][0]['ipv4addr']
			deviceflag = val['extattrs']['device']['value']
			extquery = {"_return_fields":"network","ip_address":ipval}
			if deviceflag:
				results = swis.query("SELECT Caption AS NodeName, IPAddress FROM Orion.Nodes WHERE IPAddress =@ip ",ip=ipval)
    				if results['results']:
        				print  results['results'][0]['IPAddress']+"    ...."+"Already Discovered"
    				else:
        				print "Starting Discovery"

					extresponse = requests.request("GET", exturl, auth=(user,pwd), params=extquery,verify=False)
					extvalues= extresponse.text
					extjson = json.loads(extvalues)
                                	netval = extjson[0]['network'] 
					networkquery = {"_return_fields":"extattrs","network":netval}
					netresponse = requests.request("GET", networkurl, auth=(user,pwd), params=networkquery,verify=False)
					netvalues = netresponse.text
					netjson = json.loads(netvalues)
					sitename= netjson[0]['extattrs']['Site Name']['value']
					province= netjson[0]['extattrs']['Province/State']['value']
                                	sbu = netjson[0]['extattrs']['sbu']['value']
					pci = netjson[0]['extattrs']['pci']['value']
					ctrel_code = netjson[0]['extattrs']['CTREL Code']['value']
					main(ipval,ctrel_code,pci,province,sbu,sitename)	
					print sitename+" "+province+" "+sbu+" "+pci+" "+ctrel_code
		except KeyError:
			#print val['ipv4addrs'][0]['host']+" "+val['ipv4addrs'][0]['ipv4addr']
			pass
		try:
                	next_page_id = newresponse.json()['next_page_id']
        	except Exception:
                	next_page_id = 0

