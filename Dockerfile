FROM r2e:base_dockerfile_100

RUN pip install scons

COPY paths.py install_repos.py utils.py /INSTALL_C/ 
RUN chmod +x install_repos.py

# TODO: Add a requirements.txt 
#RUN pip install -r requirements.txt
RUN ln -s /usr/include/pcap/bpf.h /usr/include/net/bpf.h

RUN apt-get update && apt-get install -y libpq-dev postgresql-server-dev-all postgresql-common libmysqlclient-dev libusb-1.0 autoconf autogen automake build-essential libasound2-dev libtool libvorbis-dev libopus-dev libmp3lame-dev
RUN apt-get update && apt-get install -y autoconf-archive texinfo libyaml-dev byacc libmpfr-dev libmpc-dev flex
RUN apt-get update && apt-get install -y libudev-dev libasound2-dev libdbus-1-dev node-gyp npm git cmake git cmake libcbor-dev cmake automake autoconf libtool pkg-config doxygen git libssl-dev libmbedtls-dev zlib1g-dev python3 node-gyp npm libcbor-dev ninja-build gettext cmake unzip curl build-essential

WORKDIR /
RUN wget https://ftp.gnu.org/pub/gnu/gettext/gettext-0.21.1.tar.gz
RUN tar -xf gettext-0.21.1.tar.gz
WORKDIR /gettext-0.21.1
RUN time ./configure
RUN time make  # took my computer about 4 minutes
RUN make install
WORKDIR /INSTALL_C

RUN python install_repos.py
CMD ["/bin/bash"]
