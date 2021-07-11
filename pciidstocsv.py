#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of usbidspciidstocsv.
#
# Copyright (C) 2021, Thomas Debize <tdebize at mail.com>
# All rights reserved.
#
# usbidspciidstocsv is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# usbidspciidstocsv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with usbidspciidstocsv.  If not, see <http://www.gnu.org/licenses/>.

from os import path
from concurrent import futures
import os
import re
import csv
import argparse
import functools

# Script version
VERSION = '1.0'

# Options definition
parser = argparse.ArgumentParser(description="version: " + VERSION)

input_grp = parser.add_argument_group('Input parameters')
input_grp.add_argument('-i', '--input-file', help='Input usb.ids file (default ./pciids/pci.ids)', default=path.abspath(path.join(os.getcwd(), './pciids/pci.ids')))

output_grp = parser.add_argument_group('Output parameters')
output_grp.add_argument('-o', '--output-file-vdi', help='Output csv file of vendors, devices and interfaces (default ./pci.ids_vdi.csv)', default=path.abspath(path.join(os.getcwd(), './pci.ids_vdi.csv')))
#output_grp.add_argument('-c', '--output-file-csp', help='Output csv file of classes, subclasses and programming interfaces (default ./pci.ids_csp.csv)', default=path.abspath(path.join(os.getcwd(), './pci.ids_csp.csv')))

output_grp.add_argument('-d', '--delimiter', help = 'CSV output delimiter (default ";"). Ex: -d ","', default = ';')

def parse(opts):
    vdi = {}
    vdi_start = "# Vendors"
    vdi_stop = "# List of known device classes"
    vdi_block_in = False
    
    p_vendor_vendor_name = re.compile("(?P<vid>[0-9a-fA-F]*)  (?P<vid_name>.*)$")
    p_vendor_device_name = re.compile("\t(?P<did>[0-9a-fA-F]*)  (?P<did_name>.*)$")
    p_subvendor = re.compile("\t\t(?P<svid>[0-9a-fA-F]*) (?P<svdid>[0-9a-fA-F]*)  (?P<svdid_name>.*)$")
    
    with open(opts.input_file, mode='r', encoding="unicode_escape") as fd_input:
        for line in fd_input:
            
            # VDI block
            if line.startswith(vdi_start):
                vdi_block_in = True
            
            if line.startswith(vdi_stop):
                vdi_block_in = False
            
            if vdi_block_in:
                vendor_name = p_vendor_vendor_name.match(line)
                if vendor_name:
                    vid = vendor_name.group('vid').upper()
                    if not(vid) in vdi:
                        vdi[vid] = {'name': vendor_name.group('vid_name')}
                
                device_name = p_vendor_device_name.match(line)
                if device_name:
                    if not('devices') in vdi[vid]:
                        vdi[vid]['devices'] = {}
                    
                    did = device_name.group('did').upper()
                    did_name = device_name.group('did_name')
                    vdi[vid]['devices'][did] = {'name' : did_name}
                
                subvendor = p_subvendor.match(line)
                if subvendor:
                    if not('subdevices') in vdi[vid]['devices'][did]:
                        vdi[vid]['devices'][did]['subdevices'] = {}
                    
                    svid = subvendor.group('svid').upper()
                    svdid = subvendor.group('svdid').upper()
                    svdid_name = subvendor.group('svdid_name')
                    vdi[vid]['devices'][did]['subdevices']['%s%s' % (svdid, svid)] = svdid_name
                   
    
    return vdi

def generate_csv(results, opts):
    keys = ['VEN_DEV_SUBSYS', 'VEN', 'VEN_name', 'DEV', 'DEV_name', 'SUBSYS', 'SUBSYS_name']
    
    
    if results:
        with open(opts.output_file_vdi, mode='w', encoding='utf-8') as fd_output:
            spamwriter = csv.writer(fd_output, delimiter=opts.delimiter, quoting=csv.QUOTE_ALL, lineterminator='\n')
            spamwriter.writerow(keys)
            
            counter = 0
            for vid in results.keys():
                item = results[vid]
                vid_name = item['name'] if 'name' in item else ''
                output_line = ['', vid, vid_name, '', '', '', '']
                
                if 'devices' in item:
                    for did, item in item['devices'].items():
                        did_name = item['name'] if 'name' in item else ''
                        output_line = ["VEN_%s&DEV_%s" % (vid, did), vid, vid_name, did, did_name, '', '']
                        spamwriter.writerow(output_line)
                        counter = counter + 1
                        
                        if 'subdevices' in item:
                            for svdid, svdid_name in item['subdevices'].items():
                                output_line = ["VEN_%s&DEV_%s&SUBSYS_%s" % (vid, did, svdid), vid, vid_name, did, did_name, svdid, svdid_name]
                                spamwriter.writerow(output_line)
                                counter = counter + 1
                    
                else:
                    spamwriter.writerow(output_line)
                    counter = counter + 1
            
        print("[+] %s ids written to '%s'" % (counter, opts.output_file_vdi))
    return

def main():
    """
        Dat main
    """
    options = parser.parse_args()
    
    options.input_file = path.abspath(path.join(os.getcwd(), options.input_file)) if options.input_file else options.input_file
    options.output_file_vdi = path.abspath(path.join(os.getcwd(), options.output_file_vdi)) if options.output_file_vdi else options.output_file_vdi
    
    results = parse(options)
    generate_csv(results, options)
    
    return

if __name__ == "__main__" :
    main()