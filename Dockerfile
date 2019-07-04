FROM ubuntu:xenial

VOLUME /mnt/input
VOLUME /mnt/output

RUN apt-get update && apt-get install -y sudo default-jre jq python python-pip python3 python3-pip curl perl git
RUN apt-get install -y python3-numpy python3-scipy python3-matplotlib python-numpy python-scipy python-matplotlib
RUN pip3 install setuptools matplotlib numpy scikit_learn tensorflow==1.8.0 Keras==2.2.4 h5py imbalanced-learn

COPY . /app
WORKDIR /app

RUN git clone https://github.com/carter-yagemann/barnum-learner.git barnum
RUN easy_install /app/mimicus/dist/mimicus-1.0-py2.7.egg

CMD ["bash", "run.sh"]
