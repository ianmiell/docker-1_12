#!/bin/bash
while true 
do
	VBoxManage list runningvms | grep xenial | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
	if [[ $(VBoxManage list vms | grep xenial | wc -l | xargs) == '0' ]]
	then
		break
	else
		ps -ef | grep virtualbox | grep xenial | awk '{print $2}' | xargs kill
		sleep 10
	fi
done
