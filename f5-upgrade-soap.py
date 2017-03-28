#! /usr/bin/env python
# Module imports
# JSON module for formatting
# Import required Modules
# Upgrade sequence
    # Login to device (SOAP API)
        # REQUIRES
            # Hostname/IP address
            # username
            # password
    # Create and download UCS archive
        # REQUIRES
            # Login
        # Provides
            # UCS archive file
    # Upload ISO and hotfix
        # REQUIRES
            # Login
            # File name and path. Must be in same name format as provided by F5
            # Destination location? Set default to /shared/images
    # Check disk space is > 5GB
        # REQUIRES
            # Login
        # Provides
            # True/False boolean
    # Install ISO image to new HD
        # REQUIRES
            # Login
            # Free space = True
            # Image name
    # Activate new HD and reboot
        # REQUIRES
            # Login
            # Volume name
    # Install Hotfix
        # REQUIRES
            # Login
            # Free space = True
            # image name

import json
# Time module for filename generation
import time
# Argparse module needed for the parsing of arguments
import argparse
# Decimal module for rounding digits to human readable form
from decimal import *
# BIGSUDS module for integration to F5
import bigsuds
# Sys module which is needed to leverage various features, specifically arguments.
import sys
# Base64 module is used during file transfers for file decode/encode.
import base64
# Variables
args = sys.argv
parser = argparse.ArgumentParser(description='This script does xyz...')
#parser.add_argument('-h', '--hostname', help = 'Defines the BIG-IP Hostname(must be resolvable) or IP Address')
hostname = '10.1.10.157'
username = 'admin'
password = 'admin'
b = bigsuds.BIGIP(hostname = hostname, username = username, password = password)
# Used to deterimin if a F5 device is connected or not.
f5_connected = False
f5sw = b.System.SoftwareManagement
f5disks = b.System.Disk
logical_disks = f5disks.get_list_of_logical_disks()
softwarestatus = f5sw.get_all_software_status()
# Connect to F5
def connect_to_f5():
    global f5_connected
    if b: f5_connected = True
    return;
# Identify the name of the install volume
def identify_tgt_install_volume():
    tgt_install_volume = "HD" + str(Decimal(softwarestatus[-1]['installation_id']['install_volume'].strip('HD')) + Decimal('0.1'))
    return tgt_install_volume;
# Install image
def image_installation():
    f5sw.install_software_image_v2(
    volume=identify_tgt_install_volume(),
    product='BIGIP',
    version='11.6.1',
    build='0.0.317',
    create_volume=True,
    reboot=False,
    retry=False
    )
# Control image installation based on F5 connection state
def start_image_install():
    successfull_connection = "F5 {} connected, starting installation...".format(hostname)
    failed_connection = "F5 {} not connected, initiating connection...".format(hostname)
    successfull_install = "Installation to {} has completed successfully. \nSoftware status: \n{}".format(hostname, json.dumps(f5sw.get_all_software_status(), indent=4))
    failed_install = "Installation to {} failed, please check the device log files for details. \nSoftware status: \n{}".format(hostname, json.dumps(f5sw.get_all_software_status(), indent=4))
    if f5_connected:
        print successfull_connection
        if image_installation():
            print successfull_install
        else:
            print failed_install
    else:
        print failed_connection
        if connect_to_f5():
            print successfull_connection
            if image_installation():
                print successfull_install
            else:
                print failed_install
        else:
            print failed_connection

    return;
# Remove a volume
def delete_volume(hostname):
    f5sw.delete_volume(volume)
    return;
# Disk free space check, outputs logical disk name and free space in GB
def disk_5GB_free():
    for disk in logical_disks:
        freespace = f5disks.get_logical_disk_space_free([disk])
        if (freespace[0]/1000 >= 5): EnoughGBfree = True # Diskfreestatement = "Disk check is GOOD as >= 5GB free: Logical disk '{}' has {}GB free".format(disk.get('name'),freespace[0]/1000)
        else: EnoughGBfree = False # Diskfreestatement = "WARNING disk check failed as <= 5GB free: Logical disk '{}' has {}GB free, you should not proceed with install".format(disk.get('name'),freespace[0]/1000)
    return EnoughGBfree;
# Generate a unique filename
def generate_configname(hostname):
    """
    This function will generate a file name based on the BIG-IP
    hostname and the current date and time in the format:
    hostname_dd-mm-yyyy_hh-mm-ss.ucs.
    It requires the hostname of the F5 target as an input.
        params: hostname(str)
        return: Provides 'filename' variable in string format."""
    now = time.strftime("_%d-%m-%y_%H.%M.%S")
    configname = '{}{}.ucs'.format(hostname,now)
    return configname;
# Create UCS backup
def save_configuration():
    config_name = generate_configname(hostname)
    save_config = b.System.ConfigSync.save_configuration(config_name, 'SAVE_FULL')
    list_of_archives = b.System.ConfigSync.get_configuration_list()
    # def print_archive_files():
    #     for archives in list_of_archives[0:]: print """Archive file: '{}', created on: {}""".format(files['file_name'],files['file_datetime'])
    #     return;
    return "The file from THIS save action is called: '{}'".format(config_name),"Here is a full list of archives on the device:",list_of_archives;
# Create UCS backup and download to working directory (./) of script.
def save_and_download_configuration():
    chunk_size = 64 * 1024
    file_offset = 0
    write_continue = 1
    #instantiate connection to bigip
    b
    #first save config file on bigip device
    config_name = generate_configname(hostname)
    save_config = b.System.ConfigSync.save_configuration(config_name, 'SAVE_FULL')
    # list_of_archives = b.System.ConfigSync.get_configuration_list()
    #open target file for writing
    f = open('./' + config_name,'wb') # <---- This line
    #download data to file
    while write_continue == 1:
        temp_config = b.System.ConfigSync.download_configuration(config_name,chunk_size,file_offset)
        file_info = temp_config['return']
        f.write(base64.b64decode(file_info['file_data'])) # <---- And this line

        #detect EOF
        if file_info['chain_type']  == 'FILE_LAST' or file_info['chain_type'] == 'FILE_FIRST_AND_LAST':
            write_continue = 0

        #set offset
        file_offset = file_offset + chunk_size

        #track download progress
        print str(file_offset) + " bytes written"

        #DEBUG
        print file_info['chain_type']
    print "File {} should now have been downloaded to the working directory of script, please check to ensure it is present and test it by uploading it to the F5 and checking it's details.".format(f.name)
    #cleanup
    f.close()
    return;
# Function tests
connect_to_f5()
f5_connected
generate_configname(hostname)
disk_5GB_free()
tgt_install_volume = identify_tgt_install_volume()
tgt_install_volume
save_and_download_configuration()
save_configuration()

# General Testing

# Retrieve software status on BIG-IP Device in standard output
f5sw.get_all_software_status()

# Post connection Variables
