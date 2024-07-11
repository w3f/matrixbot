FROM ghcr.io/opsdroid/opsdroid:v0.29.1

#RUN adduser -D -g '' opsdroid

COPY skills /app/skills

#USER opsdroid
