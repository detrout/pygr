import pygr.Data
import random
import unittest
from nosebase import *
from pygr import sequence

class Conserve_Suite(unittest.TestCase):
	def exonquery_megatest(self):
		def printConservation(id,label,site):
			if msa.seqs.IDdict: # skip if alignment is empty
				for src,dest,edge in msa[site].edges(mergeMost=True):
					print '%d\t%s\t%s\t%s\t%s\t%s\t%2.1f\t%2.1f' \
						  %(id,label,repr(src),src,idDict[dest],dest,
							100*edge.pIdentity(),100*edge.pAligned())

		def getConservation(id,label,site):
			if msa.seqs.IDdict: # skip if alignment is empty
				for src,dest,edge in msa[site].edges(mergeMost=True):
					a = '%d\t%s\t%s\t%s\t%s\t%s\t%2.1f\t%2.1f' \
						%(id,label,repr(src),src,idDict[dest],dest,
						  100*edge.pIdentity(),100*edge.pAligned())

		exons = pygr.Data.getResource('Bio.Annotation.ASAP2.HUMAN.hg17.exons')
		msa = pygr.Data.getResource('Bio.MSA.UCSC.hg17_multiz17way')
		idDict = ~(msa.seqDict) # INVERSE: MAPS SEQ --> STRING IDENTIFIER
		l = exons.keys()
		coverage = 0.001  # 1% coverage -> ~90 minutes wall-clock time

		for i in range(int(len(l) * coverage)):
			k = random.randint(0,len(l) - 1)
			id = l[k]
			exon = exons[id].sequence

			ss1=exon.before()[-2:] # GET THE 2 NT SPLICE SITES
			ss2=exon.after()[:2]
			cacheHint=msa[ss1+ss2] #CACHE THE COVERING INTERVALS FROM ss1 TO ss2
			try:
				getConservation(id,'ss1',ss1)
				getConservation(id,'ss2',ss2)
				getConservation(id,'exon',exon)
			except TypeError:
				print id, exon


class Blast_Suite(unittest.TestCase):
	def setUp(self):
		self.genomes = ['.'.join(x.split('.')[-2:]) for x in pygr.Data.dir('Bio.Seq.Genome')]
		available_exons = [x for x in pygr.Data.dir('Bio.Annotation.ASAP2') if 'exons' in x and 'cDNA' not in x and 'Map' not in x]
		self.available_exons = [x.replace('Bio.Annotation.ASAP2.','').replace('.exons','') for x in available_exons]

		
	def genome_blast_megatest(self):

		for genome in self.genomes:
			if genome in self.available_exons:
				#print genome

				g = pygr.Data.getResource('Bio.Seq.Genome.%s' % genome)
				exons = pygr.Data.getResource('Bio.Annotation.ASAP2.%s.exons' % genome)
				it = exons.iteritems()
				id, exon = it.next()
				id, exon = it.next()
				del it
				exon2 = exon
				exon = sequence.Sequence(str(exon.sequence),'1')

				m = g.megablast(exon, maxseq=1, minIdentity=0.9)
				if m.seqs.IDdict: # skip if alignment is empty
					tmp = m[exon].edges(mergeMost=True)
					if tmp:
						src, dest, edge = tmp[0]
						#print repr(src), repr(dest), len(tmp)
						self.assertEqual(edge.pIdentity(trapOverflow=False), 1.)
					#else:
						#print 'no destination matches of proper length'


	def all_v_all_blast_test(self):
		from pygr import cnestedlist,seqdb
		from pygr import sequence
		stored = PygrDataTextFile('results/seqdb1.pickle','r')
		old_result = stored['sp_allvall']
		
		msa=cnestedlist.NLMSA('all_vs_all',mode='w',bidirectional=False) # ON-DISK
		sp=seqdb.BlastDB('sp_hbb1') # OPEN SWISSPROT DATABASE
		for id,s in sp.iteritems(): # FOR EVERY SEQUENCE IN SWISSPROT
			sp.blast(s,msa,expmax=1e-10, verbose=False) # GET STRONG HOMOLOGS, SAVE ALIGNMENT IN msa
		msa.build(saveSeqDict=True) # DONE CONSTRUCTING THE ALIGNMENT, SO BUILD THE ALIGNMENT DB INDEXES

		db = msa.seqDict.dicts.keys()[0]
		result = []
		for k in db.values():
			#edges = msa[k].edges(minAlignSize=12,pIdentityMin=0.5)
			edges = msa[k].edges(minAlignSize=12)
			for t in edges:
				assert len(t[0]) >= 12
			result.append([(t[0], t[1], t[2].pIdentity(trapOverflow=False)) for t in edges])

		result.sort()

		for i in range(len(result)):
			for j in range(len(result[i])):
				src, dest, identity = result[i][j]
				old_src, old_dest, old_identity = old_result[i][j]
				assert (str(src), str(dest)) == (str(old_src), str(old_dest))
				assert identity - old_identity < .0001
			

def all_v_all_blast_save():
 	from pygr import cnestedlist,seqdb
	working = PygrDataTextFile('results/seqdb1.pickle','a')
 	msa=cnestedlist.NLMSA('all_vs_all',mode='w',bidirectional=False) # ON-DISK
 	sp=seqdb.BlastDB('sp_hbb1') # OPEN SWISSPROT DATABASE
 	for id,s in sp.iteritems(): # FOR EVERY SEQUENCE IN SWISSPROT
 		sp.blast(s,msa,expmax=1e-10, verbose=False) # GET STRONG HOMOLOGS, SAVE ALIGNMENT IN msa
 	msa.build(saveSeqDict=True) # DONE CONSTRUCTING THE ALIGNMENT, SO BUILD THE ALIGNMENT DB INDEXES

	db = msa.seqDict.dicts.keys()[0]
	result = []
	for k in db.values():
		edges = msa[k].edges(minAlignSize=12)
		for t in edges:
			assert len(t[0]) >= 12
		result.append([(t[0], t[1], t[2].pIdentity(trapOverflow=False)) for t in edges])

	result.sort()
	working['sp_allvall'] = result

 	return msa
		
				

	
	
