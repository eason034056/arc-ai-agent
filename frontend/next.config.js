/** @type {import('next').NextConfig} */
const nextConfig = {
  // 啟用 standalone 輸出模式（用於 Docker）
  output: 'standalone',
  
  // 嚴格模式
  reactStrictMode: true,
  
  // 環境變數
  env: {
    NEXT_PUBLIC_BACKEND_BASE_URL: process.env.NEXT_PUBLIC_BACKEND_BASE_URL,
  },

  // API 代理（開發時避免 CORS）
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

