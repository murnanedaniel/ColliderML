import { defineConfig } from 'vitepress'

const config = defineConfig({
  title: 'ColliderML',
  description: 'A modern machine learning library for high-energy physics data analysis',
  lang: 'en-US',
  lastUpdated: true,
  // Set base for GitHub Pages project site if repo is 'colliderml'.
  // If using a custom domain or org/user site, adjust to '/'
  base: '/colliderml/',
  
  themeConfig: {
    logo: '/logo.png',
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'API', link: '/api/core' },
      { text: 'GitHub', link: 'https://github.com/murnanedaniel/colliderml' }
    ],
    sidebar: {
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Introduction', link: '/guide/introduction' },
            { text: 'Installation', link: '/guide/installation' },
            { text: 'Quick Start', link: '/guide/quickstart' },
          ]
        },
        {
          text: 'Core Concepts',
          items: [
            { text: 'Data Management', link: '/guide/data-management' },
            { text: 'Machine Learning', link: '/guide/machine-learning' },
            { text: 'Visualization', link: '/guide/visualization' },
          ]
        }
      ],
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Core', link: '/api/core' },
            { text: 'IO', link: '/api/io' },
            { text: 'Utils', link: '/api/utils' },
          ]
        }
      ]
    },
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2023-present ColliderML Contributors'
    }
  },
  
  vite: {
    server: {
      proxy: {
        '/nersc': {
          target: 'https://portal.nersc.gov/cfs/m4958/ColliderML',
          changeOrigin: true,
          rewrite: (path: string) => path.replace(/^\/nersc/, '')
        }
      }
    },
    resolve: {
      alias: {
        '@components': './components'
      }
    },
    plugins: []
  },
  
  vue: {
    template: {
      compilerOptions: {
        isCustomElement: (tag: string) => tag.includes('-')
      }
    }
  }
})

if (config.vite) {
  config.vite.optimizeDeps = {
    include: ['vue'],
    exclude: ['vitepress']
  }
}

export default config 