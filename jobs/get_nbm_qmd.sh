#!/usr/bin/env bash

set -x

module reset
module load PrgEnv-intel/8.2.0
module load intel/19.1.3.304
module load craype/2.7.13
module load prod_util/2.0.13
module use /lfs/h1/mdl/nbm/save/apps/modulefiles
module load itdlp/2.0.2

wrkdir=$STMP/getqmd.${PBS_JOBID} #dummy directory on stmp for effeciency
mkdir -p ${wrkdir}
cd ${wrkdir}

#import var info to identify which hour we are looking for
if [[ $VAR == "maxt" || $VAR == "MAXT" ]] ; then
	HH=12
	fcsthrs="018 042 066 090 114 138 162 186 210 234 258"
elif [[ $VAR == "mint" || $var == "MINT" ]] ; then
	HH=12
	fcsthrs="030 054 078 102 126 150 174 198 222 246 270"
elif [[ $VAR == "qpf" ]] ; then
	HH=12
	fcsthrs="006 012 018 024 030 036 042 048 054 060 066 072 078 084 090 096 102 108 114 120 126 132 138 144 150 156 162 168 174 180 186 192"
fi

if [[ $VER == "4.0" ]] ; then
	baseurl="https://noaa-nbm-grib2-pds.s3.amazonaws.com"
	wrkdir=${PTMP}/blend.v4.0/${PDY}
	mkdir -p ${wrkdir}
	cd ${wrkdir}
	for fhr in $fcsthrs; do
		wget ${baseurl}/blend.${PDY}/${HH}/qmd/blend.t${HH}z.qmd.f${fhr}.co.grib2
        done

elif [[ $VER == "4.1" || $VER == "MOS" ]] ; then

	hpssdir=/NCEPDEV/mdl-blend/5year/blend.v4.1-para
	wrkdir=${PTMP}/blend.v4.1/${PDY}
	#Check to see if directory/files exist already.  If so, exit gracefully
	if [[ -s ${wrkdir}/blend.t12z.temp_forecast.co.2p5.tdlp || -s ${wrkdir}/blend.t12z.precip_forecast.co.2p5.tdlp ]] ; then
		echo "QMD files already pulled!  Exiting..."
		exit 0	
	fi
	mkdir -p ${wrkdir}
	cd ${wrkdir}
	htar -tvf ${hpssdir}/blend.${PDY}.tar > blend.qmd.prep.${PDY}
	if [[ $VAR == "mint" || $VAR == "maxt" ]] ; then
		egrep "blend.t${HH}z.temp_forecast" blend.qmd.prep.${PDY} | awk '{print $7}' > blend.qmd.find.${PDY}
	elif [[ $VAR == "qpf" ]] ; then
		egrep "blend.t${HH}z.precip_forecast" blend.qmd.prep.${PDY} | awk '{print $7}' > blend.qmd.find.${PDY}
	elif [[ $VAR == "mxwnd" || $VAR == "gust" ]] ; then
		egrep "blend.t${HH}z.wind_forecast" blend.qmd.prep.${PDY} | awk '{print $7}' > blend.qmd.find.${PDY}
	else
		err_exit "Improper variable: $VAR"
	fi
	if [[ -s blend.qmd.find.${PDY} ]] ; then
		htar -H nostage -xvf ${hpssdir}/blend.${PDY}.tar -L blend.qmd.find.${PDY}
		cut -c2- blend.qmd.find.${PDY} > tmpqmd.${PDY}
		while read fname
		do
			mv $fname $wrkdir
		done < tmpqmd.${PDY}
	else
		echo "Can't find file in archive!"
		exit 1
	fi
else
	echo "FATAL ERROR: Invalid Version Number: ${VER}"
	exit 1
fi

exit
