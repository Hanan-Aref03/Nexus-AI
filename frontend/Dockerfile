FROM node:22-slim

WORKDIR /app

COPY package*.json /app/

RUN npm ci

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
