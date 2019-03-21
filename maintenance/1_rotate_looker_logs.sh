#!/bin/bash
#file: 1_rotate_looker_logs.sh

#description - Compresses the Looker application  logs older than 5 days and removes them after 92.

#usage: $ ./1_rotate_looker_logs.sh
# This file can be run from any location.

# **** Gzip all log files older than 5 days without re-zipping *** 
  find /home/looker/looker/log/*.log.* -mtime +5 -exec ls {} \; | sed 's/^/"/' | sed 's/$/"/' | grep -v ".gz" | grep -v ".tgz" | xargs gzip -f 2>/dev/null

# delete log files older than 92 days
  find /home/looker/looker/log/*.log.* -mtime +92 -exec ls {} \; | sed 's/^/"/' | sed 's/$/"/' | xargs rm -f
