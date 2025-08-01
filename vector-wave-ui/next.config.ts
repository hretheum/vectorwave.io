import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  serverExternalPackages: ["@aws-sdk", "@smithy"],
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        path: false,
        os: false,
        stream: false,
        buffer: false,
      };
    }
    
    // Ignore AWS SDK modules that cause issues
    config.resolve.alias = {
      ...config.resolve.alias,
      "@aws-sdk/credential-provider-sso": false,
      "@smithy/shared-ini-file-loader": false,
    };
    
    return config;
  },
};

export default nextConfig;
