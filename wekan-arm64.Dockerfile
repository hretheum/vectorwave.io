FROM --platform=linux/arm64/v8 ubuntu:22.04 AS build

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git ca-certificates python3 make g++ curl build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /build

# Install Meteor (compatible with Wekan)
RUN curl https://install.meteor.com/ | sed s/--progress-bar/-sL/g | /bin/sh
ENV PATH=/root/.meteor:$PATH \
    METEOR_ALLOW_SUPERUSER=1

# Fetch Wekan source
RUN git clone --depth=1 https://github.com/wekan/wekan.git .

# Build server bundle
RUN meteor npm ci && meteor build /bundle --directory

FROM --platform=linux/arm64/v8 ubuntu:22.04
ENV MONGO_URL=mongodb://wekandb:27017/wekan \
    ROOT_URL=http://localhost:8090 \
    PORT=8080 \
    WITH_API=true
WORKDIR /app
COPY --from=build /bundle/bundle /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nodejs npm ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app/programs/server
RUN npm install --production --no-audit --no-fund
WORKDIR /app
EXPOSE 8080
CMD ["node","main.js"]
