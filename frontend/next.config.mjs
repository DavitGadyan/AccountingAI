/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["react-force-graph-3d", "three"],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.API_BASE_URL ?? "http://localhost:8000"}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
