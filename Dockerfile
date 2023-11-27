FROM ubuntu:18.04

RUN set -eux ; \
    apt-get update && apt-get upgrade -y && apt-get clean ; \
    apt-get install -y curl wget python3.7 python3.7-dev python3.7-distutils python3-setuptools ; \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1 ; \
    update-alternatives --set python /usr/bin/python3.7 ; \
    curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py --force-reinstall && \
    rm get-pip.py

RUN set -eux ; \
    apt-get install -y --no-install-recommends  \
    libedit-dev build-essential \
    llvm-10 llvm-10-dev libsndfile1

RUN set -eux ; \
    curl https://sh.rustup.rs -sSf | bash -s -- -y ; \
    echo 'source $HOME/.cargo/env' >> $HOME/.bashrc

ENV LLVM_CONFIG='/usr/bin/llvm-config-10'
ENV SETUPTOOLS_USE_DISTUTILS='stdlib'
ENV RESULT_DIR='/opt/results'
ARG WORK_DIR='/opt/app/current'

RUN mkdir -p $WORK_DIR

WORKDIR $WORK_DIR

COPY . .

RUN set -eux ; \
    python -m pip install --upgrade pip==23.0.1 wheel==0.34.2 setuptools==49.6.0 numpy==1.20.3; \
    python -m pip install setuptools-rust ; \
    python -m pip install --ignore-installed -r ./requirements.txt ; \
    python setup.py install


RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]