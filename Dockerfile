FROM opsdroid/opsdroid:v0.25.0

#RUN adduser -D -g '' opsdroid

COPY skills /app/skills

#USER opsdroid
