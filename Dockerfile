# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

WORKDIR /app

COPY . /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r /app/requirements.txt

ENTRYPOINT ["python3"]
CMD ["server.py"]

FROM builder as dev-envs

RUN <<EOF
apk update
apk add git bash
EOF

RUN <<EOF
addgroup -S docker
adduser -S --shell /bin/bash --ingroup docker vscode
EOF

COPY --from=gloursdocker/docker / /

