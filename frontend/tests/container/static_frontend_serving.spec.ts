import { expect, test } from "@playwright/test";

test("serves exported kanban HTML at root consistently", async ({ request }) => {
  const firstResponse = await request.get("/");
  expect(firstResponse.ok()).toBeTruthy();
  const firstHtml = await firstResponse.text();
  expect(firstHtml).toContain("Checking session");

  const secondResponse = await request.get("/");
  expect(secondResponse.ok()).toBeTruthy();
  const secondHtml = await secondResponse.text();
  expect(secondHtml).toContain("Checking session");
});

test("serves static assets referenced by exported root HTML", async ({ request }) => {
  const rootResponse = await request.get("/");
  expect(rootResponse.ok()).toBeTruthy();

  const rootHtml = await rootResponse.text();
  const match = rootHtml.match(/(?:href|src)=\"([^\"]*_next\/static\/[^\"]+)\"/);
  expect(match).not.toBeNull();

  const assetPath = match![1];
  const assetResponse = await request.get(assetPath);
  expect(assetResponse.ok()).toBeTruthy();
});
