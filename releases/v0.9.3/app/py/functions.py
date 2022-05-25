def calculatePeaks8( time, signal, tc, r ):

	"""
	int i, i_MIN, i_MAX, i_M, j;
	int k;
	
	bool IS_PEAK, 
		IS_CONSTANT;
	
	peaks.resize( 0 );
	peaks.clear( );
	"""
	
	k = 0
	i_MIN = 0
	i_MAX = len( time )
	peaks = []

	# computes for t = tc onwards
	for i in range( 0, i_MAX ):
		
		# only for t after the "fault clearing time"
		if ( time[i] < tc ): continue
		
		IS_PEAK = True
		IS_CONSTANT = True
		for j in range( i-r, i+r+1 ):
			if j >= i_MIN and j < i_MAX:
				if j != i and signal[j] > signal[i]:
					IS_PEAK = False
					break
				
				if ( signal[j] != signal[i] ): IS_CONSTANT = False
		
		if not IS_CONSTANT and IS_PEAK:
			if k < 8:
				k += 1
				# is a peak
				peaks.append( {"value": signal[i], "index": i} )
				
				# debug
				#print( "located peak %.8lf at pos %d\n" % (peaks[k - 1]["value"], \
				#	peaks[k - 1]["index"]) )
				
			else:
				# not peak
				pass
				
	return peaks

# Returns the proper fault clearing time, depending
# of the name of the data file
def t_clear( filename ):

	tc = 0.0

	# Normal clearing time
	if "P1" in filename or "P2" in filename or "P3" in filename \
	or "P3" in filename or "P7" in filename:
			
		tc = 0.50 + 5.0/60;      # or 0.583333
	
	# P4 and extreme:
	# "Stuck Breaker Clearing Time"
	elif "P4" in filename or "PEE" in filename:
	
		tc = 0.50 + 15.0/60;     # or 0.75
		
	# P5:
	# "Remote End Clearing Time"
	elif "P5" in filename:
	
		tc = 0.50 + 30.0/60;     # or 1.00
		
	# otherwise 
	else:
	
		tc = 0.50;
		
	return tc

