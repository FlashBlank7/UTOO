import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  basePath: '/lilies',
  allowedDevOrigins: ['127.0.0.1'],
}

export default nextConfig
