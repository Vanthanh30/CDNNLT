# Sử dụng Node.js image nhẹ nhất
FROM node:20-alpine

# Cài đặt thư mục làm việc
WORKDIR /app

# Copy các file quản lý thư viện và cài đặt
COPY package.json package-lock.json* ./
RUN npm install

# Copy toàn bộ source code
COPY . .

# Mở cổng 5173 (Cổng mặc định của Vite)
EXPOSE 5173

# Chạy server ở chế độ dev và mở kết nối ra ngoài (--host)
CMD ["npm", "run", "dev", "--", "--host"]