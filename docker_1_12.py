from shutit_module import ShutItModule
import time

class docker_1_12(ShutItModule):

	def build(self, shutit):
		shutit.send('rm -rf /tmp/docker1_12')
		box = shutit.send_and_get_output('vagrant box list 2>/dev/null | grep ubuntu/xenial64')
		if box == '':
			shutit.send('vagrant box add --provider virtualbox https://atlas.hashicorp.com/ubuntu/boxes/xenial64',note='Download the ubuntu vagrant box')
		# Switch check exit off as there are bugs in some versions of Vagrant
		shutit.send('mkdir /tmp/docker1_12 && cd /tmp/docker1_12 && vagrant init ubuntu/xenial64 && vagrant up',check_exit=False,note='vagrant up')
		running = shutit.send_and_get_output('vagrant status 2> /dev/null | grep default | grep running | wc -l | xargs')
		if running != '1':
			shutit.fail('vagrant box not started ok')
		shutit.login(command='vagrant ssh',note='Log into the VM')
		shutit.login(user='root',command='sudo su - root')
		shutit.send('curl -sSL -O https://experimental.docker.com/builds/Linux/x86_64/docker-latest.tgz && tar -zxvf docker-latest.tgz && cd docker')
		shutit.send('mv * /usr/bin')
		shutit.send('cd')
		shutit.send('dockerd > /dev/null 2>&1 &')

		time.sleep(5)
		shutit.send('docker version',note='Confirm version of docker as 1.12')

		# Log into docker
		shutit.send('docker login',expect='sername')
		shutit.send(shutit.cfg[self.module_id]['docker_username'],expect='assword')
		shutit.send(shutit.cfg[self.module_id]['docker_password'])

		shutit.send('mkdir hello')
		shutit.send('cd hello')
		shutit.send_file('hello.py','''#!/usr/bin/env python
import os
import socket
import SimpleHTTPServer
import SocketServer
try:
    PORT = int(os.environ.get('PORT', '80'))
except Exception:
    PORT = 80
if __name__ == "__main__":
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("0.0.0.0", PORT), Handler)
    with open('index.html', 'w') as index:
        index.write(u"""
           <h1 style="text-align: center">Hello World!!!</h1>
           <h2 style="text-align: center">My IP address is %s</h2>
           <h3 style="text-align: center">Running on port %s</h3>
           """ % (
             socket.gethostbyname(socket.gethostname()), PORT
         ))

    print "Serving at 0.0.0.0:%s" % PORT
    httpd.serve_forever()''')
		shutit.send_file('Dockerfile','''
FROM alpine:3.2
RUN apk add --update python && rm -rf /var/cache/apk/*
RUN mkdir /www
ADD hello.py /www/
RUN chmod +x /www/hello.py
WORKDIR /www
HEALTHCHECK --interval=10s --timeout=3s --retries=1 CMD wget -O /tmp/wget localhost:80
EXPOSE 80
CMD ["python", "hello.py"]''')
		shutit.send('docker build -t imiell/hello .')
		#shutit.send('docker push imiell/hello')

		#Usage:	docker swarm COMMAND
		#  join        Join a Swarm as a node and/or manager
		#  update      Update the Swarm
		#  leave       Leave a Swarm
		shutit.send('docker swarm init',note='Initialise a swarm')
		shutit.pause_point('')
		#shutit.send('docker swarm inspect',note='Inspect the swarm')

		#Usage:	docker node COMMAND
		shutit.send('docker node ls',note='List the nodes in the swarm')
		#shutit.send('docker node inspect ubuntu-xenial',note='Inspect the node')

		#Usage:	docker service COMMAND
		shutit.send('docker service create imiell/hello',note='Create a simple hello service')
		shutit.send('docker service ls',note='List the services in the swarm')
		service_id = shutit.send_and_get_output("""docker service ls | tail -1 | awk '{print $1}'""")
		#shutit.send("""docker service inspect """ + service_id,note='Inspect the service')
		shutit.send("""docker service scale """ + service_id + """=2""",note='Scale the service to two containers')
		#shutit.send("""docker service inspect """ + service_id,note='Inspect the service, note it now has 2 replicas')
		shutit.send('docker node tasks self',note='List the tasks running on this node.')
		shutit.send('docker node update --availability=pause ubuntu-xenial',note='')
		shutit.send('docker node tasks self',note='')
		shutit.send('docker node update --availability=active ubuntu-xenial',note='')
		shutit.send('docker service rm ' + service_id,note='Remove the hello service')
		shutit.send('docker service ls',note='No services remain')

# TODO: (experimental) New stack and deploy commands to manage and deploy multi-service applications #23522
		shutit.pause_point('')
		shutit.logout()
		return True

	def get_config(self, shutit):
		# CONFIGURATION
		# shutit.get_config(module_id,option,default=None,boolean=False)
		#                                    - Get configuration value, boolean indicates whether the item is 
		#                                      a boolean type, eg get the config with:
		# shutit.get_config(self.module_id, 'myconfig', default='a value')
		#                                      and reference in your code with:
		# shutit.cfg[self.module_id]['myconfig']
		shutit.get_config(self.module_id, 'docker_username',default='imiell')
		shutit.get_config(self.module_id, 'docker_password',secret=True)
		return True

	def test(self, shutit):
		# For test cycle part of the ShutIt build.
		return True

	def finalize(self, shutit):
		# Any cleanup required at the end.
		return True
	
	def is_installed(self, shutit):
		return False


def module():
	return docker_1_12(
		'shutit.docker_1_12.docker_1_12', 1113159394.00,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['tk.shutit.vagrant.vagrant.vagrant']
	)

