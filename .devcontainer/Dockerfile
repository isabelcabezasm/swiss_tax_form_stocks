FROM mcr.microsoft.com/devcontainers/base:jammy AS base

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

ENV UV_LINK_MODE="copy"
COPY --from=ghcr.io/astral-sh/uv:0.7.15 /uv /uvx /bin/

FROM base AS devcontainer

# Install the Microsoft Linux Repository
RUN curl -sSL -O https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb && \
    sudo dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    sudo apt-get update

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    shellcheck
