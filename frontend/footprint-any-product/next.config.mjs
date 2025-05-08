/** @type {import('next').NextConfig} */

const nextConfig = {
  // Environment variables are handled automatically when prefixed with NEXT_PUBLIC_
  // so we don't need to manually expose them here
  
  // Configure webpack to handle Node.js modules
  webpack: (config) => {
    // Add a fallback for Node.js specific modules
    config.resolve.fallback = {
      ...config.resolve.fallback,
      "async_hooks": false,
      "fs": false,
      "path": false,
      "os": false,
      "crypto": false,
      "stream": false,
      "http": false,
      "https": false,
      "zlib": false
    };
    
    return config;
  },
  
  // Ignore BAML client files to prevent build errors
  transpilePackages: ['@boundaryml/baml']
};

export default nextConfig;