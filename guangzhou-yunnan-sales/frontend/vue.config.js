const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  chainWebpack: config => {
    config.plugin('copy').tap(args => {
      if (args[0] && args[0].patterns) {
        args[0].patterns.forEach(pattern => {
          if (!pattern.globOptions) pattern.globOptions = {}
          if (!pattern.globOptions.ignore) pattern.globOptions.ignore = []
          pattern.globOptions.ignore.push('**/index.html')
        })
      }
      return args
    })
  },
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
