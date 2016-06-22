"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docker_1_12(ShutItModule):


	def build(self, shutit):
		# Some useful API calls for reference. See shutit's docs for more info and options:
		#
		# ISSUING BASH COMMANDS
		# shutit.send(send,expect=<default>) - Send a command, wait for expect (string or compiled regexp)
		#                                      to be seen before continuing. By default this is managed
		#                                      by ShutIt with shell prompts.
		# shutit.multisend(send,send_dict)   - Send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.send_and_get_output(send)   - Returns the output of the sent command
		# shutit.send_and_match_output(send, matches) 
		#                                    - Returns True if any lines in output match any of 
		#                                      the regexp strings in the matches list
		# shutit.send_until(send,regexps)    - Send command over and over until one of the regexps seen in the output.
		# shutit.run_script(script)          - Run the passed-in string as a script
		# shutit.install(package)            - Install a package
		# shutit.remove(package)             - Remove a package
		# shutit.login(user='root', command='su -')
		#                                    - Log user in with given command, and set up prompt and expects.
		#                                      Use this if your env (or more specifically, prompt) changes at all,
		#                                      eg reboot, bash, ssh
		# shutit.logout(command='exit')      - Clean up from a login.
		# 
		# COMMAND HELPER FUNCTIONS
		# shutit.add_to_bashrc(line)         - Add a line to bashrc
		# shutit.get_url(fname, locations)   - Get a file via url from locations specified in a list
		# shutit.get_ip_address()            - Returns the ip address of the target
		# shutit.command_available(command)  - Returns true if the command is available to run
		#
		# LOGGING AND DEBUG
		# shutit.log(msg,add_final_message=False) -
		#                                      Send a message to the log. add_final_message adds message to
		#                                      output at end of build
		# shutit.pause_point(msg='')         - Give control of the terminal to the user
		# shutit.step_through(msg='')        - Give control to the user and allow them to step through commands
		#
		# SENDING FILES/TEXT
		# shutit.send_file(path, contents)   - Send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath)
		#                                    - Send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath)
		#                                    - Send directory and contents to path on the target
		# shutit.insert_text(text, fname, pattern)
		#                                    - Insert text into file fname after the first occurrence of 
		#                                      regexp pattern.
		# shutit.delete_text(text, fname, pattern)
		#                                    - Delete text from file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.replace_text(text, fname, pattern)
		#                                    - Replace text from file fname after the first occurrence of
		#                                      regexp pattern.
		# ENVIRONMENT QUERYING
		# shutit.host_file_exists(filename, directory=False)
		#                                    - Returns True if file exists on host
		# shutit.file_exists(filename, directory=False)
		#                                    - Returns True if file exists on target
		# shutit.user_exists(user)           - Returns True if the user exists on the target
		# shutit.package_installed(package)  - Returns True if the package exists on the target
		# shutit.set_password(password, user='')
		#                                    - Set password for a given user on target
		#
		# USER INTERACTION
		# shutit.get_input(msg,default,valid[],boolean?,ispass?)
		#                                    - Get input from user and return output
		# shutit.fail(msg)                   - Fail the program and exit with status 1
		# 
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
		shutit.send('dockerd &')

		# Log into docker
		shutit.multisend('docker login',{'sername':shutit.cfg[self.module_id]['docker_username'],'assword':shutit.cfg[self.module_id]['docker_password']})

#DOCKERFILE 
#HEALTHCHECK --interval=5m --grace=20s --timeout=3s --exit-on-unhealthy CMD curl -f http://localhost/
		shutit.send('mkdir hello && cd hello')
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
HEALTHCHECK --interval=10s --timeout=3s --retries=1 CMD curl localhost:8080
CMD ["python", "hello.py"]''')
		shutit.send('docker build -t imiell/hello .')
		shutit.send('docker push imiell/hello')

		shutit.send('docker version',note='Confirm version of docker as 1.12')
#Usage:	docker swarm COMMAND
#  join        Join a Swarm as a node and/or manager
#  update      Update the Swarm
#  leave       Leave a Swarm
		shutit.send('docker swarm init',note='Initialise a swarm')
		shutit.send('docker swarm inspect',note='Inspect the swarm')

#Usage:	docker node COMMAND
#  accept      Accept a node in the swarm
#  demote      Demote a node from manager in the swarm
#  inspect     Inspect a node in the swarm
#  promote     Promote a node to a manager in the swarm
#  rm          Remove a node from the swarm
#  tasks       List tasks running on a node
#  update      Update a node
		shutit.send('docker node ls',note='List the nodes in the swarm')

#Usage:	docker service COMMAND
#  tasks       List the tasks of a service
#  rm          Remove a service
#  scale       Scale one or multiple services
#  update      Update a service
		shutit.send('docker service create imiell/hello',note='Create a simple echo service')
		shutit.send('docker service ls',note='List the services in the swarm')
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
		shutit.get_config(self.module_id, 'docker_username',secret=True)
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

