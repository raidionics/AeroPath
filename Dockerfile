# read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# you will also find guides on how best to write your Dockerfile
FROM python:3.10-slim

# set language, format and stuff
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /code

RUN apt-get update -y
#RUN apt-get install -y python3 python3-pip
RUN apt install git --fix-missing -y
RUN apt install wget -y

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

WORKDIR /code

# install dependencies
COPY ./demo/requirements.txt /code/demo/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/demo/requirements.txt

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
RUN wget "https://github.com/raidionics/Raidionics-models/releases/download/v1.3.0-rc/Raidionics-CT_Airways-v13.zip" && \
    unzip "Raidionics-CT_Airways-v13.zip" && mkdir -p resources/models/ && mv CT_Airways/ resources/models/CT_Airways/
RUN wget "https://github.com/raidionics/Raidionics-models/releases/download/v1.3.0-rc/Raidionics-CT_Lungs-v13.zip" && \
    unzip "Raidionics-CT_Lungs-v13.zip" && mv CT_Lungs/ resources/models/CT_Lungs/

RUN rm -r *.zip

# Download test sample
# @TODO: I have resampled the volume to 1mm isotropic for faster computation
RUN wget "https://github.com/andreped/neukit/releases/download/test-data/test_thorax_CT.nii.gz"

# CMD ["/bin/bash"]
CMD ["python3", "demo/app.py"]
