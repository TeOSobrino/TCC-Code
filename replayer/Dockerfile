FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tcpreplay tcpdump iproute2 ca-certificates bash \
    && rm -rf /var/lib/apt/lists/*

COPY replay.sh /replay.sh
RUN chmod +x /replay.sh

CMD ["/replay.sh"]
