#!/usr/bin/sh

set -x

wrkdir=${STMP}/getsyn.${PBS_JOBID}
mkdir -p ${wrkdir}
cd ${wrkdir}

COMOUT=${PTMP}/synobs/synobs.${PDY}
mkdir -p ${COMOUT}

if [ -s ${COMOUT}/Obs_${VAR}*${DATE}*${REGION}.json ] ; then
	echo "Obs file already present!  Exiting..."
	exit 0
fi

if [ ${VAR} == "qpf" ] ; then
	python ${HOME}/ush/get_synobs.py -element ${VAR} -region ${REGION} -date ${PDY} -network ${NETWORK} #-stageiv
	#cp StageIV*nc ${COMOUT}
else
	python ${HOME}/ush/get_synobs.py -element ${VAR} -region ${REGION} -date ${PDY} -network ${NETWORK}
fi

cp *${REGION}*json ${COMOUT}
#cp StageIV*nc ${COMOUT}

exit


