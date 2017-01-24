wait_for_init() {
  systemctl status --no-pager waggle-init > /dev/null
  while [ $? -eq 0 ]; do
    sleep 2
    systemctl status --no-pager waggle-init > /dev/null
  done
}
