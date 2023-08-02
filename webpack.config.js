const path = require("path");

module.exports = {
  mode: "development", // Set it to 'development' or 'production' as needed.
  entry: "./src/index.js",
  output: {
    filename: "index.js",
    publicPath: "app/static", // instead of publicPath: '/build/'
    path: path.resolve(__dirname, "app/static"),
  },
  devServer: {
    liveReload: true,
    static: {
      directory: path.join(__dirname, "app/static"),
    },
    watchFiles: ["src/*.js", "app/static/*.js"],
    compress: true,
    port: 9000,
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: ["babel-loader"],
      },
      {
        test: /\.s[ac]ss$/i,
        use: [
          // Creates `style` nodes from JS strings
          "style-loader",
          // Translates CSS into CommonJS
          "css-loader",
          // Compiles Sass to CSS
          "sass-loader",
        ],
      },
    ],
  },
};
