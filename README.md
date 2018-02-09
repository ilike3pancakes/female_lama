NGROK=/tmp/ngrok

wget -O $NGROK.zip https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm.zip && unzip $NGROK.zip

# nohup python bot.py > bot.out 2>&1 &

nohup $NGROK http 8080 > /dev/null 2>&1 &

curl localhost:4040/api/tunnels

Update webhook in bot.py

sudo docker build . -t female_lama

./rundocker.sh
