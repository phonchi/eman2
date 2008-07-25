/**
 * $Id$
 */
 
/*
 * Author: Grant Tang, 03/10/2008 (gtang@bcm.edu)
 * Copyright (c) 2000-2006 Baylor College of Medicine
 * 
 * This software is issued under a joint BSD/GNU license. You may use the
 * source code in this file under either license. However, note that the
 * complete EMAN2 and SPARX software packages have some GPL dependencies,
 * so you are responsible for compliance with the licenses of these packages
 * if you opt to use BSD licensing. The warranty disclaimer below holds
 * in either instance.
 * 
 * This complete copyright notice must be included in any revised version of the
 * source code. Additional authorship citations may be added, but existing
 * author citations must be preserved.
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 * 
 * */
 
#ifndef randnum_h__
#define randnum_h__ 

#include <gsl/gsl_rng.h>
 
namespace EMAN
{
	/** The wrapper class for gsl's random number generater.
	 * This class is a singleton class.
	 * the default random number generator engine is gsl default: gsl_rng_mt19937,
	 * gsl_rng_mt19937 has a period 2^19937.
	 * the default seed is from /dev/random or milli second of current time.
	 * 
	 *      - How to get a random integer in range [lo, hi]
     *@code
     *      Randnum *r = Randnum::Instance();
     * 		int i = r->get_irand(lo, hi);
     *@endcode
	 *      - How to get a random float in range [0, 1)
     *@code
     *      Random *r = Random::Instance();
     * 		float f = r.get_frand();
     *@endcode     
	 *      - How to get a random float in range (0, 1)
     *@code
     *      Randnum *r = Randnum::Instance();
     * 		float f = r.get_frand_pos();
     *@endcode     
	 *      - How to get a random float in range [lo, hi)
     *@code
     *      Randnum *r = Randnum::Instance();
     * 		float f = r.get_frand(lo, hi);
     *@endcode     
	 *      - How to get a random float in range (lo, hi)
     *@code
     *      Randnum *r = Randnum::Instance();
     * 		float f = r.get_frand_pos(lo, hi);
     *@endcode
	 *      - How to get a gaussian distribution float with given mean and sigma
     *@code
     *      Randnum *r = Randnum::Instance();
     * 		float f = r.get_gauss_rand(mean, sigma);
     *@endcode
	 *      - How to set a seed for the random number generator
     *@code
     *      Randnum *r = Randnum::Instance();
     * 		r.set_seed(12345);
     *@endcode
	 *      - How to set a random number generator other than use the default
     *@code
     *      Randnum *r = Randnum::Instance(gsl_rng_rand);	//gsl version of rand()
     * 		Randnum *r = Randnum:;Instance(gsl_rng_random128_libc5);	//gsl version of Linux's random()
     *@endcode
	 */
	class Randnum {
	  public:
	  	static Randnum * Instance();
	  	static Randnum * Instance(const gsl_rng_type * _t);
	  			
	  	/** Set the seed for the random number generator. If the generator is 
		 * seeded with the same value of s on two different runs, the same 
		 * stream of random numbers will be generated by successive calls 
		 * to the routines below. If different values of s are supplied, 
		 * then the generated streams of random numbers should be completely 
		 * different. If the seed s is zero then the standard seed from the 
		 * original implementation is used instead.
		 * 
		 * @param seed the seed for random number generator
		 * */
		void set_seed(unsigned long int seed);	
		
		/** Get the current random number seed
		 * 
		 * @return current seed*/	
		unsigned long int get_seed();
		
		/** This function returns a random integer from lo to hi inclusive.
		 * All integers in the range [lo,hi] are produced with equal probability. 
		 *  
		 * @param lo the low end of the random integer
		 * @param hi the high end of the random integer
		 * @return the long integer in [lo, hi]  
		 * */
		long get_irand(long lo, long hi) const;
		
		/** This function returns a random float from lo inclusive to hi.
		 * 
		 * @param lo the low end of the random float
		 * @param hi the high end of the random float
		 * @return the float in [lo, hi), default in [0,0,1.0)  
		 * */
		float get_frand(double lo=0.0, double hi=1.0) const;
		
		/** This function returns a random float from lo to hi.
		 * 
		 * @param lo the low end of the random float
		 * @param hi the high end of the random float
		 * @return the float in (lo, hi), default in (0,0,1.0)  
		 * */
		float get_frand_pos(double lo=0.0, double hi=1.0) const;
		
		/** Return a Gaussian random number.
		 *
		 * @param[in] mean The gaussian mean
		 * @param[in] sigma The gaussian sigma
		 * @return the gaussian random number in float.
		 */
		float get_gauss_rand(float mean, float sigma) const;
	  	
	  	/** print out all possible random number generator type in gsl*/
	    void print_generator_type() const;
	  
	  protected:
		/** The default constructor will use the gsl default random number 
		 * generator gal_rng_mt19937. This is a very good choice which has 
		 * a period of 2^19937 and not sacrifice performance too much. */	
		Randnum();
		Randnum(const Randnum&);
		
		/** This constructor is for setting the new random number generator
		 * engine other than gsl default gsl_rng_mt19937. 
		 * For example: gsl_rng_rand is the gsl version of rand() function,
		 * which is 100% faster than the rand() function in C.
		 * 
		 * @param _t the random number generator type
		 * */
		explicit Randnum(const gsl_rng_type * _t);
		
		~Randnum();
		
		
		
	  private:
		const static gsl_rng_type * T;
    	static gsl_rng * r;
    	static unsigned long int _seed;
    	
    	static Randnum* _instance;
	}; 
	
}

#endif	//randnum_h__
