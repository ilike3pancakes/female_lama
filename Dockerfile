FROM arm32v6/alpine:3.5

RUN apk add --no-cache python3 py-pip

RUN pip3 install --upgrade pip

RUN pip3 install flask kik

# COPY ngrok bot.py entrypoint.sh /workdir/

WORKDIR /workdir/

ENTRYPOINT ["/bin/sh"]
