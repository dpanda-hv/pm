import { expect, test } from "@playwright/test";

test("requires login at root and allows valid login", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /sign in to kanban/i })).toBeVisible();

  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /^sign in$/i }).click();

  await expect(page.getByRole("heading", { name: /kanban studio/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /log out/i })).toBeVisible();
});

test("rejects invalid credentials", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /sign in to kanban/i })).toBeVisible();

  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: /^sign in$/i }).click();

  await expect(page.getByText(/invalid credentials/i)).toBeVisible();
  await expect(page.getByRole("heading", { name: /sign in to kanban/i })).toBeVisible();
});

test("logout returns user to login screen", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /^sign in$/i }).click();

  await expect(page.getByRole("heading", { name: /kanban studio/i })).toBeVisible();
  await page.getByRole("button", { name: /log out/i }).click();

  await expect(page.getByRole("heading", { name: /sign in to kanban/i })).toBeVisible();
});
