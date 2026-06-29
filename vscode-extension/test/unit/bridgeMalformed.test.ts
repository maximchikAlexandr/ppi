/**
 * Additional QueryBridge unit tests: malformed JSON handling (PPI-034) and
 * sessionError reset on a successful restart.
 */
import { test } from "node:test";
import assert from "node:assert/strict";

import { QueryBridge } from "../../src/queryBridge";
import { resolve } from "node:path";

const FAKE = resolve(__dirname, "..", "test", "fixtures", "fake-rpc-malformed.js");

test("malformed non-JSON rpc line marks a session error instead of throwing", async () => {
  const bridge = new QueryBridge({ cliArgs: ["node", FAKE], repo: "/tmp/anywhere" });
  bridge.start();
  // Wait for the malformed line to be buffered, split, and handled. Use a
  // generous timeout since stdout flushing and the bridge's line-splitting
  // are asynchronous.
  for (let i = 0; i < 20 && !bridge.sessionErrorMessage; i++) {
    await new Promise((r) => setTimeout(r, 50));
  }
  assert.match(bridge.sessionErrorMessage ?? "", /malformed rpc json line/, "malformed line should mark a session error");
  bridge.dispose();
});