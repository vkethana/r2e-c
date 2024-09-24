FROM r2e:base_dockerfile

RUN apt-get update \ 
   && apt-get install gradle -y \
       pkg-config \
       meson \
       automake \
       libtool \ 
       git \ 
       vim \
       wget

RUN pip install scons

RUN apt-get update \ 
   && apt-get install fuse3 -y \
        libsystemd-dev \
        gio-2.0 \
        wayland-protocols \
        libz-dev \
        libgmp-dev \
        libjemalloc-dev \
        libjpeg-dev \
        libevent-dev \
        libreadline-dev \
        liblmdb-dev \
        libavcodec-dev \
        libsndfile-dev  \
        libpcap-dev  \
        libssl-dev  \
        libfuse-dev \
        libbfd-dev \
        libncurses-dev

COPY paths.py install_repos.py utils.py /INSTALL_C/ 
RUN chmod +x install_repos.py

# TODO: Add a requirements.txt 
#RUN pip install -r requirements.txt

RUN apt-get update \ 
    && apt-get install -y zlib1g-dev libgmp3-dev libcap-dev libx11-dev libjemalloc-dev libjpeg-dev libnetfilter-queue-dev libevent-dev libzmq3-dev libreadline-dev libsdl2-dev libssl-dev portaudio19-dev libxcb1-dev libavcodec-dev liblua5.3-dev libsndfile1-dev libncurses5-dev libpcap-dev libfuse-dev libedit-dev libbfd-dev libncurses-dev libjudy-dev

RUN apt-get update && apt-get install fuse3 libgtk-3-dev libpixman-1-dev libpng-dev gcc-multilib g++-multilib librdkafka-dev libelf-dev libmbedtls-dev libsdl1.2-dev -y

RUN apt-get update && apt-get install libbpf-dev apt-file libxcb-util0-dev libxcb-keysyms1-dev libavformat-dev lua5.3 libev-dev curl libcapstone-dev libsqlite3-dev libcurl-dev libswscale-dev libhiredis-dev -y

RUN python install_repos.py
CMD ["/bin/bash"]
