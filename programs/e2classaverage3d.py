#!/usr/bin/env python

#
# Author: Steven Ludtke, 02/15/2011 - using code and concepts drawn from Jesus Montoya's scripts
# Copyright (c) 2011 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#
#

from EMAN2 import *
from optparse import OptionParser
import math
from copy import deepcopy
import os
import sys
import random
from random import choice
from pprint import pprint
from EMAN2db import EMTask

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog <output> [options]

	This program produces iterative class-averages akin to those generated by e2classaverage, but for stacks of 3-D Volumes.
	Normal usage is to provide a stack of particle volumes and a classification matrix file defining
	class membership. Members of each class are then iteratively aligned to each other and averaged
	together.  It is also possible to use this program on all of the volumes in a single stack.

	Three preprocessing operations are provided for, mask, normproc and preprocess. They are executed in that order. Each takes
	a generic <processor>:<parm>=<value>:...  string. While you could provide any valid processor for any of these options, if
	the mask processor does not produce a valid mask, then the default normalization will fail. It is recommended that you
	specify the following, unless you really know what you're doing:
	
	--mask=mask.sharp:outer_radius=<safe radius>
	--preprocess=filter.lowpass.gauss:cutoff_freq=<1/resolution in A>
	
	"""
		
	parser = OptionParser(usage=usage,version=EMANVERSION)
	
	parser.add_option("--input", type="string", help="The name of the input volume stack. MUST be HDF or BDB, since volume stack support is required.", default=None)
	parser.add_option("--output", type="string", help="The name of the output class-average stack. MUST be HDF or BDB, since volume stack support is required.", default=None)
	parser.add_option("--oneclass", type="int", help="Create only a single class-average. Specify the class number.",default=None)
	parser.add_option("--classmx", type="string", help="The name of the classification matrix specifying how particles in 'input' should be grouped. If omitted, all particles will be averaged.", default=None)
	parser.add_option("--ref", type="string", help="Reference image(s). Used as an initial alignment reference and for final orientation adjustment if present. This is typically the projections that were used for classification.", default=None)
	parser.add_option("--resultmx",type="string",help="Specify an output image to store the result matrix. This is in the same format as the classification matrix. http://blake.bcm.edu/emanwiki/EMAN2/ClassmxFiles", default=None)
	parser.add_option("--iter", type="int", help="The number of iterations to perform. Default is 1.", default=1)
	parser.add_option("--savesteps",action="store_true", help="If set, will save the average after each iteration to class_#.hdf. Each class in a separate file. Appends to existing files.",default=False)
	parser.add_option("--sym", dest = "sym", action="append", help = "Symmetry to impose - choices are: c<n>, d<n>, h<n>, tet, oct, icos")
	parser.add_option("--mask",type="string",help="Mask processor applied to particles before alignment. Default is mask.sharp:outer_radius=-2", default="mask.sharp:outer_radius=-2")
	parser.add_option("--normproc",type="string",help="Normalization processor applied to particles before alignment. Default is to use normalize.mask. If normalize.mask is used, results of the mask option will be passed in automatically. If you want to turn this option off specify \'None\'", default="normalize.mask")
	parser.add_option("--preprocess",type="string",help="A processor (as in e2proc3d.py) to be applied to each volume prior to alignment. Not applied to aligned particles before averaging.",default=False)
	parser.add_option("--ncoarse", type="int", help="The number of best coarse alignments to refine in search of the best final alignment", default=1)
	parser.add_option("--align",type="string",help="This is the aligner used to align particles to the previous class average. Default is rotate_translate_3d:search=10:delta=15:dphi=15", default="rotate_translate_3d:search=10:delta=15:dphi=15")
	parser.add_option("--aligncmp",type="string",help="The comparator used for the --align aligner. Default is the internal tomographic ccc. Do not specify unless you need to use another specific aligner.",default="ccc.tomo")
	parser.add_option("--ralign",type="string",help="This is the second stage aligner used to refine the first alignment. Default is refine.3d, specify 'None' to disable", default="refine.3d")
	parser.add_option("--raligncmp",type="string",help="The comparator used by the second stage aligner. Default is the internal tomographic ccc",default="ccc.tomo")
	parser.add_option("--averager",type="string",help="The type of averager used to produce the class average. Default=mean",default="mean")
	parser.add_option("--cmp",type="string",dest="cmpr",help="The comparitor used to generate quality scores for the purpose of particle exclusion in classes, strongly linked to the keep argument.", default="ccc")
	parser.add_option("--keep",type="float",help="The fraction of particles to keep in each class.",default=1.0)
	parser.add_option("--keepsig", action="store_true", help="Causes the keep argument to be interpreted in standard deviations.",default=False)
	parser.add_option("--shrink", type="int",default=1,help="Optionally shrink the input volumes by an integer amount for coarse alignment.")
	parser.add_option("--shrinkrefine", type="int",default=1,help="Optionally shrink the input volumes by an integer amount for refine alignment.")
#	parser.add_option("--automask",action="store_true",help="Applies a 3-D automask before centering. Can help with negative stain data, and other cases where centering is poor.")
#	parser.add_option("--resample",action="store_true",help="If set, will perform bootstrap resampling on the particle data for use in making variance maps.",default=False)
#	parser.add_option("--odd", default=False, help="Used by EMAN2 when running eotests. Includes only odd numbered particles in class averages.", action="store_true")
#	parser.add_option("--even", default=False, help="Used by EMAN2 when running eotests. Includes only even numbered particles in class averages.", action="store_true")
	parser.add_option("--parallel",  help="Parallelism. See http://blake.bcm.edu/emanwiki/EMAN2/Parallel", default="thread:1")
	parser.add_option("--verbose", "-v", dest="verbose", action="store", metavar="n",type="int", default=0, help="verbose level [0-9], higner number means higher level of verboseness")

	(options, args) = parser.parse_args()

	if options.align : options.align=parsemodopt(options.align)
	if options.ralign : options.ralign=parsemodopt(options.ralign)
	if options.aligncmp : options.aligncmp=parsemodopt(options.aligncmp)
	if options.raligncmp : options.raligncmp=parsemodopt(options.raligncmp)
	if options.averager : options.averager=parsemodopt(options.averager)
	if options.cmpr : options.cmpr=parsemodopt(options.cmpr)
	if options.normproc : options.normproc=parsemodopt(options.normproc)
	if options.mask : options.mask=parsemodopt(options.mask)
	if options.preprocess : options.preprocess=parsemodopt(options.preprocess)

	if options.resultmx!=None : options.storebad=True

	hdr=EMData(options.input,0,True)
	nx=hdr["nx"]
	ny=hdr["ny"]
	nz=hdr["nz"]
	if nx!=ny or ny!=nz :
		print "ERROR, input volumes are not cubes"
		sys.exit(1)
	
	if options.ref!=None :
		hdr=EMData(options.ref,0,True)
		if hdr["nx"]!=nx or hdr["ny"]!=ny or hdr["nz"]!=nz : 
			print "Error, ref volume not same size as input volumes"
			sys.exit(1)
	
	logger=E2init(sys.argv)
	
	try: 
		classmx=EMData.read_images(options.classmx)		# we keep the entire classification matrix in memory, since we need to update it in most cases
		ncls=int(classmx[0]["maximum"])
	except:
		ncls=1
		#if options.resultmx!=None :
			#print "resultmx can only be specified in conjunction with a valid classmx input."
			#sys.exit(1)

	nptcl=EMUtil.get_image_count(options.input)
	if nptcl<2 : 
		print "ERROR : at least 2 particles required in input stack"
		sys.exit(1)

	# Initialize parallelism if being used
	if options.parallel :
		from EMAN2PAR import EMTaskCustomer
		etc=EMTaskCustomer(options.parallel)
		pclist=[options.input]
		if options.ref: pclist.append(options.ref)
		etc.precache(pclist)

	#########################################
	# This is where the actual class-averaging process begins
	#########################################

	# outer loop over classes, ic=class number
	for ic in range(ncls):
		if ncls==1 : ptcls=range(nptcl)				# start with a list of particle numbers in this class
		else : ptcls=classmx_ptcls(classmx,ic)		# This gets the list from the classmx
		
		# prepare a reference either by reading from disk or bootstrapping
		if options.ref : ref=EMData(options.ref,ic)
		else :
			# we need to make an initial reference. Due to the parallelism scheme we're using in 3-D and the slow speed of the
			# individual alignments we use a slightly different strategy than in 2-D. We make a binary tree from the first 2^n particles and
			# compute pairwise alignments until we get an average out. 
		
			nseed=2**int(floor(log(nptcl)/log(2.0)))	# we stick with powers of 2 for this to make the tree easier to collapse
			
			#########TODO
			
			if options.savesteps :
				ref.write_image("class_%02d.hdf"%ic,-1)
		
		# Now we iteratively refine a single class
		for it in range(options.iter):
			# In 2-D class-averaging, each alignment is fast, so we send each node a class-average to make
			# in 3-D each alignment is very slow, so we use a single ptcl->ref alignment as a task
			tasks=[]
			for p in ptcls:
				task=Align3DTask(ref,["cache",options.input,p],p,"Ptcl %d in iter %d"%(p,it),options.mask,options.normproc,options.preprocess,
					options.ncoarse,options.align,options.aligncmp,options.ralign,options.raligncmp,options.shrink,options.shrinkrefine,options.verbose-1)
				tasks.append(task)
			
			# start the alignments running
			tids=etc.send_tasks(tasks)
			if options.verbose : print "%d tasks queued in class %d iteration %d"%(len(tids),ic,it) 

			# Wait for alignments to finish and get results
			results=get_results(etc,tids,options.verbose)

			if options.verbose>2 : pprint("Results:",results)
			
			ref=make_average(options.input,results,options.averager)		# the reference for the next iteration

			if options.sym!=None : symmetrize(ref,options.sym)
			
			if options.savesteps :
				ref.write_image("class_%02d.hdf"%ic,-1)

		ref.write_image(options.output,ic)

	E2end(logger)
	
def make_average(ptcl_file,align_parms,averager):
	"""Will take a set of alignments and an input particle stack filename and produce a new class-average"""
	
	avgr=Averagers.get(averager[0], averager[1])
	for i,ptcl_parms in enumerate(align_parms):
		ptcl=EMData(ptcl_file,i)
		ptcl.process_inplace("xform",{"transform":ptcl_parms[0][1]})
		avgr.add_image(ptcl)
		
	return avgr.finish()

def symmetrize(ptcl,sym):
	"Impose symmetry in the standard orientation in-place. Does not reorient particle before symmetrization"
	xf = Transform()
	xf.to_identity()
	nsym=xf.get_nsym(sym)
	orig=ptcl.copy()
	for i in range(1,nsym):
		dc=orig.copy()
		dc.transform(xf.get_sym(sym,i))
		ptcl.add(dc)
	ptcl.mult(1.0/nsym)	
	
	return

def get_results(etc,tids,verbose):
	"""This will get results for a list of submitted tasks. Won't return until it has all requested results.
	aside from the use of options["ptcl"] this is fairly generalizable code. """
	
	# wait for them to finish and get the results
	# results for each will just be a list of (qual,Transform) pairs
	results=[0]*len(tids)		# storage for results
	ncomplete=0
	tidsleft=tids[:]
	while 1:
		time.sleep(5)
		proglist=etc.check_task(tidsleft)
		nwait=0
		for i,prog in enumerate(proglist):
			if prog==-1 : nwait+=1
			if prog==100 :
				r=etc.get_results(tidsleft[i])		# results for a completed task
				ptcl=r[0].options["ptcl"]			# get the particle number from the task rather than trying to work back to it
				results[ptcl]=r[1]["final"]			# this will be a list of (qual,Transform)
				ncomplete+=1
		
		tidsleft=[j for i,j in enumerate(tidsleft) if proglist[i]!=100]		# remove any completed tasks from the list we ask about
		if verbose:
			print "  %d tasks, %d complete, %d waiting to start        \r"%(len(tids),ncomplete,nwait)
			sys.stdout.flush()
	
		if len(tidsleft)==0: break
		
	return results

class Align3DTask(EMTask):
	"""This is a task object for the parallelism system. It is responsible for aligning one 3-D volume to another, with a variety of options"""

	def __init__(self,fixedimage,image,ptcl,label,mask,normproc,preprocess,ncoarse,align,aligncmp,ralign,raligncmp,shrink,shrinkrefine,verbose):
		"""fixedimage and image may be actual EMData objects, or ["cache",path,number]
	label is a descriptive string, not actually used in processing
	ptcl is not used in executing the task, but is for reference
	other parameters match command-line options from e2classaverage3d.py
	Rather than being a string specifying an aligner, 'align' may be passed in as a Transform object, representing a starting orientation for refinement"""
		data={}
		data={"fixedimage":fixedimage,"image":image}
		EMTask.__init__(self,"ClassAv3d",data,{},"")

		self.options={"ptcl":ptcl,"label":label,"mask":mask,"normproc":normproc,"preprocess":preprocess,"ncoarse":ncoarse,"align":align,"aligncmp":aligncmp,"ralign":raligncmp,"shrink":shrink,"shrinkrefine":shrinkrefine,"verbose":verbose}
	
	def execute(self,callback=None):
		"""This aligns one volume to a reference and returns the alignment parameters"""
		options=self.options
		if options["verbose"] : print "Aligning ",options["label"]

		if isinstance(self.data["fixedimage"],EMData) :
			fixedimage=self.data["fixedimage"]
		else : fixedimage=EMData(self.data["fixedimage"][1],self.data["fixedimage"][2])
		
		if isinstance(self.data["image"],EMData) :
			image=self.data["image"]
		else : image=EMData(self.data["image"][1],self.data["image"][2])
		
		# Preprocessing currently applied to both volumes. Often 'fixedimage' will be a reference, though, 
		# so may need to rethink whether it should be treated identically. Similar issues in 2-D single particle
		# refinement ... handled differently at the moment
		
		# Make the mask first, use it to normalize (optionally), then apply it 
		mask=EMData(image["nx"],image["ny"],image["nz"])
		mask.to_one()
		if options["mask"] != None:
			mask.process_inplace(options["mask"][0],options["mask"][1])
		
		# normalize
		if options["normproc"] != None:
			if options["normproc"][0]=="normalize.mask" : options["normproc"][1]["mask"]=mask
			fixedimage.process_inplace(options["normproc"][0],options["normproc"][1])
			image.process_inplace(options["normproc"][0],options["normproc"][1])
		
		# preprocess
		if options["preprocess"] != None:
			fixedimage.process_inplace(options["preprocess"][0],options["preprocess"][1])
			image.process_inplace(options["preprocess"][0],options["preprocess"][1])
		
		# Shrinking both for initial alignment and reference
		if options["shrink"]!=None and options["shrink"]>1 :
			sfixedimage=fixedimage.process("math.meanshrink",{"n":options["shrink"]})
			simage=image.process("math.meanshrink",{"n":options["shrink"]})
		else :
			sfixedimage=fixedimage
			simage=image
			
		if options["shrinkrefine"]!=None and options["shrinkrefine"]>1 :
			if options["shrinkrefine"]==options["shrink"] :
				s2fixedimage=sfixedimage
				s2image=simage
			else :
				s2fixedimage=fixedimage.process("math.meanshrink",{"n":options["shrinkrefine"]})
				s2image=image.process("math.meanshrink",{"n":options["shrinkrefine"]})
		else :
			s2fixedimage=fixedimage
			s2image=image
			

		# If a Transform was passed in, we skip coarse alignment
		if isinstance(options["align"],Transform):
			bestcoarse=[{"score":1.0,"xform.align3d":options["align"]}]
		# this is the default behavior, seed orientations come from coarse alignment
		else:
			# returns an ordered vector of Dicts of length options.ncoarse. The Dicts in the vector have keys "score" and "xform.align3d"
			bestcoarse=simage.xform_align_nbest(options["align"][0],sfixedimage,options["align"][1],options["ncoarse"],options["aligncmp"][0],options["aligncmp"][1])

		# verbose printout
		if options["verbose"]>1 :
			for i,j in enumerate(bestcoarse): print "coarse %d. %1.5g\t%s"%(i,j["score"],str(j["xform.align3d"]))

		if options["ralign"]!=None :
			# Now loop over the individual peaks and refine each
			bestfinal=[]
			for bc in bestcoarse:
				options["ralign"][1]["xform.align3d"]=bc["xform.align3d"]
				ali=s2image.align(options["ralign"][0],s2fixedimage,options["ralign"][1],options["raligncmp"][0],options["raligncmp"][1])
				bestfinal.append({"score":ali["score"],"xform.align3d":ali["xform.align3d"]})

			# verbose printout of fine refinement
			if options["verbose"]>1 :
				for i,j in enumerate(bestfinal): print "fine %d. %1.5g\t%s"%(i,j["score"],str(j["xform.align3d"]))
		else : bestfinal=bestcoarse
		
		bestfinal.sort()
		if options.verbose : print "Best %1.5g\t %s"%(bestfinal[0]["score"],str(bestfinal[0]["xform.align3d"]))

		if options.verbose: print "Done aligning ",options["label"]
		
		return {"final":bestfinal,"coarse":bestcoarse}


def classmx_ptcls(classmx,n):
	"""Scans a classmx file to determine which images are in a specific class. classmx may be a filename or an EMData object.
	returns a list of integers"""
	
	if isinstance(classmx,str) : classmx=EMData(classmx,0)
	
	plist=[i.y for i in classmx.find_pixels_with_value(float(n))]
	
	return plist


	
if __name__ == "__main__":
    main()
