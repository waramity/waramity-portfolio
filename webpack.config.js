const path = require("path");

module.exports = {
  mode: "development", // Set it to 'development' or 'production' as needed.
  entry: "./src/index.tsx",
  output: {
    filename: "index.js",
    publicPath: path.resolve(__dirname, "app/static"), // instead of publicPath: '/build/'
    path: path.resolve(__dirname, "app/static"),
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js", ".scss", ".css"],
  },
  devServer: {
    hot: true,
    liveReload: true,
    static: {
      directory: path.join(__dirname, "app/static"),
    },
    watchFiles: ["./src/*.js", path.join(__dirname, "app/static")],
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
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
};
