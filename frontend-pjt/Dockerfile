# Bond-EZ 프론트엔드 (Vite 개발 서버)
# 단독 실행보다는 저장소 루트의 docker-compose.yml 사용을 권장
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
