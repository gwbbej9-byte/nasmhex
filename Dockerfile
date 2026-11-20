FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nasm binutils make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY Makefile .
COPY src ./src
COPY samples ./samples
COPY tests ./tests

RUN make

CMD ["./nasmhex", "samples/hello.bin"]
