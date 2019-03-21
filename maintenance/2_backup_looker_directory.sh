#!/bin/bash
#########################
#
# Backup Looker
#
#########################

# Directories to backup
bkdir1="/home/looker/looker/"

# Backup Destination
destination="/home/looker/scripts"

# Create archive name
DATE=$(date +"%Y-%m-%d")
version=$1
archive_file="${DATE}_${HOSTNAME}_LOOKER_v${version}.tgz"

# Print Status
echo "Backing up $bkdir1 to $destination/$archive_file"

# Backup the files using tar
tar czf $destination/$archive_file $bkdir1

# Print end status message
echo
echo "Backup Complete"
date

# Long listing of files in $destination to check file sizes
ls -lh $destination
