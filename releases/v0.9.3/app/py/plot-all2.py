#!/usr/bin/env python
"""
 * TRANSIENT SCREENING TOOL
 * 
 * This module is to plot the graphs for unstable cases.
 *
 * Date:     September, 2021
 * Modified: 2021.09.23
 *
 * ===================================================================
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2019 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "January, 2019"
__modified__  = "June, 2021"
__version__   = ""
__copyright__ = "VDI Technologies, LLC"

import os, sys
from sys import argv, exit, stdin, stdout, stderr
from time import sleep
import csv

import numpy as np
import matplotlib.pyplot as plt

sys.path.append( './py' )

import functions
from functions import calculatePeaks8, t_clear
from datetime import datetime, timedelta
import re              # regex

"""
Build a dict on which each element correspond to a vector of the values
in each column shown in the CSV. The keys of the dict are the column headers
of the CSV

"""
def read_data_all( datafile = "" ):

  data = {}

  if not datafile:
    stderr.write( "read_data_all: datafile is empty" )
    return {}
  
	# creating keys from column headers
  f = open( datafile, "r" )
  headers = []
  if f:
    # trying to locate the header row
    i0 = 0
    line = f.readline().strip()
    while line and not "time(s)" in line.lower():
      i0 += 1
      line = f.readline().strip()
    
    # possibly with duplicates
    headers2 = line.split( ',' )
    headers2 = [h.strip() for h in headers2]
    
    """
    for i in range(0, len(headers2)):
      for j in range( i+1, len(headers2) ):
        if headers2[i] == headers2[j]:
          print( "Warning: columns {:d} and {:d} are equal".format(i, j) )
    """
      
    # deleting duplicates
    for key in headers2:
      if not key in headers:
        headers.append( key )
            
    if not headers: return {}
    if headers[-1] == headers[0]:
      headers = headers[:-1]
			
    for key in headers:
      # initializing empty data
      data[key] = []
    f.close( )
	  
  else:
    stderr.write( "read_data_all: unable to read '{:s}'".format(datafile) )
    return {}
    
  with open( datafile, "r" ) as f:
    
    csv_reader = csv.reader( f, delimiter=',' )
    csv_reader = list( csv_reader )
    
    for i in range(i0+1, len(csv_reader) ):      
      for k in range(0, len(headers)):
        try:
          #data[ headers[k] ].insert( i, float(csv_reader[i][k]) )
          data[ headers[k] ].append( float(csv_reader[i][k]) )
        except:
          # badformed data (e.g., not numeric)
          #print( "bad data: [{:d}][{:d}] {}".format(i,k,csv_reader[i][k]))
          #data[ headers[k] ].insert( i, 0)
          data[ headers[k] ].append(0)
      
  f.close()
  
  return data


"""
@datafile   CSV file, with values for all angles and voltages
@plot_type  if "ANGL" or "ANGLE", plots all angles
            if "VOLT", plots all voltages
"""
def plot_all( datafile, plot_type, output_dir ):
  
  #datafile = 'Files/2021S_csv/P1-1-001-001_2021S_out.csv'
  #bus = 'VOLT 512651 [CLARMR 5 161.00]'
  #bus = 'ANGL512600[KERR_U2 1 13.200]2'

  #datafile = 'Files/2021S_csv/P1-2-016-019_2021S_out.csv'	
  #bus = 'ANGL512601[KERR_U3 1 13.200]3'

  t = y = []
  Data = read_data_all( datafile )
  if not Data: return
    
  headers = list(Data.keys() )
    
  plot_type = plot_type.upper()
  if plot_type == 'ANGL': plot_type = 'ANGLE'
  
  t = Data['Time(s)']
  cnt = 0
  for k in Data.keys():
    if plot_type == 'ANGLE':
      # regular pattern to match a bus of ANGLE
      if re.search( '\\s*ANGL[0-9]*\\[.*\\][0-9]*', k ) is not None:
        y = Data[k]
        plt.plot(t, y )
        if cnt < 2:
          cnt += 1
        else:
          pass
          #break
    
    if plot_type == 'VOLT':
      # regular pattern to match a bus of VOLTAGE
      if re.search( '\\s*VOLT\\s*[0-9]*\\s\\[.*\\][0-9]*', k ) is not None:
        y = Data[k]
        plt.plot(t, y )
        if cnt < 2:
          cnt += 1
        else:
          pass
          #break

  # fault clearing time
  tc = t_clear( datafile )

  if plot_type == 'VOLT':
    plt.ylim( [0.0, 1.2] )

  # Not plotting t clear
  #ylims = plt.ylim()
  #plt.plot( [tc, tc], [ylims[0], ylims[1]], 'r--' )
  
  plt.xlabel( 't' )
  if plot_type == "ANGLE":
    plt.ylabel( 'ANGLE' )
  elif plot_type == "VOLT":
    plt.ylabel( 'VOLT (P.U.)' )
  else:
    plt.ylabel( '' )
  
  xticks = np.arange( 0, t[-1]-t[0], 1 )
  plt.xticks( xticks )
  
  # Making UNIX style filenames
  if "\\\\" in datafile:
    datafile = datafile.replace( "\\\\", "/" )
  
  if "/" in datafile:
    datafile = datafile[ datafile.rfind("/") + 1: ]
  if "_out.csv" in datafile:
    event = datafile[ :datafile.find( "_out.csv" ) ]
  elif "." in datafile:
    event = datafile[ :datafile.rfind( "." ) ]
  else:
    print( "Not a proper datafile: " + datafile )
    return
  
  if output_dir[-1] != "/": output_dir += "/"
    
  if plot_type == 'ANGLE':
    figname = output_dir + event + '[ANGLE]' + '.png'
  elif plot_type == 'VOLT':
    figname = output_dir + event + '[VOLT]' + '.png'
  else:
    figname = output_dir + event + '.png'
    
  print( "  * Generating '{:s}'".format( figname ) )
  plt.savefig( figname, dpi = 300 )
  plt.close( )
  
def usage( ):

  stderr.write( "USAGE: {:s} files_list output_dir\n" \
  + "\nIf files_list is '-', reads from stdin.\n".format( argv[0] ) )

"""
SYNTAX:  <main> files_list output_dir

Plots ANGLES and VOLTAGES for all the CSV files listed in the
argument files_list. 

If files_list is '-', reads from stdin.

The figures will be exported to the directory output_dir
"""
def main( ):

  if len( argv ) < 3:
    usage( )
    return
    
  files_list = argv[1]
  N_lines = 0
  if files_list == '-':
    f = sys.stdin
  else:
    f = open( files_list, 'r' )
    lines = f.readlines()
    for l in lines:
      if l.strip() != '': N_lines += 1
    f.seek(0, 0)      # cursor at the beginning

  output_dir = argv[2]  

  cnt = 0
  t1 = datetime.now()
    
  line = f.readline()
  while line:
    fields = line.strip().split( '\t', 1 )
    
    if len( fields ) > 0:
   
      datafile = fields[0]
      
      # Making UNIX style filenames
      if "\\\\" in datafile:
        datafile = datafile.replace( "\\\\", "/" )
      
      print( "\n==========\nProcessing {:s}".format( datafile ) )
      
      cnt += 1
      print( "[{} / {}] Processing file {:s}".format(cnt, 
        N_lines if N_lines > 0 else '?', datafile) )
            
      if not os.path.exists(output_dir + '/angle'):
        os.makedirs(output_dir + '/angle', exist_ok = True)
      if not os.path.exists(output_dir + '/volt'):
        os.makedirs(output_dir + '/volt', exist_ok = True)
                
      plot_all( datafile, "angle", output_dir + '/angle' )
      plot_all( datafile, "volt", output_dir + '/volt' )

      line = f.readline()
  
  if files_list != '-': 
    f.close()
  
  t2 = datetime.now()
  d = t2 - t1
  print( f"\nGraphics generation complete in {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}" )
  
if __name__ == '__main__':

  main()  

  
