import subprocess
import os
from dotenv import load_dotenv
import random
import sys
from io import BytesIO

import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
print('-------\n------\nAre you using the virtualenv?\ne.g. source env/bin/activate \n------\n------')
import librosa
print('Ready...')

load_dotenv() #Load ENV File

# Define the MQTT broker parameters 
broker_address = os.getenv('BROKER_ADDRESS')
broker_port = int(os.getenv('BROKER_PORT'))
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
topic = os.getenv('TOPIC')

# Generate a random client ID
client_id = f"python-{random.randint(0, 1000000)}"

# Define the audio parameters
sample_rate = 44100 # Ultramic is 192000Hz
duration = 1  # duration of audio to record in seconds
channels = 1 # use on MONO, multi channels may require MFCC (librosa.feature.mfcc)
NFFT_val = 2048 # FFT points per chunks
hop_length_val = 1024 # NFFT/2
fmin_val = 20 #lowest frequency (in Hz)
# fmax=sample_rate/2 #highest frequency (in Hz). If None, use fmax = sample_rate / 2.0

n_mels_val = 128 #number of mel bins

ref_norm = 10 #value to normalise the various spectrogram samples

vmin_value = -60 #min dB value for the image
vmax_value = 0 #max dB value for the image

#Choose the type of Spectrogram to create: 1- Mel Librosa ; 2- Linear[not implemented yet] 
spectro = 1

# Connect to MQTT
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc ==0:
            print("Connected")
        else:
            print("Connection Failed")

    client = mqtt.Client(client_id)
    client.on_connect = on_connect
    client.username_pw_set(username,password) 
    client.connect(broker_address, broker_port)
    return client

def publish(client):
    msg_count = 0
    while True:
        try:
        #Record raw audio in memory float audio using SoX - use sudo arecord -l to know the device card and number e.g. hw:1,0
            audio_command = f"sudo sox -t alsa hw:1,0 -e float -c {channels} -r {sample_rate} -t raw -e float - trim 0 {duration}"
            audio_process = subprocess.Popen(audio_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            audio_output, audio_error = audio_process.communicate()

            print(audio_error)

        #Covert audio data in numpy array - Librosa needs floting points
            audio_data = np.frombuffer(audio_output, dtype=np.float32)

        #compute using LIBROSA https://github.com/pytorch/audio/issues/1058
            S=librosa.feature.melspectrogram(y=audio_data,sr=sample_rate,n_mels=n_mels_val,n_fft=NFFT_val,hop_length=hop_length_val,fmin=fmin_val, norm='slaney', htk=True, center=False, pad_mode="reflect")
            S_dB = librosa.power_to_db(S,ref=ref_norm) #np.max change for each sample
            buf = BytesIO()

            if spectro == 1:
	            #Librosa Mel Spectrogram saved as WebP in a buffer, using Pillow args for quality
                plt.imsave(buf, S_dB, vmin=vmin_value, vmax=vmax_value, format='webp', origin='lower',cmap='magma',pil_kwargs={'lossless':True,'quality':60,'method':4})
            
            elif spectro == 2:
                #Linear Spectrogram saved as WebP in a buffer, using Pillow args for quality
                plt.imsave(buf, S_dB, vmin=vmin_value, vmax=vmax_value, format='webp', origin='lower',cmap='magma',pil_kwargs={'quality':100,'method':6})
          
            sys.stdout.flush()

            msg = f"messages:{msg_count}"
           
           #Read the buffer and send the spectrogram
            buf.seek(0)
            image_data = buf.read()
            result = client.publish(topic,image_data)

            status = result[0]
            print(status)
            if status == 0:
                print(f"Send `{msg}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")
            msg_count += 1
        except KeyboardInterrupt:
            break

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)

if __name__ == '__main__':
    run()
