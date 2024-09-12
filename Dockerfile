FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /INSTALL_C

RUN apt-get update \
    && apt-get install -y \
       build-essential \
       cmake \
       scons \
       ninja-build \
       autoconf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \ 
   && apt-get install gradle -y

COPY . /INSTALL_C/

RUN apt-get update \ 
   && apt-get install gradle -y \
       pkg-config \
       meson \
       automake \
       libtool \ 
       git \ 
       vim 

RUN wget https://github.com/bazelbuild/bazelisk/releases/download/v1.6.1/bazelisk-linux-amd64
RUN chmod +x bazelisk-linux-amd64
RUN sudo ln -s ~/bazelisk-linux-amd64 /usr/bin/bazel
RUN bazel version
RUN pip install scons

#RUN chmod +x install_repos.py

# TODO: Add a requirements.txt 
#RUN pip install -r requirements.txt

#CMD ["python", "install_repos.py"]
