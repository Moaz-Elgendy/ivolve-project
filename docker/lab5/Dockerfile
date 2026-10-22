
FROM node:26.12.1-slim

ENV NODE_ENV=production

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./

RUN if [ -f package-lock.json ]; then \
        npm ci --omit=dev --no-audit --no-fund; \
    else \
        npm install --omit=dev --no-audit --no-fund; \
    fi \
    && npm cache clean --force

COPY --chown=node:node app.js ./

USER node

EXPOSE 3000

CMD ["npm", "start"]

