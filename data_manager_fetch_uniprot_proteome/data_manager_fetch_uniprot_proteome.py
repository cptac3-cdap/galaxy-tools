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

CHUNK_SIZE = 2**20 #1mb

def uniprot_check(idtag,name,taxid,proteome,reviewed,isoforms):
    urlargs = {'query': set()}
    desc = []
    idstr = {'source': 'uniprot','idtag': idtag}
    if reviewed == 'reviewed':
        desc.append("SwissProt")
        urlargs['query'].add('reviewed:true')
        idstr['reviewed'] = 'reviewed'
    elif reviewed == 'all':
        desc.append("UniProt")
    else:
        raise RuntimeError("Bad reviewed parameter value")
    desc.append(name)
    if proteome == 'reference':
        desc.append("Reference")
        urlargs['query'].add('keyword:KW-1185')
        idstr['proteome'] = 'reference'
    elif proteome == 'all':
        pass
    else:
        raise RuntimeError("Bad proteome parameter value")
    if isoforms == 'isoforms':
        desc.append('with Isoforms')
        urlargs['includeIsoform'] = 'true'
        idstr['isoforms'] = 'isoforms'
    elif isoforms == 'noisoforms':
        pass
    else:
        raise RuntimeError("Bad isoforms parameter value")
    try:
        taxid = int(taxid)
        urlargs['query'].add('organism_id:%d'%taxid)
    except (ValueError, TypeError):
        raise RuntimeError("Invalid taxonomy id value")
    idstr['datestr'] = datetime.datetime.now().strftime("%Y%m%d")
    desc.append('(%s)'%( datetime.datetime.now().strftime("%Y-%m-%d"),))
    urlargs['query'] = ' AND '.join(urlargs['query'])
    idstr = '_'.join(filter(None,map(idstr.get,['source','idtag','reviewed','proteome','isoforms','datestr'])))
    desc = ' '.join(desc)
    return idstr,desc,urlargs,{}

def uniprot_download(idtag,name,taxid,proteome,reviewed,isoforms,targetdir):
    idstr,desc,urlargs,jsonargs = uniprot_check(idtag,name,taxid,proteome,reviewed,isoforms)
    urlargs['force'] = 'true'
    urlargs['format'] = 'fasta'
    urlargs['compressed'] = 'true'

    fasta_filename = os.path.join(targetdir,idstr+".fasta")

    # print fasta_filename

    assert (not os.path.exists(fasta_filename))
    fasta_writer = open( fasta_filename, 'wb' )

    url = "https://rest.uniprot.org/uniprotkb/stream?"+urlencode(urlargs)
    print url
    
    downloader = urllib2.urlopen(url)
    decompressor = zlib.decompressobj(16+zlib.MAX_WBITS) 
    while True:
        buffer = downloader.read(CHUNK_SIZE)
        if not buffer:
            break
        fasta_writer.write(decompressor.decompress(buffer))
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
                  taxid=species[idtag]["taxid"],
                  reviewed=params['param_dict']['reviewed'],
                  proteome=params['param_dict']['proteome'],
                  isoforms=params['param_dict']['isoforms'],
		  targetdir=target_directory)
 
    data_table_entry = uniprot_download(**kwargs)
    data_manager_dict = add_data_table_entry( {}, 'all_proteome', data_table_entry )

    open( filename, 'wb' ).write( to_json_string( data_manager_dict ) )
        
if __name__ == "__main__":
    main()
