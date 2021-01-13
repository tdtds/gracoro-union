# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.154.2/containers/ruby/.devcontainer/base.Dockerfile

# [Choice] Ruby version: 2, 2.7, 2.6, 2.5
ARG VARIANT="2"
FROM mcr.microsoft.com/vscode/devcontainers/ruby:0-${VARIANT}
LABEL maintainer "@tdtds <t@tdtds.jp>"

# [Option] Install Node.js
ARG INSTALL_NODE="true"
ARG NODE_VERSION="lts/*"
RUN if [ "${INSTALL_NODE}" = "true" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# [Optional] Uncomment this section to install additional OS packages.
RUN wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian10-x86_64-100.2.1.deb \
    && apt-get install ./mongodb-database-tools-debian10-x86_64-100.2.1.deb \
    && rm mongodb-database-tools-debian10-x86_64-100.2.1.deb \
    && curl -s https://cli-assets.heroku.com/install.sh | sh

# [Optional] Uncomment this line to install additional gems.

# [Optional] Uncomment this line to install global node packages.
EXPOSE 9292
