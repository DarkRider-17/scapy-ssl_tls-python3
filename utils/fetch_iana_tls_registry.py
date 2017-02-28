#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# Author : tintinweb@oststrom.com <github.com/tintinweb>
"""
Create python dictionary from IANA only TLS registry

requires Python 2.7 (xml.etree.ElementTree)
"""

from __future__ import print_function
import sys
import os
import datetime
import urllib2
import re
import xml.etree.ElementTree as ET

DEBUG = False
URL_IANA_DEFS = ("https://www.iana.org/assignments/tls-parameters/tls-parameters.xml",
                 "https://www.iana.org/assignments/comp-meth-ids/comp-meth-ids.xml",
                 "https://www.iana.org/assignments/tls-extensiontype-values/tls-extensiontype-values.xml")

if sys.version_info[0] * 10 + sys.version_info[1] < 27:
    raise SystemExit('This utility requires Python 2.7 or higher.')


def post_process(title, d):
    norm_d = {}
    for k, v in d.items():
        if title == "APPLICATION_LAYER_PROTOCOL_NEGOTIATION_PROTOCOL_IDS":
            _ = k
            k = "'%s'" % ''.join(re.findall(r'\("([^"]+)"\)', v))
            v = normalize_value(_)
        else:
            k = normalize_key(k)
            v = normalize_value(v)
        if k and v:
            norm_d[k] = v
    return title, norm_d


def pprint(name, d):
    """dump as python dict
    """
    print ("%s = {" % name)
    for k in sorted(d):
        print ("    %s: '%s'," % (k, d[k]))
    print ("    }")


def normalize_key(strval):
    """normalize key
       form a string of 0x1234 or 1234
    """
    if '-' in strval:
        # skip ranges
        return None
    elif '0x' in strval:
        strval = "0x" + strval.replace('0x', '').replace(',', '')
    else:
        try:
            strval = "0x%0.2x" % (int(strval))
        except ValueError:
            strval = repr(strval)
    return strval.lower()


def normalize_value(strval):
    """normalize values
       strip TLS_ prefix, remove parenthesis and dots, replace ' ',/,. ->"_" and
    """
    return re.sub(r'(\s|/|\.)', '_', re.sub(r'(^TLS_|\s*\([^\)]+\))', '', strval))


def normalize_title(strval):
    """normalize registry titles
       convert -,<spaces>,parenthesis to _; strip multiple underscores and conver to uppercase
    """
    strval = re.sub(r'(-+|\s+|\([^\)]+\))', '_', strval)
    return re.sub(r'__+', '_', strval).rstrip("_").upper()


def xml_registry_to_dict(xmlroot, _id,
                         xml_key='./{http://www.iana.org/assignments}value',
                         xml_value=('./{http://www.iana.org/assignments}description',
                                    './{http://www.iana.org/assignments}name'),
                         xml_title='./{http://www.iana.org/assignments}title',
                         normalize_value=normalize_value, normalize_key=normalize_key, normalize_title=normalize_title,
                         verbose=False):
    d = {}
    registry = xmlroot.find("{http://www.iana.org/assignments}registry[@id='%s']" % _id)
    if registry is None:
        return None, None
    title = normalize_title(registry.find(xml_title).text)
    for record in registry.findall("./{http://www.iana.org/assignments}record"):
        try:
            key = record.find(xml_key).text
            for xml_v in xml_value:
                value = record.find(xml_v)
                if value is not None:
                    break
            value = value.text
            if key and value:
                d[key] = value
        except AttributeError as ae:
            if verbose:
                print ("# Skipping: %s" % repr(ae))
    return post_process(title, d)


def main(sources, ids, verbose=False):
    print ("# -*- coding: UTF-8 -*-")
    arg_ids = ids
    for source in sources:
        print ("# Generator: %s" % os.path.basename(__file__))
        print ("# date:      %s" % datetime.date.today())
        print ("# sources:   %s" % source)
        print ("#            WARNING! THIS FILE IS AUTOGENERATED, DO NOT EDIT!")
        print ("")
        if '://' in source:
            xml_data = urllib2.urlopen(source).read()
        elif os.path.isfile(source):
            with open(source, 'r') as f:
                xml_data = f.read()
        else:
            raise Exception("Source not supported (url,file)!")

        xmlroot = ET.fromstring(xml_data)
        if not arg_ids:
            # fetch all ids
            ids = (registry.attrib.get("id")
                   for registry in xmlroot.findall("{http://www.iana.org/assignments}registry") if registry.attrib.get("id"))

        for _id in ids:
            title, d = xml_registry_to_dict(xmlroot, _id=_id, verbose=verbose)
            pprint(title, d)

if __name__ == "__main__":
    ids = sys.argv[1].strip().split(",") if len(sys.argv) > 1 else None
    main(sources=URL_IANA_DEFS, ids=ids, verbose=True)
