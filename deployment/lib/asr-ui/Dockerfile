FROM continuumio/miniconda3

WORKDIR /asr

RUN apt-get update -y && \
    apt-get install git -y && \
    git clone https://huggingface.co/spaces/aadnk/faster-whisper-webui
RUN conda install python==3.10 ffmpeg -y && \
    pip install -r faster-whisper-webui/requirements-fasterWhisper.txt && \
    pip install flask boto3 requests flask_cors nvidia-cublas-cu11 nvidia-cudnn-cu11 ffmpeg-python torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

RUN echo "cd /asr/faster-whisper-webui/ \n \
export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'` \
python3 /asr/faster-whisper-webui/app.py" > run-webui.sh && chmod u+x run-webui.sh
CMD ["/bin/bash", "-c", "/asr/run-webui.sh"]
