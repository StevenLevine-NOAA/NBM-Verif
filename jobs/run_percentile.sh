#!/usr/bin/env bash

set -x

module reset
module use /lfs/h1/mdl/nbm/save/apps/modulefiles
module load PrgEnv-intel/8.2.0
module load intel/19.1.3.304
module load craype/2.7.13
module load cray-mpich/8.1.7
module load prod_util/2.0.13
module load python/3.8.6
module load python-modules/3.8.6
module load g2c/1.6.4
module load proj/7.1.0
module load geos/3.8.1

wrkdir=$STMP/percentile.${PBS_JOBID}
mkdir -p ${wrkdir}
cd ${wrkdir}

if [ $VER == "4.1" ] ; then
	#if [ $VAR == "qpf" ] ; then
	#	python ${HOME}/ush/percentile_tdlpack_withobs.py -datafiles ${PTMP}/blend.v${VER} -obfiles ${PTMP}/synobs -var ${VAR} -region ${REGION} -runtime ${RUNPDY} -validtime ${VALPDY} -network ${NETWORK} -stageiv
	#else
	COMOUT=${PTMP}/percentile_41/${VALPDY}
	mkdir -p ${COMOUT}
	python ${HOME}/ush/percentile_tdlpack_withobs.py -datafiles ${PTMP}/blend.v${VER} -obfiles ${PTMP}/synobs -var ${VAR} -region ${REGION} -runtime ${RUNPDY} -validtime ${VALPDY} -network ${NETWORK}
	cp *png ${COMOUT}
	if [ -s obs_${VAR}_${RUNPDY}_${VALPDY}_${REGION}.csv ] ; then
		cp obs_${VAR}_${RUNPDY}_${VALPDY}_${REGION}.csv ${COMOUT}
	fi
elif [ $VER == "4.0" ] ; then
	COMOUT=${PTMP}/percentile_40/${VALPDY}
	mkdir -p ${COMOUT}
	python ${HOME}/ush/percentile_grib2_final.py -datafiles ${PTMP}/blend.v${VER} -obfiles ${PTMP}/synobs -var ${VAR} -region ${REGION} -runtime ${RUNPDY} -validtime ${VALPDY} -network ${NETWORK}
	cp *png ${COMOUT}
	if [ -s obs_${VAR}_${RUNPDY}_${VALPDY}_${REGION}.csv ] ; then
		cp obs_${VAR}_${RUNPDY}_${VALPDY}_${REGION}.csv ${COMOUT}
	fi
elif [ $VER == "MOS" ] ; then
	COMOUT=${PTMP}/percentile_mos/${VALPDY}
	mkdir -p ${COMOUT}
	#python ${HOME}/ush/percentile_mos_tdlpack_withobs.py
	python ${HOME}/ush/mosobs.py -mosfile ${PTMP}/gmos -obfiles ${PTMP}/synobs -nbmfile ${PTMP}/blend.v4.1 -var ${VAR} -region ${REGION} -runtime ${RUNPDY} -validtime ${VALPDY} -network ${NETWORK} -compareto "MOS"
	cp *png ${COMOUT}
	if [ -s obs_${VAR}_${RUNPDY}_${VALPDY}_${REGION}.csv ] ; then
                cp obs_${VAR}_${RUNPDY}_${VALPDY}_${REGION}.csv ${COMOUT}
        fi
fi


exit
