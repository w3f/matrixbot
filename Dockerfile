FROM opsdroid/opsdroid:v0.26.0

#RUN adduser -D -g '' opsdroid

COPY skills /app/skills

#USER opsdroid
