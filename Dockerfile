FROM opsdroid/opsdroid:v0.17.0

RUN adduser -D -g '' opsdroid

COPY skills /app/skills

USER opsdroid
