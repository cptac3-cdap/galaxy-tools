
/mnt/galaxy/tool_dependencies/_conda/bin/conda clean --index-cache
/mnt/galaxy/tool_dependencies/_conda/bin/python /mnt/galaxy/tool_dependencies/_conda/bin/conda create -y --override-channels --channel iuc --channel bioconda --channel conda-forge --channel defaults --name __bcftools@1.5 bcftools=1.5

# Construct galaxy URL from local ip...
# LOCALIP=`wget -q -O - http://169.254.169.254/latest/meta-data/local-ipv4`
# sed -i "s/XXXXX_REPLACEWITHLOCALIP_XXXXX/$LOCALIP/" /mnt/galaxy/galaxy-app/config/job_conf.xml

if [ ! -d /mnt/galaxy/tmp/scratch ]; then
  mkdir /mnt/galaxy/tmp/scratch
  chmod a+rwxt /mnt/galaxy/tmp/scratch
  ln -s /mnt/galaxy/tmp/scratch /home/ubuntu/galaxy-scratch 
  ln -s /mnt/galaxy/tmp/job_working_directory/000 /home/ubuntu/galaxy-jobs
fi

# Install AWS CLI and NetCDF                                                                                   
# apt-get -y update
# apt-get -y install awscli
# apt-get -y install libnetcdf-dev
# apt-get -y install texlive texlive-latex-extra

# usr.local.lib.R.site-library.tgz
# mkdir -p /usr/local/lib/R/site-library
# wget --no-check-certificate -q -O - "$DOWNLOADURL/usr.local.lib.R.site-library.tgz" | tar xvzf - -C /usr/local/lib/R/site-library  
# Install the R libraries we need
# R --vanilla <<EOF
# source("http://bioconductor.org/biocLite.R")
# biocLite("MSnbase")                                                                                          
# EOF

# cp /mnt/galaxy/tools/extratools/lib/pandoc/bin/pandoc* /usr/local/bin
# wget --no-check-certificate -q -O - "$DOWNLOADURL/usr.local.bin.pandoc.tgz" | tar xvzf - -C /usr/local/bin                             
