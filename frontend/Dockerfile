FROM node:20-slim AS deps

WORKDIR /app

COPY package.json ./
RUN npm install

FROM deps AS dev

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
