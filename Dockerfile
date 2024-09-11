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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /INSTALL_C/

RUN chmod +x install_repos.py

# TODO: Add a requirements.txt 
#RUN pip install -r requirements.txt

CMD ["python", "install_repos.py"]