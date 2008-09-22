#
# Author: Pawel A.Penczek, 09/09/2006 (Pawel.A.Penczek@uth.tmc.edu)
# Copyright (c) 2000-2006 The University of Texas - Houston Medical School
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
#
from EMAN2_cppwrap import *
from global_def import *

def project(volume, params, radius):
        # angles phi, theta, psi
	from fundamentals import rot_shift2D
        myparams = {"transform":Transform({"type":"spider","phi":params[0],"theta":params[1],"psi":params[2]}), "radius":radius}
        proj = volume.project("pawel", myparams)
	if(params[3]!=0. or params[4]!=0.): 
		params2 = {"filter_type" : Processor.fourier_filter_types.SHIFT, "x_shift" : params[3], "y_shift" : params[4], "z_shift" : 0.0}
		proj=Processor.EMFourierFilter(proj, params2)
		#proj = rot_shift2D(proj, sx = params[3], sy = params[4], interpolation_method = "linear")
	proj.set_attr_dict({'phi':params[0], 'theta':params[1], 'psi':params[2], 's2x':-params[3], 's2y':-params[4]})
	proj.set_attr_dict({'active':1, 'ctf_applied':0})
	return  proj

"""
Temporarily disabled as list cannot be passed to projector.
def prl(vol, params, radius, stack = None):
	from fundamentals import rot_shift2D
	for i in xrange(len(params)):
        	myparams = {"angletype":"SPIDER", "anglelist":params[i][0:3], "radius":radius}
        	proj = vol.project("pawel", myparams)
		if(params[i][3]!=0. or params[i][4]!=0.): proj = rot_shift2D(proj, sx = params[i][3], sy = params[i][4], interpolation_method = "linear")
		proj.set_attr_dict({'phi':params[i][0], 'theta':params[i][1], 'psi':params[i][2], 's2x':-params[i][3], 's2y':-params[i][4]})
		proj.set_attr_dict({'active':1, 'ctf_applied':0})
		if(stack):
			proj.write_image(stack, i)
		else:
			if(i == 0): out= []
			out.append(proj)
	if(stack): return
	else:      return out
"""
def prj(vol, params, stack = None):
	volft,kb = prep_vol(vol)
	for i in xrange(len(params)):
		proj = prgs(volft, kb, params[i])
		proj.set_attr_dict({'phi':params[i][0], 'theta':params[i][1], 'psi':params[i][2], 's2x':-params[i][3], 's2y':-params[i][4]})
		proj.set_attr_dict({'active':1, 'ctf_applied':0})
		if(stack):
			proj.write_image(stack, i)
		else:
			if(i == 0): out= []
			out.append(proj)
	if(stack):  return
	else:       return out

def prgs(volft, kb, params):
	#  params:  phi, theta, psi, sx, sy
	from fundamentals import fft
	EULER_SPIDER = Transform3D.EulerType.SPIDER
	R= Transform3D(EULER_SPIDER, params[0], params[1], params[2])
	temp = volft.extractplane(R,kb)
	temp.fft_shuffle()
	temp.center_origin_fft()

	if(params[3]!=0. or params[4]!=0.):
		filt_params = {"filter_type" : Processor.fourier_filter_types.SHIFT,
				  "x_shift" : params[3], "y_shift" : params[4], "z_shift" : 0.0}
		temp=Processor.EMFourierFilter(temp, filt_params)
	temp.do_ift_inplace()
	temp.set_attr_dict({'phi':params[0], 'theta':params[1], 'psi':params[2], 's2x':-params[3], 's2y':-params[4]})
	temp.set_attr_dict({'active':1, 'ctf_applied':0, 'npad':2})
	temp.depad()
	return temp

def prgs1d( prjft, kb, params ):
	from fundamentals import fft
	from math import cos, sin, pi

	alpha = params[0]
	shift = params[1]

	tmp = alpha/180.0*pi

	nuxnew =  cos(tmp)
	nuynew = -sin(tmp)
	
	line = prjft.extractline(kb, nuxnew, nuynew)
	line = fft(line)

	M = line.get_xsize()/2
	Util.cyclicshift( line, {"dx":M, "dy":0, "dz":0} )
	line = Util.window( line, M, 1, 1, 0, 0, 0 )

	if shift!=0:
		filt_params = {"filter_type" : Processor.fourier_filter_types.SHIFT,
		   	       "x_shift" : shift, "y_shift" : 0.0, "z_shift" : 0.0}
		line = Processor.EMFourierFilter(temp, filt_params)

	line.set_attr_dict( {'alpha':alpha, 's1x':shift} )
	return line

def prg(volume, params):
	"""Given a volume, a set of projection angles, and Kaiser-Bessel
	   window parameters, use gridding to generate projection
	"""
	volft,kb = prep_vol(volume)
	return  prgs(volft,kb,params)

def prep_vol(vol):
	# prepare the volume
	M     = vol.get_xsize()
	# padd two times
	npad  = 2
	N     = M*npad
	# support of the window
	K     = 6
	alpha = 1.75
	r     = M/2
	v     = K/2.0/N
	kb    = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
	volft = vol.copy()
	volft.divkbsinh(kb)
	volft = volft.norm_pad(False, npad)
	volft.do_fft_inplace()
	volft.center_origin_fft()
	volft.fft_shuffle()
	return  volft,kb

def next_type(typlst, max):
	nlen = len(typlst)
	typlst[nlen-1] += 1
	for i in xrange(nlen-1, 0, -1):
		if typlst[i] == max:
			typlst[i] = 0
			typlst[i-1] += 1
	return typlst[0] < max

def change_ang(ang, type):
	if type == 0:
		return ang

	if type == 1:
		r = 180.0 - ang
		if r < 0.0: r = r + 360.0
		return r

	if type == 2:
		r = ang - 180.0
		if r < 0.0: r = r + 360.0
		return r

	assert type==3
	return 360.0 - ang

def exhaust_ang(angs, anglst, func, data=None, info=None):
	from utilities import amoeba
	origin = angs[:]
	optpsi = angs[:]
	funval = func(angs, data)

	typlst = [0]*len(anglst)

	lowers = [0.0]*len(angs)
	uppers = [360.0]*len(angs)

	while( next_type(typlst, 4) ):
		work_angs = optpsi[:]
		for i in xrange( len(typlst) ):
			iang = anglst[i]
			ityp = typlst[i]
			work_angs[iang] = change_ang(origin[iang], ityp)
		#curt_angs = work_angs
		#curt_funval = func(work_angs, data)
	
		curt_angs,curt_funval = rollover(work_angs, lowers, uppers, func, data=data)

		#print 'typlst:', typlst
		info.write( '	     typlst,funval,best:' + str(typlst) + " " + str(curt_funval) + " " + str(funval) + "\n" )
		info.flush()

		if( curt_funval > funval ):
			optpsi = curt_angs[:]
			funval = curt_funval
	return optpsi,funval

def drop_angle_doc(filename, phis, thetas, psis, comment=None):
	from utilities import dropSpiderDoc
	table = []
	for i in xrange( len(phis) ): table.append( [ phis[i], thetas[i], psis[i] ] )
	dropSpiderDoc(filename, table, comment)


###############################################################################################
## COMMON LINES NEW VERSION ###################################################################

# plot angles, map on half-sphere
# agls: [[phi0, theta0, psi0], [phi1, theta1, psi1], ..., [phin, thetan, psin]]
def plot_angles(agls):
	from math      import cos, sin, fmod, pi
	from utilities import model_blank

	# var
	nx = 256
	im = model_blank(nx, nx)
	c  = 2
	kc = 10

	# draw reperes
	for i in xrange(nx):
		im.set_value_at(i, int(nx / 2.0), 0.006)
		im.set_value_at(int(nx / 2.0), i, 0.006)
	
	# draw the circles
	lth = range(0, 90, kc)
	lth.append(90)
	
	for th in lth:
		
		if th == 90: color = 0.03
		else:        color = 0.006

		rc  = sin((float(th) / 180.0) * pi)
		rc *= (nx - 1)
		
		for n in xrange(3600):
			a  = (n / 1800.0) * pi
			px = nx / 2.0 + (rc - 1) / 2.0 * cos(a)
			py = nx / 2.0 + (rc - 1) / 2.0 * sin(a)
			im.set_value_at(int(px), int(py), color)
	
	# for each angles plot on circle area
	# agsl: [phi, theta, phi]
	for i in xrange(len(agls)):
		rc  = sin((agls[i][1] / 180.0) * pi)
		rc *= ((nx - 1) / 2)
	
		px  = nx / 2.0 + rc * cos((fmod(agls[i][0] + 90, 360.0) / 180.0) * pi)
		py  = nx / 2.0 + rc * sin((fmod(agls[i][0] + 90, 360.0) / 180.0) * pi)
	
		if px > nx - 1: px = nx - 1
		if px < 0:  px = 0
		px = int(px)

		if py > nx - 1: py = nx - 1
		if py < 0:  py = 0
		py = int(py)

		if agls[i][1] > 90: style = 2
		else:              style = 1
		
	
		for cx in xrange(px - c, px + c + 1, style):
			if cx > nx - 1: cx = nx - 1
			if cx < 0:  cx = 0
			im.set_value_at(cx, py, 1.0)
			
		for cy in xrange(py - c, py + c + 1, style):
			if cy > nx - 1: cy = nx - 1
			if cy < 0:  cy = 0
			im.set_value_at(px, cy, 1.0)

	return im

# transform an image to sinogramm
def cml_sinogram(image2D, diameter):
	from math         import cos, sin
	from fundamentals import fft
	from filter       import filt_tanh
	
	M_PI  = 3.141592653589793238462643383279502884197
	
	# prepare 
	M = image2D.get_xsize()
	# padd two times
	npad  = 2
	N     = M * npad
	# support of the window
	K     = 6
	alpha = 1.75
	r     = M / 2
	v     = K / 2.0 / N

	kb     = Util.KaiserBessel(alpha, K, r, K / (2. * N), N)
	volft  = image2D.average_circ_sub()  	# ASTA - in spider
	volft.divkbsinh(kb)		  	# DIVKB2 - in spider
	volft  = volft.norm_pad(False, npad)
	volft.do_fft_inplace()
	volft.center_origin_fft()
	volft.fft_shuffle()
	cst = 1#  5  use to be 5
	nangle = int(M_PI * r * cst)		# pi * r * cst
	dangle = M_PI / nangle			# 180 * sino

	data = []
	for j in xrange(nangle):
		nuxnew =  cos(dangle * j)
		nuynew = -sin(dangle * j)

		line = volft.extractline(kb, nuxnew, nuynew)

		# filter to omitted u**2  TODO
		#line = filt_tanh(line, 0.25, 0.25)
	
		rlines = fft(line)
		data.append(rlines.copy())
	
	e = EMData()
	e.set_size(data[0].get_xsize() ,len(data), 1)
	for n in xrange(len(data)):
		nx = data[n].get_xsize()
		for i in xrange(nx): e.set_value_at(i, n, data[n].get_value_at(i))

	Util.cyclicshift(e, {"dx":M, "dy":0, "dz":0} )

	return Util.window(e, diameter, len(data), 1, 0, 0, 0)

# write the head of the logfile
def cml_head_log(stack, outdir, delta, ir, ou, rand_seed, ncpu, refine, trials):
	from utilities import print_msg, even_angles

	anglst   = even_angles(delta, 0.0, 89.9, 0.0, 359.9, 'S')
	n_anglst = len(anglst)
	nprj     = EMUtil.get_image_count(stack)
	
	print_msg('Input stack                 : %s\n'     % stack)
	print_msg('Number of projections       : %d\n'     % nprj)
	print_msg('Output directory            : %s\n'     % outdir)
	print_msg('Angular step                : %5.2f\n'  % delta)	
	print_msg('Inner particle radius       : %5.1f\n'  % ir)	
	print_msg('Outer particle radius       : %5.2f\n'  % ou)	
	print_msg('Random seed                 : %i\n'     % rand_seed)
	print_msg('Number of trials            : %d\n'     % trials)
	print_msg('Number of cpus              : %i\n'     % ncpu)
	if refine:
		print_msg('Refinement                  : True\n')
	else:
		print_msg('Refinement                  : False\n')
	print_msg('Number of angles            : %i\n\n'   % n_anglst)

# write the end of the logfile
def cml_end_log(Prj, disc):
	from utilities import print_msg
	print_msg('\n\n')
	for i in xrange(len(Prj)): print_msg('Projection #%s: phi %10.5f    theta %10.5f    psi %10.5f\n' % (str(i).rjust(3, '0'), Prj[i].phi, Prj[i].theta, Prj[i].psi))
	print_msg('\nDiscrepancy: %10.3f\n' % abs(disc))

# write the end of the logfile for the version MPI
def cml_end_mpilog(Prj, disc):
	f = open('.tmp_txt_1a32b4', 'a')
	f.write('\n\n')
	for i in xrange(len(Prj)): f.write('Projection #%s: phi %10.5f    theta %10.5f    psi %10.5f\n' % (str(i).rjust(3, '0'), Prj[i].phi, Prj[i].theta, Prj[i].psi))
	f.write('\nDiscrepancy: %10.3f\n' % abs(disc))

# export list of angles
def cml_export_txtagls(namefile, Prj, Cst, disc, title):
	import time

	angfile = open(namefile, 'a')

	angfile.write('|%s|-----------------------------------------------%s---------\n' % (title, time.ctime()))
	for i in xrange(Cst['nprj']):
		if i == Cst['iprj']:
			angfile.write('%10.3f\t%10.3f\t%10.3f <--\n' % (Prj[i].phi, Prj[i].theta, Prj[i].psi))
		else:
			angfile.write('%10.3f\t%10.3f\t%10.3f\n'     % (Prj[i].phi, Prj[i].theta, Prj[i].psi))
			
	angfile.write('\nDiscrepancy: %10.3f\n\n' % abs(disc))
	angfile.close()

# export the progress of the find_struc function
def cml_export_progress(namefile, Prj, Cst, disc, cmd):
	#try:	         infofile = open(namefile, 'a')
	#except IOError: infofile = open(namefile, 'w')
	infofile = open(namefile, 'a')

	if cmd == 'progress':
		txt_i    = str(Cst['iprj']).rjust(3, '0')
		txt_a    = str(Prj[Cst['iprj']].pos_agls).rjust(3, '0')
		txt      = 'Prj: %s Agls: %s >> Agls (phi, theta, psi): %10.3f %10.3f %10.3f   Disc: %10.3f' % (txt_i, txt_a, Prj[Cst['iprj']].phi, Prj[Cst['iprj']].theta, Prj[Cst['iprj']].psi, abs(disc))
		if Prj[Cst['iprj']].mirror:
			infofile.write(txt + ' mirror\n')
		else:
			infofile.write(txt + '\n')

	elif cmd == 'choose':
		infofile.write('-------------------------------------------------------------------------------------------------\n')
		if Prj[Cst['iprj']].mirror:
			infofile.write('>> Choose angles (phi, theta, psi):           %10.3f %10.3f %10.3f   Disc: %10.3f mirror\n' % (Prj[Cst['iprj']].phi, Prj[Cst['iprj']].theta, Prj[Cst['iprj']].psi, abs(disc)))
		else:
			infofile.write('>> Choose angles (phi, theta, psi):           %10.3f %10.3f %10.3f   Disc: %10.3f\n' % (Prj[Cst['iprj']].phi, Prj[Cst['iprj']].theta, Prj[Cst['iprj']].psi, abs(disc)))

	elif cmd == 'mirror':
		infofile.write('                after apply mirror:           %10.3f %10.3f %10.3f\n' % (Prj[Cst['iprj']].phi, Prj[Cst['iprj']].theta, Prj[Cst['iprj']].psi))

	elif cmd == 'passed':
		txt_i    = str(Cst['iprj']).rjust(3, '0')
		txt      = 'Prj: %s    ' % (txt_i)
		infofile.write(txt + 'passed \n')

	elif cmd == 'iteration':
		txt      = 'Iteration: %7.1f    ' % (disc)
		infofile.write(txt + '\n')

	elif cmd == 'new':
		infofile.write('\n')
		
	infofile.close()

# open and transform projections
def cml_open_proj(stack, ir, ou):
	from projection  import cml_sinogram
	from utilities   import get_im, model_circle

	# ----- define structures data ---------------------------------
	class Projection:
		def __init__ (self, sino, pos_agls, pos_psi, mirror, active):
			self.sino      = sino     # sinogram
			self.pos_agls  = pos_agls # orientation angles position in list even_angles
			self.pos_psi   = pos_psi  # position of psi (psi = pos_psi * d_psi)
			self.mirror    = mirror   # the angle have a opposite direction
			self.active    = active   # if the sinogram is actived to search orientation
			self.phi       = 0.0      # value of phi if given
			self.theta     = 0.0      # value of theta if given
			self.psi       = 0.0      # value of psi if given

		def __str__(self):
			#txt  = 'pos_agls: %d   pos_psi: %d   mirror: %s   active: %s\n' % (self.pos_agls, self.pos_psi, self.mirror, self.active)
			txt = 'phi: %6.2f   theta: %6.2f   psi: %6.2f   mirror: %s' % (self.phi, self.theta, self.psi, self.mirror) 
			return txt

	nprj = EMUtil.get_image_count(stack)

	if stack.split(':')[0] == 'bdb':
		BDB = True
		DB  = db_open_dict(stack)
        else:   BDB = False

	Prj        = []
	flagheader = False
	ct_agl     = 0
	for i in xrange(nprj):
		Prj.append(Projection(None, -1, -1, False, False))
		if BDB: image = DB[i]
		else:	image = get_im(stack, i)
		if(i == 0):
			nx = image.get_xsize()
			if(ou < 1):
				ou = nx//2 - 1
			else:
				ou = int(ou)//2
				ou = 2*ou +1
			diameter = 2*ou+1
			mask2D = model_circle(ou, nx, nx)
			circ = mask2D.copy()
			if(ou > 1): circ -= model_circle(ou-1, nx, nx)
			if(ir > 0):  mask2D -= model_circle(ir, nx, nx)
		[mean_a,sigma,imin,imax] = Util.infomask(image, circ, True)
		image -= mean_a
		Util.mul_img(image, mask2D )

		Prj[i].sino = cml_sinogram(image, diameter)
		try:
			Prj[i].phi    = image.get_attr('phi')
			Prj[i].theta  = image.get_attr('theta')
			Prj[i].psi    = image.get_attr('psi')
			if Prj[i].phi != 0 or Prj[i].theta != 0 or Prj[i].psi != 0: ct_agl += 1
		except RuntimeError:
			pass

	if ct_agl >= (nprj - 1): flagheader = True
	else:                    flagheader = False

	#print_msg('Angles detected in header   : %s\n'     % flagheader)

	if BDB: DB.close()

	'''
	if FILTER:
		val = []
		for n in xrange(data.get_xsize()): val.append(float(n))
		from filter import filt_table, filt_tanl
		data = filt_table(data, val)
		data = filt_tanl(data, 0.15, 0.05)
		#data.write_image('stackd10_after_filt.hdf', i)
	'''

	return Prj

# compute common lines in 3D
def cml_cmlines_3D(Prj):
	from utilities import common_line_in3D

	# vars
	nprj   = len(Prj)
	nlines = ((nprj - 1) * nprj) / 2
	l_phs  = [0.0] * nlines  # angle phi of the common lines
	l_ths  = [0.0] * nlines  # angle theta of the common lines
	n      = 0
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			l_phs[n], l_ths[n] = common_line_in3D(Prj[i].phi, Prj[i].theta, Prj[j].phi, Prj[j].theta)
			n += 1

	return l_phs, l_ths

# compute the weight of the common lines
def cml_weights(Prj):
	from projection import cml_cmlines_3D
	from math       import fmod
	
	# vars
	tol    = 6
	nprj   = len(Prj)
	nlines = ((nprj - 1) * nprj) / 2
	weights = [1.0]*nlines
	"""
	# remove mirror if applied
	for i in xrange(nprj):
		if Prj[i].mirror:
			Prj[i].phi   = fmod(Prj[i].phi + 180.0, 360.0)
			Prj[i].theta = 180.0 - Prj[i].theta

	# compute the angles of the common lines in space
	phi, theta = cml_cmlines_3D(Prj)

	# search the sames cm lines
	mem_i_same = {}                  ## TODO dict change to list
	ocp_same   = [0] * nlines
	for i in xrange(nlines - 1):
		mem_i_same[i] = None
		v = []
		flag = False
		if ocp_same[i] == 0:
			for j in xrange(i + 1, nlines):
				if ocp_same[j] == 0:
					dist = (phi[i] - phi[j]) ** 2 + (theta[i] - theta[j]) ** 2
					if dist < tol:
						v.append(j)
						ocp_same[j] = 1
						flag = True
		if flag: mem_i_same[i] = v

	# create the new vector n_phi n_theta without
	n_phi, n_theta = [], []
	LUT   = []
	index = 0
	for n in xrange(nlines):
		if ocp_same[n] == 0:
			n_phi.append(phi[n])
			n_theta.append(theta[n])
			LUT.append(n)
			index += 1

	# compute the weights with the new list phi and theta
	n_weights = Util.vrdg(n_phi, n_theta)

	# compute the new weights according the sames cm lines
	weights = [-1] * nlines
	for n in xrange(index): weights[LUT[n]] = n_weights[n]
	for n in xrange(nlines - 1):
		if mem_i_same[n] is not None:
			val        = weights[n]
			nval       = val / (len(mem_i_same[n]) + 1)
			weights[n] = nval
			for i in mem_i_same[n]: weights[i] = nval

	# re-apply mirror if neeed
	for i in xrange(nprj):
		if Prj[i].mirror:
			Prj[i].phi   = fmod(Prj[i].phi + 180, 360)
			Prj[i].theta = 180 - Prj[i].theta
	"""
	# return the weights
	return weights

# compute the common lines in sino
def get_common_line_angles(phi1, theta1, psi1, phi2, theta2, psi2, nangle):
	from math import fmod
	SPIDER = Transform3D.EulerType.SPIDER

	R1    = Transform3D(SPIDER,phi1,theta1,psi1);
	R2    = Transform3D(SPIDER,phi2,theta2,psi2);
	R2T   = R2.inverse();
	R2to1 = R1*R2T;

	eulerR2to1 = R2to1.get_rotation(SPIDER);
	phiR2to1   = eulerR2to1["phi"];
	thetaR2to1 = eulerR2to1["theta"];
	psiR2to1   = eulerR2to1["psi"];

	alphain1 = fmod(psiR2to1 + 270.0,  360.0)
	alphain2 = fmod(-phiR2to1 + 270.0, 360.0)

	if alphain1 < 0:
		alpha1 = 180 - alphain1
	else:
		alpha1 = alphain1

	if alphain2 < 0:
		alpha2 = 180 - alphain2
	else:
		alpha2 = alphain2
		
	n1 = int(nangle * (fmod(alpha1, 180.0) / 180.0)) 
	n2 = int(nangle * (fmod(alpha2, 180.0) / 180.0))

	return [alphain1, alphain2, n1, n2]

# compute discrepancy according the projections
def cml_disc_proj(Prj):
	from projection import cml_weights, get_common_line_angles
	from math       import pi, fmod

	weights = cml_weights(Prj)

	nprj   = len(Prj)
	nangle = Prj[0].sino.get_ysize()
	d_psi  = pi / nangle
	com    = [[] for i in xrange(((nprj - 1) * nprj) / 2)]

	# compute the common lines
	count = 0
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			com[count] = get_common_line_angles(Prj[i].phi, Prj[i].theta, Prj[i].psi, Prj[j].phi, Prj[j].theta, Prj[j].psi, nangle)
			count += 1

	n = 0
	L_tot = 0.0

	# compute the discrepancy for all sinograms
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			L      = Prj[i].sino.cm_euc(Prj[j].sino, com[n][2], com[n][3], com[n][0], com[n][1])
			L_tot += (L * weights[n])
			n     += 1

	disc = -L_tot

	return disc

# compute the discrepancy for the cml_spin_proj
def cml_disc_forspin(Prj, weights, Cst, com, com_m):
	n = 0
	L_tot = 0.0

	# compute the discrepancy for all sinograms
	for i in xrange(Cst['nprj'] - 1):
		for j in xrange(i + 1, Cst['nprj']):
			L      = Prj[i].sino.cm_euc(Prj[j].sino, com[n][2], com[n][3], com[n][0], com[n][1])
			L_tot += (L * weights[n])
			n     += 1

	n = 0
	L_tot_m = 0.0

	# compute the discrepancy for all sinograms with mirror angles
	for i in xrange(Cst['nprj'] - 1):
		for j in xrange(i + 1, Cst['nprj']):
			L_m       = Prj[i].sino.cm_euc(Prj[j].sino, com_m[n][2], com_m[n][3], com_m[n][0], com_m[n][1])
			L_tot_m  += (L_m * weights[n])
			n        += 1
	#nn = n
	#for n in xrange(nn):  print  com[n][2], com[n][3], com[n][0], com[n][1], com_m[n][2], com_m[n][3], com_m[n][0], com_m[n][1]

	#print  "forspin",L_tot,L_tot_m
	#from sys import exit
	# choose the best discrepancy
	if L_tot_m < L_tot:
		mirror = True
		disc   = -L_tot_m
	else:
		mirror = False
		disc   = -L_tot

	return disc, mirror

# compute the discrepancy for the cml_spin_proj
def cml_disc_forspin_init(Prj, weights, Cst, com):
	n = 0
	L_tot = 0.0

	# compute the discrepancy for all sinograms
	for i in xrange(Cst['nprj'] - 1):
		for j in xrange(i + 1, Cst['nprj']):
			if(i != Cst['iprj']):
				if(j != Cst['iprj']):
					L      = Prj[i].sino.cm_euc(Prj[j].sino, com[n][2], com[n][3], com[n][0], com[n][1])
					L_tot += (L * weights[n])
			n += 1

	return L_tot


# compute the discrepancy for the cml_spin_proj
def cml_disc_forspin_full(Prj, weights, Cst, com, com_m, discinit):
	n = 0
	L_tot = discinit

	# compute the discrepancy for all sinograms
	for i in xrange(Cst['nprj'] - 1):
		for j in xrange(i + 1, Cst['nprj']):
			if(i == Cst['iprj'] or j == Cst['iprj']):
				L      = Prj[i].sino.cm_euc(Prj[j].sino, com[n][2], com[n][3], com[n][0], com[n][1])
				L_tot += (L * weights[n])
			n += 1

	n = 0
	L_tot_m = discinit

	# compute the discrepancy for all sinograms with mirror angles
	for i in xrange(Cst['nprj'] - 1):
		for j in xrange(i + 1, Cst['nprj']):
			if(i == Cst['iprj'] or j == Cst['iprj']):
				L_m       = Prj[i].sino.cm_euc(Prj[j].sino, com_m[n][2], com_m[n][3], com_m[n][0], com_m[n][1])
				L_tot_m  += (L_m * weights[n])
			n += 1

	#print  "forspin",L_tot,L_tot_m
	# choose the best discrepancy
	if L_tot_m < L_tot:
		mirror = True
		disc   = -L_tot_m
	else:
		mirror = False
		disc   = -L_tot

	return disc, mirror

# interface between the simplex function to refine the angles and the function to compute the discrepancy
def cml_refine_agls(vec_in, data):
	# vec_in: [phi_i, theta_i, psi_i]
	# data:   [Prj, Cst]

	# unpack
	phi, theta, psi = vec_in
	Prj, Cst        = data

	# prepare the variables
	Prj[Cst['iprj']].phi   = phi
	Prj[Cst['iprj']].theta = theta
	Prj[Cst['iprj']].psi   = psi

	# compute the discrepancy
	disc = cml_disc_proj(Prj)

	return disc

# spin Prj in order to select the best orientation
def cml_spin_proj(Prj, Cst, weights):
	from math import fmod

	# vars
	com     = [[] for i in xrange(Cst['nlines'])]
	com_m   = [[] for i in xrange(Cst['nlines'])]
	#  This is strange, only one has to be mirrored, so why the work is duplicated? PAP
	# prepare angles for the mirror
	phi_m   = fmod(Prj[Cst['iprj']].phi + 180.0, 360.0)
	theta_m = 180.0 - Prj[Cst['iprj']].theta
	psi_m   = 0

	Prj[Cst['iprj']].psi = 0
	#print  Cst
	#print  Cst['iprj']

	#s_time = time.time()
	# compute the common line
	count = 0
	index = 0
	for i in xrange(Cst['nprj'] - 1):
		for j in xrange(i + 1, Cst['nprj']):
			com[count]   = get_common_line_angles(Prj[i].phi, Prj[i].theta, Prj[i].psi, Prj[j].phi, Prj[j].theta, Prj[j].psi, Cst['nangle'])
			if(i == Cst['iprj']):
				com_m[count] = get_common_line_angles(phi_m, theta_m, psi_m, Prj[j].phi, Prj[j].theta, Prj[j].psi, Cst['nangle'])
			elif(j == Cst['iprj']):
				com_m[count] = get_common_line_angles(Prj[i].phi, Prj[i].theta, Prj[i].psi, phi_m, theta_m, psi_m, Cst['nangle'])
			else:
				com_m[count] = com[count]
			count += 1

	#print  'compute the common line time: %8.3f s' % (time.time() - s_time)
	#s_time = time.time()
	#nn = count
	#for n in xrange(nn):  print  com[n][2], com[n][3], com[n][0], com[n][1], com_m[n][2], com_m[n][3], com_m[n][0], com_m[n][1]

	# first value of discrepancy for psi = 0.0
	#print cml_disc_forspin(Prj, weights, Cst, com, com_m)
	disc_init = cml_disc_forspin_init(Prj, weights, Cst, com)
	#print  "disc_init ",disc_init
	disc, mirror = cml_disc_forspin_full(Prj, weights, Cst, com, com_m, disc_init)

	#print  'first value of discrepancy for psi = 0.0 time: %8.3f s' % (time.time() - s_time)
	#s_time = time.time()
	best_psi = 0
	# spin function d_psi to 360
	for n in xrange(1, Cst['npsi']):
		Prj[Cst['iprj']].psi += Cst['d_psi_pi']

		# update common lines
		count = 0
		for i in xrange(Cst['nprj'] - 1):
			for j in xrange(i + 1, Cst['nprj']):
				if i == Cst['iprj']:
					# increase the value by step
					com[count][0]   = com[count][0] + Cst['d_psi_pi']         # a1 + d_psi in degree
					com[count][2]   = com[count][2] + 1                      # n1 + 1

					com_m[count][0] = com_m[count][0] + Cst['d_psi_pi']       # a1 + d_psi in degree
					com_m[count][2] = com_m[count][2] + 1                    # n1 + 1

					# check value
					if com[count][0]   > 360:                 com[count][0]   = 0
					if com_m[count][0] > 360:                 com_m[count][0] = 0
					if com[count][2]   > (Cst['nangle'] - 1):  com[count][2]   = 0
					if com_m[count][2] > (Cst['nangle'] - 1):  com_m[count][2] = 0

				elif j == Cst['iprj']:
					# increase the value by step
					com[count][1]   = com[count][1]   + Cst['d_psi_pi']       # a2 + d_psi in degree
					com_m[count][1] = com_m[count][1] + Cst['d_psi_pi']       # a2 + d_psi in degree

					if com[count][1] > 270 + Cst['d_psi_pi']:
						com[count][1] = 180 - (com[count][1] - 2 * Cst['d_psi_pi'])
				
					if com_m[count][1] > 270 + Cst['d_psi_pi']:
						com_m[count][1] = 180 - (com_m[count][1] - 2 * Cst['d_psi_pi'])
		
					if com[count][1] < 0:   com[count][3] = com[count][3] - 1
					else:                   com[count][3] = com[count][3] + 1

					if com_m[count][1] < 0: com_m[count][3] = com_m[count][3] - 1
					else:                   com_m[count][3] = com_m[count][3] + 1
					
					if com_m[count][3] > (Cst['nangle'] - 1): com_m[count][3] =  0
					if com[count][3]   > (Cst['nangle'] - 1): com[count][3]   =  0

				count += 1

		# compute the new discrepancy
		#print "     AAAAAAAAAA"
		#disc_new, mirror_new = cml_disc_forspin(Prj, weights, Cst, com, com_m)
		disc_new, mirror_new = cml_disc_forspin_full(Prj, weights, Cst, com, com_m, disc_init)
		#from sys import exit
		#exit()

		# choose the best
		if disc_new >= disc:
			disc     = disc_new
			mirror   = mirror_new
			best_psi = Prj[Cst['iprj']].psi
	#print best_psi, mirror, disc
	#print  'next discrepancy time: %8.3f s' % (time.time() - s_time)
	#exit()
	return best_psi, mirror, disc

# export result obtain by the function find_struct
def cml_export_struc(stack, outdir, Prj):
	from projection import plot_angles
	from utilities  import get_im, set_params3D

	if stack.split(':')[0] == 'bdb':
		ST    = db_open_dict(stack)
		BDBIN = True
	else:
		BDBIN = False
	if outdir.split(':')[0] == 'bdb':
		OD     = db_open_dict(outdir + '_structure')
		BDBOUT = True
	else:
		BDBOUT = False
	
	pagls = []
	for i in xrange(len(Prj)):
		if BDBIN: data = ST[i]
		else:     data = get_im(stack, i)
		p = [Prj[i].phi, Prj[i].theta, Prj[i].psi, 0.0, 0.0, 0.0, 0, 1]
		set_params3D(data, p)
		data.set_attr('active', 1)
		if BDBOUT: OD[i] = data
		else: data.write_image(outdir + '/structure.hdf', i)

		# prepare angles to plot
		pagls.append([Prj[i].phi, Prj[i].theta, Prj[i].psi])

	if BDBIN: ST.close()
	if BDBOUT:
		OD.close()
		OD = db_open_dict(outdir + '_plot_agls')

	# plot angles
	im = plot_angles(pagls)
	if BDBOUT:
		OD[0] = im
		OD.close()
	else:	im.write_image(outdir + '/plot_agls.hdf')

# cml init for MPI version
def cml_init_MPI(trials):
	from mpi 	  import mpi_init, mpi_comm_size, mpi_comm_rank, mpi_barrier, MPI_COMM_WORLD
	from utilities    import bcast_number_to_all
	from random       import randint
	import sys
	
	# init
	sys.argv       = mpi_init(len(sys.argv),sys.argv)
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid           = mpi_comm_rank(MPI_COMM_WORLD)

	# chose a random node as a main one
	main_node = 0
	if myid  == 0:	main_node = randint(0, number_of_proc - 1)
	main_node = bcast_number_to_all(main_node, 0)
	mpi_barrier(MPI_COMM_WORLD)

	# define the number of loop per node
	loop = trials / number_of_proc
	if trials % number_of_proc != 0: loop += 1

	return main_node, myid, number_of_proc, loop

# cml init list of rand_seed for trials version
def cml_init_rnd(trials, rand_seed):
	from random import seed, randrange

	if trials == 1: return [rand_seed]
	
	if rand_seed > 0: seed(rand_seed)
	else:             seed()

	r_min = 100
	r_max = 1000000
	f_min = 1
	f_max = 100

	rnd     = []
	itrials = 0
	while itrials < trials:
		val_rnd = randrange(r_min, r_max)
		val_f   = randrange(f_min, f_max)
		val_o   = randrange(0, 2)
		if val_o: val_rnd = int(val_rnd * val_f)
		else:     val_rnd = int(val_rnd / float(val_f))
		if val_rnd not in rnd:
			rnd.append(val_rnd)
			itrials += 1

	return rnd


# main function for sxfind_struct
def cml_find_struc(Prj, delta, outdir, outnum, Iter = 10, rand_seed=1000, refine = False, DEBUG = False):
	from projection import cml_head_log, cml_weights, cml_disc_proj, cml_spin_proj
	from projection import cml_export_txtagls, cml_export_progress, cml_refine_agls
	from utilities  import print_msg, amoeba, even_angles
	from random     import seed, randrange, shuffle
	from copy       import deepcopy
	from math       import pi, fmod
	import time
	import os

	## TO WORK
	search = 'ALL'

	# Init
	if rand_seed > 0: seed(rand_seed)
	else:             seed()

	# Cst
	Cst     = {}
	Cst['nprj']     = len(Prj)
	Cst['npsi']     = 2 * Prj[0].sino.get_ysize()
	Cst['nlines']   = ((Cst['nprj'] - 1) * Cst['nprj']) / 2
	Cst['nangle']   = Prj[0].sino.get_ysize()
	Cst['d_psi']    = pi / Cst['nangle']
	Cst['d_psi_pi'] = Cst['d_psi'] * 180.0 / pi
	Cst['iprj']     = -1

	# Define list of angle randomly distribute
	anglst   = even_angles(delta, 0.0, 89.9, 0.0, 359.9, 'S')
	n_anglst = len(anglst)
	ocp_agls = [-1] * n_anglst               # list of occupied angles
	
	# check if the number of orientations is sufficient
	if n_anglst <= Cst['nprj']:
		print 'Not enough angles in the list of orientation, decrease the value of delta!'
		exit()

	if DEBUG:
		# Compute the discrepancy if the angles are given to debug
		flaggiven = False
		ct_agl    = 0
		for i in xrange(Cst['nprj']):
			if Prj[i].phi != 0 or Prj[i].theta != 0 or Prj[i].psi != 0: ct_agl += 1
		if ct_agl >= Cst['nprj']: flaggiven = True

		if flaggiven:
			for i in xrange(Cst['nprj']): print '%6.2f %6.2f %6.2f' % (Prj[i].phi, Prj[i].theta, Prj[i].psi)
			# compute the discrepancy
			disc = cml_disc_proj(Prj)
			print 'disc given: %10.3f' % disc

	# Init file name to info display
	infofilename = outdir + '/progress_' + str(outnum).rjust(3, '0')
	angfilename  = outdir + '/angles_'   + str(outnum).rjust(3, '0')
	
	# Assign the direction of the first sinograms
	Prj[0].pos_agls = 0     # assign (phi=0, theta=0)
	Prj[0].pos_psi  = 0
	Prj[0].phi      = 0.0
	Prj[0].theta    = 0.0
	Prj[0].psi      = 0.0
	ocp_agls[0]     = 0     # first position angles is occupied by sino 0

	# Assign randomly direction for the others sinograms
	n = 1
	while n < Cst['nprj']:
		i = randrange(1, n_anglst)
		if ocp_agls[i] == -1:
			Prj[n].pos_agls = i
			Prj[n].pos_psi  = randrange(0, Prj[0].sino.get_ysize())
			Prj[n].phi      = anglst[i][0]
			Prj[n].theta    = anglst[i][1]
			Prj[n].psi      = Prj[n].pos_psi * Cst['d_psi_pi']
			ocp_agls[i]     = n
			n += 1

	# compute the first discrepancy
	disc = cml_disc_proj(Prj)
	disc_initial = disc
	# export the first values in the angfile
	cml_export_txtagls(angfilename, Prj, Cst, disc, 'init')

	if DEBUG:
		for i in xrange(Cst['nprj']): print '%6.2f %6.2f %6.2f' % (Prj[i].phi, Prj[i].theta, Prj[i].psi)
		print 'disc init: %10.3f' % disc

	list_prj = range(1, Cst['nprj'])
	from math import exp
	T = 1.0
	F = 0.999
	kiter = -1
	while T>1.0e-5:
		kiter += 1
		cml_export_progress(infofilename, Prj, Cst, kiter, 'iteration')
		# ---------- loop for all sinograms ---------------------------------
		t_start  = time.time()
		shuffle(list_prj)
		ct_prj   = 0
		for iprj in list_prj:
			# count proj
			ct_prj += 1

			if DEBUG:
				print '>>' + str(iprj)
				g_time = time.time()

			# Preserve active sinogram
			Cst['iprj'] = iprj
			best_Prj = deepcopy(Prj[iprj])

			# choose new position randomly from the list of available positions
			old_pos = Prj[iprj].pos_agls
			from random import randrange, random
			search = True
			while search:
				new_pos = randrange(n_anglst)
				if(ocp_agls[new_pos] == -1):
					Prj[iprj].pos_agls = new_pos
					search = False

			# update list of occupied angles
			ocp_agls[old_pos]            = -1
			ocp_agls[Prj[iprj].pos_agls] = iprj

			# change angles
			Prj[iprj].phi	 = anglst[Prj[iprj].pos_agls][0]
			Prj[iprj].theta  = anglst[Prj[iprj].pos_agls][1]
			Prj[iprj].psi	 = 0.0
			Prj[iprj].mirror = False

				
			if DEBUG: s_time = time.time()

			# compute the weight for each common lines with Voronoi
			weights = cml_weights(Prj)
			if DEBUG: 
				print  'weights time: %8.3f s' % (time.time() - s_time)
				s_time = time.time()

			# spin for psi of iprj projection			
			best_psi, mirror, new_disc = cml_spin_proj(Prj, Cst, weights)

			if DEBUG: 
				print  'spin time: %8.3f s' % (time.time() - s_time)
				s_time = time.time()
			# ---- strategy to select the next orientation ----------------------
			difd = new_disc - disc
			if difd < 0.0: accept = True
			else:
				qrd = random()
				drd = exp(-difd/1000.0/T)
			if new_disc >= disc or random()>0.6:
				#accept new one
				disc	 = new_disc
				# tag if mirror
				Prj[iprj].mirror = mirror
				Prj[iprj].psi = best_psi
				# display info
				cml_export_progress(infofilename, Prj, Cst, disc, 'progress')

				# apply mirror if need
				if Prj[iprj].mirror:
					Prj[iprj].phi	 = fmod(Prj[iprj].phi + 180, 360)
					Prj[iprj].theta  = 180 - Prj[iprj].theta
					#  THIS IS STRANGE PAP, shouldn't it be set to False ??
					Prj[iprj].mirror = True

					# display info
					#cml_export_progress(infofilename, Prj, Cst, disc, 'mirror')
			else:
				# revert to the original one
				ocp_agls[Prj[iprj].pos_agls] = -1
				Prj[iprj]                    = deepcopy(best_Prj)
				ocp_agls[Prj[iprj].pos_agls] = iprj
				cml_export_progress(infofilename, Prj, Cst, new_disc, 'passed')
	
			if DEBUG:
				print 'ct_agl: %3d' % ct_agl, 'pos_agls: %3d' % Prj[iprj].pos_agls, 'time: %8.3f s' % (time.time() - s_time)



			if DEBUG:
				tmp1 = cml_disc_proj(Prj)
				print 'Time: %8.3f s' % (time.time() - g_time)
				print 'Disc:', disc, 'check', tmp1, '\n'

			# display info
			cml_export_progress(infofilename, Prj, Cst, disc, 'new')
		ct_prj = 0
		cml_export_txtagls(angfilename, Prj, Cst, disc, str(ct_prj).rjust(3, '0'))
		if( kiter%10 == 0): T*=F

	# ----- refine angles ---------------------------------
	scales = [delta] * (Cst['nprj'] + 2)

	# if refine use simplex
	if refine:
		for iprj in xrange(1, Cst['nprj']):
			# active projection
			Cst['iprj'] = iprj

			# init vec_in
			vec_in   = [Prj[iprj].phi, Prj[iprj].theta, Prj[iprj].psi]
		
			# prepare vec_data
			vec_data = [Prj, Cst]

			# simplex
			optvec, disc, niter = amoeba(vec_in, scales, cml_refine_agls, data = vec_data)

			# assign new angles refine
			Prj[iprj].phi   = optvec[0]
			Prj[iprj].theta = optvec[1]
			Prj[iprj].psi   = optvec[2]

			# info display
			cml_export_txtagls(angfilename, Prj, Cst, disc, 'REFINE %s' % str(iprj).rjust(3, '0'))

			if DEBUG: print '>> refine %d   disc: %10.3f' % (iprj, disc)
	
	return Prj, abs(disc)


# main function for sxfind_struct
def cml_find_struc___(Prj, delta, outdir, outnum, Iter = 10, rand_seed=1000, refine = False, DEBUG = False):
	from projection import cml_head_log, cml_weights, cml_disc_proj, cml_spin_proj
	from projection import cml_export_txtagls, cml_export_progress, cml_refine_agls
	from utilities  import print_msg, amoeba, even_angles
	from random     import seed, randrange, shuffle
	from copy       import deepcopy
	from math       import pi, fmod
	import time
	import os

	## TO WORK
	search = 'ALL'

	# Init
	if rand_seed > 0: seed(rand_seed)
	else:             seed()

	# Cst
	Cst     = {}
	Cst['nprj']     = len(Prj)
	Cst['npsi']     = 2 * Prj[0].sino.get_ysize()
	Cst['nlines']   = ((Cst['nprj'] - 1) * Cst['nprj']) / 2
	Cst['nangle']   = Prj[0].sino.get_ysize()
	Cst['d_psi']    = pi / Cst['nangle']
	Cst['d_psi_pi'] = Cst['d_psi'] * 180.0 / pi
	Cst['iprj']     = -1

	# Define list of angle randomly distribute
	anglst   = even_angles(delta, 0.0, 89.9, 0.0, 359.9, 'S')
	n_anglst = len(anglst)
	ocp_agls = [-1] * n_anglst               # list of occupied angles
	
	# check if the number of orientations is sufficient
	if n_anglst <= Cst['nprj']:
		print 'Not enough angles in the list of orientation, decrease the value of delta!'
		exit()

	if DEBUG:
		# Compute the discrepancy if the angles are given to debug
		flaggiven = False
		ct_agl    = 0
		for i in xrange(Cst['nprj']):
			if Prj[i].phi != 0 or Prj[i].theta != 0 or Prj[i].psi != 0: ct_agl += 1
		if ct_agl >= Cst['nprj']: flaggiven = True

		if flaggiven:
			for i in xrange(Cst['nprj']): print '%6.2f %6.2f %6.2f' % (Prj[i].phi, Prj[i].theta, Prj[i].psi)
			# compute the discrepancy
			disc = cml_disc_proj(Prj)
			print 'disc given: %10.3f' % disc

	# Init file name to info display
	infofilename = outdir + '/progress_' + str(outnum).rjust(3, '0')
	angfilename  = outdir + '/angles_'   + str(outnum).rjust(3, '0')
	
	# Assign the direction of the first sinograms
	Prj[0].pos_agls = 0     # assign (phi=0, theta=0)
	Prj[0].pos_psi  = 0
	Prj[0].phi      = 0.0
	Prj[0].theta    = 0.0
	Prj[0].psi      = 0.0
	ocp_agls[0]     = 0     # first position angles is occupied by sino 0

	# Assign randomly direction for the others sinograms
	n = 1
	while n < Cst['nprj']:
		i = randrange(1, n_anglst)
		if ocp_agls[i] == -1:
			Prj[n].pos_agls = i
			Prj[n].pos_psi  = randrange(0, Prj[0].sino.get_ysize())
			Prj[n].phi      = anglst[i][0]
			Prj[n].theta    = anglst[i][1]
			Prj[n].psi      = Prj[n].pos_psi * Cst['d_psi_pi']
			ocp_agls[i]     = n
			n += 1

	# compute the first discrepancy
	disc = cml_disc_proj(Prj)

	# export the first values in the angfile
	cml_export_txtagls(angfilename, Prj, Cst, disc, 'init')

	if DEBUG:
		for i in xrange(Cst['nprj']): print '%6.2f %6.2f %6.2f' % (Prj[i].phi, Prj[i].theta, Prj[i].psi)
		print 'disc init: %10.3f' % disc

	list_prj = range(1, Cst['nprj'])
	for kiter in xrange(Iter):
		# ---------- loop for all sinograms ---------------------------------
		t_start  = time.time()
		shuffle(list_prj)
		ct_prj   = 0
		for iprj in list_prj:
			# count proj
			ct_prj += 1

			if DEBUG:
				print '>>' + str(iprj)
				g_time = time.time()

			# change the active sinogram iprj
			Cst['iprj'] = iprj
			best_Prj = deepcopy(Prj[iprj])

			#loop for all angles from the list even_anglst
			run    = True
			ct_agl = -1
			while run:
				# count number of angles tested
				ct_agl += 1
				
				if DEBUG: s_time = time.time()

				# compute the weight for each common lines with Voronoi
				weights = cml_weights(Prj)
				if DEBUG: 
					print  'weights time: %8.3f s' % (time.time() - s_time)
					s_time = time.time()

				# spin for psi of iprj projection			
				best_psi, mirror, new_disc = cml_spin_proj(Prj, Cst, weights)

				if DEBUG: 
					print  'spin time: %8.3f s' % (time.time() - s_time)
					s_time = time.time()
				# tag if mirror
				Prj[iprj].mirror = mirror
				Prj[iprj].psi = best_psi

				# display in infofile
				cml_export_progress(infofilename, Prj, Cst, new_disc, 'progress')

				if DEBUG:
					print  'export time: %8.3f s' % (time.time() - s_time)
					s_time = time.time()
				# ---- strategy to select the next orientation ----------------------

				# == search all angles one by one ==
				if search == 'ALL':

					# select the best Prj
					if new_disc >= disc:
						disc	 = new_disc
						best_Prj = deepcopy(Prj[iprj])

					# choose the next
					old_pos = Prj[iprj].pos_agls
					while ocp_agls[Prj[iprj].pos_agls] != -1:
						Prj[iprj].pos_agls += 1
						if Prj[iprj].pos_agls > (n_anglst - 1):
							Prj[iprj].pos_agls = 1

					# update list of occupied angles
					ocp_agls[old_pos]			 = -1
					ocp_agls[Prj[iprj].pos_agls] = iprj

					# control running
					if ct_agl > (n_anglst - Cst['nprj']) - 1:
						run = False

					# change angles
					Prj[iprj].phi	 = anglst[Prj[iprj].pos_agls][0]
					Prj[iprj].theta  = anglst[Prj[iprj].pos_agls][1]
					Prj[iprj].psi	 = 0.0
					Prj[iprj].mirror = False

				# == search with simulated annealing ==
				elif search == 'SA':
					# define the probability of new state
					flag = 0
				
				if DEBUG:
					print 'ct_agl: %3d' % ct_agl, 'pos_agls: %3d' % Prj[iprj].pos_agls, 'time: %8.3f s' % (time.time() - s_time)

			# Assign the best orientation
			ocp_agls[Prj[iprj].pos_agls] = -1
			Prj[iprj]                    = deepcopy(best_Prj)
			ocp_agls[Prj[iprj].pos_agls] = iprj

			# display info
			cml_export_progress(infofilename, Prj, Cst, disc, 'choose')

			# apply mirror if need
			if Prj[iprj].mirror:
				Prj[iprj].phi	 = fmod(Prj[iprj].phi + 180, 360)
				Prj[iprj].theta  = 180 - Prj[iprj].theta
				#  THIS IS STRANGE PAP, shouldn't it be set to False ??
				Prj[iprj].mirror = True

				# display info
				cml_export_progress(infofilename, Prj, Cst, disc, 'mirror')

			if DEBUG:
				tmp1 = cml_disc_proj(Prj)
				print 'Time: %8.3f s' % (time.time() - g_time)
				print 'Disc:', disc, 'check', tmp1, '\n'

			# display info
			cml_export_progress(infofilename, Prj, Cst, disc, 'new')
			cml_export_txtagls(angfilename, Prj, Cst, disc, str(ct_prj).rjust(3, '0'))

	# ----- refine angles ---------------------------------
	scales = [delta] * (Cst['nprj'] + 2)

	# if refine use simplex
	if refine:
		for iprj in xrange(1, Cst['nprj']):
			# active projection
			Cst['iprj'] = iprj

			# init vec_in
			vec_in   = [Prj[iprj].phi, Prj[iprj].theta, Prj[iprj].psi]
		
			# prepare vec_data
			vec_data = [Prj, Cst]

			# simplex
			optvec, disc, niter = amoeba(vec_in, scales, cml_refine_agls, data = vec_data)

			# assign new angles refine
			Prj[iprj].phi   = optvec[0]
			Prj[iprj].theta = optvec[1]
			Prj[iprj].psi   = optvec[2]

			# info display
			cml_export_txtagls(angfilename, Prj, Cst, disc, 'REFINE %s' % str(iprj).rjust(3, '0'))

			if DEBUG: print '>> refine %d   disc: %10.3f' % (iprj, disc)
	
	return Prj, abs(disc)

## END COMMON LINES NEW VERSION ###############################################################
###############################################################################################

