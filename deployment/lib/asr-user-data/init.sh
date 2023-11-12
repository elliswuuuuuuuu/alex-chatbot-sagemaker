#!/bin/bash

################################################################################################################################
#
# This script acts as start-up script when EC2 spins up.
#
# Faster-whisper model will be downloaded to ~/.cache/huggingface/hub/models--guillaumekln--faster-whisper-large-v2/, when it
# firstly being invoked.
#
################################################################################################################################


# Create required folders
mkdir /asr && mkdir -p /asr/output_dir/ /asr/logs/transcription/ /asr/logs/execution/
cd /asr

# Clone utilities
git clone https://huggingface.co/spaces/aadnk/faster-whisper-webui

conda install ffmpeg-python -y
# Python Version must be greater than 3.7
/opt/conda/bin/python3 -m venv asr-venv && source asr-venv/bin/activate 
pip install -r faster-whisper-webui/requirements-fasterWhisper.txt
pip install flask boto3 requests flask_cors nvidia-cublas-cu11 nvidia-cudnn-cu11

#############
#
# For china
# pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple
#
#############

## To-be-done


# Download model directly from HuggingFace, for CN, need to change to 
cat > /asr/download_model.py <<EOF
import huggingface_hub
huggingface_hub.snapshot_download('guillaumekln/faster-whisper-large-v2')
EOF

python3 /asr/download_model.py

# Create app.py
cat > /asr/app.py <<EOF

from flask import Flask, request, render_template
from flask_cors import CORS, cross_origin
from faster_whisper import WhisperModel
import boto3
import uuid
from faster_whisper import WhisperModel
from faster_whisper.vad import VadOptions

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for whole app
s3_res = boto3.resource('s3')
s3_cli = boto3.client('s3')

TMP_LOCAL_STORAGE = "/tmp"

def download_s3_file(bucket_name, file_name, local_file):
    """
    Function for downloading S3 file into local storage
    """
    s3_cli.download_file(
        Bucket=bucket_name,
        Key=file_name,
        Filename=local_file
    )


@app.route('/')
def hello():
    return 'Hello, World!'
    

@app.route('/transcribe', methods=['POST', 'OPTIONS'])
@cross_origin()
def transcribe():
    
    data = request.get_json()
    
    try:
        audio_file_location = data['audio_file_location']
    except KeyError:
        response = """{
            "message": "Missing image location."
        }
        """
        return response
    
    audio_s3_path_no_scheme = audio_file_location[5:]
    bucket_name = audio_s3_path_no_scheme[:audio_s3_path_no_scheme.find("/")]
    prefix = audio_s3_path_no_scheme[audio_s3_path_no_scheme.find("/") + 1:audio_s3_path_no_scheme.rfind('/')]
    audio_name = audio_s3_path_no_scheme[audio_s3_path_no_scheme.rfind('/') + 1:]
    
    uuid_str = uuid.uuid4()
    local_file_path = f"{TMP_LOCAL_STORAGE}/{audio_name}_{uuid_str}"
    
    # Download S3 file to local
    download_s3_file(
        bucket_name=bucket_name,
        file_name=f"{prefix}/{audio_name}",
        local_file=local_file_path
    )
    
    print(f"local_file_path is : {local_file_path}")
    
    # import subprocess

    # process = subprocess.Popen(["/asr/invoke.sh", f"{local_file_path}"],
    #                               stdout=subprocess.PIPE,
    #                               stderr=subprocess.PIPE,
    #                               text=True
    #                               )
    # print("Start to transcribe, please wait...")
    # process.communicate()
    # process.wait()
    # print("Completed transcription.")

    # # Read output from output_dir
    # try:
        
    #     with open(f"/asr/output_dir/{audio_name}_{uuid_str}-transcript.txt") as f:
    #         transcription_result = f.read()
        
    #     print(f"Transcription: {transcription_result}")
    #     return transcription_result
        
    # except Exception as e:
    #     print('Unable to find the output')
    #     print(f'Error occured: {e}')
    #     return 'Unable to find the output'
    
    model_size = "large-v2"

    # Run on GPU with FP16
    model = WhisperModel(model_size, device="cuda", compute_type="float16")

    segments, _ = model.transcribe(local_file_path,
                                   temperature=0.0,
                                   vad_filter=True,
                                   vad_parameters=VadOptions())
    
    segments = list(segments)

    transcription = ".".join([segment.text for segment in segments])

    print(transcription)

    return {
        "result": transcription
    }


if __name__ == '__main__':
    app.run('0.0.0.0')

EOF


## Create a script for running app.py in backend
cat > run.sh <<EOF
source /asr/asr-venv/bin/activate && export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'` && python3 app.py
EOF

# Run service and put to background with disown
bash run.sh 2>&1 > /asr/logs/execution/`date +%Y%m%d_%H%M%S`.log & disown


cat > Dockerfile <<EOF
FROM continuumio/miniconda3

WORKDIR /asr

RUN apt-get update -y && \
    apt-get install git -y && \
    git clone https://huggingface.co/spaces/aadnk/faster-whisper-webui
RUN conda install python==3.10 ffmpeg -y && \
    pip install -r faster-whisper-webui/requirements-fasterWhisper.txt && \
    pip install flask boto3 requests flask_cors nvidia-cublas-cu11 nvidia-cudnn-cu11 ffmpeg-python torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

RUN echo "cd /asr/faster-whisper-webui/ \n \
export LD_LIBRARY_PATH=/opt/conda/lib/python3.10/site-packages/nvidia/cublas/lib:/opt/conda/lib/python3.10/site-packages/nvidia/cudnn/lib \n\
python3 /asr/faster-whisper-webui/app.py" > run-webui.sh && chmod u+x run-webui.sh

CMD ["/bin/bash", "-c", "/asr/run-webui.sh"]
EOF

### Start to build webui docker
docker build -t whisper-webui:latest . -f /asr/Dockerfile

### Download silero-vad model
git clone https://github.com/snakers4/silero-vad.git /root/.cache/torch/hub/snakers4_silero-vad_master/

# Download custom app.py & config.json5 and Spin up WebUI via Docker
cd /asr/faster-whisper-webui
region=`curl -s http://169.254.169.254/latest/meta-data/placement/region`
account_id=`aws sts get-caller-identity --query "Account" --output text`
instance_id=`curl -s http://169.254.169.254/latest/meta-data/instance-id`
default_sagemaker_bucket="sagemaker-${region}-${account_id}"

aws s3 cp s3://${default_sagemaker_bucket}/app.py app.py
aws s3 cp s3://${default_sagemaker_bucket}/config.json5 config.json5
# python3 app-local.py 2>&1 > /asr/logs/execution/ui_`date +%Y%m%d_%H%M%S`.log & disown
docker run -d -p 7860:7860 \
              -e REGION=${region} \
              -e INSTANCE_ID=${instance_id} \
              -v /root/.cache/:/root/.cache/ \
              -v /asr/faster-whisper-webui/:/asr/faster-whisper-webui/ \
              --gpus all \
              whisper-webui:latest