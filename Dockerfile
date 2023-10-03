# read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# you will also find guides on how best to write your Dockerfile

# creates virtual ubuntu in docker image
FROM ubuntu:22.04

# set language, format and stuff
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# NOTE: using -y is conveniently to automatically answer yes to all the questions
# installing python3 with a specific version
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt update
RUN apt install python3.7 -y
RUN apt install python3.7-distutils -y
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

# installing other libraries
RUN apt-get install python3-pip -y && \
    apt-get -y install sudo
RUN apt-get install curl -y
RUN apt-get install nano -y
RUN apt-get update && apt-get install -y git
RUN apt-get install libblas-dev -y && apt-get install liblapack-dev -y
RUN apt-get install gfortran -y
RUN apt-get install libpng-dev -y
RUN apt-get install python3-dev -y
# RUN apt-get -y install cmake curl

WORKDIR /code

# install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# resolve issue with tf==2.4 and gradio dependency collision issue
RUN pip install --force-reinstall typing_extensions==4.7.1

# Install wget
RUN apt install wget -y && \
    apt install unzip

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Download pretrained models
RUN wget "https://github.com/raidionics/Raidionics-models/releases/download/1.2.0/Raidionics-CT_Airways-ONNX-v12.zip" && \
    unzip "Raidionics-CT_Airways-ONNX-v12.zip" && mkdir -p resources/models/ && mv CT_Airways/ resources/models/CT_Airways/
RUN wget "https://github.com/raidionics/Raidionics-models/releases/download/1.2.0/Raidionics-CT_Lungs-ONNX-v12.zip" && \
    unzip "Raidionics-CT_Lungs-ONNX-v12.zip" && mv CT_Lungs/ resources/models/CT_Lungs/

RUN rm -r *.zip

# Download test sample
RUN wget "https://github.com/andreped/neukit/releases/download/test-data/test_thorax_CT.nii.gz"

# CMD ["/bin/bash"]
CMD ["python3", "demo/app.py"]
