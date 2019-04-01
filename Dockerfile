FROM opsdroid/opsdroid:v0.14.1

RUN adduser -D -g '' opsdroid

COPY skills /app/skills

USER opsdroid
