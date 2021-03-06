# used in the fft data preparation
import numpy as np

# used in obtaining the dbfs and bark length
import pydub

# used in file enumeration
import os

# used in output of CSV
import csv
import constants

# used in obtaining arguments
import sys

args = list(sys.argv)

EXPERIMENT = False

if len(args) > 1:
    if args.count("exp"):
        print("extracting for experiment")
        EXPERIMENT = True
    else:
        EXPERIMENT = False
else:
    print("extracting for data collection")

'''------------------------------------
AVERAGE LOUDNESS OBTAINER:
    receives object ( the array that contains all sequences ),
    returns mean loudness of the entire file ( object )
------------------------------------'''
def get_average_loudness( obj ):
    meanLoudness = 0

    # does a summation of the loudness for each sequence
    for sequence in range(len(obj)):
        currentSequence = obj[sequence]
        meanLoudness += currentSequence['dbfs']
        
    # gets the average
    return meanLoudness / len(obj)


'''------------------------------------
AVERAGE INTERBARK INTERVAL OBTAINER:
    receives data stream and sample rate,
    returns mean interbark interval
------------------------------------'''
def get_IBI(_data, fs):
    # just reassigns the variable
    data = _data
    data_size = len(data)
    # constant : size of indices to jump incase a bark is detected
    FOCUS_SIZE = int(constants.SECONDS * fs)
    
    focuses = []
    distances = []
    idx = 0
    
    while idx < len(data):
        # if a value in the data stream exceeds the preset minimum value
        if (data[idx] > constants.MIN_VAL):

            # gets the index in the middle of the detected index and focus size
            mean_idx = idx + FOCUS_SIZE // 2

            # appends that index into the focuses 
            focuses.append(float(mean_idx) / data_size)

            # calculates the distance between the latest and second latest focus indices
            if len(focuses) > 1:
                last_focus = focuses[-2]
                actual_focus = focuses[-1]
                distances.append(actual_focus - last_focus)

            # skips FOCUS_SIZE indices ahead
            idx += FOCUS_SIZE
        else:
            idx += 1
    
    mean = 0

    print(focuses)
    print(distances)
    print(len(distances) + 1 , "barks detected")

    # does a summation of all the distances
    for val in distances:
        mean += val
    
    # tries to get the average
    # if there's only one bark detected, will set the mean as 0
    try:
        mean = mean/len(distances)
    except ZeroDivisionError as e:
        mean = 0

    return mean

'''------------------------------------
LOUDNESS EXTRACTOR:
    receives frequency domain data and maximum detected frequency,
    returns the "rougness" of the data
------------------------------------'''
def get_roughness(fftData, max):
    # to contain the points above a percentage of max
    filtered = []

    # used as a link to obtain the frequencies
    i = 0
    
    # value used for "filtering" the points in the freq. domain
    threshold_percent_of_max = max * constants.PERCENT_OF_MAX
    
    # iterates through all the values in fftData
    for value in fftData:
        # a check if the value is higher than the preset percentage of max and that the value is not the max value
        if (value > threshold_percent_of_max and value != max):
            # adds the value and its corresponding frequency into the 'filtered' array
            filtered.append({ 'value' : value , 'freq' : w[i] })
        i += 1

    # summation
    sum = 0.0
    for value in filtered:
        sum += value['value']
    
    try:
        # getting the mean roughness of the points
        temp_roughness = sum / float(len(filtered))
    
        # getting the roughness
        roughness = temp_roughness / max
    except Exception as e:
        roughness = 0
    
    return roughness

'''------------------------------------
FOURIER TRANSFORM:
    receives data stream and sample rate,
    returns amplitudes (fourier_to_plot) and corresponding frequencies (w)
------------------------------------'''
def doFFT(data, sampleRate):
    # transforming the data (in time domain) to frequency domain using 1DFFT
    # audio data and sample rate
    aud_data = data
    aud_sr = sampleRate

    # data length
    len_data = len(aud_data)

    # padding zeros into data "zero-pad out your data to a power of 2" for faster FFT
    # https://stackoverflow.com/a/48015264
    data = np.zeros(2**(int(np.ceil(np.log2(len_data)))))
    data[0:len_data] = aud_data


    """A vectorized, non-recursive version of the Cooley-Tukey FFT"""

    data = np.asarray(data, dtype=float)
    N = data.shape[0]

    if np.log2(N) % 1 > 0:
        raise ValueError("size of x must be a power of 2")

    # N_min here is equivalent to the stopping condition above,
    # and should be a power of 2
    N_min = min(N, 32)
    
    # Perform an O[N^2] DFT on all length-N_min sub-problems at once
    n = np.arange(N_min)
    k = n[:, None]
    M = np.exp(-2j * np.pi * n * k / N_min)
    X = np.dot(M, data.reshape((N_min, -1)))

    # build-up each level of the recursive calculation all at once
    while X.shape[0] < N:
        X_even = X[:, :X.shape[1] // 2]
        X_odd = X[:, X.shape[1] //2:]
        factor = np.exp(-1j * np.pi * np.arange(X.shape[0])
                        / X.shape[0])[:, None]
        X = np.vstack([X_even + factor * X_odd,
                       X_even - factor * X_odd])
    
    
    # doing fft into the data
    fft_data = X.ravel()

    # makes an array with values from parameter 1 to parameter 2 
    # number of elements in array depends on parameter 3 
    # -- to be used as "steps" for frequencies --
    w = np.linspace(0, aud_sr, len(fft_data))

    # "First half is the real component, second half is imaginary"
    fourier_to_plot = fft_data[0:len(fft_data)//2]
    w = w[0:len(fft_data)//2]

    # transforms all values in fourier_to_plot to their absolute value
    # so we can have the representation in amplitude spectrum
    # https://docs.scipy.org/doc/numpy-1.15.0/reference/routines.fft.html#implementation-details
    fourier_to_plot = np.abs(fourier_to_plot)

    # returns the values (fourier_to_plot) of the corresponding frequencies (w)
    return fourier_to_plot, w

# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
'''------------------------------------
 S T A R T 
    O F 
 C O D E S 
 (AKA MAIN FUNCTION)
------------------------------------'''

targetFolder = 'data'

toBePreprocessed = []
toBePreprocessed = os.listdir(targetFolder)

samples = []
sets = []

# gets all wav files
for s in toBePreprocessed:
    container = s.split('.')[-1]
    if container == 'wav':
        samples.append(s)

# print(samples)

# gets the unique names of all wav files
for s in samples:
    name = s.split('-')[1]
    if name not in sets:
        sets.append(name)

# print(sets)

print("start of read")

# array to contain all sequences as data
allData = []

# set : the original name of the unsplit wav files
# example:  split-barks-0.wav
#           is a part of the 'barks' set    
for s in sets:
    i = 0
    
    # will contain the bark sequences and the respective info for those
    dataForThisSet = []

    while True:
        try:
            # reconstructing the filenames
            filename = 'split-' + s + '-' + str(i) + '.wav'
            filestr = targetFolder + '/' + filename

            # making a pydub AudioSegment from the wav file pointed to by the filenames
            sound = pydub.AudioSegment.from_wav(filestr)
            print(">>> got " + filestr)

            # parsing the data steam
            data = sound.get_array_of_samples()
            data = np.array(data)
            data = data.reshape(sound.channels, -1, order='F')
            
            # getting the sample rate
            sr = sound.frame_rate

            # getting the loudness
            dbfs = sound.dBFS

            # makes a temporary object with the attributes set
            obj = {
                'filename' : filename,
                'data' : data,
                'sr' : sr,
                'dbfs' : dbfs
            }

            # adds this sequence into the array
            dataForThisSet.append(obj)

            # iterate to the next bark sequence
            i += 1

        except Exception as e:
            # when no more sequences in the set
            print("end")
            break
    # adds the array with sequences information to the main array with the set name as the key
    allData.append({ s : dataForThisSet})
    
# to contain all rows for the final csv file
allForExport = []


for recording in range(len(allData)):
    # to contain all rows for the recording
    rowsForRecording = []
    
    # set a variable to have the reference to the object
    current = allData[recording]
    key = list(current.keys())[0]

    if not EXPERIMENT:
        # getting the classification for the entire set
        # (assumes that one set is of only one classification aggressive/non-aggressive)
        print("-------------------------------------")
        print("Processing **" + str(key) + "** recording")

        s = str(key)
        classif = s.split('_')[0]
        if classif == 'aggr':
            classif = 1
        else:
            classif = 0
    print("-------------------------------------")

    # getting the average loudness (for perceptual spread)
    meanLoudness = get_average_loudness(current[key])
    print(meanLoudness)

    # the part where rows are filled in
    for sequence in range(len(current[key])):
        # make a temporary row
        tempRow = {}
        
        # make a temporary variable to handle the sequence data
        currentSequence = current[key][sequence]
        
        data = currentSequence['data'][0]
        dataLength = len(data)
        sampleRate = currentSequence['sr']

        # name is the file name
        tempRow['name'] = currentSequence['filename']   
        print("---S T A R T for", currentSequence['filename'])
        
        # calculating perceptual spread
        diffInLoudness = meanLoudness - currentSequence['dbfs']
        tempRow['perceptual_spread'] = diffInLoudness

        # calculating bark length
        # initializing a pydub AudioSegment using the array
        audio = pydub.AudioSegment(
            data=data.tobytes(),
            sample_width=4,
            frame_rate=sampleRate,
            channels=1
        )

        # TODO: refactor
        # splits the AudioSegment into "chunks" of barks
        chunks = pydub.silence.split_on_silence(audio,
            min_silence_len = 100,  # length in ms when a chunk is declared as a chunk

            silence_thresh = -35,   # threshold in dbfs that is used to detect non-silence
            keep_silence = 50       # amount of time in ms to keep
        )

        # summation of bark length
        bl = 0.0
        for i , chunk in enumerate(chunks):
            print(len(chunk))
            bl = bl + float(len(chunk) / sampleRate)
        
        # getting the average bark length
        try:
            bark_len = bl / float(len(chunks))
        except Exception as e:
            bark_len = 0

        tempRow['bark_length'] = bark_len

        ##################################################################

        # calculating interbark interval
        ibi = get_IBI(data,sr)
        tempRow['interbark_interval'] = ibi

        # - - FREQUENCY DOMAIN FEATURE EXTRACTION FOLLOWS - -

        # DOING FFT
        fftData, w = doFFT(data, sr)
        
        # gets the maximum index
        max_index = np.argmax(fftData)
        # gets the maximum value
        max = np.amax(fftData)

        # gets the corresponding frequency with the highest amplitude
        pitch = w[max_index] 

        tempRow['pitch'] = pitch

        # # --- FOR VISUALIZATION PURPOSES ONLY ---

        # # x is w (frequency steps)
        # # y is fftData (amplitude values)
        # plt.plot(w, fftData)
        
        # # shows filename and labels in the plot
        # plt.title(currentSequence['filename'])
        # plt.xlabel('frequency')
        # plt.ylabel('amplitude')
        # #plt.show()

        # # --- FOR VISUALIZATION PURPOSES ONLY ---

        # obtaining tone quality/roughness
        roughness = get_roughness(fftData, max)
        
        tempRow['roughness'] = roughness
        if not EXPERIMENT:
            tempRow['aggressive'] = classif

        allForExport.append(tempRow)

print('saving...')

if EXPERIMENT:
    output_filename = 'output_experiment.csv'
    fieldnames = ['name','perceptual_spread','bark_length','interbark_interval','roughness', 'pitch']
else:
    output_filename = 'output.csv'
    fieldnames = ['name','perceptual_spread','bark_length','interbark_interval','roughness', 'pitch','aggressive']
    
with open(output_filename, mode='w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for row in allForExport:
        writer.writerow(row)

print('success')
print('output saved as ', output_filename)

if EXPERIMENT:
    exit()
    
import pandas as pd 

data = pd.read_csv(output_filename)
data = data.sample(frac=1).reset_index(drop=True)

shuffled_filename = output_filename.split('.')[:1][0] +  '_shuffled.csv'

data.to_csv( shuffled_filename )

print('shuffled dataset saved as ', shuffled_filename )

