from python:latest

RUN pip install discord schedule python-dotenv

COPY . .

ARG DOCKER_DISCORD_TOKEN
ENV DISCORD_TOKEN=$DOCKER_DISCORD_TOKEN
ENTRYPOINT python triviabot.py
