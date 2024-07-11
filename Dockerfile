FROM ghcr.io/opsdroid/opsdroid:v0.29.0

#RUN adduser -D -g '' opsdroid

COPY skills /app/skills

#USER opsdroid
