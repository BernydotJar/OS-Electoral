/* eslint-disable @typescript-eslint/no-require-imports */
"use strict";

const safeModule = require("brace-expansion-safe");
const expand =
  typeof safeModule === "function"
    ? safeModule
    : safeModule.expand ?? safeModule.default;

if (typeof expand !== "function") {
  throw new TypeError("brace-expansion 5.0.8 did not expose an expansion function");
}

module.exports = expand;
module.exports.expand = expand;
