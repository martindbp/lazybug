FROM martindbp/lazybug-server
SHELL ["/bin/bash", "--login", "-c"]

COPY requirements.txt requirements.txt
RUN apt -y update && apt -y full-upgrade && apt install -y libcairo2-dev
RUN pip --no-cache-dir install -r requirements.txt
RUN npm install canvas utfstring
RUN rm -rf /var/lib/apt/lists/*
