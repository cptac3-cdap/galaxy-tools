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

def refseq_check(idtag,name,sciname,prefix):
    urlargs = {}
    desc = []
    idstr = {}
    label = prefix
    desc.append('RefSeq')
    idstr['source'] = 'refseq'
    desc.append(name.strip())
    urlargs['label'] = label
    urlargs['sciname'] = sciname
    idstr['idtag'] = idtag
    idstr['datestr'] = datetime.datetime.now().strftime("%Y%m%d")
    desc.append('(%s)'%( datetime.datetime.now().strftime("%Y-%m-%d"),))
    idstr = '_'.join(filter(None,map(idstr.get,['source','idtag','datestr'])))
    desc = ' '.join(desc)
    return idstr,desc,urlargs,{}

def refseq_download(idtag,name,sciname,prefix,targetdir):
    idstr,desc,urlargs,jsonargs = refseq_check(idtag,name,sciname,prefix)

    baseurl = "ftp://ftp.ncbi.nlm.nih.gov/refseq/%(sciname)s/mRNA_Prot"%urlargs
    listurl = baseurl + '/%(label)s.files.installed'%urlargs
    parts = []
    for l in urllib2.urlopen(listurl):
	sl = l.split()
	if len(sl) != 2:
	    continue
	if sl[1].endswith('.protein.faa.gz'):
	    parts.append(sl[1])
    parts.sort(key=lambda p: int(p.split('.')[1]))

    fasta_filename = os.path.join(targetdir,idstr+".fasta")
    assert (not os.path.exists(fasta_filename))
    fasta_writer = open( fasta_filename, 'wb' )

    for part in parts:
	downloader = urllib2.urlopen(baseurl + '/' + part)
        decompressor = zlib.decompressobj(16+zlib.MAX_WBITS) 
        while True:
            buffer = downloader.read(CHUNK_SIZE)
            if not buffer:
                break
            fasta_writer.write(decompressor.decompress(buffer))
            print "%s: %d"%(part,os.path.getsize(fasta_filename))
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
        os.makedirs( target_directory )
    except OSError:
        traceback.print_exec()

    tooldatadir=params['param_dict']['__tool_data_path__']
    idtag=params['param_dict']['organism']
    species = dict()
    for l in open(os.path.join(tooldatadir,'all_proteome_species.loc')):
        d = dict(zip("idtag name taxid refseqsciname refseqprefix".split(),l.split()))
        species[d["idtag"]] = d

    kwargs = dict(idtag=idtag,
                  name=species[idtag]["name"],
                  sciname=species[idtag]["refseqsciname"],
                  prefix=species[idtag]["refseqprefix"],
		  targetdir=target_directory)
 
    data_table_entry = refseq_download(**kwargs)
    data_manager_dict = add_data_table_entry( {}, 'all_proteome', data_table_entry )

    open( filename, 'wb' ).write( to_json_string( data_manager_dict ) )
        
if __name__ == "__main__":
    main()
