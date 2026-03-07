/** @type {import('next').NextConfig} */
const nextConfig = {
  // In AWS mode, NEXT_PUBLIC_API_URL points to API Gateway — no proxy needed.
  // In local mode, proxy /api/* to the local FastAPI server.
  async rewrites() {
    if (process.env.NEXT_PUBLIC_API_URL) {
      return []; // Direct calls to API Gateway
    }
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
  // Enable static export for S3 deployment (set via NEXT_PUBLIC_STATIC_EXPORT=true)
  ...(process.env.NEXT_PUBLIC_STATIC_EXPORT === "true" ? { output: "export" } : {}),
};

module.exports = nextConfig;
