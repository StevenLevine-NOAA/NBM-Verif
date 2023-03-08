import sys
sys.path.append('/lfs/h1/mdl/nbm/noscrub/steven.levine/python_mods')

import argparse
import numpy as np
from scipy.interpolate import CubicSpline as cs, UnivariateSpline as us
import pandas as pd
from urllib.request import urlretrieve
from datetime import datetime, timedelta
import json
#import gdal,osr,ogr
#import pygrib
from netCDF4 import Dataset
import pytdlpack
import pyproj
from pyproj import Proj, transform
import os, re, traceback
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
#from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.axes as maxes
import matplotlib.patheffects as PathEffects
from matplotlib.path import Path
from matplotlib.textpath import TextToPath
import matplotlib.gridspec as gridspec
from matplotlib.font_manager import FontProperties
matplotlib.rcParams['font.sans-serif'] = 'Liberation Sans'
matplotlib.rcParams['font.family'] = "sans-serif"
from matplotlib.cm import get_cmap
import seaborn as sns

from cartopy import crs as ccrs, feature as cfeature
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature
import contextily as cx
import itertools

import warnings
warnings.filterwarnings("ignore")

def cwa_list(input_region):
	region_dict ={"WR":"BYZ,BOI,LKN,EKA,FGZ,GGW,TFX,VEF,LOX,MFR,MTR,MSO,PDT,PSR,PIH,PQR,REV,STO,SLC,SGX,HNX,SEW,OTX,TWC","CR":"ABR,BIS,CYS,LOT,DVN,BOU,DMX,DTX,DDC,DLH,FGF,GLD,GJT,GRR,GRB,GID,IND,JKL,EAX,ARX,ILX,LMK,MQT,MKX,MPX,LBF,APX,IWX,OAX,PAH,PUB,UNR,RIW,FSD,SGF,LSX,TOP,ICT","ER":"ALY,LWX,BGM,BOX,BUF,BTV,CAR,CTP,RLX,CHS,ILN,CLE,CAE,GSP,MHX,OKX,PHI,PBZ,GYX,RAH,RNK,AKQ,ILM","SR":"ABQ,AMA,FFC,EWX,BMX,BRO,CRP,EPZ,FWD,HGX,HUN,JAN,JAX,KEY,MRX,LCH,LZK,LUB,MLB,MEG,MFL,MOB,MAF,OHX,LIX,OUN,SJT,SHV,TAE,TBW,TSA"}
	if (input_region in ["WR", "CR", "SR", "ER"]):
		cwas_list = region_dict[input_region]
	else:
		cwas_list = input_region
	return cwas_list

def project_hrap(lon, lat, s4x, s4y):
	lon = float(lon)
	lat = float(lat)
	
	globe = ccrs.Globe(semimajor_axis=6371200)
	hrap_ccrs = ccrs.Stereographic(central_latitude=90.0,central_longitude=255.0,true_scale_latitude=60.0,globe=globe)
	latlon_ccrs = ccrs.PlateCarree()
	hrap_coords = hrap_ccrs.transform_point(lon,lat,src_crs=latlon_ccrs)
	hrap_idx = ll_to_index(s4x,s4y,hrap_coords[0],hrap_coords[1])
	#coordX = hrap_coords[0]
	#coordY = hrap_coords[1]

	return(hrap_idx)

def project3(lon, lat, prj):
	lon = float(lon)
	lat = float(lat)

	outproj = prj
	inproj = Proj(init='epsg:4326')
	nbm_coords = transform(inproj, outproj, lon, lat)
	coordX = nbm_coords[0]
	coordY = nbm_coords[1]
	#print(f'Lat: {lat}, Y: {coordY} | Lon: {lon}, X: {coordX}')
	return(coordX, coordY)


def ll_to_index(datalons, datalats, loclon, loclat):
	abslat = np.abs(datalats-loclat)
	abslon = np.abs(datalons-loclon)
	c = np.maximum(abslon, abslat)
	latlon_idx_flat = np.argmin(c)
	latlon_idx = np.unravel_index(latlon_idx_flat, datalons.shape)
	#print("ll2ij: lat, lon, idx, tuple: " +  str(loclat) + " " + str(loclon) + " " + str(latlon_idx_flat) + " " + str(latlon_idx))
	return(latlon_idx)

def K_to_F(kelvin):
	test=np.full_like(kelvin,-9999.0)
	if np.array_equiv(kelvin,test):
		print("WARNING: All Kelvin values are missing!")
		fahrenheit=np.full_like(kelvin,-9999.0)
	else:
		fahrenheit = 1.8*(kelvin-273)+32.
	return fahrenheit

def mm_to_in(millimeters):
	test=np.full_like(millimeters,-9999.0)
	if np.array_equiv(millimeters,test):
		print("WARNING: All Precip values in mm are missing!")
		inches=np.full_like(millimeters,-9999.0)
	else:
		inches = millimeters * 0.0393701
	return inches

def flip(items, ncol):
	return itertools.chain(*[items[i::ncol] for i in range(ncol)])

def find_roots(x,y):
	s = np.abs(np.diff(np.sign(y))).astype(bool)
	return x[:-1][s] + np.diff(x)[s]/(np.abs(y[1:][s]/y[:-1][s])+1)

def rounder(t):
	return (t.replace(second=0,microsecond=0,minute=0,hour=t.hour)+timedelta(hours=t.minute//30))

def plotrg(obs,name,longname,text_color,inax):
	mean=obs(name)[compare_var].mean()
	median=obs(name)[compare_var].median()
	inax.set_anchor('N')
	sns.histplot(data=obs[name],x=compare_var,ax=inax,kde=True,bins=range(0,110,10),color='steelblue',edgecolor='lightgrey')
	inax.set_xlabel(longname,color=text_color,fontsize=12)
	inax.axvline(mean,color='salmon',linestyle='--',label="Mean")
	inax.axvline(median,color='mediumaquamarine',linestyle='-',label="Median")
	inax.grid(False)
	for tick in inax.get_xticklabels():
		tick.set_color(text_color)
	for tick in inax.get_yticklabels():
		tick.set_color(text_color)
	inax.tick_params(axis='y',labelsize=8,color=text_color)
	inlegend=inax.legend()
	for text in inlegend.get_texts():
		text.set_color(text_color)
	inax.set(ylabel=None)

def main():

	#arg parser here?
	parser = argparse.ArgumentParser()
	parser.add_argument('-datafiles',type=str,dest="tdlloc",required=True,help="REQUIRED location of input tdlpack files")
	parser.add_argument('-obfiles',type=str,dest="obloc",help="REQUIRED location of input obs files!")
	parser.add_argument('-var',type=str,dest="element",required=True,choices=['mint','maxt','qpf'],help="REQUIRED variable we are interrogating (mint/maxt/qpf}")
	parser.add_argument('-region',type=str,dest="region",required=True,help="REQUIRED region or WFO to collect stats over")
	parser.add_argument('-runtime',type=str,dest="runtime",required=True,help="REQUIRED initial runtime YYYYMMDD")
	parser.add_argument('-validtime',type=str,dest="validtime",required=True,help="REQUIRED valid time YYYYMMDD")
	parser.add_argument('-stageiv',dest="use_stageiv",action='store_true',help="Use stage IV precip obs (default is no)")
	parser.add_argument('-cwa',type=bool,dest="cwa_outline",help="Include CWA in plot (default is no)")
	parser.add_argument('-style',type=str,dest="style",choices=['light', 'dark'],help="Plot style: light or dark (default dark)")
	parser.add_argument('-network',type=str,dest="network",choices=["ALL","NWS","RAWS","NWS+RAWS"],help="Network to use (ALL/NWS/RAWS/NWS+RAWS)")
	parser.add_argument('-compareto',type=str,dest="compare_to",choices=["obs","deterministic"],help="Compare NBM percentiles against obs or deterministic (default obs)")
	parser.add_argument('-validat',type=int,dest="qpf_valid",help="Valid time at which to pull qpf from (HH)")
	parser.set_defaults(cwa=False,stageiv=False,style='dark',network="NWS",compare_to="obs",qpf_valid="00")

	argz=parser.parse_args()
	tdlloc=argz.tdlloc
	element=argz.element
	region=argz.region
	nbm_init_date=argz.runtime
	valid_date=argz.validtime
	network=argz.network
	cwa_outline=argz.cwa_outline
	plot_style=argz.style
	use_stageiv=argz.use_stageiv
	compare_to=argz.compare_to
	export_csv=True
	qpf_valid_time=argz.qpf_valid
	#if compare_to == "obs":
	obdir=argz.obloc
	#elif compare_to == "deterministic":
	#obdir=argz.obloc

	#nbm_init = datetime.strptime(nbm_init_date,'%Y-%m-%d') + timedelta(hours=int(nbm_init_hour))
	#nbm_init=datetime.strptime(nbm_init_date,'%Y%m%d')

	if element == "maxt":
		nbm_core_valid_hour="06"
		nbm_qmd_valid_hour="06"
		nbm_init_hour="12"
		valid_date_start = datetime.strptime(valid_date,'%Y%m%d')
		valid_date_end = valid_date_start + timedelta(days=1)
		obs_start_hour = "1200"
		obs_end_hour = "0600"
		ob_stat = "maximum"
		valid_end_datetime = valid_date_end + timedelta(hours=(int(obs_end_hour)/100))
		nbm_core_valid_end_datetime = valid_date_end + timedelta(hours=int(nbm_core_valid_hour))
		print("Valid end datetime: ",valid_end_datetime.strftime("%m-%d-%Y %H:%M"))
		print("NBM Core valid end datetime: ",nbm_core_valid_end_datetime.strftime("%m-%d-%Y %H:%M"))
		nbm_qmd_valid_end_datetime = valid_date_end + timedelta(hours=int(nbm_qmd_valid_hour))
	
	elif element == "mint":
		nbm_core_valid_hour="18"
		nbm_qmd_valid_hour="18"
		nbm_init_hour="12"
		valid_date_start = datetime.strptime(valid_date,'%Y%m%d')
		valid_date_end = datetime.strptime(valid_date,'%Y%m%d')
		obs_start_hour = "0000"
		obs_end_hour = "1800"
		ob_stat = "minimum"
		valid_end_datetime = valid_date_end + timedelta(hours=(int(obs_end_hour)/100))
		print("Valid end datetime: ",valid_end_datetime.strftime("%m-%d-%Y %H:%M"))
		nbm_core_valid_end_datetime = valid_date_end + timedelta(hours=int(nbm_core_valid_hour))
		print("NBM Core valid end datetime: ",nbm_core_valid_end_datetime.strftime("%m-%d-%Y %H:%M"))
		nbm_qmd_valid_end_datetime = valid_date_end + timedelta(hours=int(nbm_qmd_valid_hour))
	
	elif element == "qpf":
		#element="qpf24"
		nbm_core_valid_hour = "12" #str(qpf_valid_time)
		nbm_valid_hour = "12" #str(qpf_valid_time)
		nbm_init_hour = nbm_valid_hour
		nbm_qmd_valid_hour=str(qpf_valid_time)
		valid_date_end = datetime.strptime(valid_date,'%Y%m%d')
		valid_date_start = valid_date_end - timedelta(hours=12)
		obs_start_hour = "1200"
		obs_end_hour = "1200"
		ob_stat = "total"
		valid_end_datetime = valid_date_end + timedelta(hours=12)#,minutes=59)
		nbm_core_valid_end_datetime = valid_end_datetime
		nbm_qmd_valid_end_datetime = valid_end_datetime 
	
	
	nbm_init = datetime.strptime(nbm_init_date,'%Y%m%d') + timedelta(hours=int(nbm_init_hour))
	current_datetime = datetime.now()
	
	nbm_core_fhdelta = rounder(nbm_core_valid_end_datetime) - nbm_init
	nbm_core_forecasthour = nbm_core_fhdelta.total_seconds() / 3600.
	print("NBM Core Forecast hour: ",str(nbm_core_forecasthour))
	nbm_qmd_fhdelta = rounder(nbm_qmd_valid_end_datetime) - nbm_init
	nbm_qmd_forecasthour = nbm_qmd_fhdelta.total_seconds() / 3600.
	if element == "qpf":
		nbm_qmd_forecasthour_start = nbm_qmd_forecasthour - 24
	else:
		nbm_qmd_forecasthour_start = nbm_qmd_forecasthour - 18

	# Setup a dictionary for translating a form selection into a something we can pass to mesowest API
	#network_dict = {"NWS+RAWS":"&network=1,2", "NWS":"&network=1", "RAWS": "&network=2", "ALL":"", "CUSTOM": "&network="+network_input, "LIST": "&stid="+network_input}
	network_string=network
	
	if element == "qpf":
		cmap = get_cmap('BrBG_r')
		cmap.set_under(color='black')
		cmap.set_over(color='yellow')
	else:
		cmap = get_cmap('bwr')
		cmap.set_under(color='black')
		cmap.set_over(color='yellow')
	if use_stageiv:
		points_str = 'Stage IV @ ' + network_string
	else:
		points_str = network_string
	
	if plot_style=="light":
		background_color = 'whitesmoke'
		text_color = '#121212'
		map_land_color = 'goldenrod'
		map_water_color = 'aqua'
		map_border_color = 'black'
	elif plot_style=="dark":
		background_color = '#272727'
		text_color = 'white'
		map_land_color = '#414143'
		map_water_color = '#272727'
		map_border_color = '#3B3B3D'

	#if region == "CONUS":
	#	region_list = ["WR", "CR", "SR", "ER"]
	#else:
	region_list = [region]
	obs={}
	for region in region_list:
		json_name=obdir + "/synobs." + valid_date + "/Obs_" + element + "_" + valid_date_start.strftime("%Y%m%d") + obs_start_hour + "_" + valid_date_end.strftime("%Y%m%d") + obs_end_hour + "_" + region + ".json"
		#print("Looking for JSON file: " + json_name)
		if use_stageiv is True:
			sivname=obdir + "/synobs." + valid_date + "/StageIV_qpf_" + valid_date_start.strftime("%Y%m%d") + obs_start_hour + "_" + valid_date_end.strftime("%Y%m%d") + obs_end_hour + "_" + region + ".nc"
			print("Looking for Stage IV file: " + sivname)
			if os.path.exists(sivname):
				ivdata=Dataset(sivname,'r',format='NETCDF4')
				stageIV=ivdata.variables['observation']
				s4xs = ivdata.variables['x']
				s4ys = ivdata.variables['y']
				s4xs,s4ys = np.meshgrid(s4xs,s4ys)
			else:
				print("WARNING: Can't find Stage IV file!  Turning Stage IV off...")
				use_stageiv = False
		print("Looking for JSON file: " + json_name)
		if os.path.exists(json_name):
			with open(json_name) as json_file:
				obs_json = json.load(json_file)
				obs_lats = []
				obs_lons = []
				obs_value = []
				obs_elev = []
				obs_stid = []
				obs_name = []
				for stn in obs_json["STATION"]:
					if "OBSERVATIONS" in stn or "STATISTICS" in stn:
						if stn["STID"] is None:
							stid = "N0N3"
						else:
							stid = stn["STID"]
							#print("For Station ID: " + stid)
							#for key, value in stn.items():
							#	print(key, value)
						name = stn["NAME"]
						if stn["ELEVATION"] and stn["ELEVATION"] is not None:
							elev = stn["ELEVATION"]
						else:
							elev = -999
						lat = stn["LATITUDE"]
						lon = stn["LONGITUDE"]
						if element == "mint" or element=="maxt":
							if 'air_temp_set_1' in stn['STATISTICS'] and stn['STATISTICS']['air_temp_set_1']:
								if ob_stat in stn['STATISTICS']['air_temp_set_1'] and float(stn["LATITUDE"]) != 0. and float(stn["LONGITUDE"]) != 0.:
									stat = stn['STATISTICS']['air_temp_set_1'][ob_stat]
									obs_stid.append(str(stid))
									obs_name.append(str(name))
									obs_elev.append(int(elev))
									obs_lats.append(float(lat))
									obs_lons.append(float(lon))
									obs_value.append(float(stat))
						elif (element == "qpf"):
							if stn["STATUS"] == "ACTIVE" and float(stn["LATITUDE"]) != 0. and float(stn["LONGITUDE"]) != 0.:
								obs_stid.append(str(stid))
								obs_name.append(str(name))
								obs_elev.append(int(elev))
								obs_lats.append(float(lat))
								obs_lons.append(float(lon))
								if use_stageiv:
									coords = project_hrap(lon,lat,s4xs,s4ys)
									siv_value=float(stageIV[coords])
									if (siv_value >= 0.01):
										obs_value.append(siv_value)
									else:
										obs_value.append(np.NaN)
								else:
									if "precipitation" in stn["OBSERVATIONS"]:
										if "total" in stn["OBSERVATIONS"]["precipitation"][0] and stn["OBSERVATIONS"]["precipitation"][0] is not None:
											ptotal = stn["OBSERVATIONS"]["precipitation"][0]["total"]
											if (float(ptotal) >= 0.01):
												obs_value.append(float(ptotal))
											else:
												obs_value.append(np.nan)
										else:
											obs_value.append(np.nan)
									else:
										obs_value.append(np.nan)
	
				csv_name = "obs_"+element+"_"+region+".csv"
				obs[region] = pd.DataFrame()
				obs[region]["stid"] = obs_stid
				obs[region]["name"] = obs_name
				obs[region]["elevation"] = obs_elev
				obs[region]["lat"] = obs_lats
				obs[region]["lon"] = obs_lons
				obs[region]["ob_"+element] = obs_value
				obs[region].to_csv(csv_name)
		else:
			print("FATAL ERROR: Can't find obs file: " + json_name)
			quit()

###################################################################
###############################Process NBM Data####################
###################################################################

	if compare_to == "deterministic":
		nbm_init_filen = nbm_init.strftime('%Y%m%d') + "_" + nbm_init.strftime('%H')
		temp_vars = ["maxt","mint"]
		if (element == "qpf"):
			hh=str().zfill(2)
			detr_file="blend.t"+hh+"z.blend_expertfcst_precip.co.grd_ra"

		elif any(te in element for te in temp_vars):
			hh=str(nbm_init_hour).zfill(2)
			fh=str(nbm_core_forecasthour).zfill(3)
			detr_file="blend.t"+hh+"z.blend_maewfcst_tmp.co.grd_ra"

		dfilename=tdlloc + "/" + nbm_init_date + "/" + detr_file
		print("dfilename=",dfilename)
		nbmd=pytdlpack.open(dfilename,mode='r',format='r') #,format='random-access')
		if element == "maxt":
			print("NBM core forecast hour=" + str(nbm_core_forecasthour))
			detrec=nbmd.read(id=[222358039,0,int(nbm_core_forecasthour),0])
			detrec.unpack(data=True,missing_value=-9999.0)
			deterministic_array = K_to_F(detrec.data)
			nbmlats, nbmlons = detrec.latlons()
		elif element == "mint":
			detrec=nbmd.read(id=[222368039,0,int(nbm_core_forecasthour),0])
			detrec.unpack(data=True,missing_value=-9999.0)
			deterministic_array = K_to_F(detrec.data)
			nbmlats, nbmlons = detrec.latlons()
		elif element == "qpf":
			qpfrec=nbmd.read(id=[22312039,0,int(nbm_core_forecasthour),0])
			qpfrec.unpack(data=True,missing_value=-9999.0)
			deterministic_array = qpfrec.data
			nbmlats, nbmlons = qpfrec.latlons()
		#reverse longitudes from tdlpack file
		nbmlons=nbmlons*-1.
		nbmd.close()

		for region in region_list:
			print("     >> Extracting NBM deterministic and coordinate values")
			point_lats = obs[region]["lat"].values
			point_lons = obs[region]["lon"].values
			detr_values = []
			nbm_fidx = []
			for i in range(0, len(point_lats)):
				coords = ll_to_index(nbmlons, nbmlats, point_lons[i], point_lats[i])
				detr_value = deterministic_array[coords]
				nbm_fidx.append(coords)
				detr_values.append(detr_value)
			obs[region]["NBM_fidx"] = nbm_fidx
			obs[region]["NBM_D"] = detr_values
	else:
		print("WARNING: Comparing to obs, so not loading determinstic values")

	#setup for loading percentile values into dataframe
	perc_list = [1,5,10,20,30,40,50,60,70,80,90,95,99]
	#perc_list = range(1,100,1)
	perc_dict = {"maxt":"maxt18p", "mint":"mint18p", "qpf":"qpf24p"}
	hh=str(nbm_init_hour).zfill(2)
	fh=str(nbm_qmd_forecasthour).zfill(3)
	if element == "maxt" or element == "mint":
		perc_file=tdlloc + "/" + nbm_init_date + "/" + "blend.t"+hh+"z.temp_forecast.co.2p5.tdlp_ra"
	elif element == "qpf":
		perc_file=tdlloc + "/" + nbm_init_date + "/" + "blend.t"+hh+"z.precip_forecast.co.2p5.tdlp_ra"
	else:
		print("FATAL ERROR: Can't find percentile file for variable: " + element)
		exit()

	#load percentile values into dataframe
	print("perc_file=" + perc_file)
	nbmperc=pytdlpack.open(perc_file,mode='r',format='r')
	print('   > Extracting NBM Probabilistic') 
	for perc in perc_list:
		perci=str(perc).zfill(2)
		print("     >> Extracting NBM P" + perci)
		perc_name = "NBM_P"+str(perci)
		perc_int=int(perci)*10000
		perc_str=str(perc_int).zfill(9)
		print("    >>> Looking at perc_val, qmd_fcst_hour:" + perc_str + ',' + str(nbm_qmd_forecasthour))
		if element == "maxt":
			percrec=nbmperc.read(id=[242450066,int(perc_str),int(nbm_qmd_forecasthour),0])
			percrec.unpack(data=True,missing_value=-9999.0)
			percdata=K_to_F(percrec.data)
		elif element == "mint":
			percrec=nbmperc.read(id=[242480066,int(perc_str),int(nbm_qmd_forecasthour),0])
			percrec.unpack(data=True,missing_value=-9999.0)
			percdata=K_to_F(percrec.data)
		elif element == "qpf":
			percrec=nbmperc.read(id=[243520066,int(perc_str),int(nbm_qmd_forecasthour),0])
			percrec.unpack(data=True) #,missing_value=-9999.0)
			#percdata = mm_to_in(percrec.data)
			percdata = percrec.data
		#load nbmlats,lons and index values if this has not been done already
		try:
			nbmlats,nbmlons
		except: # NameError:
			print ("Probablistic file only: assigning lats/lons...")
			nbmlats,nbmlons=percrec.latlons()
			nbmlons=nbmlons*-1.
			point_lats = obs[region]["lat"].values
			point_lons = obs[region]["lon"].values
			nbm_fidx = []
			for i in range(0,len(point_lats)):
				coords = ll_to_index(nbmlons,nbmlats,point_lons[i],point_lats[i])
				nbm_fidx.append(coords)
			obs[region]["NBM_fidx"] = nbm_fidx
		else:
			print("Lats and lons defined already")

		for region in region_list:
			nbm_coords = obs[region]["NBM_fidx"].values
			nbm_stations= obs[region]["stid"].values
			perc_values = []
			for i in range(0, len(nbm_coords)):
				perc_value = percdata[nbm_coords[i]]
				#print("Station, coords, value:" + str(nbm_stations[i]) + " " + str(nbm_coords[i]) + " " + str(perc_value))
				#perc_value = percdata[nbm_coords[i]]
				perc_values.append(perc_value)
			obs[region][perc_name] = perc_values
			print("Percentiles being loaded into dataframe: " + perc_name)
	nbmperc.close()

########################################################################################################################
# This section creates a distribution curve at each site, and interpolates ob and deterministic to percentile space    #
########################################################################################################################
	print('Creating point distribution curves and interpolating...')
	for region in region_list:
		perc_start = obs[region].columns.get_loc("NBM_P01")
		perc_end = obs[region].columns.get_loc("NBM_P99")
		all_percs = obs[region].iloc[:, perc_start:perc_end+1].values
		var_string = "ob_"+element
		all_obs = obs[region][[var_string]].values
		#try:
			#obs[region][['NBM_D']] #.values
		if 'NBM_D' in obs[region].index:
			all_nbmd = obs[region][['NBM_D']].values
		else:
			all_nbmd = np.empty(len(all_obs))
			all_nbmd.fill(np.nan) #= np.nan
		obs_percs = []
		nbmd_percs = []
		for i in range(0,len(all_obs)):
			udf = us(perc_list, all_percs[i,:], bbox=[0,100], ext=0)
			if all_obs[i] <= udf(0):
				ob_perc = -10
			elif all_obs[i] >= udf(100):
				ob_perc = 110
			else:
				ob_perc = find_roots(np.arange(0,101,1), udf(np.arange(0,101,1)) - all_obs[i])
				ob_perc = ob_perc[0].round(1)

			if np.isnan(all_nbmd[i]):
				nbm_perc = np.nan
			elif all_nbmd[i] <= udf(0):
				nbm_perc = -10
			elif all_nbmd[i] >= udf(100):
				nbm_perc = 110
			else:
				nbm_perc = find_roots(np.arange(0,101,1), udf(np.arange(0,101,1)) - all_nbmd[i])
				nbm_perc = nbm_perc[0].round(1)
	
			if np.isnan(ob_perc):
				obs_percs.append(ob_perc)
			else:
				obs_percs.append(int(ob_perc))
			if np.isnan(nbm_perc):
				nbmd_percs.append(nbm_perc)
			else:
				nbmd_percs.append(int(nbm_perc))    

	obs[region]["ob_perc"] = obs_percs
	obs[region]["NBMd_perc"] = nbmd_percs
	if export_csv:
		csv_name = "obs_"+element+"_"+nbm_init_date+ "_"+valid_end_datetime.strftime('%Y%m%d')+"_"+region+".csv"
		obs[region].to_csv(csv_name)
		print("  > Created and saved: " + csv_name)

########################################################################################################################
# Finally, this section makes our plot.                                                                                #
########################################################################################################################
	print("Making plot (almost done!)...")
	if compare_to =="obs":
		compare_var = "ob_perc"
		compare_element = "Obs"
	elif compare_to == "deterministic":
		compare_var = "NBMd_perc"
		if element =="qpf":
	  		compare_element = "pMean"
		else:
			compare_element = "Detr"
	
	title_dict = {"maxt":["Max T","PMaxT"],"mint":["Min T","PMinT"], "qpf":["QPF","PQPF"]}
	matplotlib.rc('axes',facecolor=background_color, edgecolor=text_color)
	if (element == "qpf"):
		#valid_datetime = datetime.strptime(valid_date, '%Y%m%d')
		fig_valid_date = valid_end_datetime.strftime('%Y%m%d_%HZ')
		valid_title = valid_end_datetime.strftime('%HZ %a %m-%d-%Y')
	else:
		valid_datetime = datetime.strptime(valid_date,'%Y%m%d')
		fig_valid_date = valid_datetime.strftime('%Y%m%d')
		valid_title = valid_datetime.strftime('%a %m-%d-%Y')
	nbm_init_title = nbm_init.strftime('%HZ %m-%d-%Y')

	if region == "CONUS":
		dataframeid = "CONUS"
		#set up multipanel plot
		west =-125.650
		south = 23.377
		east = -66.008
		north = 50.924
		width_ratios = [7,3,3,3]
		lloc = "lower right"
		fig = plt.figure(constrained_layout=True, figsize=(16,9), facecolor=background_color, frameon=True, dpi=150)
		grid = fig.add_gridspec(4,4, width_ratios=width_ratios, hspace=0.2, wspace=0.2, left=0.1, right=0.9)
		#fig.text(0.30, 0.885,f'{region} {title_dict[element][0]} {compare_element} in NBM {title_dict[element][1]} Percentile Space',horizontalalignment='center',weight='bold',fontsize=25,color=text_color)
		#tmptxt=region + " " + title_dict[element][0]] + " " + compare_element + " in NBM " + title_dict[element][1] + " Percentile Space"
		fig.text(0.30, 0.885, region + " " + title_dict[element][0] + " " + compare_element + " in NBM v4.1 " + title_dict[element][1] + " Percentile Space",horizontalalignment='center',weight='bold',fontsize=25,color=text_color)
		#fig.text(0.30,0.85,tmptxt,horizontalalignment='center',weight='bold',fontsize=25,color=text_color)
		fig.text(0.30, 0.855, "Valid: " + valid_title + "  | NBM Init: " + nbm_init_title + "  |  Points: " + points_str,horizontalalignment='center',fontsize=16,color=text_color)
		
		ax1 = fig.add_subplot(grid[:,:-2], projection=ccrs.Mercator(globe=None))
		ax2 = fig.add_subplot(grid[0,2])
		ax3 = fig.add_subplot(grid[0,3])
		ax4 = fig.add_subplot(grid[1,2])
		ax5 = fig.add_subplot(grid[1,3])
		ax6 = fig.add_subplot(grid[2:,2:])
		
		conus_df = pd.concat([obs["WR"], obs["CR"], obs["ER"],obs["SR"]])
		lats = conus_df["lat"].values
		lons = conus_df["lon"].values
		point_data = conus_df[compare_var].values
		mean = conus_df[compare_var].mean()
		median = conus_df[compare_var].median()
		mode = conus_df[compare_var].mode().values[0]
		
		proj = ccrs.PlateCarree()

		ax1.set_anchor('S')
		ax1.set_extent([west, east, south, north], crs=proj)
		ax1.add_feature(cfeature.LAND, edgecolor='none', facecolor='#414143') #, zorder=-1)
		ax1.add_feature(cfeature.OCEAN, edgecolor='none', facecolor=map_water_color) #, zorder=-2)
		ax1.add_feature(cfeature.STATES, edgecolor=map_border_color, facecolor='none', linewidth=1)
		ax1.add_feature(cfeature.LAKES, edgecolor='none', facecolor=map_water_color)#, zorder=0)
		#ax1.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '50m', edgecolor='none', facecolor=map_land_color)) #, zorder=-1))
		#ax1.add_feature(cfeature.NaturalEarthFeature('physical', 'lakes', '10m', edgecolor='none', facecolor=map_water_color)) #, zorder=0))
		ax1.add_feature(cfeature.BORDERS, edgecolor=map_border_color, facecolor='none', linewidth=2)#, zorder=1)
		#ax1.add_feature(cfeature.NaturalEarthFeature('cultural', 'countries', '50m', edgecolor=map_border_color, facecolor='none', linewidth=2)) #, zorder=2))
		#ax1.add_feature(cfeature.NaturalEarthFeature('cultural', 'admin_1_states_provinces_lines', '50m', edgecolor=map_border_color, facecolor='none', linewidth=2))#, zorder=2))
		#cx.add_basemap(ax1, source='https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', attribution=False)
		scatter = ax1.scatter(lons, lats, c= point_data, cmap=cmap, s=45, transform=proj)
		#handles, labels = scatter.legend_elements(num=10)
		#legend1 = ax1.legend(flip(handles, 6), flip(labels, 6), ncol=6,loc=lloc, title=f'{compare_element} in NBM Percentile Space', fancybox=True)
		#legend1 = ax1.legend(*scatter.legend_elements(num=10), loc=lloc, title=f'{compare_element} \n Rank', fancybox=True)
		legend1 = ax1.legend(*scatter.legend_elements(num=10), loc=lloc, title=compare_element + " \n Rank",fancybox=True)
		plt.setp(legend1.get_title(), multialignment='center', color=text_color)
		for text in legend1.get_texts():
			text.set_color(text_color)
		ax1.add_artist(legend1)
		#ax1.add_feature(cfeature.NaturalEarthFeature('cultural','admin_1_states_provinces_lines','110m',edgecolor='black',facecolor='none'))
		#if cwa_outline:
		#	try:
		#		if os.path.exists("shp/w_22mr22.shp"):
		#			pass
		#		else:
		#			cwa_url = "https://www.weather.gov/source/gis/Shapefiles/WSOM/w_22mr22.zip"
		#			os.mkdir("shp")
		#			urlretrieve(cwa_url, "shp/nws_cwa_outlines.zip")
		#			os.unzip("shp/nws_cwa_outlines.zip -d shp")
		#		cwa_feature = ShapelyFeature(Reader("shp/w_22mr22.shp").geometries(),ccrs.PlateCarree(), edgecolor='grey', facecolor='none', linewidth=0.5, linestyle=':', zorder=3)
		#		ax1.add_feature(cwa_feature)
		#	except:
		#		print("   > Aw shucks, no CWA boundaries for you. Sorry bout that.")
#
		plotrg("WR","Western Region",obs,text_color,ax2)
		plotrg("CR","Central Region",obs,text_color,ax3)
		plotrg("ER","Eastern Region",obs,text_color,ax4)
		plotrg("SR","Southern Region",obs,text_color,ax5)
		plotrg("NC","North Central",obs,text_color,ax6)

	else:
	#set up 2 panel plot
		if (region == "WR"):
			west = -126.917
			south = 30.586
			east = -102.740
			north = 49.755
			width, height = (16,9)
			width_ratios = [9,8]
			lloc = "lower right"
		elif (region == "CR"):
			print("Making plot for central region!")
			west = -111.534
			south = 33.295
			east = -81.723
			north = 49.755
			width, height = (16,7)
			width_ratios = [9,7]
			lloc = "lower center"
		elif (region == "ER"):
			west = -86.129
			south = 31.223
			east = -66.465
			north = 47.676
			width, height = (16,7.25)
			width_ratios = [6.9,9.5]
			lloc = "lower right"
		elif (region == "SR"):
			west = -109.758
			south = 23.313
			east = -79.247
			north = 36.899
			width, height = (16,5.6)
			width_ratios = [10,6]
			lloc = "lower center"
		#if (region == "CWA"):
		else: #Individual CWA
			print("Making plot for custom region!")
			west = np.min(obs[region]["lon"]) - 0.5
			south = np.min(obs[region]["lat"]) - 0.5
			east = np.max(obs[region]["lon"]) + 1.0
			north = np.max(obs[region]["lat"]) + 0.5
			width, height = (16,9)
			ratioxy = 16./9.
			width_ratios = [ratioxy, 1]
			lloc = "center right"
		
		#width, height = (14,8.5)
		#try:
		#	width
		#except:
		#	width,height = (14,8.5)
		fig = plt.figure(constrained_layout=True, figsize=(width,height), facecolor=background_color, frameon=True, dpi=150)
		if (region == "CWA"):
			dataframeid = cwa_id
		else:
			dataframeid = region
		#ratioxy = 16./9.
		#width_ratios = [ratioxy, 1]
		grid = fig.add_gridspec(1,2, hspace=0.2, width_ratios=width_ratios, height_ratios = [1], wspace=0.2)
		ax1 = fig.add_subplot(grid[0,0], projection=ccrs.Mercator())
		#ax1 = fig.add_subplot(grid[0,0], projection=ccrs.LambertConformal(central_latitude=25, central_longitude=265, standard_parallels=(25,25)))
		ax2 = fig.add_subplot(grid[0,1], ) 
		#fig.text(0.5, 1.05,f'{dataframeid} {title_dict[element][0]} {compare_element} in NBM {title_dict[element][1]} Percentile Space',horizontalalignment='center', verticalalignment='bottom', weight='bold',fontsize=20,color=text_color)
		fig.text(0.5, 1.05,dataframeid + " " + title_dict[element][0] + " " + compare_element + " in NBM v4.1 " + title_dict[element][1] + " Percentile Space",horizontalalignment='center', verticalalignment='bottom', weight='bold',fontsize=20,color=text_color)
		#fig.text(0.5, 1.05,f'Valid: {valid_title} | NBM Init: {nbm_init_title} | Points: {points_str}',horizontalalignment='center',verticalalignment='top', fontsize=16,color=text_color)
		fig.text(0.5,1.05,"Valid: " + valid_title + " | NBM Init: " + nbm_init_title + " | Points: " + points_str,horizontalalignment='center',verticalalignment='top', fontsize=16,color=text_color)

		lats = obs[dataframeid]["lat"].values
		lons = obs[dataframeid]["lon"].values
		point_data = obs[dataframeid][compare_var].values
		mean = obs[dataframeid][compare_var].mean()
		median = obs[dataframeid][compare_var].median()
		#mode = obs[dataframeid][compare_var].mode().values[0]
		proj = ccrs.PlateCarree()

		ax1.set_anchor('N')
		ax1.set_facecolor(background_color)
		ax1.set_extent([west, east, south, north], crs=proj)
		ax1.add_feature(cfeature.LAND, edgecolor='none', facecolor=map_land_color)#, zorder=-1)
		ax1.add_feature(cfeature.OCEAN, edgecolor='none', facecolor=map_water_color)#, zorder=-2)
		#ax1.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '50m', edgecolor='none', facecolor=map_land_color, zorder=-1))
		ax1.add_feature(cfeature.LAKES, edgecolor='none', facecolor=map_water_color)#, zorder=0)
		#ax1.add_feature(cfeature.NaturalEarthFeature('physical', 'lakes', '10m', edgecolor='none', facecolor=map_water_color, zorder=0))
		ax1.add_feature(cfeature.BORDERS, edgecolor=map_border_color, facecolor='none', linewidth=2) #, zorder=2)
		ax1.add_feature(cfeature.STATES, edgecolor=map_border_color, facecolor='none', linewidth=1)
		#ax1.add_feature(cfeature.NaturalEarthFeature('cultural', 'countries', '50m', edgecolor=map_border_color, facecolor='none', linewidth=2)) #, zorder=2))
		#ax1.add_feature(cfeature.NaturalEarthFeature('cultural', 'admin_1_states_provinces_lines', '50m', edgecolor=map_border_color, facecolor='none', linewidth=2))#, zorder=2))
		#cx.add_basemap(ax1, source='https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', attribution=False)
		scatter = ax1.scatter(lons, lats, c= point_data, cmap=cmap, s=45, transform=proj, zorder=2, vmin=0, vmax=100)

		if region in ("CR","SR"):
			handles, labels = scatter.legend_elements(num=10)
			legend1 = ax1.legend(flip(handles, 6), flip(labels, 6), ncol=6,loc=lloc, title=compare_element + " in NBM Percentile Space", fancybox=True)
		else:
			legend1 = ax1.legend(*scatter.legend_elements(num=10),loc=lloc, title=compare_element + " \n Rank", fancybox=True)
		plt.setp(legend1.get_title(), multialignment='center', color=text_color)
		for text in legend1.get_texts():
			text.set_color(text_color)
		ax1.add_artist(legend1)
		#ax1.set(aspect='equal', adjustable='box')

		#if cwa_outline:
		#	try:
		#		if os.path.exists("shp/w_22mr22.shp"):
		#			pass
		#		else:
		#			cwa_url = "https://www.weather.gov/source/gis/Shapefiles/WSOM/w_22mr22.zip"
		#			os.mkdir("shp")
		#			urlretrieve(cwa_url, "shp/nws_cwa_outlines.zip")
		#			#unzip shp/nws_cwa_outlines.zip -d shp
		#		cwa_feature = ShapelyFeature(Reader("shp/w_22mr22.shp").geometries(),ccrs.PlateCarree(), edgecolor='grey', facecolor='none', linewidth=0.5, linestyle=':', zorder=3)
		#		ax1.add_feature(cwa_feature)
		#	except:
		#		print("Aw shucks, no CWA boundaries for you. Sorry bout that.")

		#if region == "SR":
		#ax2.set(aspect=1)
		ax2.set_anchor('C')
		sns.histplot(data=obs[dataframeid], x=compare_var, ax=ax2, kde=True, bins=range(-10,115,10),color='steelblue',edgecolor='lightgrey')
		ax2.set_xlabel(compare_element + " in NBM " + title_dict[element][1] + " Percentile Bins", color=text_color, fontsize=12)
		ax2.axvline(mean, color='salmon', linestyle='--', label="Mean")
		ax2.axvline(median, color='mediumaquamarine', linestyle='-', label="Median")

		ax2.grid(False)
		for tick in ax2.get_xticklabels():
			tick.set_color(text_color)
		for tick in ax2.get_yticklabels():
			tick.set_color(text_color)
		ax2.tick_params(axis='y',labelsize=8, color=text_color)
		legend2 = ax2.legend()
		for text in legend2.get_texts():
			text.set_color(text_color)
		ax2.set(ylabel=None)

	figname=dataframeid+"_"+compare_element+"_"+element+"_"+nbm_init_date+"_"+fig_valid_date+".png"
	#plt.savefig(figname,facecolor=fig.get_facecolor(),bbox_inches='tight',pad_inches=0.2,dpi='figure')
	plt.savefig(figname,bbox_inches='tight',pad_inches=0.2,dpi='figure')
	print("   >Done! Saved plot as " + figname)

if __name__ == "__main__":
	main()
	exit()
