FROM python:3.12-slim
# This image has no published ports, host credentials, Docker socket, or installed Crew state.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && apt-get clean
COPY . /opt/workshop
RUN python -m pip install --no-cache-dir /opt/workshop \
    && mkdir -p /state /tmp \
    && chmod 1777 /state /tmp
USER 65532:65532
CMD ["/bin/sh"]
