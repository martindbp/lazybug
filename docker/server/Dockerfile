FROM ubuntu:20.04
SHELL ["/bin/bash", "--login", "-c"]

RUN apt-get update --fix-missing
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt install -y tzdata pkg-config curl python3.10 python3-pip libcairo2
ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 14.18.1
RUN mkdir /usr/local/nvm && \
    curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

COPY requirements.txt requirements.txt
RUN pip --no-cache-dir install -r requirements.txt
RUN npm install -g vue@next @vue/cli-service @vue/compiler-sfc @vue/cli-init sass
RUN npm install canvas utfstring
RUN rm -rf /var/lib/apt/lists/*
