# Defects4J v2.0.1 (the version the paper's prompt names) on Amazon Corretto 8u412
# (the JDK the paper's scripts select: `sdk use java 8.0.412-amzn`).
# Built once; every agent run starts a no-network container from it with the checkout mounted at /testbed.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive TZ=America/Los_Angeles
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
      ca-certificates curl git subversion perl cpanminus build-essential unzip jq \
      libdbi-perl libdbd-csv-perl liburi-perl libjson-perl libjson-parse-perl liblist-moreutils-perl \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL -o /tmp/jdk.tgz https://corretto.aws/downloads/resources/8.412.08.1/amazon-corretto-8.412.08.1-linux-x64.tar.gz \
    && mkdir -p /opt/jdk && tar -xzf /tmp/jdk.tgz -C /opt/jdk --strip-components=1 && rm /tmp/jdk.tgz
ENV JAVA_HOME=/opt/jdk PATH=/opt/jdk/bin:/opt/defects4j/framework/bin:$PATH
RUN git clone -q --branch v2.0.1 --depth 1 https://github.com/rjust/defects4j.git /opt/defects4j \
    && cd /opt/defects4j && cpanm --quiet --installdeps --notest . \
    && ./init.sh
# The paper's trace scripts call `sdk use java 8.0.412-amzn`; a no-op `sdk` keeps them unchanged.
RUN mkdir -p /root/.sdkman/bin && printf 'sdk() { :; }\n' > /root/.sdkman/bin/sdkman-init.sh
WORKDIR /testbed
CMD ["sleep", "infinity"]
