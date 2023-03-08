import sys,os,re,traceback
import argparse
from urllib.request import urlretrieve, urlopen
from netCDF4 import Dataset
from datetime import datetime, timedelta
import numpy as np
#import datetime
#from datetime import timedelta
import warnings
warnings.filterwarnings("ignore")

def cwa_list(input_region):
        region_dict ={"WR":"BYZ,BOI,LKN,EKA,FGZ,GGW,TFX,VEF,LOX,MFR,MTR,MSO,PDT,PSR,PIH,PQR,REV,STO,SLC,SGX,HNX,SEW,OTX,TWC","CR":"ABR,BIS,CYS,LOT,DVN,BOU,DMX,DTX,DDC,DLH,FGF,GLD,GJT,GRR,GRB,GID,IND,JKL,EAX,ARX,ILX,LMK,MQT,MKX,MPX,LBF,APX,IWX,OAX,PAH,PUB,UNR,RIW,FSD,SGF,LSX,TOP,ICT","ER":"ALY,LWX,BGM,BOX,BUF,BTV,CAR,CTP,RLX,CHS,ILN,CLE,CAE,GSP,MHX,OKX,PHI,PBZ,GYX,RAH,RNK,AKQ,ILM","SR":"ABQ,AMA,FFC,EWX,BMX,BRO,CRP,EPZ,FWD,HGX,HUN,JAN,JAX,KEY,MRX,LCH,LZK,LUB,MLB,MEG,MFL,MOB,MAF,OHX,LIX,OUN,SJT,SHV,TAE,TBW,TSA"}
        if (input_region in ["WR", "CR", "SR", "ER"]):
                cwas_list = region_dict[input_region]
        else:
                cwas_list = input_region
        return cwas_list

def get_stageiv(enddate):
	#if isinstance(enddate, datetime.date):
	siv_url="https://water.weather.gov/precip/downloads/"+enddate.strftime('%Y')+"/"+enddate.strftime('%m')+"/"+enddate.strftime('%d')+"/nws_precip_1day_"+enddate.strftime('%Y%m%d')+"_conus.nc"
	data=urlopen(siv_url).read()
	nc = Dataset('data',memory=data)
	stageiv = nc.variables['observation']
	s4x = nc.variables['x']
	s4y = nc.variables['y']
	return stageiv,s4x,s4y
	#else:
	#	print("FATAL ERROR: Improper end date time for stageiv: " + enddate)


def main():

	parser=argparse.ArgumentParser()
	parser.add_argument('-element',type=str,dest="element",choices=["maxt","mint","qpf"],required=True,help="REQUIRED element to look for obs file (maxt, mint)")
	parser.add_argument('-region',type=str,dest="region",required=True,help="REQUIRED region or WFO to collect stats over")
	parser.add_argument('-date',type=str,dest="date",required=True,help="REQUIRED date of obs YYYYMMDD")
	parser.add_argument('-network',type=str,dest="network",choices=["ALL","NWS","RAWS","NWS+RAWS"],help="Network to use (ALL/NWS/RAWS/NWS+RAWS)")
	parser.add_argument('-stageiv',dest='use_stageiv',action='store_true')
	parser.set_defaults(network="ALL",use_stageiv=False)

	argz=parser.parse_args()
	element=argz.element
	region=argz.region
	obdate=argz.date
	network_selection=argz.network
	fixeddate=datetime.strptime(obdate,'%Y%m%d')
	use_stageiv=argz.use_stageiv

	if element == "maxt":
		valid_date_start = fixeddate
		valid_date_end = fixeddate + timedelta(days=1)
		obs_start_hour = "1200"
		obs_end_hour = "0600"
		ob_stat = "maximum"
		valid_end_datetime = valid_date_end + timedelta(hours=(int(obs_end_hour)/100))
	elif element == "mint":
		valid_date_start = fixeddate
		valid_date_end = fixeddate
		obs_start_hour = "0000"
		obs_end_hour = "1800"
		ob_stat = "minimum"
		valid_end_datetime = valid_date_end + timedelta(hours=(int(obs_end_hour)/100))
	elif element == "qpf":
		valid_date_start=fixeddate - timedelta(days=1)
		valid_date_end=fixeddate
		obs_start_hour="1200"
		obs_end_hour="1200"
		valid_end_datetime = valid_date_end + timedelta(hours=12)
		valid_start_datetime = valid_date_start + timedelta(hours=12)
		print("Valid date start, end =" + valid_date_start.strftime('%Y%m%d') + "   " + valid_date_end.strftime('%Y%m%d'))
	elif element == "maxwind":
		nbm_qmd_valid_hour="06"
		obs_start_hour="0600"
		obs_end_hour="0600"
		ob_stat="maximum"
		valid_date_start = datetime.strptime(valid_date,'%Y-%m-%d')
		valid_date_end = datetime.strptime(valid_date,'%Y-%m-%d') + timedelta(days=1)
		valid_end_datetime=valid_date_end + timedelta(hours=(int(obs_end_hour)/100))
		core_init = nbm_init
		nbm_core_valid_end_datetime = valid_date_end
		nbm_qmd_valid_end_datetime = valid_date_end + timedelta(hours=int(nbm_qmd_valid_hour))
		nbm_core_fhdelta = valid_end_datetime - nbm_init


	current_datetime=datetime.now()

	synoptic_token = "62e9269f0a164da1b2415ddcf8f4f29e" #hard coded from synoptic data
	
	# Setup a dictionary for translating a form selection into a something we can pass to mesowest API
	network_dict = {"NWS+RAWS":"&network=1,2", "NWS":"&network=1", "RAWS": "&network=2", "NWS+RAWS+HADS": "network=1,2,106", "ALL":""} #, "CUSTOM": "&network="+network_input, "LIST": "&stid="+network_input}
	network_string = network_dict[network_selection]

	print('Getting obs...')
	obs = {}
	if region == "CONUS":
	       region_list = ["WR", "CR", "SR", "ER"]
	else:
        	region_list = [region]
	for region in region_list:
		if (valid_end_datetime <= current_datetime):
			print("  > Grabbing obs for: ", region)
			print("List of CWAs: ", cwa_list(region) )
			json_name = "Obs_"+element+"_"+valid_date_start.strftime('%Y%m%d')+obs_start_hour+"_"+valid_date_end.strftime('%Y%m%d')+obs_end_hour+"_"+region+".json"
			if os.path.exists(json_name):
				pass
			else:
				if element == "maxt" or element == "mint":
					obs_url = "https://api.synopticlabs.org/v2/stations/statistics?token="+synoptic_token+"&cwa="+cwa_list(region)+"&vars=air_temp&start="+ valid_date_start.strftime('%Y%m%d')+obs_start_hour+"&end="+valid_date_end.strftime('%Y%m%d')+obs_end_hour+"&units=temp%7Cf&within=1440&type="+ob_stat+"&status=active"+network_string
				elif element == "maxwind":
					obs_url = "https://api.synopticlabs.org/v2/stations/statistics?token="+synoptic_token+"&cwa="+cwa_list(region)+"&vars=wind_speed&start="+valid_date_start.strftime('%Y%m%d')+obs_start_hour+"&end="+valid_date_end.strftime('%Y%m%d')+obs_end_hour+"&type="+ob_stat+"&status=active"+network_string #leaving out units - meters per second is default
				elif (element == "qpf"):
					obs_start = valid_start_datetime.strftime('%Y%m%d%H%M')
					obs_end = fixeddate
					obs_end = valid_end_datetime.strftime('%Y%m%d%H%M')
					if use_stageiv:
						obs_url = "https://api.synopticdata.com/v2/stations/metadata?&token="+synoptic_token+"&cwa="+cwa_list(region)+"&fields=status,latitude,longitude,name,elevation"+network_string
						stageiv_url = "https://water.weather.gov/precip/downloads/"+valid_date_end.strftime('%Y')+"/"+valid_date_end.strftime('%m')+"/"+valid_date_end.strftime('%d')+"/nws_precip_1day_"+valid_date_end.strftime('%Y%m%d')+"_conus.nc"
						stageiv_name = "StageIV_qpf_"+valid_date_start.strftime('%Y%m%d')+obs_start_hour+"_"+valid_date_end.strftime('%Y%m%d')+obs_end_hour+"_"+region+".nc"
						print("Grabbing Stage IV file: " + stageiv_url)
						urlretrieve(stageiv_url,stageiv_name)
						#stageiv,s4xs,s4ys = get_stageiv(valid_end_datetime)
						#s4xs,s4ys = np.meshgrid(s4xs,s4ys)
					else:
						obs_url = "https://api.synopticdata.com/v2/stations/precipitation?&token="+synoptic_token+"&start="+obs_start+"&end="+obs_end+"&pmode=totals&obtimezone=utc&units=precip|in&cwa="+cwa_list(region)+"&fields=status,latitude,longitude,name,elevation"+network_string
				print(obs_url)
				urlretrieve(obs_url, json_name)
				print ("Obs file retrieved!")
				#os.system("cat " + json_name + " >> " + finalname)

if __name__ == "__main__":
	main()
	exit()
