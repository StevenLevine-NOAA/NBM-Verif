#!/usr/bin/env bash

set -x

module reset
module use /lfs/h1/mdl/nbm/save/apps/modulefiles
module load PrgEnv-intel/8.2.0
module load intel/19.1.3.304
module load craype/2.7.13
module load prod_util/2.0.13
module use /lfs/h1/mdl/nbm/save/apps/modulefiles
module load itdlp/2.0.2

wrkdir=${PTMP}/blend.v${VER}/${PDY}

if [ $VAR == "maxt" ] ; then
	HH=12
elif [ $VAR == "mint" ] ; then
	HH=12
else
	HH=12
fi

if [ $VER == "4.0" ] ; then
	echo "Version number is v4.0...grib files so no need to convert!"
	exit 0
fi

if [ -d ${wrkdir} ] ; then
	cd ${wrkdir}
	if [ -s tmpcore.${PDY} ] ; then
		while read fname; do
			fonly=`echo $fname | sed 's:.*/::'`
                        fout=`echo $fonly | sed 's/grd_sq/grd_ra/'`
			if [ -s $fonly ] ; then
				if [ -s $fout ] ; then
					rm $fout
				fi
				itdlp $fonly -tdlpra $fout -rasize large -date ${PDY}${HH}
			else
				echo "ERROR: Core file not found!"
				exit 1
			fi
		done < tmpcore.${PDY}
	else
		echo "ERROR: Core file list not found!"
		exit 1
	fi
else
	echo "ERROR: Directory not found!"
	exit 1
fi

exit 0
