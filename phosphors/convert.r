#! D:\software\R\R-3.3.0\bin\x64\Rscript --vanilla --default-packages=XML

  options(warn = -1)
  suppressMessages(library(MSnbase))
  suppressMessages(library(XML))
  args <- commandArgs(TRUE)

  mgf.file=args[1] # "d:/research/Collaborations/CPTAC/Nathan/CPTAC_263d3f-I_blcdb9-I_c4155b-C_117C_P_BI_20140520_H-PM_f02.mgf"
  psm.file=args[2] # "d:/research/Collaborations/CPTAC/Nathan/CPTAC_263d3f-I_blcdb9-I_c4155b-C_117C_P_BI_20140520_H-PM_f02.raw.cap.psm"
  modification.file=args[3] # "d:/research/Collaborations/CPTAC/Nathan/modification.mass.table.2.txt"
  
  mgf.file.info=strsplit(mgf.file, ".", fixed=TRUE)[[1]]
  xml.file=paste(mgf.file.info[1], ".xml", sep="")
  xml.phospho.outfile=paste(mgf.file.info[1], ".phospho.xml", sep="")
  xml.phospho.complete.outfile=paste(mgf.file.info[1], ".phospho.complete.txt", sep="")
  	
  strcount <- function(x, patterns, split){
		n=0
		for(pattern in patterns){
			n=n+unlist(lapply(
				strsplit(x, split),
				   function(z) na.omit(length(grep(pattern, z)))
				))
		}
		return(n)
  }

  activationtypes=args[4] # "CID"
  mass.tolerance.value=args[5] # default 0.5
  topn = 0
  if (args[6] != "") {
    topn=as.numeric(args[6]) # default 0
  }
  relint = 0
  if (args[7] != "") {
    relint=as.numeric(args[7]) # default 0
  }
  
  start.time = proc.time()[[3]]
  ms.data=readMgfData(mgf.file)
  cat(sprintf("MGF read time: %.2f sec.\n",proc.time()[[3]] - start.time))
  start.time = proc.time()[[3]]
  
  psm.data=read.csv(psm.file, sep="\t")
  peptide.sequence.columnID=if(length(which(colnames(psm.data)=="PeptideSequence"))>0){
								which(colnames(psm.data)=="PeptideSequence")
							}else{
								which(colnames(psm.data)=="Peptide")							
							}
   
   cat(sprintf("PSM read time: %.2f sec.\n",proc.time()[[3]] - start.time))
   start.time = proc.time()[[3]]

   modification.mass.table=read.table(modification.file, stringsAsFactors=FALSE) #"d:/research/Collaborations/CPTAC/Nathan/modification.mass.table.2.txt"
   colnames(modification.mass.table)=c("index", "AA", "Mass", "Modification", "MassPrecise", "MassLost")
   
   xml <- xmlTree() # xml<-xmlOutputDOM()
   xml$addTag("phosphoRSInput", close=FALSE)
   xml$addTag("MassTolerance", attrs=c(Value=mass.tolerance.value)) ## double check
   xml$addTag("Phosphorylation", attrs=c(Symbol=1))
   xml$addTag("Spectra", close=FALSE)
  
  for(i in 1:dim(attributes(ms.data@featureData)$data)[1]){
  #for(i in 1:100){
		
		#a=proc.time(); for (i in 1:1000){
		scan.num=0
		precursorcharge=substr(as.vector(attributes(ms.data@featureData)$data[i,'CHARGE']),1,1)
		title.info=as.vector(attributes(ms.data@featureData)$data[i, 'TITLE'])
		scan.num=
			if(length(grep("^Scan:", title.info))>0){
				strsplit(strsplit(title.info, " ", fixed=TRUE)[[1]][1], ":")[[1]][2]
			}else{
				strsplit(title.info, ".", fixed=TRUE)[[1]][2]
			}
		if((!is.null(scan.num)) & (scan.num>0)){
			
			matched.psm.peptides=psm.data[which(psm.data$ScanNum==scan.num), peptide.sequence.columnID]
			matched.psm.peptides=unique(as.vector(matched.psm.peptides)) ## one scan number, multiple spectrum
	 
			#id.name=paste(c(scan.num, matched.psm.peptide), collapse="_")
			id.name=scan.num #id.name=paste(c(scan.num, i), collapse="_")
			putSpectrum=TRUE

			if(length(matched.psm.peptides)>0){
				for(matched.psm.peptide in matched.psm.peptides){
					peptide.sequence.values=na.omit(unlist(strsplit(unlist(matched.psm.peptide), "[^a-zA-Z]+")))
					peptide.sequence=paste(peptide.sequence.values, collapse="")
					modification.values=na.omit(unlist(strsplit(unlist(matched.psm.peptide), "[a-zA-Z]+")))
				 
					phospho.list=c()
					oxidation.list=c()
					peak.list.df=as.data.frame(ms.data[[i]])

					# min relative intensity
					if (relint > 0) {
					  maxi = max(peak.list.df$i)
					  peak.list.df = peak.list.df[which(peak.list.df$i>=(maxi*relint/100.0)),]
					}

					# Top n peaks
					if ((topn > 0) & (topn < dim(peak.list.df)[1])) {
					  inds = sort(order(peak.list.df$i,decreasing=TRUE)[1:topn])
					  peak.list.df = peak.list.df[inds,]
					}
					
					peak.list.list.1=unlist(lapply(1:dim(peak.list.df)[1], function(n){paste0(peak.list.df[n, ], collapse=":")}))
					peak.list.list.2=paste0(peak.list.list.1, collapse=",")
				 
					aa.pos.info=rep('0', nchar(peptide.sequence))
                    nmods = 0
					k=0
					for(j in 1:length(peptide.sequence.values)){
						s=peptide.sequence.values[j]
						if(nchar(s)>0 & length(modification.values)>=j){
							nucleotide=substr(s, nchar(s), nchar(s))
							k=k+nchar(s)
							mv=modification.values[j]
							#if(nucleotide=="S" | nucleotide=="T" | nucleotide=="Y"){aa.pos.info[k]=1}#else if(nucleotide=="M"){aa.pos.info[k]=2}
							index=which(modification.mass.table[,2]==nucleotide & 
							modification.mass.table[,3]==as.numeric(substr(mv,2,nchar(mv))))
							aa.pos.info[k]=modification.mass.table[index, 1]#index[1]
                            nmods = nmods+1
						}
					}
					## very important, need to redefine the N terminal if mode definition changes
					n.terminal=if(substr(matched.psm.peptide, 1, 4)=="+144"){4} else if(substr(matched.psm.peptide, 1, 3)=="+42"){6} else if(substr(matched.psm.peptide, 1, 4)=="+229"){8} else{0}
					modification.info=paste(c(n.terminal, ".", paste(aa.pos.info, sep=""), ".0"), collapse="")
					
					# condition 1: remove empty phosphorylation
					num.phospho.site=strcount(peptide.sequence, c("S", "T", "Y"), "")
					if(num.phospho.site!=0){
						if(nmods>0){
							#if(length(which(unique.id.name.list==id.name))==0){
							if(putSpectrum==TRUE){
								xml$addTag("Spectrum", attrs=c(ID=id.name, PrecursorCharge=precursorcharge, ActivationTypes=activationtypes), close=FALSE)
								xml$addTag("Peaks", peak.list.list.2)
								xml$addTag("IdentifiedPhosphorPeptides", close=FALSE)
								putSpectrum=FALSE
							}
							peptide.id=paste(c(scan.num, matched.psm.peptide), collapse="_") # can be different from spectrum id name
							xml$addTag("Peptide", attrs=c(ID=peptide.id, Sequence=peptide.sequence, ModificationInfo=modification.info))
						}
					}
				}
			}
			if(putSpectrum==FALSE){
				xml$closeTag()
				xml$closeTag()
			}
		}
	}
   
  xml$closeTag()
  ## pay attention to mass for phosphorylation? 79.966331?
  xml$addTag("ModificationInfos", close=FALSE)
  for(index in unique(modification.mass.table$index)){
	modifications=unique(modification.mass.table[which(modification.mass.table$index==index), 'Modification'])
	AAs=modification.mass.table[which(modification.mass.table$index==index), 'AA']
	MassPrecise=unique(modification.mass.table[which(modification.mass.table$index==index), 'MassPrecise'])
	MassLost=unique(modification.mass.table[which(modification.mass.table$index==index), 'MassLost'])
	AAs.p=paste(AAs, collapse="")
	AAs.p=gsub("[^[:alnum:][:blank:]+?&/\\-]", "", AAs.p)
	the.string=if(index==1){
			paste(c('', index, ':', modifications,':', modifications, ':', MassPrecise, ':PhosphoLoss:', MassLost, ':', AAs.p,''), collapse="")
		}else{
			paste(c('', index, ':', modifications, ':', modifications, ':', MassPrecise, ':null:', 0, ':', AAs.p,''), collapse="")
		}
	#print(the.string)
	xml$addTag("ModificationInfo", attrs=c(Symbol=index, Value=the.string))
  }
  xml$closeTag()
  xml$closeTag()

  cat(sprintf("XML construct time: %.2f sec.\n",proc.time()[[3]] - start.time))
  start.time = proc.time()[[3]]

  output.file=xml.file # "d:/research/Collaborations/CPTAC/Nathan/CPTAC_263d3f-I_blcdb9-I_c4155b-C_117C_P_BI_20140520_H-PM_f02.v6.xml"
  sink(output.file)
  print(xml$value())
  sink()

  cat(sprintf("XML output time: %.2f sec.\n",proc.time()[[3]] - start.time))
  
  
  
  
