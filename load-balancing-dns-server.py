#!/usr/bin/python

from twisted.internet import reactor, defer
from twisted.internet import task
from twisted.names import dns, error, server
from twisted.web import http
import random
import time;

#config
http_port   = 80
password    = 'kkkkkkkk'

ip_list     = []
ip_ttl      = {}

timeout     = 60 #1 min

class DynamicResolver(object):
	def _doDynamicResponse(self, query):
		idx = random.randint(0,len(ip_list)-1 )
		ip  = ip_list[idx]

		print (ip , query.name.name)

		payload = dns.Record_A( ip , ttl = 0)

		answer  = dns.RRHeader(
			name=query.name.name ,
			payload=payload,
			type=dns.A,
			ttl = 0 ,
		)

		answers    = [answer]
		authority  = []
		additional = []
		return answers, authority, additional

	def query(self, query, timeout=None):
		if query.type == dns.A and len(ip_list)> 0 :
			return defer.succeed(self._doDynamicResponse(query))
		else:
			return defer.fail(error.DomainError())



class MyRequestHandler(http.Request):
	resources={
		'/':"<h1>DNS Load Balancing</h1><p> /add-ip?key=????????<p><p> current : <p>",
		}
	def process(self):
		self.setHeader('Content-Type','text/html')
		if self.path == '/':
			self.write( "%s%d" % (self.resources[self.path] , len(ip_list) ) )
		elif self.path == '/add-ip' : 
			key = self.args.get('key')
			if key[0] == password :
				client = self.getClientAddress().host
				if(not ip_ttl.has_key(client)):
					ip_list.append(client)
				ip_ttl[client] = time.time()
				self.write('Add ok!')
			else:
				self.write('Add error!')
		else:
			self.setResponseCode(http.NOT_FOUND)
			self.write("<h1>Not Found</h1>Sorry, no such source")
		self.finish()

class MyHTTP(http.HTTPChannel):
	requestFactory=MyRequestHandler

class MyHTTPFactory(http.HTTPFactory):
	def buildProtocol(self,addr):
		return MyHTTP()


def CheckTimeout():
	num = len(ip_list)
	for idx in range( num-1 , -1 , -1) :
		ip  = ip_list[idx]
		if time.time() - ip_ttl[ip] > timeout :
			del ip_ttl[ip]
			del ip_list[idx]

def main():

	factory = server.DNSServerFactory(
		clients=[DynamicResolver()]
	)
	protocol = dns.DNSDatagramProtocol(controller=factory)
	reactor.listenUDP(53, protocol)

	reactor.listenTCP(http_port,MyHTTPFactory())


	l = task.LoopingCall(CheckTimeout)
	l.start(10.0)

	reactor.run()



if __name__ == '__main__':
	raise SystemExit(main())
