FROM ghcr.io/opsdroid/opsdroid:v0.30.0

#RUN adduser -D -g '' opsdroid

COPY skills /app/skills

#USER opsdroid
