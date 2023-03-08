#!/usr/bin/env bash

set -x

module reset
module load PrgEnv-intel/8.2.0
module load intel/19.1.3.304
module load craype/2.7.13
module load prod_util/2.0.13
module use /lfs/h1/mdl/nbm/save/apps/modulefiles
module load itdlp/2.0.2
module load wgrib2/2.0.8

wrkdir=$STMP/getcore.${PBS_JOBID} #dummy directory on stmp for effeciency
mkdir -p ${wrkdir}
cd ${wrkdir}

#import var info to identify which hour we are looking for
if [[ $VAR == "maxt" ]] || [[ $VAR == "MAXT" ]] ; then
	HH=12
	fcsthrs="018 042 066 090 114 138 162 186 210 234 258"
elif [[ $VAR == "mint" ]] || [[ $var == "MINT" ]] ; then
	HH=12
	fcsthrs="030 054 078 102 126 150 174 198 222 246" # 270"
elif [[ $VAR == "qpf" ]] ; then
	HH=12
	fcsthrs="006 012 018 024 030 036 042 048 054 060 066 072 078 084 090 096 102 108 114 120 126 132 138 144"
fi

if [[ $VER == "4.0" ]] ; then
	#override HH and fcst hours for tmax/tmin core to match with grib2 formatting
	if [[ $VAR == "maxt" || $VAR == "MAXT" ]] ; then
		HH=19
		fcsthrs="029 053 077 101 125 149 173 197 221 245 269"
		abbr="TMAX"
	elif [[ $VAR == "mint" || $VAR == "MINT" ]] ; then
		HH=19
		fcsthrs="017 041 065 089 113 137 161 185 209 233 257"
		abbr="TMIN"
	elif [[ $VAR == "qpf" ]] ; then
		abbr="APCP"
	fi
	baseurl="https://noaa-nbm-grib2-pds.s3.amazonaws.com"
	wrkdir=${PTMP}/blend.v4.0/${PDY}
	mkdir -p ${wrkdir}
	cd ${wrkdir}
	for fhr in $fcsthrs; do
		wget ${baseurl}/blend.${PDY}/${HH}/core/blend.t${HH}z.core.f${fhr}.co.grib2
		$WGRIB2 blend.t${HH}z.core.f${fhr}.co.grib2 -match ${abbr} -grib_out tmpgrib.grib2
		cp blend.t${HH}z.core.f${fhr}.co.grib2 blend.t${HH}z.core.f${fhr}.co.grib2_orig
		mv tmpgrib.grib2 blend.t${HH}z.core.f${fhr}.co.grib2
        done

elif [[ $VER == "4.1" ]] ; then

	hpssdir=/NCEPDEV/mdl-blend/5year/blend.v4.1-para
	wrkdir=${PTMP}/blend.v4.1/${PDY}
	#if file has already been pulled, skip and gracefully exit
	if [[ ${VAR} == "mint" || ${VAR} == "maxt" || ${VAR} == "MINT" || ${VAR} == "MAXT" ]] ; then
		if [ -s ${wrkdir}/blend.t${HH}z.blend.maewfcst_tmp.co.grd_sq ] ; then
			echo "V41 temp files already pulled for ${PDY}."	
			exit 0
		fi
	elif [[ $VAR == "qpf" ]] ; then
		if [ -s ${wrkdir}/blend.t${HH}z.blend_expertfcst_precip.co.grd_sq ] ; then
			echo "V41 qpf files already pulled for ${PDY}."
			exit 0
		fi
	fi
	mkdir -p ${wrkdir}
	cd ${wrkdir}
	htar -tvf ${hpssdir}/blend.${PDY}.tar > blend.core.prep.${PDY}
	if [[ $VAR == "mint" || $VAR == "maxt" ]] ; then
		egrep blend.t${HH}z.blend.maewfcst_tmp.co blend.core.prep.${PDY} | awk '{print $7}' > blend.core.find.${PDY}
	elif [[ $VAR == "qpf" ]] ; then
		egrep blend.t${HH}z.blend_expertfcst_precip.co blend.core.prep.${PDY} | awk '{print $7}' > blend.core.find.${PDY}
	fi
	if [[ -s blend.core.find.${PDY} ]] ; then
		htar -H nostage -xvf ${hpssdir}/blend.${PDY}.tar -L blend.core.find.${PDY}
		cut -c2- blend.core.find.${PDY} > tmpcore.${PDY}
		while read fname
		do
			mv $fname $wrkdir
		done < tmpcore.${PDY}
	else
		echo "Can't find file in archive!"
		exit 1
	fi
elif [[ $VER == "MOS" ]] ; then
	echo "Running with MOS...nothing to pull here!"
fi

exit
