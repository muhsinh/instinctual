import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  experimental: { optimizePackageImports: ["framer-motion"] },
};

export default config;
