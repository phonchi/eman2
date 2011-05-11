#
# Author: Pawel A.Penczek, 09/09/2006 (Pawel.A.Penczek@uth.tmc.edu)
# Copyright (c) 2000-2006 The University of Texas - Houston Medical School
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holfds
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

from global_def import *

# Comment by Zhengfan Yang on 06/11/10
# I decided to move everything related to pixel error to this file. Otherwise, they are
# scattered all over the places and there are a lot of duplications and confusions.
#
# This file contains the following functions:
#  1. max_2D_pixel_error (originally max_pixel_error, also I changed its input format)
#  2. max_3D_pixel_error
#  3. angle_diff
#  4. align_diff_params
#  5. align_diff
#  6. align_diff_textfile (new)
#  7. ave_ali_err_params
#  8. ave_ali_err
#  9. ave_ali_err_textfile (new)
# 10. multi_align_diff_params (new)
# 11. calc_connect_list (new)
# 12. ali_stable_list (new)
#
# Update on 09/01/10, we have decided for multiple alignment function 10 and 11 are not best way
# to determine the stability. We have instead written a new function to to this.
# 13. multi_align_stability (latest)
#
# Here, align_diff_params() and ave_ali_err_params() takes two lists of alignmnet parameters
# in the following format:
# [alpha1, sx1, sy1, mirror1, alpha2, sx2, sy2, mirror2, ...]
# align_diff() and ave_ali_err() takes two lists of images
# align_diff_textfile() and ave_ali_err_textfile() takes two textfiles, which are usually the output
# file of header() or sxheader.py.
# Per previous discussion, I decided not to support two stacks of images.

def max_2D_pixel_error(ali_params1, ali_params2, r):
	"""
	Compute 2D maximum pixel error
	"""
	from math import sin, pi, sqrt
	return abs(sin((ali_params1[0]-ali_params2[0])/180.0*pi/2))*r*2+sqrt((ali_params1[1]-ali_params2[1])**2+(ali_params1[2]-ali_params2[2])**2)


def max_3D_pixel_error(t1, t2, r):
	"""
	Compute maximum pixel error between two projection directions
	assuming object has radius r, t1 is the projection transformation
	of the first projection and t2 of the second one, respectively:
		t = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
		t.set_trans(Vec2f(-tx, -ty))
	Note the function is symmetric in t1, t2.
	"""
	return EMData().max_3D_pixel_error(t1, t2, r)


def angle_diff(angle1, angle2):
	'''
	This function determines the relative angle between two sets of angles.
	The resulting angle has to be added (modulo 360) to the first set.
	'''
	from math import cos, sin, pi, atan
	
	nima = len(angle1)
	nima2 = len(angle2)
	if nima2 != nima:
		print "Error: List lengths do not agree!"
		return 0
	else:
		del nima2

	cosi = 0.0
	sini = 0.0
	for i in xrange(nima):
		cosi += cos((angle2[i]-angle1[i])*pi/180.0)
		sini += sin((angle2[i]-angle1[i])*pi/180.0)
	if cosi > 0.0:
		alphai = atan(sini/cosi)/pi*180.0
	elif cosi < 0.0:
		alphai = atan(sini/cosi)/pi*180.0+180.0
	else:
		if sini > 0.0:	alphai = 90.0
		else: alphai = 270.0

	return alphai%360.0


def angle_error(ang1, ang2, delta_ang=0.0):
	'''
	This function calculate the error (variance) between two sets of angle after delta_ang (angle difference) is added to the
	first sets. When the angle difference (delta_ang) is the true difference, this function will return maximum error.
	'''
	from math import cos, sin, pi
	dg_to_rg = pi/180.0
	
	erra = 0.0
	errb = 0.0
	err = 0.0
	delta_ang = delta_ang*dg_to_rg
	for i in xrange(len(ang1)):
		p2 = ang2[i]*dg_to_rg
		p2_x = cos(p2)
		p2_y = sin(p2)
		p1 = ang1[i]*dg_to_rg
		p1_x = cos(p1)
		p1_y = sin(p1)

		erra += p2_x*p1_x+p2_y*p1_y
		errb += p2_y*p1_x-p2_x*p1_y
	err = erra*cos(delta_ang) + errb*sin(delta_ang)
	return err


def align_diff_params(ali_params1, ali_params2):
	'''
	This function determines the relative angle, shifts and mirrorness between
	the two sets of alignment parameters.	
	'''
	from math import cos, sin, pi, atan
	from utilities import combine_params2
	
	nima = len(ali_params1)
	nima2 = len(ali_params2)
	if nima2 != nima:
		print "Error: Number of images don't agree!"
		return 0.0, 0.0, 0.0, 0
	else:
		nima/=4	
		del nima2

	# Read the alignment parameters and determine the relative mirrorness
	mirror_same = 0
	for i in xrange(nima):
		if ali_params1[i*4+3] == ali_params2[i*4+3]: mirror_same += 1
	if mirror_same > nima/2:
		mirror = 0
	else:
		mirror_same = nima-mirror_same
		mirror = 1

	# Determine the relative angle
	cosi = 0.0
	sini = 0.0
	angle1 = []
	angle2 = []
	for i in xrange(nima):
		mirror1 = ali_params1[i*4+3]
		mirror2 = ali_params2[i*4+3]
		if abs(mirror1-mirror2) == mirror: 
			alpha1 = ali_params1[i*4]
			alpha2 = ali_params2[i*4]
			if mirror1 == 1:
				alpha1 = -alpha1
				alpha2 = -alpha2
			angle1.append(alpha1)
			angle2.append(alpha2)
	alphai = angle_diff(angle1, angle2)

	# Determine the relative shift
	sxi = 0.0
	syi = 0.0
	for i in xrange(nima):
		mirror1 = ali_params1[i*4+3]
		mirror2 = ali_params2[i*4+3]
		if abs(mirror1-mirror2) == mirror: 
			alpha1 = ali_params1[i*4]
			alpha2 = ali_params2[i*4]
			sx1 = ali_params1[i*4+1]
			sx2 = ali_params2[i*4+1]
			sy1 = ali_params1[i*4+2]
			sy2 = ali_params2[i*4+2]
			alpha12, sx12, sy12, mirror12 = combine_params2(alpha1, sx1, sy1, int(mirror1), alphai, 0.0, 0.0, 0)
			if mirror1 == 0: sxi += sx2-sx12
			else: sxi -= sx2-sx12
			syi += sy2-sy12

	sxi /= mirror_same
	syi /= mirror_same

	return alphai, sxi, syi, mirror


def align_diff(data1, data2=None, suffix="_ideal"):
	
	'''
	This function determines the relative angle, shifts and mirrorness between
	the two list of data
	'''
	from utilities import get_params2D
	
	nima = len(data1)

	if data2 != None: 
		nima2 = len(data2)
		if nima2 != nima:
			print "Error: Number of images don't agree!"
			return 0.0, 0.0, 0.0, 0
		else:
			del nima2

	# Read the alignment parameters and determine the relative mirrorness
	ali_params1 = []
	ali_params2 = []
	for i in xrange(nima):
		alpha1, sx1, sy1, mirror1, scale1 = get_params2D(data1[i])
		if data2 != None:
			alpha2, sx2, sy2, mirror2, scale2 = get_params2D(data2[i])
		else:
			alpha2, sx2, sy2, mirror2, scale2 = get_params2D(data1[i], "xform.align2d"+suffix)
		ali_params1.extend([alpha1, sx1, sy1, mirror1])
		ali_params2.extend([alpha2, sx2, sy2, mirror2])

	return align_diff_params(ali_params1, ali_params2)


def align_diff_textfile(textfile1, textfile2):
	
	'''
	This function determines the relative angle, shifts and mirrorness between
	the two textfile of alignment parameters
	'''
	from utilities import read_text_row
	
	ali1 = read_text_row(textfile1, "", "")
	ali2 = read_text_row(textfile2, "", "")

	nima = len(ali1)
	nima2 = len(ali2)
	if nima2 != nima:
		print "Error: Number of images don't agree!"
		return 0.0, 0.0, 0.0, 0
	else:
		del nima2

	# Read the alignment parameters and determine the relative mirrorness
	ali_params1 = []
	ali_params2 = []
	for i in xrange(nima):
		ali_params1.extend(ali1[i][0:4])
		ali_params2.extend(ali2[i][0:4])

	return align_diff_params(ali_params1, ali_params2)


def ave_ali_err(data1, data2=None, r=25, suffix="_ideal"):
	'''
	This function determines the relative angle, shifts and mirrorness between
	the two lists of data. It also calculates the mirror consistent
	rate and average pixel error between two sets of parameters.
	'''
	from utilities import get_params2D, combine_params2
	from math import sqrt, sin, pi
	
	# Determine relative angle, shifts and mirror
	alphai, sxi, syi, mirror = align_diff(data1, data2, suffix)

	# Determine the average pixel error
	err = 0.0
	nima = len(data1)
	mirror_same = 0
	for i in xrange(nima):
		alpha1, sx1, sy1, mirror1, scale1 = get_params2D(data1[i])
		if data2 != None:
			alpha2, sx2, sy2, mirror2, scale2 = get_params2D(data2[i])
		else:
			alpha2, sx2, sy2, mirror2, scale2 = get_params2D(data1[i], "xform.align2d"+suffix)
		
		if abs(mirror1-mirror2) == mirror: 
			mirror_same += 1
			alpha12, sx12, sy12, mirror12 = combine_params2(alpha1, sx1, sy1, int(mirror1), alphai, sxi, syi, 0)
			err += max_2D_pixel_error([alpha12, sx12, sy12], [alpha2, sx2, sy2], r)
	
	return alphai, sxi, syi, mirror, float(mirror_same)/nima, err/mirror_same


def ave_ali_err_params(ali_params1, ali_params2, r=25):
	'''
	This function determines the relative angle, shifts and mirrorness between
	the two sets of alignment parameters. It also calculates the mirror consistent
	rate and average pixel error between two sets of parameters.
	'''
	from utilities import combine_params2
	from math import sqrt, sin, pi
	
	# Determine relative angle, shift and mirror
	alphai, sxi, syi, mirror = align_diff_params(ali_params1, ali_params2)

	# Determine the average pixel error
	nima = len(ali_params1)/4
	mirror_same = 0
	err = 0.0
	for i in xrange(nima):
		alpha1, sx1, sy1, mirror1 = ali_params1[i*4:i*4+4]
		alpha2, sx2, sy2, mirror2 = ali_params2[i*4:i*4+4]
		
		if abs(mirror1-mirror2) == mirror: 
			mirror_same += 1
			alpha12, sx12, sy12, mirror12 = combine_params2(alpha1, sx1, sy1, int(mirror1), alphai, sxi, syi, 0)
			err += max_2D_pixel_error([alpha12, sx12, sy12], [alpha2, sx2, sy2], r)
	
	return alphai, sxi, syi, mirror, float(mirror_same)/nima, err/mirror_same


def ave_ali_err_textfile(textfile1, textfile2, r=25):
	'''
	This function determines the relative angle, shifts and mirrorness between
	the two sets of alignment parameters. It also calculates the mirror consistent
	rate and average pixel error between two sets of parameters.
	'''
	from utilities import combine_params2
	from math import sqrt, sin, pi
	from utilities import read_text_row
	
	ali1 = read_text_row(textfile1, "", "")
	ali2 = read_text_row(textfile2, "", "")

	nima = len(ali1)
	nima2 = len(ali2)
	if nima2 != nima:
		print "Error: Number of images don't agree!"
		return 0.0, 0.0, 0.0, 0, 0.0, 0.0
	else:
		del nima2

	# Read the alignment parameters
	ali_params1 = []
	ali_params2 = []
	for i in xrange(nima):
		ali_params1.extend(ali1[i][0:4])
		ali_params2.extend(ali2[i][0:4])

	# Determine relative angle, shift and mirror
	alphai, sxi, syi, mirror = align_diff_params(ali_params1, ali_params2)

	# Determine the average pixel error
	nima = len(ali_params1)/4
	mirror_same = 0
	err = 0.0
	for i in xrange(nima):
		alpha1, sx1, sy1, mirror1 = ali_params1[i*4:i*4+4]
		alpha2, sx2, sy2, mirror2 = ali_params2[i*4:i*4+4]
		
		if abs(mirror1-mirror2) == mirror: 
			mirror_same += 1
			alpha12, sx12, sy12, mirror12 = combine_params2(alpha1, sx1, sy1, int(mirror1), alphai, sxi, syi, 0)
			err += max_2D_pixel_error([alpha12, sx12, sy12], [alpha2, sx2, sy2], r)
	
	return alphai, sxi, syi, mirror, float(mirror_same)/nima, err/mirror_same


def multi_align_diff_params(ali_params, verbose=0):
	"""
	Calculate the mirror consistency and pixel error between different runs of alignment
	The input is in the following format (here n is the number of alignments done):
		[[alpha1_r1, sx1_s1, sy1_r1, mirror1_r1, alpha2_r1, sx2_r1, sy2_r1, mirror2_r1, ...],
		 [alpha1_r2, sx1_s2, sy1_r2, mirror1_r2, alpha2_r2, sx2_r2, sy2_r2, mirror2_r2, ...],
		 [alpha1_r3, sx1_s3, sy1_r3, mirror1_r3, alpha2_r3, sx2_r3, sy2_r3, mirror2_r3, ...],
		 ...
		 [alpha1_rn, sx1_sn, sy1_rn, mirror1_rn, alpha2_rn, sx2_rn, sy2_rn, mirror2_rn, ...]]
	The output is in the following format (here k=n*(n+1)/2):
		[[pixel_error_1, mirror_consistency_1, i_1, j_1, alpha_1, sx_1, sy_1, mirror_1],
		 [pixel_error_2, mirror_consistency_2, i_2, j_2, alpha_2, sx_2, sy_2, mirror_2],
		 [pixel_error_3, mirror_consistency_3, i_3, j_3, alpha_3, sx_3, sy_3, mirror_3],
		...
		 [pixel_error_k, mirror_consistency_k, i_k, j_k, alpha_k, sx_k, sy_k, mirror_k]]
	"""
	num_ali = len(ali_params)
	multi_align_results = []
	for i in xrange(num_ali-1):
		for j in xrange(i+1, num_ali):
			alpha, sx, sy, mirror, stab_mirror, pixel_error = ave_ali_err_params(ali_params[i], ali_params[j])
			if verbose == 1:
				print "Between trial %d and %d: mirror stability = %6.3f   pixel error = %6.3f"%(i, j, stab_mirror, pixel_error)
			multi_align_results.append([pixel_error, stab_mirror, i, j, alpha, sx, sy, mirror])
	return multi_align_results
	

def calc_connect_list(multi_align_results, pixel_error_threshold = 5.0, mirror_consistency_threshold = 0.8):
	"""
	Generate the connection list from the multi_align_results, which generally comes from multi_align_diff_params()
	The connection list will have the following format:
		[[1, 2, 5], [4, 6], [0, 7]]
	You will also get the size of the largest connection in the list.
	"""
	import sets
	
	k = len(multi_align_results)
	multi_align_results.sort()
	connect_list = []
	for i in xrange(k):
		if multi_align_results[i][0] <= pixel_error_threshold:
			if multi_align_results[i][1] >= mirror_consistency_threshold: 
				connect_list.append([multi_align_results[i][2], multi_align_results[i][3]])
		else:	break
	to_break = True
	while to_break:
		l = len(connect_list)
		to_break = False
		for i in xrange(l-1):
			for j in xrange(i+1, l):
				set1 = set(connect_list[i])
				set2 = set(connect_list[j])
				if list(set1.intersection(set2)) != []:
					connect_list[i] = list(set1.union(set2))
					del connect_list[j]
					to_break = True
					break
			if to_break: break
	max_connect = 0
	for l in connect_list: max_connect = max(max_connect, len(l))
	return connect_list, max_connect


def ali_stable_list(ali_params1, ali_params2, pixel_error_threshold, r=25):
	'''
	This function first determines the relative angle, shifts and mirrorness between
	the two sets of alignment parameters. It then determines whether each image is
	stable or not and return this information as an int list. (1 is stable and 0 is unstable)
	'''
	from utilities import combine_params2
	from math import sqrt, sin, pi
	
	# Determine relative angle, shift and mirror
	alphai, sxi, syi, mirror = align_diff_params(ali_params1, ali_params2)

	# Determine the average pixel error
	nima = len(ali_params1)/4
	ali_list = []
	for i in xrange(nima):
		alpha1, sx1, sy1, mirror1 = ali_params1[i*4:i*4+4]
		alpha2, sx2, sy2, mirror2 = ali_params2[i*4:i*4+4]
		if abs(mirror1-mirror2) == mirror: 
			alpha12, sx12, sy12, mirror12 = combine_params2(alpha1, sx1, sy1, int(mirror1), alphai, sxi, syi, 0)
			if max_2D_pixel_error([alpha12, sx12, sy12], [alpha2, sx2, sy2], r) < pixel_error_threshold: ali_list.append(1)
			else: ali_list.append(0)
		else: ali_list.append(0)
	
	return ali_list


def multi_align_stability(ali_params, mirror_consistency_threshold = 0.75, error_threshold = 1.0, individual_error_threshold = 1.0):

	def rot_shift(x, y, alpha, sx, sy):
		from math import pi, sin, cos
		cosi = cos(alpha/180.0*pi)
		sini = sin(alpha/180.0*pi)
		return x*cosi+y*sini+sx, -x*sini+y*cosi+sy

	def ave(a):
		n = len(a)
		ave = 0.0
		for i in xrange(n): ave+=a[i]
		ave /= n
		return ave

	def var(a):
		n = len(a)
		avg = ave(a)
		var = 0.0
		for i in xrange(n): var+=(a[i]-avg)**2
		return var/(n-1)

	def stable(args, data):
		from math import sqrt
	        x1 = 1.0
	        y1 = 0.0
        	x2 = 0.0
	        y2 = 1.0

        	all_ali_params = data
	        num_ali = len(all_ali_params)
	        nima = len(all_ali_params[0])/4
		err = [0.0]*nima

	        for i in xrange(nima):
	        	pix_error = 0
	        	x1_new = [0.0]*num_ali
	        	y1_new = [0.0]*num_ali
	        	x2_new = [0.0]*num_ali
	        	y2_new = [0.0]*num_ali
	        	alpha2, sx2, sy2, mirror2 = all_ali_params[num_ali-1][i*4:i*4+4]
	        	x1_new[num_ali-1], y1_new[num_ali-1] = rot_shift(x1, y1, alpha2, sx2, sy2)
	        	x2_new[num_ali-1], y2_new[num_ali-1] = rot_shift(x2, y2, alpha2, sx2, sy2)
	        	for j in xrange(num_ali-1):
	        		alpha1, sx1, sy1, mirror1 = all_ali_params[j][i*4:i*4+4]
	        		alphai, sxi, syi = args[j*3:j*3+3]
	        		alpha12, sx12, sy12, mirror12 = combine_params2(alpha1, sx1, sy1, int(mirror1), alphai, sxi, syi, 0)
	        		x1_new[j], y1_new[j] = rot_shift(x1, y1, alpha12, sx12, sy12)
	        		x2_new[j], y2_new[j] = rot_shift(x2, y2, alpha12, sx12, sy12)

	        	err[i] = sqrt(var(x1_new)+var(y1_new)+var(x2_new)+var(y2_new))

	        return err

	from statistics import k_means_stab_bbenum
	from utilities import combine_params2
	from numpy import array

	# Find out the subset which is mirror consistent over all runs
	all_part = []
	num_ali = len(ali_params)
	nima = len(ali_params[0])/4
	for i in xrange(num_ali):
		mirror0 = []
		mirror1 = []
		for j in xrange(nima):
			if ali_params[i][j*4+3] == 0: mirror0.append(j)
			else: mirror1.append(j)
		mirror0 = array(mirror0, 'int32')
		mirror1 = array(mirror1, 'int32')
		all_part.append([mirror0, mirror1])
	match, stab_part, CT_s, CT_t, ST, st = k_means_stab_bbenum(all_part, T=0, nguesses=1)
	mir_cons_part = stab_part[0] + stab_part[1]
	mirror_consistent_rate = len(mir_cons_part)/float(nima)
	if mirror_consistent_rate <  mirror_consistency_threshold: return [], mirror_consistent_rate, -1.0
	mir_cons_part.sort()
	del all_part, match, stab_part, CT_s, CT_t, ST, st	

	# Shrink the list the alignment paramters to whatever is mirror consistent
	ali_params_mir_cons = []
	ali_params_mir_cons_list = []
	for i in xrange(num_ali):
		ali_params_temp = []
		for j in mir_cons_part: ali_params_temp.extend(ali_params[i][j*4:j*4+4])
		ali_params_mir_cons.append(ali_params_temp)
		ali_params_mir_cons_list.extend(ali_params_temp)

	# Find out the alignment parameters for each iteration against the last one
	args = []
	for i in xrange(num_ali-1):
		alpha, sx, sy, mirror, stab_mirror, pixel_error = ave_ali_err_params(ali_params_mir_cons[i], ali_params_mir_cons[num_ali-1])
		args.extend([alpha, sx, sy])

	ps = Util.multi_align_error(args, ali_params_mir_cons_list)
	val = ps[-1]
	del ps[-1]

	if val > error_threshold: return [], mirror_consistent_rate, val
	err = stable(ps, ali_params_mir_cons)
	#  Here all errors could be printed, PAP.
	stable_set = []
	for i in xrange(len(mir_cons_part)):
		if err[i] < individual_error_threshold: stable_set.append([err[i], mir_cons_part[i]])
	stable_set.sort()
		
	return stable_set, mirror_consistent_rate, val

'''

# These are some obsolete codes, we retain them just in case.

def estimate_stability(data1, data2, CTF=False, snr=1.0, last_ring=-1):
	"""
	This function estimate the stability of two datasets
	It returns three values, the first is the mirror consistent rate
	The second is the average pixel error among the mirror consistent images
	The third is the cross_correltion coefficient of two averages
	"""

	from statistics import sum_oe, ccc
	from fundamentals import fft, rot_shift2D
	from alignment import align2d
	from utilities import get_params2D, combine_params2
	from math import sin, pi, sqrt
	from morphology import ctf_img

	PI_180 = pi/180
	nima = len(data1)
	nx = data1[0].get_xsize()
	if last_ring == -1: last_ring = nx/2-2
	if CTF:
		ctf_2_sum = EMData(nx, nx, 1, False)
		for im in xrange(nima):
			ctf_params = data1[im].get_attr("ctf")
			Util.add_img2(ctf_2_sum, ctf_img(nx, ctf_params))
		ctf_2_sum += 1/snr

	av1, av2 = sum_oe(data1, "a", CTF, EMData())
	if CTF:
		ave1 = fft(Util.divn_img(fft(Util.addn_img(av1, av2)), ctf_2_sum))
	else:
		ave1 = (av1+av2)/nima

	av1, av2 = sum_oe(data2, "a", CTF, EMData())
	if CTF:
		ave2 = fft(Util.divn_img(fft(Util.addn_img(av1, av2)), ctf_2_sum))
	else:
		ave2 = (av1+av2)/nima

	alpha21, sx21, sy21, mirror21, peak21 = align2d(ave2, ave1, 3.0, 3.0, 0.125, last_ring=last_ring)
	ave21 = rot_shift2D(ave2, alpha21, sx21, sy21, mirror21)
		
	consistent = 0
	pixel_error = []	
	for im in xrange(nima):
		alpha1, sx1, sy1, mirror1, scale1 = get_params2D(data1[im])
		alpha2, sx2, sy2, mirror2, scale2 = get_params2D(data2[im])

		alpha2n, sx2n, sy2n, mirror2n = combine_params2(alpha2, sx2, sy2, mirror2, alpha21, sx21, sy21, mirror21)

		if mirror1 == mirror2n:
			consistent += 1
			this_pixel_error = abs(sin((alpha1-alpha2n)*PI_180/2))*last_ring*2+sqrt((sx1-sx2n)**2+(sy1-sy2n)**2)
			pixel_error.append(this_pixel_error)

	return consistent/float(nima), pixel_error, ccc(ave21, ave1)



def max_3D_pixel_error(t1, t2, r):
	"""
	  Compute maximum pixel error between two projection directions
	  assuming object has radius r, t1 is the projection transformation
	  of the first projection and t2 of the second one, respectively:
		t = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
		t.set_trans(Vec2f(-tx, -ty))
	  Note the function is symmetric in t1, t2.
	"""
	from math import sin, cos, pi, sqrt
	t3 = t2*t1.inverse()
	ddmax = 0.0
	for i in xrange(int(r), int(r)+1):
		for ang in xrange(int(2*pi*i+0.5)):
			v = Vec3f(i*cos(ang), i*sin(ang), 0)
			d = t3*v - v
			dd = d[0]**2+d[1]**2+d[2]**2
			if dd > ddmax: ddmax=dd
	return sqrt(ddmax)

def max_3D_pixel_errorA(t1, t2, r):
	"""
	  Compute maximum pixel error between two projection directions
	  assuming object has radius r, t1 is the projection transformation
	  of the first projection and t2 of the second one, respectively:
		t = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
		t.set_trans(Vec2f(-tx, -ty))
	  Note the function is symmetric in t1, t2.
	"""
	from math import sin, cos, pi, sqrt
	t3 = t2*t1.inverse()
	ddmax = 0.0
	for i in xrange(int(r)+1):
		for ang in xrange(int(2*pi*i+0.5)):
			v = Vec3f(i*cos(ang), i*sin(ang), 0)
			d = t3*v - v
			dd = d[0]**2+d[1]**2+d[2]**2
			if dd > ddmax: ddmax=dd
	return sqrt(ddmax)
'''

