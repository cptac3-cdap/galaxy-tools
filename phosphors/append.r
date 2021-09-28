#! D:\software\R\R-3.3.0\bin\x64\Rscript --vanilla --default-packages=XML

  options(warn = -1)

  suppressMessages(library(XML))

  args <- commandArgs(TRUE)
  # print(args) 

  mgf.file=args[1]
  psm.file=args[2]
  
  mgf.file.info=strsplit(mgf.file, ".", fixed=TRUE)[[1]]
  xml.file=paste(mgf.file.info[1], ".xml", sep="")
  xml.phospho.outfile=paste(mgf.file.info[1], ".phospho.xml", sep="")
  xml.phospho.complete.outfile=paste(mgf.file.info[1], ".phospho.complete.txt", sep="")
  
  psm.data=read.csv(psm.file, sep="\t", colClasses = "character", check.names=FALSE)

	
  #sink("d:/research/Collaborations/CPTAC/Nathan/hello.txt")
  #print(xml.file)
  #print(psm.file)
  #print(xml.phospho.outfile)
  #print(xml.phospho.complete.outfile)
  #sink()
  
  
  ###############
  # parse XML file
  ###############

 # Why do I need to do this!!!!
 data <- readChar(xml.phospho.outfile, file.info(xml.phospho.outfile)$size)
 phospho.xml.output.data=xmlParse(data) 

 top=xmlRoot(phospho.xml.output.data)

 # print(phospho.xml.output.data)
 xml_data <- xmlToList(phospho.xml.output.data)
 #node.value=as.list(xml_data[["PhosphoRS_Results"]][["Spectra"]][["Spectra"]])
 
 #art=top[[2]][[1]]
 #art[["Peptides"]][["Peptide"]][["SitePrediction"]][[1]]
 
 # nodes=getNodeSet(top[[2]], "//Spectrum/Peptides/Peptide[@ID='13650']")[[1]]
 #lapply(nodes, function(x) xmlSApply(x, xmlValue))
 
 #val=top[[2]][[1]][["Peptides"]][["Peptide"]][["SitePrediction"]]
 #xmlToList(val)[[1]]

 
	num.spectrum=length(xml_data[[2]])
	psm.data.extra.column=matrix("", dim(psm.data)[1], 3)
	psm.data.extra.column[,2] = 0
	for(s in sequence(num.spectrum)){
	    num.specpeptides = xmlSize(top[[2]][[s]][["Peptides"]])
	    specid = xmlToList(top[[2]][[s]])$.attrs[[1]]
	    # print(c(s,specid,num.specpeptides))
	    for (pi in sequence(num.specpeptides)){
		 nodes2=top[[2]][[s]][["Peptides"]][[pi]]
		 PhosphoRSPeptide=""
		 id.name=xmlToList(nodes2)$.attrs[[1]]
		 scan.num=strsplit(id.name, "_")[[1]][1]
		 matched.psm.peptide=strsplit(id.name, "_")[[1]][2]
		 # matched.psm.peptide=as.vector(psm.data[which(psm.data$ScanNum==scan.num), 'PeptideSequence'])
		 
		 peptide.sequence=paste(na.omit(unlist(strsplit(unlist(matched.psm.peptide), "[^a-zA-Z]+"))), collapse="")
		 PhosphoRSPeptide=""
		 prev.pos=1
		 # phospho.val=0
		 FullyLocalized=0
		 FullyLocalizedSites = c()
		 if(length(matched.psm.peptide)==1){
			for(site in 1:length(xmlToList(top[[2]][[s]][["Peptides"]][["Peptide"]][["SitePrediction"]]))){
				seq.pos=as.numeric(xmlToList(top[[2]][[s]][["Peptides"]][["Peptide"]][["SitePrediction"]])[[site]][[1]])
				site.prob=as.numeric(xmlToList(top[[2]][[s]][["Peptides"]][["Peptide"]][["SitePrediction"]])[[site]][[2]])
				PhosphoRSPeptide=paste(PhosphoRSPeptide, substr(peptide.sequence, prev.pos, seq.pos), "[", sprintf("%.2f", site.prob*100), "]", sep="")
				prev.pos=seq.pos+1
				# phospho.val=phospho.val+site.prob
				if(site.prob>=0.99){
					FullyLocalized=FullyLocalized+1
					FullyLocalizedSites=c(FullyLocalizedSites,seq.pos)
				}
			}
			if(prev.pos<=nchar(peptide.sequence)){
				PhosphoRSPeptide=paste(PhosphoRSPeptide, substr(peptide.sequence, prev.pos, nchar(peptide.sequence)), sep="")
			}
			FullyLocalizedSites=sort(unique(FullyLocalizedSites))

			nPhospho=lengths(regmatches(matched.psm.peptide[[1]], gregexpr("\\+79.966", matched.psm.peptide[[1]])))
			modpos=cumsum(sapply(regmatches(matched.psm.peptide[[1]],
                                                        gregexpr("[+-]?[0-9]+(\\.[0-9]*)?", 
                                                                  matched.psm.peptide[[1]]), 
                                                         invert=TRUE),
                                              nchar))
			moddel=regmatches(matched.psm.peptide[[1]],
                                          gregexpr("[+-]?[0-9]+(\\.[0-9]*)?",
                                                   matched.psm.peptide[[1]]))
			moddel=sapply(moddel,as.numeric)
			phospos = c()
			for (ind in 1:length(moddel)) {
			    if (abs(moddel[ind]-79.966)<0.01) {
				phospos = c(phospos,modpos[ind])
			    }
                        }
			phospos=sort(unique(phospos))
			nSTY=lengths(regmatches(peptide.sequence, gregexpr("[STY]", peptide.sequence)))
			if (nPhospho == FullyLocalized && phospos == FullyLocalizedSites) {
			    FullyLocalized="Y"
			} else {
			    FullyLocalized="N"
			}
			if (nSTY == nPhospho) {
			    FullyLocalized="Y"
			    PhosphoRSPeptide <- gsub('[100.00]','[100]',PhosphoRSPeptide,fixed=TRUE)
			}
			psm.data.extra.column[which(psm.data$ScanNum==scan.num & psm.data$PeptideSequence==matched.psm.peptide),]=c(PhosphoRSPeptide, nPhospho, FullyLocalized)
		} 
	    }
	}  

	# name extra columns
	colnames(psm.data.extra.column) <- c('PhosphoRSPeptide', 'nPhospho', 'FullyLocalized')

	# remove old columns if they are there
        toremove <- names(psm.data) %in% c('PhosphoRSPeptide', 'nPhospho', 'FullyLocalized')
        psm.data.final <- psm.data[!toremove]

	# append new columns
	psm.data.final=cbind(psm.data.final, psm.data.extra.column)

	write.table(psm.data.final, file=xml.phospho.complete.outfile, quote=FALSE, sep='\t', row.names=FALSE)
