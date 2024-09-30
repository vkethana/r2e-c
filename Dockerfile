FROM r2e:base_dockerfile

RUN pip install scons

COPY paths.py install_repos.py utils.py /INSTALL_C/ 
RUN chmod +x install_repos.py

# TODO: Add a requirements.txt 
#RUN pip install -r requirements.txt
RUN ln -s /usr/include/pcap/bpf.h /usr/include/net/bpf.h

RUN python install_repos.py
CMD ["/bin/bash"]
