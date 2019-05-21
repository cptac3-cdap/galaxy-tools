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
import time
import traceback

from galaxy.util.json import from_json_string, to_json_string


CHUNK_SIZE = 2**20 #1mb

def history_check(idtag,name,source,id,dbtag,display):
    urlargs = {}
    desc = []
    idstr = {}
    desc.append(source)
    idstr['source'] = source.lower()
    desc.append(name.strip())
    desc.append(id.strip())
    idstr['idtag'] = idtag
    idstr['id'] = id.lower()
    idstr['datestr'] = datetime.datetime.now().strftime("%Y%m%d")
    desc.append('(%s)'%( datetime.datetime.now().strftime("%Y-%m-%d"),))
    if not dbtag:
        idstr = '_'.join(filter(None,map(idstr.get,['source','idtag','id','datestr'])))
    else:
	idstr = dbtag
    if not display:
        desc = ' '.join(desc)
    else:
	desc = display
    return idstr,desc,urlargs,{}

def history_download(idtag,name,source,input_fasta,id,display,dbtag,targetdir):
    idstr,desc,urlargs,jsonargs = history_check(idtag,name,source,id,dbtag,display)

    fasta_filename = os.path.join(targetdir,idstr+".fasta")
    assert (not os.path.exists(fasta_filename))
    fasta_writer = open( fasta_filename, 'wb' )
    fasta_reader = open( input_fasta )

    while True:
	buffer = fasta_reader.read(CHUNK_SIZE)
        if not buffer:
	    break
	fasta_writer.write(buffer)

    fasta_reader.close()
    fasta_writer.close()
	
    return dict(value=idstr,display_name=desc,file_path=fasta_filename,**jsonargs)

def add_data_table_entry( data_manager_dict, table_name, data_table_entry ):
    data_manager_dict['data_tables'] = data_manager_dict.get( 'data_tables', {} )
    data_manager_dict['data_tables'][table_name] = data_manager_dict['data_tables'].get( 'all_proteome', [] )
    data_manager_dict['data_tables'][table_name].append( data_table_entry )
    return data_manager_dict

def main():
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    filename = args[0]
    params = from_json_string( open( filename ).read() )
    target_directory = params[ 'output_data' ][0]['extra_files_path']
    try:
        os.mkdir( target_directory )
    except OSError:
        pass

    tooldatadir=params['param_dict']['__tool_data_path__']
    idtag=params['param_dict']['organism']
    species = dict()
    for l in open(os.path.join(tooldatadir,'all_proteome_species.loc')):
        d = dict(zip("idtag name taxid refseqsciname refseqprefix".split(),l.split()))
        species[d["idtag"]] = d

    kwargs = dict(idtag=idtag,
                  name=species[idtag]["name"],
		  source=params['param_dict']['source'],
		  input_fasta=params['param_dict']['input_fasta'],
		  id=params['param_dict']['id'],
		  display=params['param_dict']['display'],
		  dbtag=params['param_dict']['tag'],
		  targetdir=target_directory)
 
    data_table_entry = history_download(**kwargs)
    data_manager_dict = add_data_table_entry( {}, 'all_proteome', data_table_entry )

    open( filename, 'wb' ).write( to_json_string( data_manager_dict ) )
        
if __name__ == "__main__":
    main()
