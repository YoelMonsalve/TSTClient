#!/usr/bin/env python
"""
 * TRANSIENT SCREENING TOOL
 * 
 * MAIN PROGRAM
 *  This module is ...
 * ===================================================================
 *
 * This product is protected under U.S. Copyright Law.
 * Unauthorized reproduction is considered a criminal act.
 * (C) 2018-2019 VDI Technologies, LLC. All rights reserved. 
"""

__author__    = "Yoel Monsalve"
__date__      = "January, 2019"
__modified__  = "June, 2021"
__version__   = ""
__copyright__ = "VDI Technologies, LLC"

"""
Plots a Bus of a CSV file
"""

import os, sys
from sys import argv, exit, stdin, stdout, stderr
import csv

import numpy as np
import matplotlib.pyplot as plt

sys.path.append( './py' )

import functions
from functions import calculatePeaks8, t_clear
from datetime import datetime, timedelta
from time import sleep

"""
Makes a pair of arrays of t, y, from a datafile
and for the specific bus tag

@return (t,y)  t is time
               y is signal (angle or volt)
"""
def read_data( datafile = "", busTag = "" ):

  t = []
  y = []

  if not datafile:
    stderr.write( "read_data: datafile is empty" )
    return (t, y)
    
  if not busTag:
    stderr.write( "read_data: busTag is empty" )
    return (t, y)
   
  with open( datafile, "r" ) as f:
    
    csv_reader = csv.reader( f, delimiter=',' )
    csv_reader = list( csv_reader )
    
    # trying to locate the header row
    i0 = 0
    headers = None
    while not headers and i0 < len(csv_reader):
      if csv_reader[i0][0].lower() == 'time(s)': 
        headers = csv_reader[i0]
      else:
        i0 += 1
    
    if not headers: return (t,y)
    headers = [h.strip().lower() for h in headers]
    
    try:
      k = headers.index(busTag.lower())
    except Exception as e:
      # no tag found
      sys.stderr.write( format(e) + "\n" )
      return (t, y)
      
    """
    k = 0
    while k < len(first_row):
      if first_row[k].lower() == busTag.lower():
        break
      k += 1
    
    if k == len(first_row):
    """
    
    # copying the values to arrays t, y
    for i in range(i0 + 1, len(csv_reader) ):
      t.append( float(csv_reader[i][0]) )
      y.append( float(csv_reader[i][k]) )
      
  f.close()
  return (t, y)
   
def plot( datafile, bus, output_dir, SPPR1 = '', SPPR2 = '' ):
  
  #datafile = 'Files/2021S_csv/P1-1-001-001_2021S_out.csv'
  #bus = 'VOLT 512651 [CLARMR 5 161.00]'
  #bus = 'ANGL512600[KERR_U2 1 13.200]2'

  #datafile = 'Files/2021S_csv/P1-2-016-019_2021S_out.csv'	
  #bus = 'ANGL512601[KERR_U3 1 13.200]3'

  t = y = []
  (t, y) = read_data( datafile, bus )
    
  #print( t[:50] )
  #print( y[:50] )
  n = len(t)
  if n == 0: return
  xticks = np.arange( 0, t[-1]-t[0], 1 )
  plt.plot( t, y )
  
  # fault clearing time
  tc = t_clear( datafile )
  #print( "tc is: ", tc )

  # ANGLES
  # ===================================
  if "ANGL" in bus.upper():
    peaks = []
    """
		peaks has the structure
		[
			{"name": ...
  		 "index": ...
  		}
		]
		"""
    peaks = calculatePeaks8( t, y, tc, 3 )

    t2 = []
    peaks2 = []
    for i in range(0, len(peaks)):
      t2.append( t[ peaks[i]["index"] ] )
      peaks2.append( peaks[i]["value"] )
  	
    plt.plot( t2, peaks2, 'r+' )
    
    if SPPR1:
      plt.text( 15, min(y) + 8.0/10*(max(y) - min(y)), '$SPPR_1$ = ' + SPPR1 )
    if SPPR2:
      plt.text( 15, min(y) + 7.0/10*(max(y) - min(y)), '$SPPR_2$ = ' + SPPR2 ) 
  
  # VOLTAGES
  # =====================
  if "VOLT" in bus.upper():
 
    plt.ylim( [0, max(y) if max(y) > 1.40 else 1.40 ] )
    plt.plot( [0, max(t)], [1.20] * 2, 'r:' )
    plt.plot( [0, max(t)], [0.70] * 2, 'r:' )
    plt.text( 15, 1.21, '1.20 PU' )
    plt.text( 15, 0.71, '0.70 PU' )
    
  ylims = plt.ylim()
  plt.plot( [tc, tc], [ylims[0], ylims[1]], 'r--' )
  plt.xlabel( 't' )
  if "ANGL" in bus.upper():
    plt.ylabel( 'ANGLE' )
  elif "VOLT" in bus.upper():
    plt.ylabel( 'VOLT (P.U.)' )
  else:
    plt.ylabel( '' )
  plt.title( bus )
  plt.xticks( xticks )
  
  # plot
  #plt.show()
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
  
  figname = output_dir  + event + "_" + bus + '.png'
  print( "  * Generating '{:s}'".format( figname ) )
  sys.stdout.flush()
  sys.stderr.flush()
  #plt.show()
  plt.savefig( figname, dpi = 300 )
  #plt.savefig( figname )     # defaults dpi
  plt.close( )

def usage( ):

  stderr.write( "USAGE: {:s} failure_report output_dir\n".format( argv[0] ) )

"""
SYNTAX:  <main> failure_report output_dir

Plots the curve for each CSV files listed in the
argument failure_report. If '-' is passed, reads from stdin.

The figures will be exported to the directory output_dir
"""
def main( ):

  if len( argv ) < 3:
    usage( )
    return
  
  report = argv[1]
  N_lines = 0
  if report == '-':
    f = sys.stdin
  else:
    f = open( report, 'r' )
    lines = f.readlines()
    for l in lines:
      if l.strip() != '': N_lines += 1
    f.seek(0, 0)      # cursor at the beginning

  output_dir = argv[2]  

  cnt = 0
  t1 = datetime.now()

  line = f.readline()
  cnt = 0
  while line:
    cnt += 1
    fields = line.strip().split('\t', 13)
    
    if len( fields ) > 1:
      datafile = fields[0]
      bus = fields[1]
      
      # Making UNIX style filenames
      if "\\\\" in datafile:
        datafile = datafile.replace( "\\\\", "/" )

      print( "\n==== [{}/{}] ====\nProcessing {:s} {:s}".format(cnt, 
      N_lines if N_lines > 0 else '?', datafile, bus) )
      stdout.flush()
            
      if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok = True)

      try:      
        if len( fields ) > 9:
          sppr1 = fields[8]
          sppr2 = fields[9]
              
          plot( datafile, bus, output_dir, sppr1, sppr2 )
        else:
          plot( datafile, bus, output_dir )

      except Exception as e:
        stderr.write(f"{sys.argv[0]}: {str(e)}\n")
        stderr.flush()

      line = f.readline()
  
  if report != '-':
    f.close()

  t2 = datetime.now()
  d = t2 - t1
  print( f"\nGraphics generation complete in {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}" )
  
if __name__ == '__main__':

  main()  

