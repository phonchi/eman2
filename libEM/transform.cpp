/**
 * $Id$
 */

/*
 * Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 * 
 * */

#include "transform.h"
#include <cctype>

using namespace EMAN;
#ifdef WIN32
#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif
#endif

const float Transform3D::ERR_LIMIT = 0.000001f;

//  C1
Transform3D::Transform3D()  //    C1
{
	init();
}

Transform3D::Transform3D( const Transform3D& rhs )
{
    for( int i=0; i < 4; ++i )
    {
        for( int j=0; j < 4; ++j )
	{
	    matrix[i][j] = rhs.matrix[i][j];
	}
    }
}

// C2
Transform3D::Transform3D(float az, float alt, float phi) 
{
	init();
	set_rotation(az,alt,phi);
}


//  C3  Usual Constructor: Post Trans, after appying Rot
Transform3D::Transform3D( float az, float alt, float phi, const Vec3f& posttrans )
{
	init();
	set_rotation(az,alt,phi);
	set_posttrans(posttrans);
}

Transform3D::Transform3D(float m11, float m12, float m13,
                         float m21, float m22, float m23,
			 float m31, float m32, float m33)
{
	init();
	set_rotation(m11,m12,m13,m21,m22,m23,m31,m32,m33);
}

// C4
Transform3D::Transform3D(EulerType euler_type, float a1, float a2, float a3)  // usually az, alt, phi
                                                                                        // only SPIDER and EMAN supported
{
	init();
	Dict rot;
	switch(euler_type) {
	case EMAN:
		rot["az"]  = a1;
		rot["alt"] = a2;
		rot["phi"] = a3;
		break;
	case SPIDER:
		rot["phi"]   = a1;
		rot["theta"] = a2;
		rot["psi"]   = a3;
		break;
	default:
		throw InvalidValueException(euler_type, "cannot instantiate this Euler Type");
  	}  // ends switch euler_type
	set_rotation(euler_type, rot);  // Or should it be &rot ?
}

// C5
Transform3D::Transform3D(EulerType euler_type, const Dict& rotation)  //YYY
{
	init();
	set_rotation(euler_type,rotation);
}


// C6   First apply pretrans: Then rotation: Then posttrans

Transform3D::Transform3D(  const Vec3f& pretrans,  float az, float alt, float phi, const Vec3f& posttrans )  //YYY  by default EMAN
{
	init();
	set_pretrans(pretrans);
	set_rotation(az,alt,phi);
	set_posttrans(posttrans);
}




Transform3D::~Transform3D()
{
}



void Transform3D::to_identity()
{
//	for (int i = 0; i < 3; i++) {
//		matrix[i][i] = 1;
//	}

	for(int i=0; i<4; ++i) {
		for(int j=0; j<4; ++j) {
			if(i==j) {
				matrix[i][j] = 1;
			}
			else {
				matrix[i][j] = 0;
			}
		}
	}
	
	set_center(Vec3f(0,0,0));
}



bool Transform3D::is_identity()  // YYY
{
	for (int i=0; i<4; i++) {
		for (int j=0; j<4; j++) {
			if (i==j && matrix[i][j]!=1.0) return 0;
			if (i!=j && matrix[i][j]!=0.0) return 0;
		}
	}
	return 1;
}


void Transform3D::set_center(const Vec3f & center) //YYN
{
	set_pretrans( Vec3f(0,0,0)-center);
	for (int i = 0; i < 3; i++) {
		matrix[i][3]=center[i];
	}
}


void Transform3D::set_pretrans(const Vec3f & preT)  // YYN
{

//     transFinal = transPost +  Rotation * transPre;

	matrix[0][3] = matrix[3][0] + matrix[0][0]*preT[0] + matrix[0][1]*preT[1] + matrix[0][2]*preT[2]  ;
	matrix[1][3] = matrix[3][1] + matrix[1][0]*preT[0] + matrix[1][1]*preT[1] + matrix[1][2]*preT[2]  ;
	matrix[2][3] = matrix[3][2] + matrix[2][0]*preT[0] + matrix[2][1]*preT[1] + matrix[2][2]*preT[2]  ;

}



float * Transform3D::operator[] (int i)
{
	return matrix[i];
}

const float * Transform3D::operator[] (int i) const
{
	return matrix[i];
}


//            METHODS
//   Note Transform3Ds are initialized as identities
void Transform3D::init()  // M1
{
	for (int i=0; i<4; i++) {
		for (int j=0; j<4; j++) {
			matrix[i][j]=0;
		}
		matrix[i][i]=1;
	}
}


//      Set Methods


void Transform3D::set_posttrans(const Vec3f & posttrans) // YYN
{
	Vec3f preT   = get_pretrans( ) ;
	for (int i = 0; i < 3; i++) {
		matrix[3][i] = posttrans[i];
	}
//     transFinal = transPost +  Rotation * transPre;

	
	matrix[0][3] = matrix[3][0] + matrix[0][0]*preT.at(0) + matrix[0][1]*preT.at(1) + matrix[0][2]*preT.at(2)  ;
	matrix[1][3] = matrix[3][1] + matrix[1][0]*preT.at(0) + matrix[1][1]*preT.at(1) + matrix[1][2]*preT.at(2)  ;
	matrix[2][3] = matrix[3][2] + matrix[2][0]*preT.at(0) + matrix[2][1]*preT.at(1) + matrix[2][2]*preT.at(2)  ;

}




void Transform3D::apply_scale(float scale)    // YYY
{
	for (int i = 0; i < 3; i++) {
		for (int j = 0; j < 4; j++) {
			matrix[i][j] *= scale;
		}
	}
}



void Transform3D::orthogonalize()  // YYY
{
	//EulerType EMAN;
	float scale = get_scale() ;
	float inverseScale= 1/scale ;
	apply_scale(inverseScale);
//	Dict angs = get_rotation(EMAN);
//	set_Rotation(EMAN,angs);
}


void Transform3D::transpose()  // YYY
{
	float tempij;
	for (int i = 0; i < 3; i++) {
		for (int j = 0; j < i; j++) {
			tempij= matrix[i][j];
			matrix[i][j] = matrix[j][i];
			matrix[j][i] = tempij;
		}
	}
}





void Transform3D::set_scale(float scale)    // YYY
{
	float OldScale= get_scale();
	float Scale2Apply = scale/OldScale;
	apply_scale(Scale2Apply);
}

float Transform3D::get_mag() const //
{
	EulerType eulertype= SPIN ;
	Dict AA= get_rotation(eulertype);
	return AA["Omega"];
}

Vec3f Transform3D::get_finger() const //
{
	EulerType eulertype= SPIN ;
	Dict AA= get_rotation(eulertype);
	return Vec3f(AA["n1"],AA["n2"],AA["n3"]);
}

Vec3f Transform3D::get_posttrans() const    // 
{
	return Vec3f(matrix[3][0], matrix[3][1], matrix[3][2]);
}



Vec3f Transform3D::get_pretrans() const    // Fix Me
{
//	The expression is R^T(v_total - v_post);

	Vec3f pretrans;
	Vec3f posttrans(matrix[3][0], matrix[3][1], matrix[3][2]);
	Vec3f tottrans(matrix[0][3], matrix[1][3], matrix[2][3]);
	Vec3f totminuspost;
	
	totminuspost = tottrans-posttrans;
	
	for (int i=0; i<3; i++) {
                float ptnow=0;
		for (int j=0; j<3; j++) {
			ptnow += totminuspost.at(j) * matrix[j][i] ;
		}
		pretrans.set_value_at(i,ptnow) ;  // 
	}
	return pretrans;
}


 Vec3f Transform3D::get_center() const  // YYY
 {
 	return Vec3f();
 }



Vec3f Transform3D::get_matrix3_col(int i) const     // YYY
{
	return Vec3f(matrix[0][i], matrix[1][i], matrix[2][i]);
}


Vec3f Transform3D::get_matrix3_row(int i) const     // YYY
{
	return Vec3f(matrix[i][0], matrix[i][1], matrix[i][2]);
}

Vec3f Transform3D::transform(Vec3f & v3f) const     // YYY
{
//      This is the transformation of a vector, v by a matrix M
	float x = matrix[0][0] * v3f[0] + matrix[0][1] * v3f[1] + matrix[0][2] * v3f[2] + matrix[0][3] ;
	float y = matrix[1][0] * v3f[0] + matrix[1][1] * v3f[1] + matrix[1][2] * v3f[2] + matrix[1][3] ;
	float z = matrix[2][0] * v3f[0] + matrix[2][1] * v3f[1] + matrix[2][2] * v3f[2] + matrix[2][3] ;
	return Vec3f(x, y, z);
}


Vec3f Transform3D::rotate(Vec3f & v3f) const     // YYY
{
//      This is the rotation of a vector, v by a matrix M
	float x = matrix[0][0] * v3f[0] + matrix[0][1] * v3f[1] + matrix[0][2] * v3f[2]  ;
	float y = matrix[1][0] * v3f[0] + matrix[1][1] * v3f[1] + matrix[1][2] * v3f[2]  ;
	float z = matrix[2][0] * v3f[0] + matrix[2][1] * v3f[1] + matrix[2][2] * v3f[2]  ;
	return Vec3f(x, y, z);
}




Transform3D EMAN::operator*(const Transform3D & M2, const Transform3D & M1)     // YYY
{
//       This is the  left multiplication of a matrix M1 by a matrix M2; that is M2*M1
//       It returns a new matrix
	Transform3D resultant;
	for (int i=0; i<3; i++) {
		for (int j=0; j<4; j++) {
			resultant[i][j] = M2[i][0] * M1[0][j] +  M2[i][1] * M1[1][j] + M2[i][2] * M1[2][j];
		}
		resultant[i][3] += M2[i][3];  // add on the new translation (not included above)
	}
	
	for (int j=0; j<3; j++) {
		resultant[3][j] = M2[3][j];
	}
	
	return resultant; // This will have the post_trans of M2
}





Vec3f EMAN::operator*(const Vec3f & v, const Transform3D & M)   // YYY
{
//               This is the right multiplication of a row vector, v by a transform3D matrix M
	float x = v[0] * M[0][0] + v[1] * M[1][0] + v[2] * M[2][0] ;
	float y = v[0] * M[0][1] + v[1] * M[1][1] + v[2] * M[2][1];
	float z = v[0] * M[0][2] + v[1] * M[1][2] + v[2] * M[2][2];
	return Vec3f(x, y, z);
}


Vec3f EMAN::operator*( const Transform3D & M, const Vec3f & v)      // YYY
{
//      This is the  left multiplication of a vector, v by a matrix M
	float x = M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2] + M[0][3] ;
	float y = M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2] + M[1][3];
	float z = M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2] + M[2][3];
	return Vec3f(x, y, z);
}










/*             Here starts the pure rotation stuff */

/**  A rotation is given by

EMAN
  | cos phi   sin phi    0 |  |  1       0     0      | |  cos az  sin az   0 |
  |-sin phi   cos phi    0 |  |  0   cos alt  sin alt | | -sin az  cos az   0 |
  |   0          0       1 |  |  0  -sin alt  cos alt | |     0       0     1 |

---------------------------------------------------------------------------

SPIDER, FREEALIGN  (th == theta)
| cos psi   sin psi    0 |  |  cos th  0   -sin th   | |  cos phi  sin phi   0 |
|-sin psi   cos psi    0 |  |  0       1       0     | | -sin phi  cos phi   0 |
|   0          0       1 |  |  sin th  0    cos th   | |     0        0      1 |


Now this middle matrix is equal to

                 | 0 -1 0|  |1     0    0     | | 0  1  0 |
                 | 1  0 0|  |0  cos th sin th | |-1  0  0 |
                 | 0  0 1|  |0 -sin th cos th | | 0  0  1 |


 So we have

  | sin psi  -cos psi    0 |  |  1       0     0    | | -sin phi  cos phi   0 |
  | cos psi   sin psi    0 |  |  0   cos th  sin th | | -cos phi -sin phi   0 |
  |   0          0       1 |  |  0  -sin th  cos th | |     0       0     1 |


        so az = phi_SPIDER + pi/2  
          phi = psi        - pi/2

---------------------------------------------------------------------------

MRC  th=theta; om=omega ;

| cos om   sin om    0 |  |  cos th  0   -sin th   | |  cos phi  sin phi   0 |
|-sin om   cos om    0 |  |  0       1       0     | | -sin phi  cos phi   0 |
|   0        0       1 |  |  sin th  0    cos th   | |     0        0      1 |

        so az = phi     + pi/2
          alt = theta
          phi = omega   - pi/2

---------------------------------------------------------------------------
For the quaternion type operations, we can start with

R = (1-nhat nhat) cos(Omega) - sin(Omega)nhat cross + nhat nhat
Notice that this is a clockwise rotation( the xy component, for nhat=zhat,
 is calculated as - sin(Omega) xhat dot zhat cross yhat= sin(Omega): this is the
 correct sign for clockwise rotations).
Now we develop

R =  cos(Omega) one + nhat nhat (1-cos(Omega)) - sin(Omega) nhat cross
  = (cos^2(Omega/2) - sin^2(Omega/2)) one  + 2 ((sin(Omega/2)nhat ) ((sin(Omega/2)nhat )
                                    - 2 cos(Omega/2) ((sin(Omega/2)nhat )  cross
  = (e0^2 - evec^2) one  + 2 (evec evec )  - 2 e0 evec  cross

  e0 = cos(Omega/2)
  vec{e} = sin(Omega/2) nhat


SGIrot is the same as SPIN (see paper)
The update of rotations for quaternions is very easy.


*/






void Transform3D::set_rotation(float az, float alt, float phi )
{
	EulerType euler_type=EMAN;
	Dict rot;
	rot["az"]  = az;
	rot["alt"] = alt;
	rot["phi"] = phi;
        set_rotation(euler_type, rot);  // Or should it be &rot ?

}

// This is where it all happens;
void Transform3D::set_rotation(EulerType euler_type, float a1, float a2, float a3) // EMAN: az alt, phi 
 									                        // SPIDER: phi, theta, psi 
{
	init();
	Dict rot;
	switch(euler_type) {
	case EMAN:
		rot["az"]  = a1;
		rot["alt"] = a2;
		rot["phi"] = a3;
		break;
	case SPIDER:
		rot["phi"]   = a1;
		rot["theta"] = a2;
		rot["psi"]   = a3;
		break;
	default:
		throw InvalidValueException(euler_type, "cannot instantiate this Euler Type");
  	}  // ends switch euler_type
	set_rotation(euler_type, rot);  // Or should it be &rot ?
}


void Transform3D::set_rotation(EulerType euler_type, const Dict& rotation)
{
	float e0  = 0;float e1=0; float e2=0; float e3=0;
	float Omega=0;
	float az  = 0;
	float alt = 0;
	float phi = 0;
        float cxtilt = 0;
	float sxtilt = 0;
	float cytilt = 0;
	float sytilt = 0;
	bool is_quaternion = 0;
	bool is_matrix = 0;

	switch(euler_type) {
	case EMAN:
		az  = (float)rotation["az"] ;
		alt = (float)rotation["alt"]  ;
		phi = (float)rotation["phi"] ;
		break;
	case IMAGIC:
		az  = (float)rotation["alpha"] ;
		alt = (float)rotation["beta"]  ;
		phi = (float)rotation["gamma"] ;
		break;

	case SPIDER:
		az =  (float)rotation["phi"]    + 90.0f ;              ;
		alt = (float)rotation["theta"]  ;
		phi = (float)rotation["psi"]    - 90.0f ;
		break;

	case XYZ:
	        cxtilt = cos( (M_PI/180.0f)*(float)rotation["xtilt"]);
	        sxtilt = sin( (M_PI/180.0f)*(float)rotation["xtilt"]);
	        cytilt = cos( (M_PI/180.0f)*(float)rotation["ytilt"]);
	        sytilt = sin( (M_PI/180.0f)*(float)rotation["ytilt"]);
		az =  (180.0f/M_PI)*atan2(-cytilt*sxtilt,sytilt)   + 90.0f ;              ;
		alt = (180.0f/M_PI)*acos(cytilt*cxtilt)  ;
		phi = (float)rotation["ztilt"] +(180.0f/M_PI)*atan2(sxtilt,cxtilt*sytilt)   - 90.0f ;
		break;

	case MRC:
		az  = (float)rotation["phi"]   + 90.0f ;
		alt = (float)rotation["theta"] ;
		phi = (float)rotation["omega"] - 90.0f ;
		break;

	case QUATERNION:
		is_quaternion = 0;
		e0 = (float)rotation["e0"] ;
		e1 = (float)rotation["e1"] ;
		e2 = (float)rotation["e2"] ;
		e3 = (float)rotation["e3"] ;
		break;

	case SPIN:
		is_quaternion = 1;
		Omega = (float)rotation["Omega"];
		e0 = cos(Omega*M_PI/360.0f);
		e1 = sin(Omega*M_PI/360.0f)* (float)rotation["n1"];
		e2 = sin(Omega*M_PI/360.0f)* (float)rotation["n2"];
		e3 = sin(Omega*M_PI/360.0f)* (float)rotation["n3"];
		break;

	case SGIROT:
		is_quaternion = 1;
		Omega = (float)rotation["q"]  ;
		e0 = cos(Omega*M_PI/360.0f);
		e1 = sin(Omega*M_PI/360.0f)* (float)rotation["n1"];
		e2 = sin(Omega*M_PI/360.0f)* (float)rotation["n2"];
		e3 = sin(Omega*M_PI/360.0f)* (float)rotation["n3"];
		break;

	case MATRIX:
		is_matrix = 1;
		matrix[0][0] = (float)rotation["m11"]  ;
		matrix[0][1] = (float)rotation["m12"]  ;
		matrix[0][2] = (float)rotation["m13"]  ;
		matrix[1][0] = (float)rotation["m21"]  ;
		matrix[1][1] = (float)rotation["m22"]  ;
		matrix[1][2] = (float)rotation["m23"]  ;
		matrix[2][0] = (float)rotation["m31"]  ;
		matrix[2][1] = (float)rotation["m32"]  ;
		matrix[2][2] = (float)rotation["m33"]  ;
		break;

	default:
		throw InvalidValueException(euler_type, "unknown Euler Type");
	}  // ends switch euler_type


	Vec3f postT  = get_posttrans( ) ;
	Vec3f preT   = get_pretrans( ) ;


	float azp  = az*M_PI/180;
	float altp  = alt*M_PI/180;
	float phip = phi*M_PI/180;
	
	if (!is_quaternion && !is_matrix) {
		matrix[0][0] =  cos(phip)*cos(azp) - cos(altp)*sin(azp)*sin(phip);
		matrix[0][1] =  cos(phip)*sin(azp) + cos(altp)*cos(azp)*sin(phip);
		matrix[0][2] =  sin(altp)*sin(phip);
		matrix[1][0] = -sin(phip)*cos(azp) - cos(altp)*sin(azp)*cos(phip);
		matrix[1][1] = -sin(phip)*sin(azp) + cos(altp)*cos(azp)*cos(phip);
		matrix[1][2] =  sin(altp)*cos(phip);
		matrix[2][0] =  sin(altp)*sin(azp);
		matrix[2][1] = -sin(altp)*cos(azp);
		matrix[2][2] =  cos(altp);
	}	
	if (is_quaternion){
		matrix[0][0] = e0 * e0 + e1 * e1 - e2 * e2 - e3 * e3;
		matrix[0][1] = 2.0f * (e1 * e2 + e0 * e3);
		matrix[0][2] = 2.0f * (e1 * e3 - e0 * e2);
		matrix[1][0] = 2.0f * (e2 * e1 - e0 * e3);
		matrix[1][1] = e0 * e0 - e1 * e1 + e2 * e2 - e3 * e3;
		matrix[1][2] = 2.0f * (e2 * e3 + e0 * e1);
		matrix[2][0] = 2.0f * (e3 * e1 + e0 * e2);
		matrix[2][1] = 2.0f * (e3 * e2 - e0 * e1);
		matrix[2][2] = e0 * e0 - e1 * e1 - e2 * e2 + e3 * e3;
		// keep in mind matrix[0][2] is M13 gives an e0 e2 piece, etc
	}
	// Now do post and pretrans: vfinal = vpost + R vpre;
	
	matrix[0][3] = postT.at(0) + matrix[0][0]*preT.at(0) + matrix[0][1]*preT.at(1) + matrix[0][2]*preT.at(2)  ;
	matrix[1][3] = postT.at(1) + matrix[1][0]*preT.at(0) + matrix[1][1]*preT.at(1) + matrix[1][2]*preT.at(2)  ;
	matrix[2][3] = postT.at(2) + matrix[2][0]*preT.at(0) + matrix[2][1]*preT.at(1) + matrix[2][2]*preT.at(2)  ;
}


void Transform3D::set_rotation(float m11, float m12, float m13,
                               float m21, float m22, float m23,
			       float m31, float m32, float m33)
{
	EulerType euler_type= MATRIX;
	Dict rot;
	rot["m11"]  = m11;
	rot["m12"]  = m12;
	rot["m13"]  = m13;
	rot["m21"]  = m21;
	rot["m22"]  = m22;
	rot["m23"]  = m23;
	rot["m31"]  = m31;
	rot["m32"]  = m32;
	rot["m33"]  = m33;
        set_rotation(euler_type, rot);  // Or should it be &rot ?
}

void Transform3D::set_rotation(const Vec3f & eahat, const Vec3f & ebhat,
                                    const Vec3f & eAhat, const Vec3f & eBhat)
{// this rotation rotates unit vectors a,b into A,B; 
//    The program assumes a dot b must equal A dot B
	Vec3f eahatcp(eahat);
	Vec3f ebhatcp(ebhat);
	Vec3f eAhatcp(eAhat);
	Vec3f eBhatcp(eBhat);
	
	eahatcp.normalize();
	ebhatcp.normalize();
	eAhatcp.normalize();
	eBhatcp.normalize();
	
	Vec3f aMinusA(eahatcp);
	aMinusA  -= eAhatcp;
	Vec3f bMinusB(ebhatcp);
	bMinusB  -= eBhatcp;


	Vec3f  nhat;
	float aAlength = aMinusA.length();
	float bBlength = bMinusB.length();
	if (aAlength==0){
		nhat=eahatcp;
	}else if (bBlength==0){
		nhat=ebhatcp;
	}else{
		nhat= aMinusA.cross(bMinusB);
		nhat.normalize();
	}

//		printf("nhat=%f,%f,%f \n",nhat[0],nhat[1],nhat[2]);

	Vec3f neahat  = eahatcp.cross(nhat);
	Vec3f nebhat  = ebhatcp.cross(nhat);
	Vec3f neAhat  = eAhatcp.cross(nhat);
	Vec3f neBhat  = eBhatcp.cross(nhat);
	
	float cosOmegaA = (neahat.dot(neAhat))  / (neahat.dot(neahat));
//	float cosOmegaB = (nebhat.dot(neBhat))  / (nebhat.dot(nebhat));
	float sinOmegaA = (neahat.dot(eAhatcp)) / (neahat.dot(neahat));
//	printf("cosOmegaA=%f \n",cosOmegaA); 	printf("sinOmegaA=%f \n",sinOmegaA);

	float OmegaA = atan2(sinOmegaA,cosOmegaA);
//	printf("OmegaA=%f \n",OmegaA*180/M_PI);
	
	EulerType euler_type=SPIN;
	Dict rotation;
	rotation["n1"]= nhat[0];
	rotation["n2"]= nhat[1];
	rotation["n3"]= nhat[2];
	rotation["Omega"] =OmegaA*180.0/M_PI;
	set_rotation(euler_type,  rotation);
}


float Transform3D::get_scale() const     // YYY
{
	// Assumes uniform scaling, calculation uses Z only.
	float scale =0;
	for (int i=0; i<3; i++) {
		for (int j=0; j<3; j++) {
			scale = scale + matrix[i][j]*matrix[i][j];
		}
	}

	return sqrt(scale/3);
}



Dict Transform3D::get_rotation(EulerType euler_type) const
{
	Dict result;

	float max = 1 - ERR_LIMIT;
	float sca=get_scale();
	float cosalt=matrix[2][2]/sca;


	float az=0;
	float alt = 0;
	float phi=0;
	float phiS = 0; // like az   (but in SPIDER ZXZ)
	float psiS =0;  // like phi  (but in SPIDER ZYZ)


// get alt, az, phi;  EMAN

	if (cosalt > max) {  // that is, alt close to 0
		alt = 0;
		az=0;
		phi =(180/M_PI)*(float)atan2(matrix[0][1], matrix[0][0]); 
	}
	else if (cosalt < -max) { // alt close to pi
		alt = 180;
		az=0; 
		phi=360.0f-(180/M_PI)*(float)atan2(matrix[0][1], matrix[0][0]);
	}
	else {
		alt = (180/M_PI)*(float) acos(cosalt);
		az  = 360.0f+(180/M_PI)*(float)atan2(matrix[2][0], -matrix[2][1]);
		phi = 360.0f+(180/M_PI)*(float)atan2(matrix[0][2], matrix[1][2]);
	}
	az=fmod(az+180.0f,360.0f)-180.0f;
	phi=fmod(phi+180.0f,360.0f)-180.0f;

//   get phiS, psiS ; SPIDER
	if (fabs(cosalt) > max) {  // that is, alt close to 0
		phiS=0;
		psiS = phi;
	}
	else {
		phiS = az   - 90.0f;
		psiS = phi  + 90.0f;
	}
	phiS = fmod((phiS   + 540.0f ), 360.0f) - 180.0f;
	psiS = fmod((psiS   + 540.0f ), 360.0f) - 180.0f;

//   do some quaternionic stuff here

	float nphi = (az-phi)/2.0f;
    // The next is also e0
	float cosOover2 = (cos((az+phi)*M_PI/360) * cos(alt*M_PI/360)) ;
	float sinOover2 = sqrt(1 -cosOover2*cosOover2);
	float cosnTheta = sin((az+phi)*M_PI/360) * cos(alt*M_PI/360) / sqrt(1-cosOover2*cosOover2) ;
	float sinnTheta = sqrt(1-cosnTheta*cosnTheta);
	float n1 = sinnTheta*cos(nphi*M_PI/180);
	float n2 = sinnTheta*sin(nphi*M_PI/180);
	float n3 = cosnTheta;
        float xtilt = 0;
        float ytilt = 0;
        float ztilt = 0;

	
	if (cosOover2<0) {
		cosOover2*=-1; n1 *=-1; n2*=-1; n3*=-1;
	}


	switch (euler_type) {
	case EMAN:
		result["az"]  = az;
		result["alt"] = alt;
		result["phi"] = phi;
		break;

	case IMAGIC:
		result["alpha"] = az;
		result["beta"] = alt;
		result["gamma"] = phi;
		break;

	case SPIDER:
		result["phi"]   = phiS;  // The first Euler like az
		result["theta"] = alt;
		result["psi"]   = psiS;
		break;

	case MRC:
		result["phi"]   = phiS;
		result["theta"] = alt;
		result["omega"] = psiS;
		break;

	case XYZ:
	        xtilt = atan2(-sin((M_PI/180.0f)*phiS)*sin((M_PI/180.0f)*alt),cos((M_PI/180.0f)*alt));
	        ytilt = asin(  cos((M_PI/180.0f)*phiS)*sin((M_PI/180.0f)*alt));
	        ztilt = psiS*M_PI/180.0f - atan2(sin(xtilt), cos(xtilt) *sin(ytilt));

		xtilt=fmod(xtilt*180/M_PI+540.0f,360.0f) -180.0f;
		ztilt=fmod(ztilt*180/M_PI+540.0f,360.0f) -180.0f;

		result["xtilt"]  = xtilt;
		result["ytilt"]  = ytilt*180/M_PI;
		result["ztilt"]  = ztilt;
		break;



	case QUATERNION:
		result["e0"] = cosOover2 ;
		result["e1"] = sinOover2 * n1 ;
		result["e2"] = sinOover2 * n2;
		result["e3"] = sinOover2 * n3;
		break;

	case SPIN:
		result["Omega"] =360.0f* acos(cosOover2)/ M_PI ;
		result["n1"] = n1;
		result["n2"] = n2;
		result["n3"] = n3;
		break;

	case SGIROT:
		result["q"] = 360.0f*acos(cosOover2)/M_PI ;
		result["n1"] = n1;
		result["n2"] = n2;
		result["n3"] = n3;
		break;

	case MATRIX:
		result["m11"] = matrix[0][0] ;
		result["m12"] = matrix[0][1] ;
		result["m13"] = matrix[0][2] ;
		result["m21"] = matrix[1][0] ;
		result["m22"] = matrix[1][1] ;
		result["m23"] = matrix[1][2] ;
		result["m31"] = matrix[2][0] ;
		result["m32"] = matrix[2][1] ;
		result["m33"] = matrix[2][2] ;
		break;

	default:
		throw InvalidValueException(euler_type, "unknown Euler Type");
	}

	return result;
}



map<string, int> Transform3D::symmetry_map = map<string, int>();


Transform3D Transform3D::inverse() const    //   YYN need to test it for sure
{
	// First Find the scale
	EulerType eE=EMAN;


	float scale   = get_scale();
	Vec3f preT   = get_pretrans( ) ;
	Vec3f postT   = get_posttrans( ) ;
	Dict angs     = get_rotation(eE);
	Dict invAngs  ;

	invAngs["phi"]   = 180.0f - (float) angs["az"] ;
	invAngs["az"]    = 180.0f - (float) angs["phi"] ;
	invAngs["alt"]   = angs["alt"] ;

//    The inverse result
//
//           Z_phi   X_alt     Z_az
//                 is
//       Z_{pi-az}   X_alt  Z_{pi-phi}
//      The reason for the extra pi's, is because one would like to keep alt positive

	float inverseScale= 1/scale ;

	Transform3D invM;

	invM.set_rotation(EMAN, invAngs);
	invM.apply_scale(inverseScale);
	invM.set_pretrans(-postT );
	invM.set_posttrans(-preT );


	return invM;

}


// Symmetry Stuff

Transform3D Transform3D::get_sym(const string & symname, int n) const
{
	int nsym = get_nsym(symname);

	Transform3D invalid;
	invalid.set_rotation( -0.1f, -0.1f, -0.1f);

	if (n >= nsym) {
		return invalid;
	}
	// see www.math.utah.edu/~alfeld/math/polyhedra/polyhedra.html for pictures
	// By default we will put largest symmetry along z-axis.

	// Each Platonic Solid has 2E symmetry elements.


	// An icosahedron has   m=5, n=3, F=20 E=30=nF/2, V=12=nF/m,since vertices shared by 5 triangles;
	// It is composed of 20 triangles. E=3*20/2;


	// An dodecahedron has m=3, n=5   F=12 E=30  V=20
	// It is composed of 12 pentagons. E=5*12/2;   V= 5*12/3, since vertices shared by 3 pentagons;



    // The ICOS symmetry group has the face along z-axis

	float lvl0=0;                             //  there is one pentagon on top; five-fold along z
	float lvl1= 63.4349f; // that is atan(2)  // there are 5 pentagons with centers at this height (angle)
	float lvl2=116.5651f; //that is 180-lvl1  // there are 5 pentagons with centers at this height (angle)
	float lvl3=180.f;                           // there is one pentagon on the bottom
             // Notice that 63.439 is the angle between two faces of the dual object

	static double ICOS[180] = { // This is with a pentagon normal to z 
		  0,lvl0,0,    0,lvl0,288,   0,lvl0,216,   0,lvl0,144,  0,lvl0,72,
		  0,lvl1,36,   0,lvl1,324,   0,lvl1,252,   0,lvl1,180,  0,lvl1,108,
		 72,lvl1,36,  72,lvl1,324,  72,lvl1,252,  72,lvl1,180,  72,lvl1,108,
		144,lvl1,36, 144,lvl1,324, 144,lvl1,252, 144,lvl1,180, 144,lvl1,108,
		216,lvl1,36, 216,lvl1,324, 216,lvl1,252, 216,lvl1,180, 216,lvl1,108,
		288,lvl1,36, 288,lvl1,324, 288,lvl1,252, 288,lvl1,180, 288,lvl1,108,
		 36,lvl2,0,   36,lvl2,288,  36,lvl2,216,  36,lvl2,144,  36,lvl2,72,
		108,lvl2,0,  108,lvl2,288, 108,lvl2,216, 108,lvl2,144, 108,lvl2,72,
		180,lvl2,0,  180,lvl2,288, 180,lvl2,216, 180,lvl2,144, 180,lvl2,72,
		252,lvl2,0,  252,lvl2,288, 252,lvl2,216, 252,lvl2,144, 252,lvl2,72,
		324,lvl2,0,  324,lvl2,288, 324,lvl2,216, 324,lvl2,144, 324,lvl2,72,
   		  0,lvl3,0,    0,lvl3,288,   0,lvl3,216,   0,lvl3,144,   0,lvl3,72
	};


	// A cube has   m=3, n=4, F=6 E=12=nF/2, V=8=nF/m,since vertices shared by 3 squares;
	// It is composed of 6 squares.


	// An octahedron has   m=4, n=3, F=8 E=12=nF/2, V=6=nF/m,since vertices shared by 4 triangles;
	// It is composed of 8 triangles.

    // We have placed the OCT symmetry group with a face along the z-axis
        lvl0=0;
	lvl1=90;
	lvl2=180;

	static float OCT[72] = {// This is with a face of a cube along z 
		      0,lvl0,0,   0,lvl0,90,    0,lvl0,180,    0,lvl0,270,
		      0,lvl1,0,   0,lvl1,90,    0,lvl1,180,    0,lvl1,270,
		     90,lvl1,0,  90,lvl1,90,   90,lvl1,180,   90,lvl1,270,
		    180,lvl1,0, 180,lvl1,90,  180,lvl1,180,  180,lvl1,270,
		    270,lvl1,0, 270,lvl1,90,  270,lvl1,180,  270,lvl1,270,
		      0,lvl2,0,   0,lvl2,90,    0,lvl2,180,    0,lvl2,270
	};
	// B^4=A^3=1;  BABA=1; implies   AA=BAB, ABA=B^3 , AB^2A = BBBABBB and
	//   20 words with at most a single A
    //   1 B BB BBB A  BA AB BBA BAB ABB BBBA BBAB BABB ABBB BBBAB BBABB BABBB 
    //                        BBBABB BBABBB BBBABBB 
     // also     ABBBA is distinct yields 4 more words
     //    ABBBA   BABBBA BBABBBA BBBABBBA
     // for a total of 24 words
     // Note A BBB A BBB A  reduces to BBABB
     //  and  B A BBB A is the same as A BBB A BBB etc.

    // The TET symmetry group has a face along the z-axis
    // It has n=m=3; F=4, E=6=nF/2, V=4=nF/m
        lvl0=0;         // There is a face along z
	lvl1=109.4712f;  //  that is acos(-1/3)  // There  are 3 faces at this angle

	static float TET[36] = {// This is with the face along z 
	      0,lvl0,0,   0,lvl0,120,    0,lvl0,240,
	      0,lvl1,60,   0,lvl1,180,    0,lvl1,300,
	    120,lvl1,60, 120,lvl1,180,  120,lvl1,300,
	    240,lvl1,60, 240,lvl1,180,  240,lvl1,300
	};
	// B^3=A^3=1;  BABA=1; implies   A^2=BAB, ABA=B^2 , AB^2A = B^2AB^2 and
	//   12 words with at most a single A
    //   1 B BB  A  BA AB BBA BAB ABB BBAB BABB BBABB
    // at most one A is necessary

	Transform3D ret;
	SymType type = get_sym_type(symname);

	switch (type) {
	case CSYM:
		ret.set_rotation( n * 360.0f / nsym, 0, 0);
		break;
	case DSYM:
		if (n >= nsym / 2) {
			ret.set_rotation((n - nsym/2) * 360.0f / (nsym / 2),180.0f, 0);
		}
		else {
			ret.set_rotation( n * 360.0f / (nsym / 2),0, 0);
		}
		break;
	case ICOS_SYM:
		ret.set_rotation((float)ICOS[n * 3 ]    ,
				 (float)ICOS[n * 3 + 1] ,
				 (float)ICOS[n * 3 + 2] );
		break;
	case OCT_SYM:
		ret.set_rotation((float)OCT[n * 3]     ,
				 (float)OCT[n * 3 + 1] , 
				 (float)OCT[n * 3 + 2] );
		break;
	case TET_SYM:
		ret.set_rotation((float)TET[n * 3 ]    ,
				 (float)TET[n * 3 + 1] ,
				 (float)TET[n * 3 + 2] );
		break;
	case ISYM:
		ret.set_rotation(0, 0, 0);
	default:
		throw InvalidValueException(type, symname);
	}

	ret = (*this) * ret;

	return ret;
}



int Transform3D::get_nsym(const string & name)
{
	if (name == "") {
		return 0;
	}

	if (symmetry_map.find(name) != symmetry_map.end()) {
		return symmetry_map[name];
	}

	string symname = name;

	for (size_t i = 0; i < name.size(); i++) {
		if (isalpha(name[i])) {
			symname[i] = (char)tolower(name[i]);
		}
	}

	if (symmetry_map.find(name) != symmetry_map.end()) {
		return symmetry_map[symname];
	}

	SymType type = get_sym_type(symname);
	int nsym = 0;

	switch (type) {
	case CSYM:
		nsym = atoi(symname.c_str() + 1);
		break;
	case DSYM:
		nsym = atoi(symname.c_str() + 1) * 2;
		break;
	case ICOS_SYM:
		nsym = 60;
		break;
	case OCT_SYM:
		nsym = 24;
		break;
	case TET_SYM:
		nsym = 12;
		break;
	case ISYM:
		nsym = 1;
		break;
	case UNKNOWN_SYM:
	default:
		throw InvalidValueException(type, name);
	}

	symmetry_map[symname] = nsym;

	return nsym;
}



Transform3D::SymType Transform3D::get_sym_type(const string & name)
{
	SymType t = UNKNOWN_SYM;

	if (name[0] == 'c') {
		t = CSYM;
	}
	else if (name[0] == 'd') {
		t = DSYM;
	}
	else if (name == "icos") {
		t = ICOS_SYM;
	}
	else if (name == "oct") {
		t = OCT_SYM;
	}
	else if (name == "tet") {
		t = TET_SYM;
	}
	else if (name == "i") {
		t = ISYM;
	}
	return t;
}

vector<Transform3D*>
Transform3D::angles2tfvec(EulerType eulertype, const vector<float> ang) {
	int nangles = ang.size() / 3;
	vector<Transform3D*> tfvec;
	for (int i = 0; i < nangles; i++) {
		tfvec.push_back(new Transform3D(eulertype,ang[3*i],ang[3*i+1],ang[3*i+2]));
	}
	return tfvec;
}


/* vim: set ts=4 noet: */
