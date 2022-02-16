# Arguments:
# - PIP_VERSION: the version of pip to use (upgrade on base image), defaults to 21.0.1
# - POETRY_VERSION: the version of poetry to use, defaults to 1.1.7

FROM python:3.9 AS python-base

ARG PIP_VERSION=21.0.1
ARG POETRY_VERSION=1.1.12

# Install all base system components
COPY bin/install-system-dependencies.sh \
    bin/install-python-dependencies.sh \
    scripts/

RUN /scripts/install-system-dependencies.sh $PIP_VERSION $POETRY_VERSION
ENV PATH="/root/.local/bin:$PATH"
ENV PATH=$PATH:/app
ENV PYTHONPATH /app

# Set up Python virtualenv and make it default for system and Poetry
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV

# Copy pyproject.toml
COPY pyproject.toml ./
COPY poetry.lock ./

# Install python dependencies
# For whatever reason this doesn't work if you install setuptools with poetry
RUN pip install setuptools==45
RUN /scripts/install-python-dependencies.sh $BUILD_ENV
WORKDIR /app
COPY . .

# Install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# Install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

