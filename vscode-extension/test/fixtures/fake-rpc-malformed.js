// Fake `ppi rpc` that writes a malformed non-JSON line to stdout, then idles.
process.stdout.write("this is not valid JSON\n");
process.stdin.resume();
process.stdin.setEncoding("utf-8");
process.stdin.on("data", () => {
  // idle
});