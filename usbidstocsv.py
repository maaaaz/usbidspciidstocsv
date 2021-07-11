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
input_grp.add_argument('-i', '--input-file', help='Input usb.ids file (default ./usbids/usb.ids)', default=path.abspath(path.join(os.getcwd(), './usbids/usb.ids')))

output_grp = parser.add_argument_group('Output parameters')
output_grp.add_argument('-o', '--output-file-vdi', help='Output csv file of vendors, devices and interfaces (default ./usb.ids_vdi.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_vdi.csv')))
#output_grp.add_argument('-c', '--output-file-csp', help='Output csv file of classes, subclasses and protocols (default ./usb.ids_csp.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_csp.csv')))
#output_grp.add_argument('-a', '--output-file-actt', help='Output csv file of audio class terminal types (default ./usb.ids_actt.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_actt.csv')))
#output_grp.add_argument('-b', '--output-file-hdt', help='Output csv file of HID descriptor types (default ./usb.ids_hdt.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_hdt.csv')))
#output_grp.add_argument('-e', '--output-file-hdit', help='Output csv file of HID descriptor items types (default ./usb.ids_hdit.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_hdit.csv')))
#output_grp.add_argument('-p', '--output-file-pdbt', help='Output csv file of physical descriptor bias types (default ./usb.ids_pdbt.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_pdbt.csv')))
#output_grp.add_argument('-t', '--output-file-pdit', help='Output csv file of physical descriptor items types (default ./usb.ids_pdit.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_pdit.csv')))
#output_grp.add_argument('-u', '--output-file-hu', help='Output csv file of HID usages (default ./usb.ids_hu.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_hu.csv')))
#output_grp.add_argument('-l', '--output-file-lang', help='Output csv file of languages (default ./usb.ids_lang.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_lang.csv')))
#output_grp.add_argument('-k', '--output-file-hcc', help='Output csv file of HID country codes (default ./usb.ids_hcc.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_hcc.csv')))
#output_grp.add_argument('-v', '--output-file-vctt', help='Output csv file of video class terminal types (default ./usb.ids_vctt.csv)', default=path.abspath(path.join(os.getcwd(), './usb.ids_vctt.csv')))

output_grp.add_argument('-d', '--delimiter', help = 'CSV output delimiter (default ";"). Ex: -d ","', default = ';')

def parse(opts):
    vdi = {}
    vdi_start = "# Vendors"
    vdi_stop = "# List of known device classes"
    vdi_block_in = False
    
    p_vendor_vendor_name = re.compile("(?P<vid>[0-9a-fA-F]*)  (?P<vid_name>.*)$")
    p_vendor_device_name = re.compile("\t(?P<did>[0-9a-fA-F]*)  (?P<did_name>.*)$")
    
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
                    vdi[vid]['devices'][device_name.group('did').upper()] = device_name.group('did_name')
    
    return vdi

def generate_csv(results, opts):
    keys = ['VID_PID', 'VID', 'VID_name', 'PID', 'PID_name']
    
    
    if results:
        with open(opts.output_file_vdi, mode='w', encoding='utf-8') as fd_output:
            spamwriter = csv.writer(fd_output, delimiter=opts.delimiter, quoting=csv.QUOTE_ALL, lineterminator='\n')
            spamwriter.writerow(keys)
            
            counter = 0
            for vid in results.keys():
                item = results[vid]
                vid_name = item['name'] if 'name' in item else ''
                output_line = ['', vid, vid_name, '', '']
                
                if 'devices' in item:
                    for did, did_name in item['devices'].items():
                        output_line = ["VID_%s&PID_%s" % (vid, did), vid, vid_name, did, did_name]
                        spamwriter.writerow(output_line)
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