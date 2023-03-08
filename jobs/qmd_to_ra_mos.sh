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

wrkdir=${PTMP}/gmos/gmos.${PDY}
mkdir -p ${wrkdir}

input=/lfs/h1/mdl/nbm/noscrub/david.rudack/u850

if [ $VAR == "maxt" ] ; then
        HH=12
	infile=${input}/12z.nbm_prob-maxt_percentiles.202011-202211.metar
	outfile=gmos_maxt_${PDY}.grd_ra
elif [ $VAR == "mint" ] ; then
        HH=12
	#infile=${input}/12z.nbm_prob-mint_percentiles.202011-202211.metar
	infile=${input}/qmd_probmint.forecasts.t12z.2210-2211.yes-climo
	outfile=gmos_mint_${PDY}.grd_ra
else
        #HH=12
	echo "FATAL ERROR: Improper variable: ${VAR}"
	exit 1
fi

if [ -d ${wrkdir} ] ; then
	cd ${wrkdir}
	if [ -s ${infile} ] ; then
		if [ -s ${outfile} ] ; then
			echo "Random access file already exists!  Exiting..."
			exit 0
		else
			itdlp ${infile} -tdlpra $outfile -rasize large -date ${PDY}${HH}
		fi
	else
		echo "ERROR: Input QMD MOS file not found!"
		exit 1
	fi
else
	echo "ERROR: Working directory not found!"
	exit 1
fi

exit 0
