#!/usr/bin/env python

import sys
import os
import tempfile
import shutil
import optparse
from urllib import urlencode
import urllib2
import datetime
import tarfile
import zipfile
import gzip
import zlib
import bz2

from galaxy.util.json import from_json_string, to_json_string


def add_data_table_entry( data_manager_dict, table_name, data_table_entry ):
    data_manager_dict['data_tables'] = data_manager_dict.get( 'data_tables', {} )
    data_manager_dict['data_tables'][table_name] = data_manager_dict['data_tables'].get( table_name, [] )
    data_manager_dict['data_tables'][table_name].append( data_table_entry )
    return data_manager_dict

def main():
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    filename = args[0]
    params = from_json_string( open( filename ).read() )

    table_name = "compress_seq"

    value = args[1]
    display_name = args[2]
    file_path = args[3]

    data_manager_dict = {}
    data_table_entry = dict(value=value,file_path=file_path, display_name=display_name)
    data_manager_dict = add_data_table_entry( data_manager_dict, table_name, data_table_entry )

    open( filename, 'wb' ).write( to_json_string( data_manager_dict ) )
        
if __name__ == "__main__":
    main()
