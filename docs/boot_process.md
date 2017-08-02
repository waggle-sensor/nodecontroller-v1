# First Boot
* /aafirstboot is executed (resize data partition to fill the disk)
* reboot

# Subsequent Boots
* waggle-core target is started
	- Services: init, heartbeat, reverse-tunel, wwan, epoch
* waggle-init: /root/init_finished removed at start
* waggle-init: node ID created
* waggle-init: hostname set
* waggle-init: eMMC (re)created if eMMC exists and /root/do_recovery exists
* waggle-init: /root/do_recovery removed if eMMC created successfully
* waggle-init: /root/init_finished created at end

# Flags
* /root/init_finished
	- created by init service
	- deleted by init service
	- used by heartbeat service to avoid turning off the heartbeat if
	  disk recovery is in process
* /root/do_recovery
	- created upon image creation (can be manually added)
	- deleted by init service
	- signals the init service to recover the other disk

