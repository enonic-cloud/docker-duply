FROM alpine:3.7

# Setup python
RUN apk update && apk add bash python2-dev py-setuptools librsync-dev python2 py-boto gnupg ncftp py-lockfile alpine-sdk libffi libffi-dev ca-certificates build-base py-pip linux-headers haveged

# Setup duplicity
RUN cd /tmp && \
    wget https://code.launchpad.net/duplicity/0.7-series/0.7.17/+download/duplicity-0.7.17.tar.gz && \
    tar zxvf duplicity-0.7.17.tar.gz && \
    cd  duplicity-0.7.17 && \
    python2 setup.py install

# Setup duply
RUN cd /tmp && \
    wget https://netix.dl.sourceforge.net/project/ftplicity/duply%20%28simple%20duplicity%29/2.0.x/duply_2.0.4.tgz && \
    tar zxvf duply_2.0.4.tgz && \
    cp /tmp/duply_2.0.4/duply /usr/local/bin && \
    chmod +x /usr/local/bin/duply

# Install requirements
COPY . /tmp

RUN \
    # Install requirements
    pip install pbr==4.0.0 && \
    pip install -r /tmp/requirements.txt && \
    # Patch swift backend
    mv /tmp/swiftbackend.py /usr/lib/python2.7/site-packages/duplicity/backends/swiftbackend.py && \
    rm /usr/lib/python2.7/site-packages/duplicity/backends/swiftbackend.pyc && \
    # Cleanup
    rm -r /tmp/*