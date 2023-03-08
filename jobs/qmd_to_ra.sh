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
elif [ $VAR == "qpf" ] ; then
        HH=12
elif [ $VAR == "maxwind" ] ; then
	HH=12
else
	echo "Unknown variable: ${VAR}."
	exit 1
fi

if [ $VER == "4.0" ] ; then
	echo "Version v4.0 uses grib2 files...no need for conversion"
	exit 0
fi

if [ -d ${wrkdir} ] ; then
	cd ${wrkdir}
	if [ -s tmpqmd.${PDY} ] ; then
		while read fname; do
			fonly=`echo $fname | sed 's:.*/::'`
                        fout=`echo $fonly | sed 's/tdlp/tdlp_ra/'`
			if [ -s $fonly ] ; then
				if [ -s $fout ] ; then
					rm $fout
				fi
				itdlp $fonly -tdlpra $fout -rasize large -date ${PDY}${HH}
			else
				echo "ERROR: QMD file not found!"
				exit 1
			fi
		done < tmpqmd.${PDY}
	else
		echo "ERROR: QMD file list not found!"
		exit 1
	fi
else
	echo "ERROR: Directory not found!"
	exit 1
fi

exit 0
